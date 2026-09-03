from alpaca.trading.client import TradingClient

from app.config import settings


def get_options_client() -> TradingClient:
    """
    Return the Alpaca Trading Client.

    This client will later be used to retrieve option contracts
    and submit option orders.
    """

    return TradingClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=settings.alpaca_paper,
    )