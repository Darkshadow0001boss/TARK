from typing import Any, Dict


class RiskAgent:
    """
    TARK's deterministic risk gate.

    The Risk Agent decides whether a trading opportunity is safe
    enough to proceed to options contract selection.

    AI reasoning may provide evidence, but this agent applies
    deterministic safety rules.
    """

    def evaluate(
        self,
        opportunity: Dict[str, Any],
        thesis: Dict[str, Any],
        hourly_features: Dict[str, Any],
        entry_features: Dict[str, Any],
    ) -> Dict[str, Any]:

        reasons = []

        # Rule 1: Only deterministic candidates can proceed.
        if opportunity.get("action") != "CANDIDATE":
            return {
                "decision": "WAIT",
                "approved": False,
                "reasons": [
                    "Opportunity Engine did not identify a valid trade candidate"
                ],
            }

        # Rule 2: AI confidence must not be LOW.
        confidence = thesis.get("confidence", "LOW")

        if confidence == "LOW":
            return {
                "decision": "REJECT",
                "approved": False,
                "reasons": [
                    "Thesis Agent confidence is LOW"
                ],
            }

        # Rule 3: Reject overextended momentum.
        rsi = entry_features.get("rsi_14")

        if rsi is not None:
            if rsi > 75:
                return {
                    "decision": "REJECT",
                    "approved": False,
                    "reasons": [
                        f"Entry RSI is overextended at {rsi}"
                    ],
                }

            if rsi < 25:
                return {
                    "decision": "REJECT",
                    "approved": False,
                    "reasons": [
                        f"Entry RSI is oversold at {rsi}"
                    ],
                }

        # Rule 4: Require minimum volume participation.
        volume_ratio = entry_features.get("volume_ratio")

        if volume_ratio is not None and volume_ratio < 0.20:
            return {
                "decision": "REJECT",
                "approved": False,
                "reasons": [
                    f"Volume participation is too weak: {volume_ratio}"
                ],
            }

        # Rule 5: Too many contradictions reduce confidence.
        contradictions = thesis.get("contradictions", [])

        if len(contradictions) >= 3:
            return {
                "decision": "REJECT",
                "approved": False,
                "reasons": [
                    "Thesis contains too many significant contradictions"
                ],
            }

        # All deterministic checks passed.
        reasons.append(
            "Opportunity is a valid deterministic candidate"
        )

        reasons.append(
            f"Thesis confidence is {confidence}"
        )

        reasons.append(
            "Risk checks passed"
        )

        return {
            "decision": "APPROVE",
            "approved": True,
            "reasons": reasons,
        }