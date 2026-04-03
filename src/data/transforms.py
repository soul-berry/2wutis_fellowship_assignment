import numpy as np
import pandas as pd

def prepare_intraday_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp")

    df["date"] = df["timestamp"].dt.date
    df["time"] = df["timestamp"].dt.strftime("%H:%M:%S")
    df["minute"] = df.groupby("date").cumcount() + 1

    df["ret"] = np.log(df["close"]).diff()

    df["open_price"] = df.groupby("date")["open"].transform("first")
    df["move_from_open"] = (df["close"] / df["open_price"] - 1).abs()

    return df