from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest

from app.config import settings


def get_option_data_client():
    """
    Create the Alpaca option market data client.
    """

    return OptionHistoricalDataClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
    )


def get_option_quote(symbol: str) -> dict:
    """
    Get the latest bid and ask quote for an option contract.
    """

    client = get_option_data_client()

    request = OptionLatestQuoteRequest(
        symbol_or_symbols=symbol,
    )

    quotes = client.get_option_latest_quote(request)

    quote = quotes[symbol]

    return {
        "symbol": symbol,
        "bid_price": float(quote.bid_price),
        "ask_price": float(quote.ask_price),
        "bid_size": quote.bid_size,
        "ask_size": quote.ask_size,
        "timestamp": str(quote.timestamp),
    }