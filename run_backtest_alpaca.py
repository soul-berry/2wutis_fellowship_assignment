import os
import pandas as pd

from src.strategy.adaptive_vol_regime import AdaptiveVolRegimeStrategy
from src.backtest.backtester import load_historical_from_alpaca, run_backtest
from src.backtest.metrics import compute_performance_stats


def main():
    symbol = "SPY"
    start = "2025-04-01"
    end = "2026-04-02"

    df_raw = load_historical_from_alpaca(symbol, start, end)

    strategy = AdaptiveVolRegimeStrategy(
        k_base=2.0,
        noise_window=15,
        train_ratio=0.7,
        cost_bps=1.0,
    )

    data_ext, daily_pnl, train_dates, test_dates = run_backtest(df_raw, strategy)

    train_daily = daily_pnl[daily_pnl.index.isin(train_dates)]
    test_daily = daily_pnl[daily_pnl.index.isin(test_dates)]

    overall_stats = compute_performance_stats(daily_pnl)
    train_stats = compute_performance_stats(train_daily)
    test_stats = compute_performance_stats(test_daily)

    print("Overall stats:", overall_stats)
    print("Train stats:", train_stats)
    print("Test stats:", test_stats)

    out = pd.DataFrame(
        {
            "date": daily_pnl.index,
            "daily_pnl": daily_pnl.values,
        }
    )
    out["equity_curve"] = (1 + out["daily_pnl"]).cumprod()

    os.makedirs("output", exist_ok=True)
    out.to_csv("output/daily_pnl_equity_alpaca.csv", index=False)
    print("Saved Alpaca backtest results to output/daily_pnl_equity_alpaca.csv")


if __name__ == "__main__":
    main()