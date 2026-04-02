from datetime import datetime, timezone
from pathlib import Path

from src.config import load_config
from src.data.alpaca_provider import AlpacaDataProvider

def main():
    cfg = load_config()

    provider = AlpacaDataProvider(
        api_key=cfg["apikey"],
        secret_key=cfg["secretkey"]
    )

    bars = provider.get_minute_bars(
        symbol=cfg.get("symbol", "SPY"),
        start=datetime(2025, 1, 2, tzinfo=timezone.utc),
        end=datetime(2025, 1, 5, tzinfo=timezone.utc),
    )

    print(bars.head())
    print(f"Rows fetched: {len(bars)}")

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    bars.to_csv(output_dir / "spy_minute_bars_sample.csv", index=False)

if __name__ == "__main__":
    main()