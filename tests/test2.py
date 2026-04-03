import itertools
import os

import numpy as np
import pandas as pd

from src.strategy.adaptive_vol_regime import AdaptiveVolRegimeStrategy
import inspect
import src.strategy.adaptive_vol_regime as mod

print("Strategy module file:", mod.__file__)
print("Has run:", hasattr(AdaptiveVolRegimeStrategy, "run"))

from src.data.transforms import prepare_intraday_features
from src.strategy.adaptive_vol_regime import AdaptiveVolRegimeStrategy

def run_single_config(
    df_raw: pd.DataFrame,
    k_base: float,
    noise_window: int,
    train_ratio: float,
    cost_bps: float,
) -> dict:
    """
    Run the full strategy for one parameter configuration and return a metrics dict.
    """
    # Prepare features from raw bars
    df = df_raw.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["time"] = df["timestamp"].dt.strftime("%H:%M:%S")
    df = prepare_intraday_features(df)

    # Instantiate strategy with given parameters
    strategy = AdaptiveVolRegimeStrategy(
        k_base=k_base,
        noise_window=noise_window,
        train_ratio=train_ratio,
        cost_bps=cost_bps,
    )

    data_ext, daily_rv, train_dates, test_dates = strategy.run(df)

    # Normalize date types for matching
    data_ext["date"] = pd.to_datetime(data_ext["date"]).dt.normalize()
    train_dates = pd.to_datetime(train_dates).normalize()
    test_dates = pd.to_datetime(test_dates).normalize()

    # Core diagnostics
    days_with_entry_rate = (
        data_ext.groupby("date")["first_signal"]
        .apply(lambda s: s.notna().any())
        .mean()
    )
    avg_pos_size = data_ext["pos_size"].mean()
    net_strategy_return = data_ext["strategy_ret_ext"].sum()
    avg_trades_per_day = (
        data_ext.groupby("date")["trade_ext"].sum().mean()
    )

    daily_pnl = (
        data_ext.groupby("date")["strategy_ret_ext"].sum()
    )

    # Overall stats
    overall_mean = daily_pnl.mean()
    overall_std = daily_pnl.std()
    overall_min = daily_pnl.min()
    overall_max = daily_pnl.max()
    overall_win_rate = (daily_pnl > 0).mean()

    # Train/test splits
    train_daily = daily_pnl[daily_pnl.index.isin(train_dates)]
    test_daily = daily_pnl[daily_pnl.index.isin(test_dates)]

    train_mean = train_daily.mean()
    test_mean = test_daily.mean()
    train_win_rate = (train_daily > 0).mean()
    test_win_rate = (test_daily > 0).mean()
    train_worst = train_daily.min()
    train_best = train_daily.max()
    test_worst = test_daily.min()
    test_best = test_daily.max()

    return {
        "k_base": k_base,
        "noise_window": noise_window,
        "train_ratio": train_ratio,
        "cost_bps": cost_bps,
        "days_with_entry_rate": days_with_entry_rate,
        "avg_pos_size": avg_pos_size,
        "net_strategy_return": net_strategy_return,
        "avg_trades_per_day": avg_trades_per_day,
        "overall_mean_daily_pnl": overall_mean,
        "overall_std_daily_pnl": overall_std,
        "overall_min_daily_pnl": overall_min,
        "overall_max_daily_pnl": overall_max,
        "overall_win_rate": overall_win_rate,
        "train_mean_daily_pnl": train_mean,
        "test_mean_daily_pnl": test_mean,
        "train_win_rate": train_win_rate,
        "test_win_rate": test_win_rate,
        "train_worst_day": train_worst,
        "train_best_day": train_best,
        "test_worst_day": test_worst,
        "test_best_day": test_best,
    }


def main():
    # 1) Load raw data once
    df_raw = pd.read_csv("output/historical_bars.csv")

    # 2) Define parameter grid
    k_base_grid = [1.8, 2.0, 2.2]
    noise_window_grid = [10, 15, 20]
    train_ratio_grid = [0.6, 0.7]
    cost_bps_grid = [0.5, 1.0]

    grid = list(
        itertools.product(
            k_base_grid,
            noise_window_grid,
            train_ratio_grid,
            cost_bps_grid,
        )
    )

    results = []

    print("Running parameter grid with", len(grid), "combinations...\n")

    # 3) Loop over grid
    for (
        k_base,
        noise_window,
        train_ratio,
        cost_bps,
    ) in grid:
        metrics = run_single_config(
            df_raw=df_raw,
            k_base=k_base,
            noise_window=noise_window,
            train_ratio=train_ratio,
            cost_bps=cost_bps,
        )
        results.append(metrics)

        # Compact on-screen summary
        print(
            f"k_base={k_base}, noise_window={noise_window}, "
            f"train_ratio={train_ratio}, cost_bps={cost_bps} | "
            f"test_mean={metrics['test_mean_daily_pnl']:.6f}, "
            f"overall_mean={metrics['overall_mean_daily_pnl']:.6f}, "
            f"days_entry={metrics['days_with_entry_rate']:.3f}, "
            f"avg_trades/day={metrics['avg_trades_per_day']:.3f}"
        )

    # 4) Save results as CSV
    results_df = pd.DataFrame(results)
    os.makedirs("output", exist_ok=True)
    out_path = "output/param_grid_results2.csv"
    results_df.to_csv(out_path, index=False)
    print("\nSaved grid results to", out_path)


if __name__ == "__main__":
    main()