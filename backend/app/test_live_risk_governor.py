import json

from app.brokers.account_client import get_account_snapshot
from app.risk.risk_governor import RiskGovernor
from app.brokers.position_client import get_open_positions

def main():

    # --------------------------------------------------------
    # Get REAL Alpaca paper account data
    # --------------------------------------------------------

    account = get_account_snapshot()

    # Safety check
    if account["trading_blocked"] or account["account_blocked"]:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "reason": "Alpaca account is currently blocked",
                },
                indent=2,
            )
        )
        return

    # --------------------------------------------------------
    # Create Risk Governor
    # --------------------------------------------------------

    governor = RiskGovernor()

    # --------------------------------------------------------
    # Example proposed trade
    # --------------------------------------------------------

    proposed_position = {
        "net_debit": 2.50,
        "contracts": 5,
    }

    # --------------------------------------------------------
    # Evaluate using REAL account values
    # --------------------------------------------------------

    result = governor.evaluate(
        decision="TRADE",
        symbol="QQQ",
        strategy="BEAR_PUT_SPREAD",

        account_equity=account["equity"],

        # For this initial integration test, use current equity.
        # Later the portfolio/account service will track true
        # start-of-day equity.
        start_of_day_equity=account["equity"],

        buying_power=account["buying_power"],

        open_positions=get_open_positions(),

        daily_realized_pnl=0.0,
        new_entries_today=0,

        proposed_position=proposed_position,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()