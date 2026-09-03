import json

from app.agents.thesis_agent import ThesisAgent
from app.engines.opportunity import evaluate_opportunity


def main():
    symbol = "QQQ"

    hourly_features = {
        "timestamp": "2026-09-02T15:00:00+00:00",
        "close": 708.82,
        "ema_20": 710.07,
        "ema_50": 712.42,
        "rsi_14": 35.51,
        "atr_14": 3.04,
        "volume_ratio": 0.22,
    }

    entry_features = {
        "timestamp": "2026-09-02T15:15:00+00:00",
        "close": 708.82,
        "ema_20": 707.95,
        "ema_50": 709.13,
        "rsi_14": 54.49,
        "atr_14": 1.23,
        "volume_ratio": 0.19,
    }

    opportunity = evaluate_opportunity(
        symbol=symbol,
        hourly_features=hourly_features,
        entry_features=entry_features,
    )

    agent = ThesisAgent()

    result = agent.analyze(
        symbol=symbol,
        hourly_features=hourly_features,
        entry_features=entry_features,
        opportunity=opportunity,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()