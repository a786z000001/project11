import pandas as pd
import numpy as np

def generate_signals(features, weights=None):
    # Default weights if none are provided
    if weights is None:
        weights = {
            "mom_vol_adj": 0.4,
            "reversal_5": 0.2,
            "trend": 0.3,
            "rsi": -0.1,        # Fade extreme RSI
            "bb_width": 0.0     # Available to optimize later
        }

    signals = pd.DataFrame(index=features.index)
    
    # Extract stock names cleanly
    stocks = sorted(list(set([c.split("_")[0] for c in features.columns if "_close" in c])))
    
    alpha = pd.DataFrame(index=features.index)

    for stock in stocks:
        close_prefix = f"{stock}_close"
        signal = 0

        # Dynamically apply weights to existing features
        if f"{close_prefix}_mom_vol_adj" in features:
            signal += weights.get("mom_vol_adj", 0) * features[f"{close_prefix}_mom_vol_adj"]
        
        if f"{close_prefix}_reversal_5" in features:
            signal += weights.get("reversal_5", 0) * features[f"{close_prefix}_reversal_5"]
            
        if f"{close_prefix}_trend" in features:
            signal += weights.get("trend", 0) * features[f"{close_prefix}_trend"]

        if f"{close_prefix}_rsi" in features:
            # Normalize RSI around 0 (RSI is 0-100, we center it at 50)
            centered_rsi = (features[f"{close_prefix}_rsi"] - 50) / 50 
            signal += weights.get("rsi", 0) * centered_rsi
            
        if f"{close_prefix}_bb_width" in features:
            signal += weights.get("bb_width", 0) * features[f"{close_prefix}_bb_width"]

        alpha[stock] = signal

    # =======================
    # CROSS-SECTIONAL RANK
    # =======================
    ranked = alpha.rank(axis=1, pct=True)
    
    # Convert to centered signals
    signals = ranked - 0.5

    # =======================
    # MARKET NEUTRALIZATION
    # =======================
    signals = signals.sub(signals.mean(axis=1), axis=0)

    return signals.fillna(0)
