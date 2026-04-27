import itertools
import pandas as pd
from src.signals import generate_signals
from src.portfolio import build_portfolio
from src.metrics import calculate_metrics

def run_grid_search(df_train, features_train):
    print("Starting Grid Search Optimization...")
    
    # Define the parameter grid to test
    weight_grids = [
        {"mom_vol_adj": 0.8, "reversal_5": 0.1, "trend": 0.1, "rsi": -0.2},
        {"mom_vol_adj": 0.2, "reversal_5": 0.6, "trend": 0.2, "rsi": -0.4}, # Reversal heavy
        {"mom_vol_adj": 0.5, "reversal_5": 0.0, "trend": 0.5, "rsi": 0.0},  # Pure trend
    ]
    top_k_options = [1, 2, 3] # Test different portfolio concentrations
    
    best_sharpe = -999
    best_params = {}

    # Iterate through all combinations
    for weights, top_k in itertools.product(weight_grids, top_k_options):
        
        # 1. Generate Signals with specific weights
        signals_train = generate_signals(features_train, weights=weights)
        
        # 2. Build Portfolio
        portfolio = build_portfolio(
            df=df_train, 
            features=features_train, 
            signals=signals_train, 
            top_k=top_k, 
            transaction_cost=0.0005
        )
        
        # 3. Calculate Metrics
        sharpe, drawdown, total_return = calculate_metrics(portfolio)
        
        print(f"Tested: K={top_k}, Weights={weights} | Sharpe: {sharpe:.2f}")
        
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = {"weights": weights, "top_k": top_k}

    print("\n=== OPTIMIZATION COMPLETE ===")
    print(f"Best Train Sharpe: {best_sharpe:.2f}")
    print(f"Best Parameters: {best_params}")
    
    return best_params
