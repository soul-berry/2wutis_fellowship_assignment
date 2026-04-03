from src.data.transforms import prepare_intraday_features
from src.strategy.adaptive_vol_regime import AdaptiveVolRegimeStrategy

df = prepare_intraday_features(raw_bars_df)

strategy = AdaptiveVolRegimeStrategy()
data_ext, daily_rv, train_dates, test_dates = strategy.run(df)

print(data_ext.columns.tolist())
print(data_ext[[
    "date", "time", "close", "k_adaptive", "pos_size",
    "upper_ext", "lower_ext", "raw_signal",
    "base_position", "position_ext", "strategy_ret_ext"
]].tail())
