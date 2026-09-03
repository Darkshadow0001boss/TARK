from app.engines.position_evaluator import evaluate_position
from app.engines.spread_pricing import calculate_spread_pricing
from app.execution.order_executor import OrderExecutor


class PositionLifecycleService:

    def __init__(self):

        self.order_executor = OrderExecutor(
            dry_run=True
        )

    def monitor(
        self,
        position: dict,
        thesis_invalidated: bool = False,
    ) -> dict:

        # --------------------------------------------------
        # STEP 1 — VALIDATE POSITION
        # --------------------------------------------------

        required_fields = [
            "symbol",
            "strategy",
            "entry_debit",
            "long_leg",
            "short_leg",
            "contracts",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in position
        ]

        if missing_fields:

            return {
                "status": "ERROR",
                "message": "Missing required position data",
                "missing_fields": missing_fields,
            }

        # --------------------------------------------------
        # STEP 2 — LIVE SPREAD PRICING
        # --------------------------------------------------

        pricing = calculate_spread_pricing(
            long_symbol=position["long_leg"]["symbol"],
            short_symbol=position["short_leg"]["symbol"],
        )

        current_debit = pricing["estimated_debit"]

        # --------------------------------------------------
        # STEP 3 — POSITION EVALUATION
        # --------------------------------------------------

        evaluation = evaluate_position(
            entry_debit=position["entry_debit"],
            current_debit=current_debit,
            thesis_invalidated=thesis_invalidated,
        )

        # --------------------------------------------------
        # STEP 4 — HOLD
        # --------------------------------------------------

        if evaluation["action"] == "HOLD":

            return {
                "symbol": position["symbol"],
                "strategy": position["strategy"],
                "status": "HOLD",

                "position": position,
                "pricing": pricing,
                "evaluation": evaluation,

                "execution": None,
            }

        # --------------------------------------------------
        # STEP 5 — EXIT POSITION
        # --------------------------------------------------

        execution = self.order_executor.close_position(
            position=position,
            limit_price=current_debit,
        )

        # --------------------------------------------------
        # STEP 6 — EXIT COMPLETE
        # --------------------------------------------------

        return {
            "symbol": position["symbol"],
            "strategy": position["strategy"],
            "status": evaluation["action"],

            "position": position,
            "pricing": pricing,
            "evaluation": evaluation,

            "execution": execution,
        }