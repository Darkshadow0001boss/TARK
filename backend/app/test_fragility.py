import json

from app.engines.fragility import calculate_fragility


def print_result(title: str, result: dict):
    print()
    print(title)
    print("-" * 60)
    print(json.dumps(result, indent=2))


def main():

    # ==================================================
    # TEST 1 — HEALTHY BEARISH SETUP
    # Expected: LOW fragility → TRADE
    # ==================================================

    hourly_features = {
        "close": 700.0,
        "ema_20": 705.0,
        "ema_50": 710.0,
        "rsi_14": 40.0,
        "atr_14": 3.0,
        "volume_ratio": 1.2,
    }

    entry_features = {
        "close": 699.0,
        "ema_20": 702.0,
        "ema_50": 706.0,
        "rsi_14": 38.0,
        "atr_14": 1.0,
        "volume_ratio": 1.0,
    }

    opportunity = {
        "symbol": "QQQ",
        "direction": "BEARISH",
        "action": "CANDIDATE",
        "strategy": "BEAR_PUT_SPREAD",
    }

    thesis = {
        "confidence": "HIGH",
        "contradictions": [],
        "neutral_scenario": "",
        "failure_scenario": "",
    }

    result = calculate_fragility(
        hourly_features,
        entry_features,
        opportunity,
        thesis,
    )

    print_result(
        "TEST 1 — HEALTHY BEARISH SETUP",
        result,
    )

    # ==================================================
    # TEST 2 — FRAGILE LOW-VOLUME SETUP
    # Expected: MEDIUM/HIGH fragility
    # ==================================================

    hourly_features_2 = {
        "close": 705.63,
        "ema_20": 710.92,
        "ema_50": 713.03,
        "rsi_14": 32.29,
        "atr_14": 2.94,
        "volume_ratio": 0.01,
    }

    entry_features_2 = {
        "close": 705.63,
        "ema_20": 707.71,
        "ema_50": 709.62,
        "rsi_14": 36.76,
        "atr_14": 0.91,
        "volume_ratio": 0.02,
    }

    opportunity_2 = {
        "symbol": "QQQ",
        "direction": "BEARISH",
        "action": "CANDIDATE",
        "strategy": "BEAR_PUT_SPREAD",
    }

    thesis_2 = {
        "confidence": "LOW",
        "contradictions": [
            "Extremely low volume",
            "RSI approaching oversold",
            "Price consolidation",
        ],
        "neutral_scenario": "Price may consolidate.",
        "failure_scenario": "Price may reclaim key EMAs.",
    }

    result = calculate_fragility(
        hourly_features_2,
        entry_features_2,
        opportunity_2,
        thesis_2,
    )

    print_result(
        "TEST 2 — FRAGILE LOW-VOLUME SETUP",
        result,
    )

    # ==================================================
    # TEST 3 — BULLISH MOMENTUM CONTRADICTION
    # Expected: increased fragility
    # ==================================================

    hourly_features_3 = {
        "close": 720.0,
        "ema_20": 715.0,
        "ema_50": 710.0,
        "rsi_14": 65.0,
        "atr_14": 5.0,
        "volume_ratio": 0.8,
    }

    entry_features_3 = {
        "close": 721.0,
        "ema_20": 718.0,
        "ema_50": 714.0,
        "rsi_14": 78.0,
        "atr_14": 2.0,
        "volume_ratio": 0.4,
    }

    opportunity_3 = {
        "symbol": "QQQ",
        "direction": "BULLISH",
        "action": "CANDIDATE",
        "strategy": "BULL_CALL_SPREAD",
    }

    thesis_3 = {
        "confidence": "MEDIUM",
        "contradictions": [
            "Momentum is overextended",
            "Volume participation is weak",
        ],
        "neutral_scenario": "Possible consolidation.",
        "failure_scenario": "Potential reversal.",
    }

    result = calculate_fragility(
        hourly_features_3,
        entry_features_3,
        opportunity_3,
        thesis_3,
    )

    print_result(
        "TEST 3 — BULLISH FRAGILITY",
        result,
    )

    # ==================================================
    # TEST 4 — MISSING DATA
    # Expected: HIGH → ABSTAIN
    # ==================================================

    broken_hourly_features = {
        "close": 700.0,
    }

    result = calculate_fragility(
        broken_hourly_features,
        entry_features,
        opportunity,
        thesis,
    )

    print_result(
        "TEST 4 — MISSING CRITICAL DATA",
        result,
    )


if __name__ == "__main__":
    main()