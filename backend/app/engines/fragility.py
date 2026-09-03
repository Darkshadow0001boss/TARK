def calculate_fragility(
    hourly_features: dict,
    entry_features: dict,
    opportunity: dict,
    thesis: dict,
) -> dict:
    """
    Calculate TARK's deterministic Fragility Score.

    Fragility measures how vulnerable a trading thesis is to
    contradictory evidence and alternative market scenarios.

    Score:
        0   = very low fragility
        100 = extreme fragility
    """

    required_hourly = [
        "close",
        "ema_20",
        "ema_50",
        "rsi_14",
        "atr_14",
        "volume_ratio",
    ]

    required_entry = [
        "close",
        "ema_20",
        "ema_50",
        "rsi_14",
        "atr_14",
        "volume_ratio",
    ]

    # --------------------------------------------------
    # HARD OVERRIDE — Missing critical data
    # --------------------------------------------------

    for field in required_hourly:
        if field not in hourly_features:
            return {
                "score": 100,
                "classification": "HIGH",
                "decision": "ABSTAIN",
                "override": "MISSING_CRITICAL_DATA",
                "components": {},
            }

    for field in required_entry:
        if field not in entry_features:
            return {
                "score": 100,
                "classification": "HIGH",
                "decision": "ABSTAIN",
                "override": "MISSING_CRITICAL_DATA",
                "components": {},
            }

    direction = opportunity.get("direction")

    if direction not in ["BULLISH", "BEARISH"]:
        return {
            "score": 100,
            "classification": "HIGH",
            "decision": "ABSTAIN",
            "override": "INVALID_DIRECTION",
            "components": {},
        }

    components = {}

    # --------------------------------------------------
    # 1. TREND FRAGILITY
    # --------------------------------------------------

    trend_fragility = 0

    hourly_bullish = (
        hourly_features["close"] > hourly_features["ema_20"]
        and hourly_features["ema_20"] > hourly_features["ema_50"]
    )

    hourly_bearish = (
        hourly_features["close"] < hourly_features["ema_20"]
        and hourly_features["ema_20"] < hourly_features["ema_50"]
    )

    entry_bullish = (
        entry_features["close"] > entry_features["ema_20"]
        and entry_features["ema_20"] > entry_features["ema_50"]
    )

    entry_bearish = (
        entry_features["close"] < entry_features["ema_20"]
        and entry_features["ema_20"] < entry_features["ema_50"]
    )

    if direction == "BULLISH":

        if not hourly_bullish:
            trend_fragility += 20

        if not entry_bullish:
            trend_fragility += 15

    elif direction == "BEARISH":

        if not hourly_bearish:
            trend_fragility += 20

        if not entry_bearish:
            trend_fragility += 15

    components["trend"] = min(trend_fragility, 25)

    # --------------------------------------------------
    # 2. MOMENTUM FRAGILITY
    # --------------------------------------------------

    momentum_fragility = 0

    rsi = entry_features["rsi_14"]

    if direction == "BULLISH":

        if rsi < 50:
            momentum_fragility += 15

        if rsi > 70:
            momentum_fragility += 10

    elif direction == "BEARISH":

        if rsi > 50:
            momentum_fragility += 15

        if rsi < 30:
            momentum_fragility += 10

    components["momentum"] = min(momentum_fragility, 20)

    # --------------------------------------------------
    # 3. VOLUME FRAGILITY
    # --------------------------------------------------

    volume_ratio = entry_features["volume_ratio"]

    if volume_ratio < 0.25:
        volume_fragility = 20

    elif volume_ratio < 0.50:
        volume_fragility = 12

    elif volume_ratio < 0.80:
        volume_fragility = 6

    else:
        volume_fragility = 0

    components["volume"] = volume_fragility

    # --------------------------------------------------
    # 4. NEUTRAL SCENARIO PRESSURE
    # --------------------------------------------------

    neutral_fragility = 0

    contradictions = thesis.get("contradictions", [])

    if len(contradictions) >= 3:
        neutral_fragility = 15

    elif len(contradictions) >= 2:
        neutral_fragility = 10

    elif len(contradictions) >= 1:
        neutral_fragility = 5

    components["neutral_pressure"] = neutral_fragility

    # --------------------------------------------------
    # 5. FAILURE SCENARIO PRESSURE
    # --------------------------------------------------

    failure_fragility = 0

    failure_scenario = thesis.get(
        "failure_scenario",
        "",
    )

    if failure_scenario:
        failure_fragility = 10

    components["failure_pressure"] = failure_fragility

    # --------------------------------------------------
    # 6. VOLATILITY PRESSURE
    # --------------------------------------------------

    volatility_fragility = 0

    hourly_atr = hourly_features["atr_14"]
    hourly_close = hourly_features["close"]

    atr_ratio = hourly_atr / hourly_close

    if atr_ratio > 0.03:
        volatility_fragility = 15

    elif atr_ratio > 0.02:
        volatility_fragility = 10

    elif atr_ratio > 0.01:
        volatility_fragility = 5

    components["volatility"] = volatility_fragility

    # --------------------------------------------------
    # TOTAL SCORE
    # --------------------------------------------------

    score = sum(components.values())

    score = min(score, 100)

    # --------------------------------------------------
    # CLASSIFICATION + DECISION
    # --------------------------------------------------

    if score <= 30:

        classification = "LOW"
        decision = "TRADE"

    elif score <= 60:

        classification = "MEDIUM"
        decision = "REDUCE"

    else:

        classification = "HIGH"
        decision = "ABSTAIN"

    return {
        "score": score,
        "classification": classification,
        "decision": decision,
        "override": None,
        "components": components,
    }