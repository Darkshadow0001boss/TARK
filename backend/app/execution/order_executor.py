from typing import Dict, Any

from alpaca.trading.enums import (
    OrderClass,
    OrderSide,
    TimeInForce,
)
from alpaca.trading.requests import (
    LimitOrderRequest,
    OptionLegRequest,
)

from app.brokers.alpaca_client import get_trading_client


class OrderExecutor:
    """
    Converts an approved TARK trade into an Alpaca
    multi-leg options order.

    Dry-run mode prevents any order from being sent.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def execute(
        self,
        trade: Dict[str, Any],
        risk_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        # --------------------------------------------------
        # SAFETY GATE 1 — Risk approval
        # --------------------------------------------------

        if risk_result["status"] != "APPROVED":

            return {
                "status": "BLOCKED",
                "reason": "Risk Governor did not approve the trade",
            }

        contracts = risk_result.get("approved_contracts", 0)

        if contracts <= 0:

            return {
                "status": "BLOCKED",
                "reason": "No contracts approved by Risk Governor",
            }

        # --------------------------------------------------
        # SAFETY GATE 2 — Required execution price
        # --------------------------------------------------

        if "limit_price" not in trade:

            return {
                "status": "BLOCKED",
                "reason": "Trade does not contain a limit_price",
            }

        limit_price = float(trade["limit_price"])

        if limit_price <= 0:

            return {
                "status": "BLOCKED",
                "reason": "Invalid limit_price",
            }

        # --------------------------------------------------
        # BUILD MULTI-LEG ORDER
        # --------------------------------------------------

        legs = [
            OptionLegRequest(
                symbol=trade["long_leg"]["symbol"],
                ratio_qty=1,
                side=OrderSide.BUY,
            ),
            OptionLegRequest(
                symbol=trade["short_leg"]["symbol"],
                ratio_qty=1,
                side=OrderSide.SELL,
            ),
        ]

        order_request = LimitOrderRequest(
            qty=contracts,
            limit_price=limit_price,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.MLEG,
            legs=legs,
        )

        # --------------------------------------------------
        # DRY RUN
        # --------------------------------------------------

        if self.dry_run:

            return {
                "status": "DRY_RUN",
                "message": "Multi-leg order built but NOT sent to Alpaca",
                "order": {
                    "strategy": trade["strategy"],
                    "symbol": trade["symbol"],
                    "contracts": contracts,
                    "limit_price": limit_price,
                    "expiration_date": trade["expiration_date"],
                    "legs": [
                        {
                            "symbol": trade["long_leg"]["symbol"],
                            "side": "BUY",
                            "ratio_qty": 1,
                        },
                        {
                            "symbol": trade["short_leg"]["symbol"],
                            "side": "SELL",
                            "ratio_qty": 1,
                        },
                    ],
                },
            }

        # --------------------------------------------------
        # PAPER / LIVE EXECUTION
        # --------------------------------------------------

        client = get_trading_client()

        submitted_order = client.submit_order(
            order_data=order_request
        )

        return {
            "status": "SUBMITTED",
            "message": "Multi-leg order submitted to Alpaca",
            "order_id": str(submitted_order.id),
            "order_status": str(submitted_order.status),
            "contracts": contracts,
        }

    # ======================================================
    # CLOSE POSITION
    # ======================================================

    def close_position(
        self,
        position: Dict[str, Any],
        limit_price: float,
    ) -> Dict[str, Any]:

        # --------------------------------------------------
        # VALIDATE POSITION
        # --------------------------------------------------

        contracts = position.get("contracts", 0)

        if contracts <= 0:

            return {
                "status": "BLOCKED",
                "reason": "Invalid position contract quantity",
            }

        if limit_price <= 0:

            return {
                "status": "BLOCKED",
                "reason": "Invalid limit_price",
            }

        # --------------------------------------------------
        # BUILD CLOSING LEGS
        #
        # Reverse the original spread:
        #
        # Long leg  → SELL
        # Short leg → BUY
        # --------------------------------------------------

        legs = [
            OptionLegRequest(
                symbol=position["long_leg"]["symbol"],
                ratio_qty=1,
                side=OrderSide.SELL,
            ),
            OptionLegRequest(
                symbol=position["short_leg"]["symbol"],
                ratio_qty=1,
                side=OrderSide.BUY,
            ),
        ]

        order_request = LimitOrderRequest(
            qty=contracts,
            limit_price=float(limit_price),
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.MLEG,
            legs=legs,
        )

        # --------------------------------------------------
        # DRY RUN
        # --------------------------------------------------

        if self.dry_run:

            return {
                "status": "DRY_RUN",
                "message": (
                    "Closing multi-leg order built but NOT sent to Alpaca"
                ),
                "order": {
                    "action": "CLOSE_POSITION",
                    "strategy": position["strategy"],
                    "symbol": position["symbol"],
                    "contracts": contracts,
                    "limit_price": round(limit_price, 2),
                    "legs": [
                        {
                            "symbol": position["long_leg"]["symbol"],
                            "side": "SELL",
                            "ratio_qty": 1,
                        },
                        {
                            "symbol": position["short_leg"]["symbol"],
                            "side": "BUY",
                            "ratio_qty": 1,
                        },
                    ],
                },
            }

        # --------------------------------------------------
        # PAPER / LIVE EXECUTION
        # --------------------------------------------------

        client = get_trading_client()

        submitted_order = client.submit_order(
            order_data=order_request
        )

        return {
            "status": "SUBMITTED",
            "message": "Closing multi-leg order submitted to Alpaca",
            "order_id": str(submitted_order.id),
            "order_status": str(submitted_order.status),
            "contracts": contracts,
        }