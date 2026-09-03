import json

from app.services.position_lifecycle import (
    PositionLifecycleService,
)


def main():

    position = {
        "symbol": "QQQ",
        "strategy": "BEAR_PUT_SPREAD",

        "entry_debit": 1.14,

        "contracts": 4,

        "long_leg": {
            "symbol": "QQQ260903P00706000",
        },

        "short_leg": {
            "symbol": "QQQ260903P00701000",
        },
    }

    lifecycle = PositionLifecycleService()

    result = lifecycle.monitor(
        position=position,
        thesis_invalidated=True,
    )

    print("\nPOSITION LIFECYCLE RESULT")
    print("-" * 60)

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()