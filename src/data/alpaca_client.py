import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv 
import pandas as pd
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

load_dotenv()

@dataclass
class AlpacaConfig:
    api_key: str
    secret_key: str
    paper: bool = True  # use paper trading


class AlpacaClient:
    def __init__(self, config: Optional[AlpacaConfig] = None):
        if config is None:
            config = AlpacaConfig(
                api_key=os.environ["ALPACA_API_KEY"],
                secret_key=os.environ["ALPACA_SECRET_KEY"],
                paper=True,
            )
        self.config = config
        self.data_client = StockHistoricalDataClient(
            config.api_key, config.secret_key
        )
        self.trading_client = TradingClient(
            config.api_key, config.secret_key, paper=config.paper
        )

    def fetch_historical_bars(
        self,
        symbol: str,
        start: str,
        end: str,
        timeframe: TimeFrame = TimeFrame.Minute,
    ) -> pd.DataFrame:
        req = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
        )
        bars = self.data_client.get_stock_bars(req).df.reset_index()
        # Standardize columns to what your pipeline expects
        bars = bars.rename(
            columns={
                "timestamp": "timestamp",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
                "trade_count": "trade_count",
                "vwap": "vwap",
            }
        )
        return bars

    def submit_market_order(
        self,
        symbol: str,
        qty: int,
        side: str,
    ):
        side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side_enum,
            time_in_force=TimeInForce.DAY,
        )
        return self.trading_client.submit_order(order)