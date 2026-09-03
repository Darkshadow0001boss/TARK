from typing import Any, Dict, List, Optional

from app.services.trade_registry import TradeRegistry

from app.data.market_data import (
    get_hourly_bars,
    get_15m_bars,
)

from app.engines.quant_features import (
    calculate_features,
)

from app.engines.opportunity import (
    evaluate_opportunity,
)

from app.engines.fragility import (
    calculate_fragility,
)

from app.engines.spread_pricing import (
    calculate_spread_pricing,
)

from app.execution.order_executor import (
    OrderExecutor,
)


class PositionManager:

    """
    TARK Position Management Engine.

    Responsible for:

    - Monitoring OPEN and SIMULATED positions
    - Re-evaluating market structure
    - Recalculating fragility
    - Validating the original thesis
    - Calculating mark-to-market P&L
    - Deciding HOLD or EXIT
    - Executing simulated or real exits
    - Recording the complete position lifecycle

    Important:

    TradeRegistry is the source of truth for
    TARK's internal position lifecycle.

    Real broker positions should only be marked CLOSED
    after exit execution is confirmed.
    """

    # ======================================================
    # CONFIGURATION
    # ======================================================

    CRITICAL_FRAGILITY = 20

    MANAGEABLE_STATUSES = {
        "OPEN",
        "SIMULATED",
    }


    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(
        self,
        dry_run: bool = True,
    ):

        self.dry_run = dry_run

        self.registry = TradeRegistry()

        self.order_executor = OrderExecutor(
            dry_run=dry_run
        )


    # ======================================================
    # MANAGE ALL POSITIONS
    # ======================================================

    def manage_all(self) -> Dict[str, Any]:

        positions = (
            self.registry
            .get_manageable_positions()
        )

        results = []

        for position in positions:

            try:

                result = self.manage_position(
                    position
                )

                results.append(result)

            except Exception as exc:

                results.append(
                    {
                        "trade_id":
                            position.get("id"),

                        "symbol":
                            position.get("symbol"),

                        "status":
                            "ERROR",

                        "decision":
                            "ERROR",

                        "error":
                            str(exc),
                    }
                )

        return {

            "status":
                "COMPLETED",

            "positions_checked":
                len(positions),

            "results":
                results,
        }


    # ======================================================
    # MANAGE SINGLE POSITION
    # ======================================================

    def manage_position(
        self,
        position: Dict[str, Any],
    ) -> Dict[str, Any]:

        trade_id = position.get("id")

        symbol = position.get("symbol")

        position_status = position.get(
            "position_status"
        )

        # --------------------------------------------------
        # VALIDATE POSITION
        # --------------------------------------------------

        if not trade_id:

            raise ValueError(
                "Position is missing trade ID"
            )

        if not symbol:

            raise ValueError(
                "Position is missing symbol"
            )

        if (
            position_status
            not in self.MANAGEABLE_STATUSES
        ):

            return {

                "trade_id":
                    trade_id,

                "symbol":
                    symbol,

                "status":
                    "SKIPPED",

                "decision":
                    "NOT_MANAGEABLE",

                "reason":
                    (
                        "Position status is not "
                        "eligible for management."
                    ),

                "position_status":
                    position_status,
            }


        original_direction = position.get(
            "direction"
        )

        original_strategy = position.get(
            "strategy"
        )

        original_thesis = position.get(
            "thesis"
        ) or {}


        # ==================================================
        # MARKET DATA
        # ==================================================

        hourly_response = get_hourly_bars(
            symbol
        )

        entry_response = get_15m_bars(
            symbol
        )


        hourly_bars = (
            hourly_response.data.get(
                symbol,
                [],
            )
        )

        entry_bars = (
            entry_response.data.get(
                symbol,
                [],
            )
        )


        if not hourly_bars:

            raise ValueError(
                f"No hourly market data found for {symbol}"
            )


        if not entry_bars:

            raise ValueError(
                f"No 15-minute market data found for {symbol}"
            )


        # ==================================================
        # FEATURES
        # ==================================================

        hourly_features = calculate_features(
            hourly_bars
        )

        entry_features = calculate_features(
            entry_bars
        )


        # ==================================================
        # CURRENT OPPORTUNITY
        # ==================================================

        current_opportunity = (
            evaluate_opportunity(

                symbol=symbol,

                hourly_features=hourly_features,

                entry_features=entry_features,
            )
        )


        # ==================================================
        # CURRENT FRAGILITY
        # ==================================================

        current_fragility = (
            calculate_fragility(

                hourly_features=hourly_features,

                entry_features=entry_features,

                opportunity=current_opportunity,

                thesis=original_thesis,
            )
        )


        # ==================================================
        # CURRENT PRICING
        # ==================================================

        current_pricing = (
            self._get_current_pricing(
                position
            )
        )


        # ==================================================
        # MARK-TO-MARKET P&L
        # ==================================================

        position_pnl = (
            self._calculate_position_pnl(

                position=position,

                current_pricing=current_pricing,
            )
        )


        # ==================================================
        # THESIS VALIDATION
        # ==================================================

        thesis_valid = (
            self._is_thesis_valid(

                original_direction=original_direction,

                current_opportunity=current_opportunity,
            )
        )


        # ==================================================
        # DECISION
        # ==================================================

        decision = "HOLD"

        reason = (
            "Original trade thesis remains structurally valid."
        )


        # --------------------------------------------------
        # EXIT CONDITION 1
        #
        # Original thesis invalidated.
        # --------------------------------------------------

        if not thesis_valid:

            decision = "EXIT"

            reason = (
                "Market direction no longer matches "
                "the original TARK thesis."
            )


        # --------------------------------------------------
        # EXIT CONDITION 2
        #
        # Critical fragility threshold.
        # --------------------------------------------------

        elif (

            current_fragility.get(
                "score",
                0,
            )

            >= self.CRITICAL_FRAGILITY

        ):

            decision = "EXIT"

            reason = (
                "Structural fragility reached "
                "the critical exit threshold."
            )


        # --------------------------------------------------
        # EXIT CONDITION 3
        #
        # Fragility engine abstains.
        # --------------------------------------------------

        elif (

            current_fragility.get(
                "decision"
            )

            == "ABSTAIN"

        ):

            decision = "EXIT"

            reason = (
                "Current fragility analysis indicates "
                "the original trade thesis is no longer "
                "acceptable."
            )


        # ==================================================
        # HOLD
        # ==================================================

        if decision == "HOLD":

            return self._hold_position(

                trade_id=trade_id,

                symbol=symbol,

                strategy=original_strategy,

                reason=reason,

                current_opportunity=current_opportunity,

                current_fragility=current_fragility,

                current_pricing=current_pricing,

                position_pnl=position_pnl,

                thesis_valid=thesis_valid,
            )


        # ==================================================
        # EXIT
        # ==================================================

        return self._exit_position(

            position=position,

            reason=reason,

            current_opportunity=current_opportunity,

            current_fragility=current_fragility,

            current_pricing=current_pricing,

            position_pnl=position_pnl,

            thesis_valid=thesis_valid,
        )


    # ======================================================
    # HOLD POSITION
    # ======================================================

    def _hold_position(

        self,

        trade_id: str,

        symbol: str,

        strategy: Optional[str],

        reason: str,

        current_opportunity: Dict[str, Any],

        current_fragility: Dict[str, Any],

        current_pricing: Dict[str, Any],

        position_pnl: Dict[str, Any],

        thesis_valid: bool,

    ) -> Dict[str, Any]:

        details = {

            "opportunity":
                current_opportunity,

            "fragility":
                current_fragility,

            "thesis_valid":
                thesis_valid,

            "pricing":
                current_pricing,

            "pnl":
                position_pnl,
        }


        updated_trade = (

            self.registry
            .add_position_decision(

                trade_id=trade_id,

                decision="HOLD",

                reason=reason,

                details=details,
            )
        )


        return {

            "trade_id":
                trade_id,

            "symbol":
                symbol,

            "strategy":
                strategy,

            "decision":
                "HOLD",

            "reason":
                reason,

            "current_opportunity":
                current_opportunity,

            "current_fragility":
                current_fragility,

            "current_pricing":
                current_pricing,

            "position_pnl":
                position_pnl,

            "thesis_valid":
                thesis_valid,

            "position_status": (

                updated_trade.get(
                    "position_status"
                )

                if updated_trade

                else None
            ),
        }


    # ======================================================
    # CURRENT PRICING
    # ======================================================

    def _get_current_pricing(
        self,
        position: Dict[str, Any],
    ) -> Dict[str, Any]:

        contracts = position.get(
            "contracts"
        ) or {}


        long_leg = contracts.get(
            "long_leg"
        )

        short_leg = contracts.get(
            "short_leg"
        )


        if not long_leg:

            raise ValueError(
                "Position has no long option leg"
            )


        if not short_leg:

            raise ValueError(
                "Position has no short option leg"
            )


        long_symbol = long_leg.get(
            "symbol"
        )

        short_symbol = short_leg.get(
            "symbol"
        )


        if not long_symbol:

            raise ValueError(
                "Long option symbol unavailable"
            )


        if not short_symbol:

            raise ValueError(
                "Short option symbol unavailable"
            )


        return calculate_spread_pricing(

            long_symbol=long_symbol,

            short_symbol=short_symbol,
        )


    # ======================================================
    # POSITION QUANTITY
    # ======================================================

    def _get_quantity(
        self,
        position: Dict[str, Any],
    ) -> int:

        risk = position.get(
            "risk"
        ) or {}


        quantity = (

            risk.get(
                "approved_contracts"
            )

            or position.get(
                "approved_contracts"
            )

            or 0
        )


        try:

            quantity = int(quantity)

        except (
            TypeError,
            ValueError,
        ):

            return 0


        return max(quantity, 0)


    # ======================================================
    # UNREALIZED P&L
    # ======================================================

    def _calculate_position_pnl(

        self,

        position: Dict[str, Any],

        current_pricing: Dict[str, Any],

    ) -> Dict[str, Any]:

        original_pricing = position.get(
            "pricing"
        ) or {}


        entry_price = self._safe_float(

            original_pricing.get(
                "estimated_debit"
            )
        )


        current_mark = self._safe_float(

            current_pricing.get(
                "estimated_mid_debit"
            )
        )


        quantity = self._get_quantity(
            position
        )


        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if entry_price <= 0:

            return {

                "available":
                    False,

                "reason":
                    "Original entry price unavailable",
            }


        if current_mark <= 0:

            return {

                "available":
                    False,

                "reason":
                    "Current mark price unavailable",
            }


        if quantity <= 0:

            return {

                "available":
                    False,

                "reason":
                    "Position contract quantity unavailable",
            }


        # --------------------------------------------------
        # CALCULATE
        # --------------------------------------------------

        unrealized_pnl = (

            current_mark
            - entry_price

        ) * 100 * quantity


        unrealized_pnl_percent = (

            (
                current_mark
                - entry_price
            )

            / entry_price

        ) * 100


        return {

            "available":
                True,

            "entry_price":
                round(entry_price, 2),

            "current_mark":
                round(current_mark, 2),

            "contracts":
                quantity,

            "unrealized_pnl":
                round(unrealized_pnl, 2),

            "unrealized_pnl_percent":
                round(
                    unrealized_pnl_percent,
                    2,
                ),
        }


    # ======================================================
    # REALIZED P&L
    # ======================================================

    def _calculate_realized_pnl(

        self,

        position: Dict[str, Any],

        exit_credit: float,

    ) -> Dict[str, Any]:

        original_pricing = position.get(
            "pricing"
        ) or {}


        entry_debit = self._safe_float(

            original_pricing.get(
                "estimated_debit"
            )
        )


        quantity = self._get_quantity(
            position
        )


        if entry_debit <= 0:

            return {

                "available":
                    False,

                "reason":
                    "Original entry debit unavailable",
            }


        if exit_credit <= 0:

            return {

                "available":
                    False,

                "reason":
                    "Exit credit unavailable",
            }


        if quantity <= 0:

            return {

                "available":
                    False,

                "reason":
                    "Position contract quantity unavailable",
            }


        # --------------------------------------------------
        # Debit spread:
        #
        # Entry: Pay debit
        # Exit: Receive credit
        # --------------------------------------------------

        realized_pnl_value = (

            exit_credit
            - entry_debit

        ) * 100 * quantity


        realized_pnl_percent = (

            (
                exit_credit
                - entry_debit
            )

            / entry_debit

        ) * 100


        return {

            "available":
                True,

            "entry_price":
                round(entry_debit, 2),

            "exit_price":
                round(exit_credit, 2),

            "contracts":
                quantity,

            "realized_pnl":
                round(
                    realized_pnl_value,
                    2,
                ),

            "realized_pnl_percent":
                round(
                    realized_pnl_percent,
                    2,
                ),
        }


    # ======================================================
    # THESIS VALIDATION
    # ======================================================

    def _is_thesis_valid(

        self,

        original_direction: Optional[str],

        current_opportunity: Dict[str, Any],

    ) -> bool:

        current_direction = (

            current_opportunity.get(
                "direction"
            )
        )


        if not original_direction:

            return False


        if not current_direction:

            return False


        return (

            current_direction
            == original_direction
        )


    # ======================================================
    # EXIT POSITION
    # ======================================================

    def _exit_position(

        self,

        position: Dict[str, Any],

        reason: str,

        current_opportunity: Dict[str, Any],

        current_fragility: Dict[str, Any],

        current_pricing: Dict[str, Any],

        position_pnl: Dict[str, Any],

        thesis_valid: bool,

    ) -> Dict[str, Any]:


        trade_id = position["id"]

        symbol = position["symbol"]

        contracts = position.get(
            "contracts"
        ) or {}


        quantity = self._get_quantity(
            position
        )


        # ==================================================
        # EXIT CREDIT
        # ==================================================

        exit_credit = self._safe_float(

            current_pricing.get(
                "estimated_exit_credit"
            )
        )


        # ==================================================
        # VALIDATE EXIT
        # ==================================================

        if quantity <= 0:

            exit_execution = {

                "status":
                    "EXIT_BLOCKED",

                "reason":
                    "No valid contract quantity available for exit.",
            }


        elif exit_credit <= 0:

            exit_execution = {

                "status":
                    "EXIT_BLOCKED",

                "reason":
                    (
                        "Unable to determine a valid "
                        "executable exit credit."
                    ),
            }


        else:

            execution_position = {

                "strategy":
                    position.get("strategy"),

                "symbol":
                    symbol,

                "contracts":
                    quantity,

                "long_leg":
                    contracts.get("long_leg"),

                "short_leg":
                    contracts.get("short_leg"),
            }


            # ==============================================
            # CLOSE DEBIT SPREAD
            #
            # SELL long leg
            # BUY short leg
            #
            # Expected result: CREDIT
            # ==============================================

            exit_execution = (

                self.order_executor
                .close_position(

                    position=execution_position,

                    limit_price=exit_credit,
                )
            )


        # ==================================================
        # REALIZED P&L
        # ==================================================

        realized_pnl = {

            "available":
                False,

            "reason":
                "Position closure not confirmed",
        }


        # --------------------------------------------------
        # DRY RUN
        #
        # Simulated execution is treated as completed.
        # --------------------------------------------------

        if (

            exit_execution.get("status")
            == "DRY_RUN"

        ):

            realized_pnl = (

                self._calculate_realized_pnl(

                    position=position,

                    exit_credit=exit_credit,
                )
            )


        # ==================================================
        # RECORD EXIT DECISION
        # ==================================================

        self.registry.add_position_decision(

            trade_id=trade_id,

            decision="EXIT",

            reason=reason,

            details={

                "opportunity":
                    current_opportunity,

                "fragility":
                    current_fragility,

                "pricing":
                    current_pricing,

                "pnl":
                    position_pnl,

                "realized_pnl":
                    realized_pnl,

                "thesis_valid":
                    thesis_valid,

                "exit_execution":
                    exit_execution,
            },
        )


        # ==================================================
        # RECORD EXIT EXECUTION
        # ==================================================

        self.registry.record_exit_execution(

            trade_id=trade_id,

            exit_execution=exit_execution,
        )


        # ==================================================
        # CLOSE SIMULATED POSITION
        # ==================================================

        if (

            exit_execution.get("status")
            == "DRY_RUN"

        ):

            updated_trade = (

                self.registry
                .mark_closed(

                    trade_id=trade_id,

                    exit_execution=exit_execution,

                    realized_pnl=realized_pnl,
                )
            )


        # ==================================================
        # REAL EXECUTION
        #
        # Keep position open until broker confirms fill.
        # ==================================================

        else:

            updated_trade = (

                self.registry.get_trade(
                    trade_id
                )
            )


        # ==================================================
        # RETURN
        # ==================================================

        return {

            "trade_id":
                trade_id,

            "symbol":
                symbol,

            "strategy":
                position.get("strategy"),

            "decision":
                "EXIT",

            "reason":
                reason,

            "current_opportunity":
                current_opportunity,

            "current_fragility":
                current_fragility,

            "current_pricing":
                current_pricing,

            "position_pnl":
                position_pnl,

            "realized_pnl":
                realized_pnl,

            "thesis_valid":
                thesis_valid,

            "exit_execution":
                exit_execution,

            "position_status": (

                updated_trade.get(
                    "position_status"
                )

                if updated_trade

                else None
            ),
        }


    # ======================================================
    # SAFE FLOAT
    # ======================================================

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float:

        try:

            if value is None:

                return 0.0

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return 0.0