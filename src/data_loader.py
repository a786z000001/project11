import yfinance as yf
import pandas as pd

def load_data(stocks, start_date, end_date):
    frames = []

    for stock in stocks:
        df = yf.download(stock, start=start_date, end=end_date, progress=False)[['Close', 'Volume']].copy()
        df.columns = [f"{stock}_close", f"{stock}_volume"]
        frames.append(df)

    combined = pd.concat(frames, axis=1)
    
    # 🔥 FIX: Forward-fill small gaps (like trading halts), but keep pre-IPO days as NaN
    combined = combined.ffill()
    
    # 🔥 FIX: Only drop a row if the ENTIRE market was closed (e.g., weekends/holidays)
    combined = combined.dropna(how='all')
    
    return combined
