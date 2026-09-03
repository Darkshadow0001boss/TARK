import json

from app.risk.risk_governor import RiskGovernor


def main():

    governor = RiskGovernor()

    # --------------------------------------------------------
    # Simulated official hackathon paper account
    # --------------------------------------------------------

    account_equity = 100000.0
    start_of_day_equity = 100000.0
    buying_power = 100000.0

    # No positions currently open
    open_positions = []

    # No losses today
    daily_realized_pnl = 0.0

    # No trades entered today
    new_entries_today = 0

    # --------------------------------------------------------
    # Proposed QQQ Bear Put Spread
    # --------------------------------------------------------

    proposed_position = {
        # Example net debit:
        # $2.50 × 100 = $250 maximum risk per spread
        "net_debit": 2.50,

        # Request 5 spreads.
        # Risk Governor should reduce this if necessary.
        "contracts": 5,
    }

    # --------------------------------------------------------
    # Run Risk Governor
    # --------------------------------------------------------

    result = governor.evaluate(
        decision="TRADE",
        symbol="QQQ",
        strategy="BEAR_PUT_SPREAD",

        account_equity=account_equity,
        start_of_day_equity=start_of_day_equity,
        buying_power=buying_power,

        open_positions=open_positions,

        daily_realized_pnl=daily_realized_pnl,
        new_entries_today=new_entries_today,

        proposed_position=proposed_position,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()