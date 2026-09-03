import json

from app.brokers.account_client import get_account_snapshot
from app.brokers.position_client import get_open_positions

from app.engines.spread_pricing import calculate_spread_pricing

from app.risk.risk_governor import RiskGovernor

from app.execution.order_executor import OrderExecutor


def main():

    # ---------------------------------------------
    # TRADE SELECTED BY TARK
    # ---------------------------------------------

    trade = {
        "strategy": "BEAR_PUT_SPREAD",
        "symbol": "QQQ",
        "expiration_date": "2026-09-03",

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

    # ---------------------------------------------
    # LIVE SPREAD PRICING
    # ---------------------------------------------

    pricing = calculate_spread_pricing(
        long_symbol=trade["long_leg"]["symbol"],
        short_symbol=trade["short_leg"]["symbol"],
    )

    trade["limit_price"] = pricing["estimated_debit"]

    print("\nLIVE SPREAD PRICING")
    print("-" * 50)
    print(json.dumps(pricing, indent=2))

    # ---------------------------------------------
    # LIVE ACCOUNT + POSITIONS
    # ---------------------------------------------

    account = get_account_snapshot()

    positions = get_open_positions()

    # ---------------------------------------------
    # RISK GOVERNOR
    # ---------------------------------------------

    governor = RiskGovernor()

    risk_result = governor.evaluate(
        decision="TRADE",
        symbol=trade["symbol"],
        strategy=trade["strategy"],

        account_equity=account["equity"],
        start_of_day_equity=account["equity"],
        buying_power=account["buying_power"],

        open_positions=positions,

        daily_realized_pnl=0.0,
        new_entries_today=0,

        proposed_position={
            "net_debit": pricing["estimated_debit"],
            "contracts": 5,
        },
    )

    print("\nRISK GOVERNOR RESULT")
    print("-" * 50)
    print(json.dumps(risk_result, indent=2))

    # ---------------------------------------------
    # ORDER EXECUTOR
    # ---------------------------------------------

    executor = OrderExecutor(dry_run=True)

    execution_result = executor.execute(
        trade=trade,
        risk_result=risk_result,
    )

    print("\nORDER EXECUTION RESULT")
    print("-" * 50)
    print(json.dumps(execution_result, indent=2))


if __name__ == "__main__":
    main()