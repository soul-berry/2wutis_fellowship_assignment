import time
from datetime import datetime, timezone

import pandas as pd

from src.data.alpaca_client import AlpacaClient
from src.data.transforms import prepare_intraday_features
from src.strategy.adaptive_vol_regime import AdaptiveVolRegimeStrategy


class LiveTrader:
    def __init__(
        self,
        symbol: str,
        strategy: AdaptiveVolRegimeStrategy,
        poll_interval_seconds: int = 60,
    ):
        self.symbol = symbol
        self.strategy = strategy
        self.poll_interval_seconds = poll_interval_seconds
        self.client = AlpacaClient()
        self.current_position = 0

    def get_today_bars(self) -> pd.DataFrame:
        now = datetime.now(timezone.utc)
        start = now.replace(hour=13, minute=30, second=0, microsecond=0)
        end = now

        df_raw = self.client.fetch_historical_bars(
            self.symbol,
            start=start.isoformat(),
            end=end.isoformat(),
        )
        return df_raw

    def compute_latest_signal(self, df_raw: pd.DataFrame) -> float:
        df = df_raw.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date
        df["time"] = df["timestamp"].dt.strftime("%H:%M:%S")
        df = prepare_intraday_features(df)

        data_ext, daily_rv, train_dates, test_dates = self.strategy.run(df)

        today = data_ext["date"].max()
        today_df = data_ext[data_ext["date"] == today].copy()
        today_df = today_df.sort_values("timestamp")

        latest = today_df.iloc[-1]
        target_position = latest["position_ext"]
        return target_position

    def send_orders(self, target_position: float):
        target_shares = int(round(target_position))
        delta = target_shares - self.current_position

        if delta == 0:
            print("No position change needed.")
            return

        side = "buy" if delta > 0 else "sell"
        qty = abs(delta)

        print(f"Submitting {side} order for {qty} shares of {self.symbol}")
        # Uncomment only for Alpaca paper trading:
        # self.client.submit_market_order(self.symbol, qty=qty, side=side)

        self.current_position = target_shares

    def run(self):
        print(f"Starting live trader for {self.symbol}...")

        while True:
            try:
                df_today = self.get_today_bars()

                if df_today.empty:
                    print("No bars yet, sleeping...")
                    time.sleep(self.poll_interval_seconds)
                    continue

                target_position = self.compute_latest_signal(df_today)
                print(
                    f"New bar: target_position={target_position:.2f}, "
                    f"current_position={self.current_position}"
                )
                self.send_orders(target_position)

                time.sleep(self.poll_interval_seconds)

            except KeyboardInterrupt:
                print("Stopping live trader.")
                break
            except Exception as e:
                print("Error in live loop:", e)
                time.sleep(self.poll_interval_seconds)