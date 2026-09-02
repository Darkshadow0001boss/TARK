from datetime import datetime, timedelta, timezone

from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from backend.app.config import settings


def get_market_data_client() -> StockHistoricalDataClient:
    """Create and return an Alpaca market data client."""

    return StockHistoricalDataClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
    )


def get_daily_bars(symbol: str, days: int = 100):
    """
    Fetch recent daily price bars using the IEX feed.
    """

    client = get_market_data_client()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days * 2)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX,
    )

    return client.get_stock_bars(request)