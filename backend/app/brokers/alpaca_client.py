from alpaca.trading.client import TradingClient

from backend.app.config import settings


def get_trading_client() -> TradingClient:
    """Create and return an Alpaca Trading API client."""
    return TradingClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=settings.alpaca_paper,
    )