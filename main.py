import pandas as pd
import matplotlib.pyplot as plt
from config import START_DATE, END_DATE, TRANSACTION_COST, TOP_K
from src.universe import STOCKS
from src.data_loader import load_data
from src.features import generate_features
from src.signals import generate_signals
from src.portfolio import build_portfolio
from src.metrics import calculate_metrics
from src.optimize import run_grid_search

def main():
    print("Loading data and generating features...")
    df_raw = load_data(STOCKS, START_DATE, END_DATE)
    
    # 🔥 STEP 1: KILL DUPLICATES AT THE SOURCE
    df_raw = df_raw[~df_raw.index.duplicated(keep='last')]
    
    features_raw = generate_features(df_raw)
    features_raw = features_raw[~features_raw.index.duplicated(keep='last')]
    
    # Align dates
    df = df_raw.loc[features_raw.index]
    features = features_raw.copy()

    # Walk-Forward parameters
    train_size = 252 * 2  
    step_size = 63        
    
    out_of_sample_returns = []
    
    print(f"\nStarting Walk-Forward Optimization... Total days: {len(df)}")
    
    for start_idx in range(0, len(df) - train_size, step_size):
        end_train_idx = start_idx + train_size
        end_test_idx = min(end_train_idx + step_size, len(df))
        
        if end_train_idx >= len(df): break

        df_train = df.iloc[start_idx:end_train_idx]
        features_train = features.iloc[start_idx:end_train_idx]
        
        df_test = df.iloc[end_train_idx:end_test_idx]
        features_test = features.iloc[end_train_idx:end_test_idx]
        
        if len(df_test) == 0: continue

        print(f"Testing: {df_test.index[0].date()} to {df_test.index[-1].date()}")
        
        best_params = run_grid_search(df_train, features_train)
        best_weights = best_params.get("weights")
        best_k = best_params.get("top_k", TOP_K)
        
        signals_test = generate_signals(features_test, weights=best_weights)
        
        portfolio_test = build_portfolio(
            df=df_test,
            features=features_test,
            signals=signals_test,
            top_k=best_k,
            transaction_cost=TRANSACTION_COST
        )
        
        out_of_sample_returns.append(portfolio_test["portfolio_returns"])

    # 🔥 STEP 2: STITCH AND PURGE OVERLAPS
    final_returns_series = pd.concat(out_of_sample_returns)
    final_returns_series = final_returns_series[~final_returns_series.index.duplicated(keep='last')]
    
    final_portfolio = final_returns_series.to_frame(name="portfolio_returns")
    final_portfolio["cum_returns"] = (1 + final_portfolio["portfolio_returns"]).cumprod()
    
    sharpe, drawdown, total_return = calculate_metrics(final_portfolio)

    print("\n=== FINAL RESULTS ===")
    print(f"Sharpe: {sharpe:.2f} | Return: {(total_return - 1):.2%}")

    # 🔥 STEP 3: ALIGN BENCHMARK WITHOUT DUPLICATES
    # We slice df_raw using the unique index of our final_portfolio
    plot_results(df_raw.reindex(final_portfolio.index), final_portfolio)

def plot_results(df_benchmark, portfolio):
    # Benchmark Calculation
    price_cols = [col for col in df_benchmark.columns if "_close" in col]
    # Ensure benchmark data is also clean
    bench_df = df_benchmark[price_cols].pct_change().fillna(0)
    ew_benchmark_returns = bench_df.mean(axis=1)
    ew_cum_returns = (1 + ew_benchmark_returns).cumprod()

    plt.figure(figsize=(12, 6))
    plt.plot(portfolio.index, portfolio["cum_returns"], label="Alpha Strategy (WFO)", color="#1f77b4", linewidth=2)
    plt.plot(portfolio.index, ew_cum_returns, label="Equal-Weight Benchmark", color="#ff7f0e", linestyle="--", linewidth=2)
    plt.title("Out-of-Sample Walk-Forward Performance")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

if __name__ == "__main__":
    main()