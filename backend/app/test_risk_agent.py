import json

from app.agents.risk_agent import RiskAgent


def main():
    opportunity = {
        "symbol": "QQQ",
        "direction": "BEARISH",
        "action": "CANDIDATE",
        "strategy": "BEAR_PUT_SPREAD",
        "reasons": [
            "1H trend is bearish",
            "15M trend confirms bearish direction",
            "15M RSI confirms bearish momentum",
        ],
    }

    thesis = {
        "symbol": "QQQ",
        "direction": "BEARISH",
        "confidence": "LOW",
        "supporting_evidence": [
            "Bearish EMA alignment",
            "Bearish RSI confirmation",
        ],
        "contradictions": [
            "Very low volume participation",
            "RSI approaching oversold territory",
            "Weak market participation",
        ],
    }

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

    agent = RiskAgent()

    result = agent.evaluate(
        opportunity=opportunity,
        thesis=thesis,
        hourly_features=hourly_features,
        entry_features=entry_features,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()