from fastapi import FastAPI, HTTPException

from backend.app.brokers.alpaca_client import get_trading_client
from backend.app.data.market_data import get_daily_bars
from backend.app.engines.quant_features import calculate_features
from backend.app.data.market_data import (
    get_daily_bars,
    get_hourly_bars,
    get_15m_bars,
)

from backend.app.engines.opportunity import evaluate_opportunity
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

@app.get("/features/{symbol}")
def get_features(symbol: str):
    """
    Calculate TARK quantitative features for a symbol.
    """

    try:
        symbol = symbol.upper()

        bars_response = get_daily_bars(symbol)

        bars = bars_response.data.get(symbol, [])

        features = calculate_features(bars)

        return {
            "symbol": symbol,
            "features": features,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to calculate features: {str(exc)}",
        )

@app.get("/opportunity/{symbol}")
def get_opportunity(symbol: str):
    """
    Evaluate a TARK trading opportunity using:

    - 1H directional context
    - 15M entry confirmation
    """

    try:
        symbol = symbol.upper()

        hourly_response = get_hourly_bars(symbol)
        entry_response = get_15m_bars(symbol)

        hourly_bars = hourly_response.data.get(symbol, [])
        entry_bars = entry_response.data.get(symbol, [])

        hourly_features = calculate_features(hourly_bars)
        entry_features = calculate_features(entry_bars)

        opportunity = evaluate_opportunity(
            symbol=symbol,
            hourly_features=hourly_features,
            entry_features=entry_features,
        )

        return {
            "hourly_features": hourly_features,
            "entry_features": entry_features,
            "opportunity": opportunity,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to evaluate opportunity: {str(exc)}",
        )