import pandas as pd
from src.data.transforms import prepare_intraday_features
from src.strategy.adaptive_vol_regime import AdaptiveVolRegimeStrategy

def main():
    df = pd.read_csv("output/historical_bars.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["time"] = df["timestamp"].dt.strftime("%H:%M:%S")

    # THIS is the missing step
    df = prepare_intraday_features(df)

    # print("Columns BEFORE strategy.run:", df.columns.tolist())
    # print("Unique dates in raw/prepared data:", df["date"].nunique())
    # print("Min date:", df["date"].min())
    # print("Max date:", df["date"].max())

    strategy = AdaptiveVolRegimeStrategy()
    data_ext, daily_rv, train_dates, test_dates = strategy.run(df)

    # print("Columns AFTER strategy.run:", data_ext.columns.tolist())
    # print("Raw signals count:", data_ext["raw_signal"].abs().sum())
    # print("First signal days:", data_ext["first_signal"].fillna(0).abs().sum())
    # print("Nonzero base positions:", (data_ext["base_position"] != 0).sum())
    # print("Nonzero position_ext:", (data_ext["position_ext"] != 0).sum())

    # print(
    #     data_ext.loc[
    #         data_ext["raw_signal"].notna(),
    #         ["date", "time", "raw_signal", "first_signal", "base_position", "position_ext"],
    #     ].head(20)
    # )

    print("Days with entry rate:", data_ext.groupby("date")["first_signal"].apply(lambda s: s.notna().any()).mean())
    print("Average pos_size:", data_ext["pos_size"].mean())
    print("Net strategy return:", data_ext["strategy_ret_ext"].sum())
    print("Average trades per day:", data_ext.groupby("date")["trade_ext"].sum().mean())

    data_ext["date"] = pd.to_datetime(data_ext["date"]).dt.normalize()
    train_dates = pd.to_datetime(train_dates).normalize()
    test_dates = pd.to_datetime(test_dates).normalize()
    
    # train_pnl = data_ext.loc[data_ext["date"].isin(train_dates), "strategy_ret_ext"].sum()
    # test_pnl  = data_ext.loc[data_ext["date"].isin(test_dates), "strategy_ret_ext"].sum()

    # print("Train net return:", train_pnl)
    # print("Test net return:", test_pnl)
    # print("Train days:", len(train_dates))
    # print("Test days:", len(test_dates))

    daily_pnl = data_ext.groupby("date")["strategy_ret_ext"].sum()
    print(daily_pnl.describe())
    print("Winning day rate:", (daily_pnl > 0).mean())

    # print("DATE CHECKS")
    # print(data_ext["date"].dtype)
    # print(type(train_dates[0]), train_dates[0])
    # print(type(test_dates[0]), test_dates[0])

    # print(data_ext["date"].head())
    # print(train_dates[:3])
    # print(test_dates[:3])

    # print("Train matches:", data_ext["date"].isin(train_dates).sum())
    # print("Test matches:", data_ext["date"].isin(test_dates).sum())

    print("SECOND CHECK")
    
    train_daily = daily_pnl[daily_pnl.index.isin(train_dates)]
    test_daily = daily_pnl[daily_pnl.index.isin(test_dates)]

    print("Train mean daily pnl:", train_daily.mean())
    print("Test mean daily pnl:", test_daily.mean())
    print("Train win rate:", (train_daily > 0).mean())
    print("Test win rate:", (test_daily > 0).mean())
    print("Train worst day:", train_daily.min(), "best day:", train_daily.max())
    print("Test worst day:", test_daily.min(), "best day:", test_daily.max())

if __name__ == "__main__":
    main()