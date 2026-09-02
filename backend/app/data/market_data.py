from datetime import datetime, timedelta, timezone

from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from backend.app.config import settings


def get_market_data_client() -> StockHistoricalDataClient:
    """Create and return an Alpaca market data client."""

    return StockHistoricalDataClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
    )


def get_bars(symbol: str, timeframe, days: int = 30):
    """Fetch historical bars using the Alpaca IEX feed."""

    client = get_market_data_client()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        feed=DataFeed.IEX,
    )

    return client.get_stock_bars(request)


def get_daily_bars(symbol: str, days: int = 100):
    """Fetch daily bars."""

    return get_bars(
        symbol=symbol,
        timeframe=TimeFrame.Day,
        days=days * 2,
    )


def get_hourly_bars(symbol: str, days: int = 30):
    """Fetch 1-hour bars for directional context."""

    return get_bars(
        symbol=symbol,
        timeframe=TimeFrame.Hour,
        days=days,
    )


def get_15m_bars(symbol: str, days: int = 10):
    """Fetch 15-minute bars for entry confirmation."""

    return get_bars(
        symbol=symbol,
        timeframe=TimeFrame(15, TimeFrameUnit.Minute),
        days=days,
    )