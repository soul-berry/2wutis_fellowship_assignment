from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "timestamp",
    "date",
    "time",
    "minute",
    "close",
    "open_price",
    "ret",
    "move_from_open",
]


@dataclass
class AdaptiveVolRegimeStrategy:
    k_base: float = 2
    lam: float = 0.15
    rv_window: int = 20
    noise_window: int = 15
    train_ratio: float = 0.7
    max_size: float = 2.0
    cost_bps: float = 2

    def validate_columns(self, df: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def compute_daily_rv(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list, list]:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        daily_rv = (
            df.groupby("date", as_index=False)["ret"]
            .agg(lambda x: x.std(ddof=1) * np.sqrt(390))
            .rename(columns={"ret": "daily_rv"})
            .sort_values("date")
        )

        daily_rv["prev_rv"] = daily_rv["daily_rv"].shift(1)
        daily_rv["rv_roll_mean"] = daily_rv["prev_rv"].rolling(self.rv_window).mean()
        daily_rv["rv_roll_sd"] = daily_rv["prev_rv"].rolling(self.rv_window).std()
        daily_rv["vol_zscore"] = (
            (daily_rv["prev_rv"] - daily_rv["rv_roll_mean"]) /
            (daily_rv["rv_roll_sd"] + 1e-8)
        )
        daily_rv["k_adaptive"] = self.k_base * np.exp(self.lam * daily_rv["vol_zscore"])

        dates = list(daily_rv["date"].unique())
        n_train = int(np.floor(len(dates) * self.train_ratio))
        train_dates = dates[:n_train]
        test_dates = dates[n_train:]

        return daily_rv, train_dates, test_dates

    def compute_position_sizing(
        self,
        daily_rv: pd.DataFrame,
        train_dates: list,
    ) -> pd.DataFrame:
        daily_rv = daily_rv.copy()

        target_vol = (
            daily_rv.loc[daily_rv["date"].isin(train_dates), "prev_rv"]
            .median()
        )

        daily_rv["pos_size"] = np.minimum(
            target_vol / (daily_rv["prev_rv"] + 1e-8),
            self.max_size,
        )

        # New: volatility cap – if daily_rv is above some multiple, shrink position
        vol_cap = 2.0  # e.g. cap days with prev_rv > 2 * target_vol
        high_vol_mask = daily_rv["prev_rv"] > vol_cap * target_vol
        daily_rv.loc[high_vol_mask, "pos_size"] *= 0.5  # or any factor < 1

        return daily_rv

    def build_noise_bands(
        self,
        df: pd.DataFrame,
        daily_rv: pd.DataFrame
    ) -> pd.DataFrame:
        noise_ext = (
            df.groupby(["minute", "date"], as_index=False)["move_from_open"]
            .mean()
            .rename(columns={"move_from_open": "move"})
            .sort_values(["minute", "date"])
        )

        noise_ext["avg_move_ext"] = (
            noise_ext.groupby("minute")["move"]
            .transform(lambda s: s.rolling(self.noise_window).mean())
        )

        out = (
            df.merge(
                daily_rv[["date", "k_adaptive", "pos_size", "vol_zscore"]],
                on="date",
                how="left"
            )
            .merge(
                noise_ext[["date", "minute", "avg_move_ext"]],
                on=["date", "minute"],
                how="left"
            )
        )

        out["upper_ext"] = out["open_price"] * (1 + out["k_adaptive"] * out["avg_move_ext"])
        out["lower_ext"] = out["open_price"] * (1 - out["k_adaptive"] * out["avg_move_ext"])

        out = out.dropna(subset=["avg_move_ext", "k_adaptive"]).copy()
        return out

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        print("generate_signals date dtype:", df["date"].dtype)
        df = df.copy()

        # Step 1: raw band-breach signal
        df["raw_signal"] = np.select(
            [df["close"] > df["upper_ext"], df["close"] < df["lower_ext"]],
            [1.0, -1.0],
            default=np.nan,
        )

        # Optional: time-of-day filter (only allow entries between 10:00 and 15:30)
        df["time_str"] = df["time"].astype(str)
        entry_mask = (df["time_str"] >= "10:00:00") & (df["time_str"] <= "15:30:00")
        df.loc[~entry_mask, "raw_signal"] = np.nan

        def first_touch(group: pd.DataFrame) -> pd.DataFrame:
            group = group.copy()
            group["first_signal"] = np.nan

            valid_idx = group.index[group["raw_signal"].notna()]
            if len(valid_idx) > 0:
                first_idx = valid_idx[0]
                group.loc[first_idx, "first_signal"] = group.loc[first_idx, "raw_signal"]

            group["base_position"] = group["first_signal"].ffill().fillna(0.0)

            group.loc[group["time"] == "16:00:00", "base_position"] = 0.0
            return group

        df = df.groupby("date", group_keys=False).apply(first_touch)

        if "base_position" not in df.columns:
            raise RuntimeError(
                "base_position missing after first_touch; "
                "check groupby('date') and time column."
            )

        df["position_ext"] = df["base_position"] * df["pos_size"]

        return df
    def apply_costs(self, df: pd.DataFrame) -> pd.DataFrame:
            df = df.copy()

            # Make sure 'date' is present; re-derive from timestamp if needed
            if "date" not in df.columns and "timestamp" in df.columns:
                df["date"] = pd.to_datetime(df["timestamp"]).dt.date

            cost_rate = self.cost_bps / 10000.0

            df["strategy_ret_ext"] = df["position_ext"] * df["ret"]
            df["trade_ext"] = (
                df.groupby("date")["position_ext"]
                .diff()
                .abs()
                .fillna(df["position_ext"].abs())
            )
            df["cost_ext"] = df["trade_ext"] * cost_rate
            df["strategy_ret_ext"] = df["strategy_ret_ext"] - df["cost_ext"]

            return df

    def run(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list, list]:
        df = df.copy()
        self.validate_columns(df)

        # Ensure date is a pandas datetime (not raw Python date)
        df["date"] = pd.to_datetime(df["date"])

        daily_rv, train_dates, test_dates = self.compute_daily_rv(df)
        daily_rv = self.compute_position_sizing(daily_rv, train_dates)
        data_ext = self.build_noise_bands(df, daily_rv)
        data_ext = self.generate_signals(data_ext)
        data_ext = self.apply_costs(data_ext)

        return data_ext, daily_rv, train_dates, test_dates
    