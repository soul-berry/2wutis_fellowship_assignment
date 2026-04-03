from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed


class AlpacaDataProvider:
    def __init__(self, api_key: str, secret_key: str):
        self.client = StockHistoricalDataClient(api_key, secret_key)

    def get_minute_bars(self, symbol: str, start, end, timeframe=TimeFrame.Minute):
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            feed=DataFeed.IEX,
        )
        bars = self.client.get_stock_bars(request).df.reset_index()
        return bars