from typing import Any, Dict


class FallbackThesisAgent:

    """
    Deterministic fallback thesis generator.

    Used when the external AI provider is unavailable,
    rate-limited, or returns an invalid response.

    This ensures the TARK decision pipeline remains
    operational without depending completely on Gemini.
    """

    def analyze(

        self,

        symbol: str,

        opportunity: Dict[str, Any],

        hourly_features: Dict[str, Any],

        entry_features: Dict[str, Any],

    ) -> Dict[str, Any]:

        direction = opportunity.get(
            "direction",
            "NEUTRAL",
        )


        hourly_close = float(
            hourly_features.get(
                "close",
                0,
            ) or 0
        )

        hourly_ema_20 = float(
            hourly_features.get(
                "ema_20",
                0,
            ) or 0
        )

        hourly_ema_50 = float(
            hourly_features.get(
                "ema_50",
                0,
            ) or 0
        )


        entry_close = float(
            entry_features.get(
                "close",
                0,
            ) or 0
        )

        entry_ema_20 = float(
            entry_features.get(
                "ema_20",
                0,
            ) or 0
        )

        entry_ema_50 = float(
            entry_features.get(
                "ema_50",
                0,
            ) or 0
        )


        hourly_rsi = float(
            hourly_features.get(
                "rsi_14",
                50,
            ) or 50
        )

        entry_rsi = float(
            entry_features.get(
                "rsi_14",
                50,
            ) or 50
        )


        volume_ratio = float(
            entry_features.get(
                "volume_ratio",
                1,
            ) or 1
        )


        supporting_evidence = []

        contradictions = []


        # ==================================================
        # TREND EVIDENCE
        # ==================================================

        if direction == "BULLISH":

            if (
                hourly_close > hourly_ema_20
                and hourly_close > hourly_ema_50
            ):

                supporting_evidence.append(
                    "Hourly price remains above both "
                    "the 20 EMA and 50 EMA, supporting "
                    "a bullish market structure."
                )


            if (
                entry_close > entry_ema_20
                and entry_close > entry_ema_50
            ):

                supporting_evidence.append(
                    "Entry timeframe structure confirms "
                    "the bullish direction."
                )


            if (
                hourly_rsi > 50
                and entry_rsi > 50
            ):

                supporting_evidence.append(
                    "RSI remains above the neutral 50 "
                    "level across both timeframes."
                )


            failure_scenario = (
                "Price loses the short-term moving average "
                "structure and breaks below the key "
                "hourly trend levels."
            )


        elif direction == "BEARISH":

            if (
                hourly_close < hourly_ema_20
                and hourly_close < hourly_ema_50
            ):

                supporting_evidence.append(
                    "Hourly price remains below both "
                    "the 20 EMA and 50 EMA, supporting "
                    "a bearish market structure."
                )


            if (
                entry_close < entry_ema_20
                and entry_close < entry_ema_50
            ):

                supporting_evidence.append(
                    "Entry timeframe structure confirms "
                    "the bearish direction."
                )


            if (
                hourly_rsi < 50
                and entry_rsi < 50
            ):

                supporting_evidence.append(
                    "RSI remains below the neutral 50 "
                    "level across both timeframes."
                )


            failure_scenario = (
                "Price recovers above the short-term "
                "moving average structure and invalidates "
                "the bearish directional thesis."
            )


        else:

            contradictions.append(
                "No strong directional alignment is "
                "currently present."
            )

            failure_scenario = (
                "The market develops a strong directional "
                "move against the current neutral thesis."
            )


        # ==================================================
        # VOLUME ANALYSIS
        # ==================================================

        if volume_ratio >= 2:

            supporting_evidence.append(
                "Entry timeframe volume is elevated, "
                "indicating increased market participation."
            )


        if volume_ratio >= 4:

            contradictions.append(
                "Extremely elevated volume may represent "
                "exhaustion or a potential reversal event."
            )


        # ==================================================
        # MOMENTUM CONTRADICTIONS
        # ==================================================

        if direction == "BEARISH":

            if entry_rsi > hourly_rsi:

                contradictions.append(
                    "Entry RSI is stronger than hourly RSI, "
                    "indicating possible weakening bearish "
                    "momentum."
                )


        elif direction == "BULLISH":

            if entry_rsi < hourly_rsi:

                contradictions.append(
                    "Entry RSI is weaker than hourly RSI, "
                    "indicating possible weakening bullish "
                    "momentum."
                )


        # ==================================================
        # CONFIDENCE
        # ==================================================

        if len(contradictions) == 0:

            confidence = "HIGH"

        elif len(contradictions) <= 2:

            confidence = "MEDIUM"

        else:

            confidence = "LOW"


        # ==================================================
        # RETURN THESIS
        # ==================================================

        return {

            "symbol":
                symbol,

            "direction":
                direction,

            "confidence":
                confidence,

            "supporting_evidence":
                supporting_evidence,

            "contradictions":
                contradictions,

            "neutral_scenario": (
                "Price consolidates and directional "
                "momentum weakens, causing the market "
                "structure to become inconclusive."
            ),

            "failure_scenario":
                failure_scenario,

            "reasoning_summary": (
                "This thesis was generated using TARK's "
                "deterministic fallback analysis because "
                "the external AI provider was unavailable."
            ),

            "source":
                "DETERMINISTIC_FALLBACK",
        }