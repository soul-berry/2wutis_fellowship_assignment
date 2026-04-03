from src.strategy.adaptive_vol_regime import AdaptiveVolRegimeStrategy
from src.trading.live_trader import LiveTrader


def main():
    strategy = AdaptiveVolRegimeStrategy(
        k_base=2.0,
        noise_window=15,
        train_ratio=0.7,
        cost_bps=1.0,
    )

    trader = LiveTrader(
        symbol="SPY",
        strategy=strategy,
        poll_interval_seconds=60,
    )

    trader.run()


if __name__ == "__main__":
    main()