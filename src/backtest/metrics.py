import numpy as np
import pandas as pd


def compute_performance_stats(
    daily_pnl: pd.Series,
    trading_days: int = 252,
) -> dict:
    mean_daily = daily_pnl.mean()
    std_daily = daily_pnl.std()
    ann_return = mean_daily * trading_days
    ann_vol = std_daily * np.sqrt(trading_days)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

    return {
        "mean_daily": mean_daily,
        "std_daily": std_daily,
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
    }