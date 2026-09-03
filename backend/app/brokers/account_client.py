from app.brokers.alpaca_client import get_trading_client


def get_account_snapshot() -> dict:
    """
    Retrieve the current Alpaca trading account state
    required by the TARK Risk Governor.
    """

    client = get_trading_client()

    account = client.get_account()

    return {
        "equity": float(account.equity),
        "cash": float(account.cash),
        "buying_power": float(account.buying_power),
        "portfolio_value": float(account.portfolio_value),
        "daytrade_count": int(account.daytrade_count or 0),
        "trading_blocked": bool(account.trading_blocked),
        "account_blocked": bool(account.account_blocked),
    }