from math import floor
from typing import Any, Dict, List

# ============================================================
# TARK RISK GOVERNOR — MVP v1.0
# ============================================================

MAX_RISK_PER_TRADE = 0.01
MAX_PORTFOLIO_RISK = 0.02
MAX_OPEN_POSITIONS = 2
MAX_POSITIONS_PER_SYMBOL = 1
MAX_NEW_ENTRIES_PER_DAY = 2
DAILY_LOSS_LIMIT = 0.02
REDUCE_RISK_MULTIPLIER = 0.50

ALLOWED_STRATEGIES = {
    "BULL_CALL_SPREAD",
    "BEAR_PUT_SPREAD",
}

EXECUTABLE_DECISIONS = {
    "TRADE",
    "REDUCE",
}


class RiskGovernor:
    """
    TARK's deterministic capital and risk control layer.

    AI may propose a trade.
    Risk Governor decides whether capital may be allocated.

    This component must fail closed.
    """

    def evaluate(
        self,
        decision: str,
        symbol: str,
        strategy: str,
        account_equity: float,
        start_of_day_equity: float,
        buying_power: float,
        open_positions: List[Dict[str, Any]],
        daily_realized_pnl: float,
        new_entries_today: int,
        proposed_position: Dict[str, Any],
    ) -> Dict[str, Any]:

        reason_codes = []

        # ====================================================
        # 1. REQUIRED DATA VALIDATION
        # ====================================================

        required_values = [
            decision,
            symbol,
            strategy,
            account_equity,
            start_of_day_equity,
            buying_power,
            open_positions,
            daily_realized_pnl,
            new_entries_today,
            proposed_position,
        ]

        if any(value is None for value in required_values):
            return self._reject(
                ["INVALID_OR_MISSING_RISK_DATA"]
            )

        if account_equity <= 0 or start_of_day_equity <= 0:
            return self._reject(
                ["INVALID_ACCOUNT_STATE"]
            )

        if buying_power < 0:
            return self._reject(
                ["INVALID_ACCOUNT_STATE"]
            )

        # ====================================================
        # 2. UPSTREAM DECISION CHECK
        # ====================================================

        if decision not in EXECUTABLE_DECISIONS:
            return {
                "status": "REJECTED",
                "reason_codes": [
                    "UPSTREAM_DECISION_NOT_EXECUTABLE"
                ],
                "approved_contracts": 0,
            }

        # ====================================================
        # 3. STRATEGY VALIDATION
        # ====================================================

        if strategy not in ALLOWED_STRATEGIES:
            return self._reject(
                ["UNSUPPORTED_STRATEGY"]
            )

        # ====================================================
        # 4. DAILY LOSS CIRCUIT BREAKER
        # ====================================================

        max_daily_loss = (
            start_of_day_equity * DAILY_LOSS_LIMIT
        )

        daily_loss = (
            abs(daily_realized_pnl)
            if daily_realized_pnl < 0
            else 0
        )

        if daily_loss >= max_daily_loss:
            return self._reject(
                ["DAILY_LOSS_LIMIT_REACHED"]
            )

        # ====================================================
        # 5. MAXIMUM OPEN POSITIONS
        # ====================================================

        if len(open_positions) >= MAX_OPEN_POSITIONS:
            return self._reject(
                ["MAX_OPEN_POSITIONS_REACHED"]
            )

        # ====================================================
        # 6. DUPLICATE UNDERLYING CHECK
        # ====================================================

        for position in open_positions:

            if position.get("symbol") == symbol:
                return self._reject(
                    ["DUPLICATE_UNDERLYING_EXPOSURE"]
                )

        # ====================================================
        # 7. DAILY ENTRY LIMIT
        # ====================================================

        if new_entries_today >= MAX_NEW_ENTRIES_PER_DAY:
            return self._reject(
                ["DAILY_ENTRY_LIMIT_REACHED"]
            )

        # ====================================================
        # 8. VALIDATE PROPOSED POSITION DATA
        # ====================================================

        net_debit = proposed_position.get("net_debit")
        requested_contracts = proposed_position.get(
            "contracts"
        )

        if (
            net_debit is None
            or requested_contracts is None
        ):
            return self._reject(
                ["INVALID_OR_MISSING_RISK_DATA"]
            )

        if net_debit <= 0:
            return self._reject(
                ["INVALID_OR_MISSING_RISK_DATA"]
            )

        if requested_contracts <= 0:
            return {
                "status": "WAIT",
                "reason_codes": [
                    "CALCULATED_POSITION_SIZE_ZERO"
                ],
                "approved_contracts": 0,
            }

        # ====================================================
        # 9. POSITION SIZING
        # ====================================================

        max_trade_risk = (
            account_equity * MAX_RISK_PER_TRADE
        )

        risk_per_spread = round(net_debit * 100, 2)

        if risk_per_spread <= 0:
            return self._reject(
                ["INVALID_OR_MISSING_RISK_DATA"]
            )

        maximum_contracts = floor(
            max_trade_risk / risk_per_spread
        )

        if decision == "TRADE":

            approved_contracts = min(
                requested_contracts,
                maximum_contracts,
            )

        else:
            reduced_risk = (
                max_trade_risk
                * REDUCE_RISK_MULTIPLIER
            )

            reduced_contracts = floor(
                reduced_risk / risk_per_spread
            )

            approved_contracts = min(
                requested_contracts,
                reduced_contracts,
            )

        # ====================================================
        # 10. ZERO POSITION SIZE CHECK
        # ====================================================

        if approved_contracts <= 0:
            return {
                "status": "WAIT",
                "reason_codes": [
                    "CALCULATED_POSITION_SIZE_ZERO"
                ],
                "account_equity": account_equity,
                "max_trade_risk": max_trade_risk,
                "approved_contracts": 0,
            }

        # ====================================================
        # 11. PROPOSED POSITION MAXIMUM LOSS
        # ====================================================

        proposed_max_loss = round(
            net_debit
            * 100
            * approved_contracts,
            2,
        )

        # ====================================================
        # 12. MAXIMUM TRADE RISK CHECK
        # ====================================================

        if proposed_max_loss > max_trade_risk:
            return self._reject(
                ["TRADE_RISK_LIMIT_EXCEEDED"]
            )

        # ====================================================
        # 13. CURRENT PORTFOLIO RISK
        # ====================================================

        current_portfolio_risk = 0.0

        for position in open_positions:

            maximum_loss = position.get(
                "maximum_loss"
            )

            if maximum_loss is None:
                return self._reject(
                    ["INVALID_OR_MISSING_RISK_DATA"]
                )

            if maximum_loss < 0:
                return self._reject(
                    ["INVALID_OR_MISSING_RISK_DATA"]
                )

            current_portfolio_risk += maximum_loss

        # ====================================================
        # 14. PORTFOLIO RISK CHECK
        # ====================================================

        max_portfolio_risk = (
            account_equity
            * MAX_PORTFOLIO_RISK
        )

        proposed_portfolio_risk = round(
            current_portfolio_risk
            + proposed_max_loss,
            2,
        )

        if (
            proposed_portfolio_risk
            > max_portfolio_risk
        ):
            return self._reject(
                ["PORTFOLIO_RISK_LIMIT_EXCEEDED"]
            )

        # ====================================================
        # 15. BUYING POWER CHECK
        # ====================================================

        required_capital = proposed_max_loss

        if required_capital > buying_power:
            return self._reject(
                ["INSUFFICIENT_BUYING_POWER"]
            )

        # ====================================================
        # 16. APPROVED
        # ====================================================

        return {
            "status": "APPROVED",
            "reason_codes": reason_codes,
            "symbol": symbol,
            "strategy": strategy,
            "decision": decision,

            "account_equity": account_equity,
            "start_of_day_equity": start_of_day_equity,

            "max_trade_risk": max_trade_risk,
            "risk_per_spread": risk_per_spread,

            "requested_contracts": requested_contracts,
            "maximum_contracts": maximum_contracts,
            "approved_contracts": approved_contracts,

            "proposed_max_loss": proposed_max_loss,

            "current_portfolio_risk": (
                current_portfolio_risk
            ),

            "proposed_portfolio_risk": (
                proposed_portfolio_risk
            ),

            "max_portfolio_risk": (
                max_portfolio_risk
            ),

            "daily_realized_pnl": daily_realized_pnl,
            "daily_loss_limit": max_daily_loss,

            "buying_power": buying_power,
        }

    def _reject(
        self,
        reason_codes: List[str],
    ) -> Dict[str, Any]:
        """
        Return a deterministic rejection result.
        """

        return {
            "status": "REJECTED",
            "reason_codes": reason_codes,
            "approved_contracts": 0,
        }