import json

from app.engines.spread_pricing import calculate_spread_pricing as get_spread_pricing
from app.engines.position_manager import evaluate_position


def main():

    # This represents a position that TARK previously opened.
    position = {
        "symbol": "QQQ",
        "strategy": "BEAR_PUT_SPREAD",
        "entry_debit": 1.68,

        "long_leg": {
            "symbol": "QQQ260903P00709000",
        },

        "short_leg": {
            "symbol": "QQQ260903P00704000",
        },
    }

    # Get current live pricing
    pricing = get_spread_pricing(
        long_symbol=position["long_leg"]["symbol"],
        short_symbol=position["short_leg"]["symbol"],
    )

    print("\nLIVE SPREAD PRICING")
    print("-" * 50)

    print(json.dumps(pricing, indent=2, default=str))

    # Current spread value
    current_debit = pricing["estimated_debit"]

    # Evaluate position
    result = evaluate_position(
        entry_debit=position["entry_debit"],
        current_debit=current_debit,
        profit_target_pct=50.0,
        stop_loss_pct=50.0,
        thesis_invalidated=False,
    )

    print("\nPOSITION MANAGEMENT RESULT")
    print("-" * 50)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()