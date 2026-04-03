import pandas as pd

from src.data.transforms import prepare_intraday_features
from src.strategy.adaptive_vol_regime import AdaptiveVolRegimeStrategy
from src.data.alpaca_client import AlpacaClient


def load_historical_from_alpaca(
    symbol: str,
    start: str,
    end: str,
) -> pd.DataFrame:
    client = AlpacaClient()
    df_raw = client.fetch_historical_bars(symbol, start, end)
    return df_raw


def run_backtest(
    df_raw: pd.DataFrame,
    strategy: AdaptiveVolRegimeStrategy,
) -> tuple[pd.DataFrame, pd.Series, list, list]:
    df = df_raw.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["time"] = df["timestamp"].dt.strftime("%H:%M:%S")
    df = prepare_intraday_features(df)

    data_ext, daily_rv, train_dates, test_dates = strategy.run(df)

    data_ext["date"] = pd.to_datetime(data_ext["date"]).dt.normalize()
    train_dates = pd.to_datetime(train_dates).normalize()
    test_dates = pd.to_datetime(test_dates).normalize()

    daily_pnl = data_ext.groupby("date")["strategy_ret_ext"].sum()

    return data_ext, daily_pnl, train_dates, test_dates