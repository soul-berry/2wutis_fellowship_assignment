from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

from src.data.alpaca_provider import AlpacaDataProvider

load_dotenv()

api_key = os.getenv("ALPACA_API_KEY")
secret_key = os.getenv("ALPACA_SECRET_KEY")

provider = AlpacaDataProvider(api_key, secret_key)

# make sure we don't hit the “recent SIP” window
now = datetime.now(tz=timezone.utc)
end = now - timedelta(minutes=20)       # instead of now
start = end - timedelta(days=365)

raw_bars_df = provider.get_bars("SPY", start=start, end=end)
raw_bars_df.to_csv("output/historical_bars.csv", index=False)

print("Saved rows:", len(raw_bars_df))
print(raw_bars_df.head())