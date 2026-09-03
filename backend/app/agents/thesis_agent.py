from typing import Any, Dict

from app.ai.provider import AIProvider


class ThesisAgent:
    """
    TARK's Thesis Agent.

    Receives quantitative market evidence and critically evaluates
    a proposed trading opportunity.
    """

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def analyze(
        self,
        symbol: str,
        hourly_features: Dict[str, Any],
        entry_features: Dict[str, Any],
        opportunity: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze the market evidence and return a structured thesis.
        """

        symbol = opportunity.get("symbol", "UNKNOWN")

        prompt = f"""
You are the Thesis Agent for TARK, an autonomous AI-powered
options trading system.

Your responsibility is NOT to blindly recommend trades.

Critically evaluate the quantitative evidence provided.

Identify:

1. Evidence supporting the proposed direction
2. Contradictions or risks
3. A neutral scenario where the evidence becomes inconclusive
4. A failure scenario that invalidates the thesis
5. A concise reasoning summary

IMPORTANT RULES:

- Do not invent market data.
- Only use the provided data.
- Be skeptical of weak signals.
- Identify contradictions even when the opportunity looks strong.
- Do not place trades.
- Do not select options contracts.
- Return ONLY valid JSON.
- Do not include markdown formatting.

SYMBOL:

{symbol}

HOURLY FEATURES:

{hourly_features}

ENTRY FEATURES:

{entry_features}

OPPORTUNITY:

{opportunity}

Return JSON in exactly this structure:

{{
    "symbol": "{symbol}",
    "direction": "BULLISH, BEARISH, or NEUTRAL",
    "confidence": "LOW, MEDIUM, or HIGH",
    "supporting_evidence": [
        "evidence"
    ],
    "contradictions": [
        "contradiction"
    ],
    "neutral_scenario": "description",
    "failure_scenario": "description",
    "reasoning_summary": "concise summary"
}}
"""

        return self.provider.generate_json(prompt)