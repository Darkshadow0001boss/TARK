from fastapi import FastAPI, HTTPException

from backend.app.brokers.alpaca_client import get_trading_client
from backend.app.data.market_data import get_daily_bars

app = FastAPI(
    title="TARK",
    description="Reason Before Risk — Autonomous AI-Powered Options Trading Agent",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "TARK",
        "message": "Reason Before Risk",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.get("/account")
def get_account():
    """Retrieve Alpaca account information."""

    try:
        client = get_trading_client()
        account = client.get_account()

        return {
            "status": str(account.status),
            "portfolio_value": str(account.portfolio_value),
            "buying_power": str(account.buying_power),
            "cash": str(account.cash),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to connect to Alpaca: {str(exc)}",
        )


@app.get("/market/{symbol}")
def get_market(symbol: str):
    """
    Retrieve recent daily market bars.
    """

    try:
        bars = get_daily_bars(symbol.upper())

        data = []

        for bar in bars.data.get(symbol.upper(), []):
            data.append(
                {
                    "timestamp": bar.timestamp.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                }
            )

        return {
            "symbol": symbol.upper(),
            "bars": data,
            "count": len(data),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve market data: {str(exc)}",
        )