from app.brokers.alpaca_client import get_trading_client


def get_open_positions() -> list:
    """
    Retrieve all currently open positions from Alpaca.

    Returns a simplified representation suitable for
    TARK's Risk Governor and Position Manager.
    """

    client = get_trading_client()

    positions = client.get_all_positions()

    result = []

    for position in positions:
        result.append(
            {
                "symbol": position.symbol,
                "quantity": float(position.qty),
                "market_value": float(position.market_value),
                "cost_basis": float(position.cost_basis),
                "unrealized_pl": float(position.unrealized_pl),
                "unrealized_plpc": float(position.unrealized_plpc),
                "side": str(position.side),
            }
        )

    return result