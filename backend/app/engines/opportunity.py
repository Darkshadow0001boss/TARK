def classify_trend(features: dict) -> str:
    """
    Deterministically classify market trend according
    to the TARK MVP strategy specification.
    """

    close = features["close"]
    ema_20 = features["ema_20"]
    ema_50 = features["ema_50"]

    if close > ema_20 and ema_20 > ema_50:
        return "BULLISH"

    if close < ema_20 and ema_20 < ema_50:
        return "BEARISH"

    return "NEUTRAL"


def classify_momentum(features: dict) -> str:
    """Classify RSI according to TARK strategy rules."""

    rsi = features["rsi_14"]

    if 55 <= rsi <= 70:
        return "BULLISH_CONFIRMED"

    if 30 <= rsi <= 45:
        return "BEARISH_CONFIRMED"

    if rsi > 70:
        return "OVEREXTENDED_BULLISH"

    if rsi < 30:
        return "OVEREXTENDED_BEARISH"

    return "NEUTRAL"


def evaluate_opportunity(
    symbol: str,
    hourly_features: dict,
    entry_features: dict,
) -> dict:
    """
    Evaluate a deterministic TARK trading opportunity.

    1H establishes directional context.
    15M confirms entry conditions.
    """

    trend_1h = classify_trend(hourly_features)
    trend_15m = classify_trend(entry_features)

    momentum_15m = classify_momentum(entry_features)

    reasons = []

    # Bullish candidate
    if (
        trend_1h == "BULLISH"
        and trend_15m == "BULLISH"
        and momentum_15m == "BULLISH_CONFIRMED"
    ):
        reasons.extend(
            [
                "1H trend is bullish",
                "15M trend confirms bullish direction",
                "15M RSI confirms bullish momentum",
            ]
        )

        return {
            "symbol": symbol,
            "direction": "BULLISH",
            "action": "CANDIDATE",
            "strategy": "BULL_CALL_SPREAD",
            "reasons": reasons,
        }

    # Bearish candidate
    if (
        trend_1h == "BEARISH"
        and trend_15m == "BEARISH"
        and momentum_15m == "BEARISH_CONFIRMED"
    ):
        reasons.extend(
            [
                "1H trend is bearish",
                "15M trend confirms bearish direction",
                "15M RSI confirms bearish momentum",
            ]
        )

        return {
            "symbol": symbol,
            "direction": "BEARISH",
            "action": "CANDIDATE",
            "strategy": "BEAR_PUT_SPREAD",
            "reasons": reasons,
        }

    # No sufficiently aligned opportunity
    reasons.extend(
        [
            f"1H trend: {trend_1h}",
            f"15M trend: {trend_15m}",
            f"15M momentum: {momentum_15m}",
            "Conditions are not sufficiently aligned for a trade candidate",
        ]
    )

    return {
        "symbol": symbol,
        "direction": "NEUTRAL",
        "action": "WAIT",
        "strategy": None,
        "reasons": reasons,
    }