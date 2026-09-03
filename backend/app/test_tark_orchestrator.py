import json

from app.services.tark_orchestrator import TarkOrchestrator


def main():

    symbol = "QQQ"

    hourly_features = {
        "timestamp": "2026-09-02T12:00:00+00:00",
        "close": 705.63,
        "ema_20": 710.92,
        "ema_50": 713.03,
        "rsi_14": 32.29,
        "atr_14": 2.94,
        "volume_ratio": 0.01,
    }

    entry_features = {
        "timestamp": "2026-09-02T12:45:00+00:00",
        "close": 705.63,
        "ema_20": 707.71,
        "ema_50": 709.62,
        "rsi_14": 36.76,
        "atr_14": 0.91,
        "volume_ratio": 0.02,
    }

    tark = TarkOrchestrator()

    result = tark.analyze(
        symbol=symbol,
        hourly_features=hourly_features,
        entry_features=entry_features,
    )

    print("\nTARK ORCHESTRATOR RESULT")
    print("-" * 60)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()