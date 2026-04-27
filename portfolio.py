import pandas as pd
import numpy as np

def build_portfolio(df, features, signals, top_k=5, transaction_cost=0.0010):
    
    # 1. Extract Price Returns
    price_cols = [col for col in df.columns if "_close" in col]
    returns = df[price_cols].pct_change().fillna(0)
    
    # 2. Align Signals Exactly to returns
    signals.columns = [c.split("_")[0] + "_close" for c in signals.columns]
    
    # 🔥 BULLETPROOF FIX 1: Only align columns that actually exist to prevent KeyErrors
    valid_cols = [c for c in price_cols if c in signals.columns]
    signals = signals[valid_cols]
    returns = returns[valid_cols]
    price_cols = valid_cols 
    
    # 3. Shift signals to prevent Look-Ahead Bias
    target_weights = signals.shift(1).fillna(0)
    
    # 4. Apply TOP_K Filter (Vectorized)
    ranks = target_weights.rank(axis=1, method='first', ascending=False)
    target_weights = target_weights.where(ranks <= top_k, 0.0)
    
    # 5. Volatility Risk Parity Sizing
    vol_cols = [f"{c.split('_')[0]}_close_volatility" for c in price_cols]
    
    # Safely extract volatility, fallback to 1.0 if column is missing
    available_vols = [v for v in vol_cols if v in features.columns]
    vols = features[available_vols].shift(1).fillna(1.0)
    
    # Rename volatility columns back to price columns for clean math alignment
    vols.columns = [c.replace("_volatility", "") for c in vols.columns]
    
    # Inverse vol (only for the Top K selected stocks)
    inv_vols = 1.0 / (vols + 1e-8)
    inv_vols = inv_vols.where(target_weights > 0, 0.0)
    
    # Normalize weights so they sum to 1.0 each day
    final_weights = inv_vols.div(inv_vols.sum(axis=1), axis=0).fillna(0)
    
    # 6. Weekly Rebalancing Logic (Safest approach)
    # 🔥 BULLETPROOF FIX 2: Use .loc instead of .where() to avoid broadcast crashes
    actual_weights = final_weights.copy()
    
    # Force index to datetime just in case, then find non-Fridays
    idx_dt = pd.to_datetime(actual_weights.index)
    is_not_friday = idx_dt.dayofweek != 4
    
    # Wipe Mon-Thu to NaN, then forward-fill the Friday weights
    actual_weights.loc[is_not_friday, :] = np.nan
    actual_weights = actual_weights.ffill().fillna(0)
    
    # 7. Transaction Cost Modeling (Turnover)
    weight_changes = actual_weights.diff().fillna(0).abs()
    daily_turnover = weight_changes.sum(axis=1)
    daily_tc = daily_turnover * transaction_cost
    
    # 8. Final Portfolio Returns calculation
    gross_returns = (actual_weights * returns).sum(axis=1)
    net_returns = gross_returns - daily_tc
    
    # Build Output DataFrame
    portfolio = pd.DataFrame(index=df.index)
    portfolio["portfolio_returns"] = net_returns
    portfolio["cum_returns"] = (1 + portfolio["portfolio_returns"]).cumprod()
    portfolio["turnover"] = daily_turnover
    
    return portfolio