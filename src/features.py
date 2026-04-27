import pandas as pd
import numpy as np

def calculate_rsi(prices, window=14):
    """Helper function to calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / (loss + 1e-8)
    return 100 - (100 / (1 + rs))

def generate_features(df):
    feature_df = pd.DataFrame(index=df.index)

    for col in df.columns:
        col_str = str(col).lower()

        # =======================
        # PRICE FEATURES
        # =======================
        if "close" in col_str:
            price = df[col]
            returns = price.pct_change()

            # Basic returns
            feature_df[f"{col}_returns"] = returns

            # Momentum (multi-horizon)
            feature_df[f"{col}_mom_5"] = returns.rolling(5).mean()
            feature_df[f"{col}_mom_20"] = returns.rolling(20).mean()

            # Volatility-adjusted momentum
            vol = returns.rolling(20).std()
            feature_df[f"{col}_mom_vol_adj"] = feature_df[f"{col}_mom_20"] / (vol + 1e-8)

            # Mean reversion (short-term)
            feature_df[f"{col}_reversal_5"] = -returns.rolling(5).mean()

            # Trend strength (MA ratio)
            ma_short = price.rolling(5).mean()
            ma_long = price.rolling(20).mean()
            feature_df[f"{col}_trend"] = (ma_short / ma_long) - 1

            # Volatility itself
            feature_df[f"{col}_volatility"] = vol

            # 🔥 NEW: RSI (Momentum/Overbought/Oversold)
            feature_df[f"{col}_rsi"] = calculate_rsi(price, window=14)

            # 🔥 NEW: Bollinger Band Width (Volatility compression)
            ma_20 = price.rolling(20).mean()
            std_20 = price.rolling(20).std()
            upper_band = ma_20 + (std_20 * 2)
            lower_band = ma_20 - (std_20 * 2)
            feature_df[f"{col}_bb_width"] = (upper_band - lower_band) / (ma_20 + 1e-8)

        # =======================
        # VOLUME FEATURES
        # =======================
        elif "volume" in col_str:
            vol = df[col]
            vol_avg = vol.rolling(20).mean()
            feature_df[f"{col}_vol_spike"] = vol / (vol_avg + 1e-8)

    # =======================
    # CROSS-SECTIONAL NORMALIZATION (CRITICAL)
    # =======================
    feature_df = feature_df.copy()

    for col in feature_df.columns:
        feature_df[col] = (
            feature_df[col] - feature_df[col].rolling(60).mean()
        ) / (feature_df[col].rolling(60).std() + 1e-8)

    feature_df = feature_df.dropna(how='all')

    return feature_df
