import json

from app.execution.order_executor import OrderExecutor

trade = {
    "strategy": "BEAR_PUT_SPREAD",
    "symbol": "QQQ",
    "expiration_date": "2026-09-03",

    "limit_price": 2.50,

    "long_leg": {
        "symbol": "QQQ260903P00709000",
        "strike": 709.0,
        "side": "BUY",
        "type": "PUT",
    },

    "short_leg": {
        "symbol": "QQQ260903P00704000",
        "strike": 704.0,
        "side": "SELL",
        "type": "PUT",
    },
}


risk_result = {
    "status": "APPROVED",
    "approved_contracts": 4,
}


executor = OrderExecutor(dry_run=True)

result = executor.execute(
    trade=trade,
    risk_result=risk_result,
)

print(json.dumps(result, indent=2))