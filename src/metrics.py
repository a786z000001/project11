import numpy as np
import pandas as pd


def calculate_metrics(portfolio: pd.DataFrame):
    if len(portfolio) == 0:
        return 0.0, 0.0, 1.0
    returns = portfolio["portfolio_returns"].dropna()

    if returns.std() == 0:
        sharpe = 0.0
    else:
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

    drawdown = (portfolio["cum_returns"] / portfolio["cum_returns"].cummax() - 1).min()
    total_return = portfolio["cum_returns"].iloc[-1]

    return sharpe, drawdown, total_return
