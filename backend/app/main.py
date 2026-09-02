from fastapi import FastAPI, HTTPException

from backend.app.brokers.alpaca_client import get_trading_client

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