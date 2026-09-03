import json
import os
import uuid

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class TradeRegistry:

    """
    Persistent backend registry for TARK decisions,
    simulated positions, and executed trade lifecycle data.

    MVP storage:

        data/tark_trades.json
    """

    def __init__(
        self,
        file_path: str = "data/tark_trades.json",
    ):

        self.file_path = file_path

        self._ensure_storage()


    # ==========================================================
    # STORAGE
    # ==========================================================

    def _ensure_storage(self) -> None:

        directory = os.path.dirname(
            self.file_path
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True,
            )

        if not os.path.exists(
            self.file_path
        ):

            with open(
                self.file_path,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    [],
                    file,
                    indent=2,
                )


    def _load(self) -> List[Dict[str, Any]]:

        self._ensure_storage()

        try:

            with open(
                self.file_path,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

                if isinstance(data, list):

                    return data

                return []

        except (
            json.JSONDecodeError,
            OSError,
        ):

            return []


    def _save(
        self,
        trades: List[Dict[str, Any]],
    ) -> None:

        self._ensure_storage()

        with open(
            self.file_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                trades,
                file,
                indent=2,
                default=str,
            )


    def _now(self) -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()


    # ==========================================================
    # RECORD DECISION
    # ==========================================================

    def record_decision(
        self,
        result: Optional[Dict[str, Any]],
        mode: str = "MANUAL",
        autonomous_data: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:

        trades = self._load()

        now = self._now()

        result = result or {}

        opportunity = (
            result.get("opportunity") or {}
        )

        fragility = (
            result.get("fragility") or {}
        )

        contracts = (
            result.get("contracts") or {}
        )

        pricing = (
            result.get("pricing") or {}
        )

        risk = (
            result.get("risk") or {}
        )

        execution = (
            result.get("execution") or {}
        )

        thesis = (
            result.get("thesis") or {}
        )

        status = (
            result.get("status")
            or "WAIT"
        )

        execution_status = (
            execution.get("status")
            or ""
        )

        # ======================================================
        # POSITION STATUS
        # ======================================================

        if execution_status == "DRY_RUN":

            position_status = "SIMULATED"

        elif execution_status in (
            "SUBMITTED",
            "FILLED",
        ):

            position_status = "OPEN"

        else:

            position_status = "NO_POSITION"


        record = {

            "id": str(uuid.uuid4()),

            "created_at": now,

            "updated_at": now,

            "mode": mode,

            # --------------------------------------------------
            # CORE DECISION
            # --------------------------------------------------

            "symbol": result.get("symbol"),

            "status": status,

            "stage": result.get("stage"),

            "message": result.get("message"),

            # --------------------------------------------------
            # OPPORTUNITY
            # --------------------------------------------------

            "direction": opportunity.get(
                "direction"
            ),

            "strategy": opportunity.get(
                "strategy"
            ),

            "opportunity": opportunity,

            # --------------------------------------------------
            # THESIS
            # --------------------------------------------------

            "thesis": thesis,

            # --------------------------------------------------
            # FRAGILITY
            # --------------------------------------------------

            "fragility_score": fragility.get(
                "score"
            ),

            "fragility_classification": fragility.get(
                "classification"
            ),

            "fragility_decision": fragility.get(
                "decision"
            ),

            "fragility": fragility,

            # --------------------------------------------------
            # OPTIONS
            # --------------------------------------------------

            "contracts": contracts,

            "pricing": pricing,

            # --------------------------------------------------
            # RISK
            # --------------------------------------------------

            "risk": risk,

            "approved_contracts": risk.get(
                "approved_contracts"
            ),

            "maximum_loss": risk.get(
                "proposed_max_loss"
            ),
            
            # --------------------------------------------------
            # EXECUTION
            # --------------------------------------------------

            "execution": execution,

            "execution_status": (
                execution_status
                or status
            ),

            "position_status": position_status,

            # --------------------------------------------------
            # POSITION MANAGEMENT
            # --------------------------------------------------

            "position_decision": (
                "PENDING"
                if position_status in (
                    "OPEN",
                    "SIMULATED",
                )
                else "NOT_APPLICABLE"
            ),

            "position_history": [],

            # --------------------------------------------------
            # AUTONOMOUS
            # --------------------------------------------------

            "autonomous": autonomous_data or {},
        }

        trades.append(record)

        self._save(trades)

        return record


    # ==========================================================
    # READ
    # ==========================================================

    def get_all(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:

        trades = self._load()

        trades = sorted(
            trades,
            key=lambda item: item.get(
                "created_at",
                "",
            ),
            reverse=True,
        )

        if limit is not None:

            trades = trades[:limit]

        return trades


    def get_trade(
        self,
        trade_id: str,
    ) -> Optional[Dict[str, Any]]:

        for trade in self._load():

            if trade.get("id") == trade_id:

                return trade

        return None


    def get_manageable_positions(
        self,
    ) -> List[Dict[str, Any]]:

        manageable_statuses = (
            "OPEN",
            "SIMULATED",
        )

        return [

            trade

            for trade in self._load()

            if trade.get(
                "position_status"
            )
            in manageable_statuses

        ]


    # ==========================================================
    # UPDATE
    # ==========================================================

    def update_trade(
        self,
        trade_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        trades = self._load()

        for index, trade in enumerate(trades):

            if trade.get("id") != trade_id:

                continue

            trade.update(updates)

            trade["updated_at"] = self._now()

            trades[index] = trade

            self._save(trades)

            return trade

        return None


    # ==========================================================
    # POSITION DECISION
    # ==========================================================

    def add_position_decision(
        self,
        trade_id: str,
        decision: str,
        reason: str,
        details: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Optional[Dict[str, Any]]:

        trade = self.get_trade(
            trade_id
        )

        if not trade:

            return None

        history = trade.get(
            "position_history",
            [],
        )

        history.append(
            {
                "timestamp": self._now(),

                "decision": decision,

                "reason": reason,

                "details": details or {},
            }
        )

        updates = {

            "position_decision": decision,

            "position_history": history,
        }

        if decision == "EXIT":

            updates[
                "position_status"
            ] = "EXIT_REQUESTED"

        elif decision == "HOLD":

            updates[
                "position_status"
            ] = trade.get(
                "position_status"
            )

        return self.update_trade(
            trade_id,
            updates,
        )
    # ==========================================================
    # RECORD ENTRY EXECUTION
    # ==========================================================

    def record_entry_execution(
        self,
        trade_id: str,
        execution_result: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        """
        Record the initial entry order submission.

        Important:

        SUBMITTED / ACCEPTED does NOT mean
        the position is open.

        Only FILLED creates an OPEN position.
        """

        execution_status = str(
            execution_result.get(
                "status",
                ""
            )
        ).upper()


        # ------------------------------------------------------
        # DEFAULT POSITION STATUS
        # ------------------------------------------------------

        position_status = "NO_POSITION"

        position_decision = "NOT_APPLICABLE"


        # ------------------------------------------------------
        # DRY RUN
        # ------------------------------------------------------

        if execution_status == "DRY_RUN":

            position_status = "SIMULATED"

            position_decision = "PENDING"


        # ------------------------------------------------------
        # ORDER SUBMITTED / ACCEPTED
        # ------------------------------------------------------

        elif execution_status in (

            "SUBMITTED",

            "ACCEPTED",

            "PENDING_NEW",

            "NEW",

        ):

            position_status = "PENDING_FILL"

            position_decision = "PENDING"


        # ------------------------------------------------------
        # PARTIALLY FILLED
        # ------------------------------------------------------

        elif execution_status in (

            "PARTIALLY_FILLED",

            "PARTIAL",

        ):

            position_status = "PARTIAL"

            position_decision = "PENDING"


        # ------------------------------------------------------
        # FILLED
        # ------------------------------------------------------

        elif execution_status == "FILLED":

            position_status = "OPEN"

            position_decision = "PENDING"


        # ------------------------------------------------------
        # FAILED ORDER STATES
        # ------------------------------------------------------

        elif execution_status in (

            "REJECTED",

            "CANCELED",

            "CANCELLED",

            "EXPIRED",

        ):

            position_status = "NO_POSITION"

            position_decision = "NOT_APPLICABLE"


        # ------------------------------------------------------
        # UPDATE
        # ------------------------------------------------------

        return self.update_trade(

            trade_id,

            {

                "execution":
                    execution_result,

                "execution_status":
                    execution_status,

                "position_status":
                    position_status,

                "position_decision":
                    position_decision,

            },
        )
# ==========================================================
# UPDATE ORDER STATUS
# ==========================================================

def update_order_status(
    self,
    trade_id: str,
    order_status: str,
    order_data: Optional[
        Dict[str, Any]
    ] = None,
) -> Optional[Dict[str, Any]]:

    """
    Update the latest Alpaca order status.

    This synchronizes:

    Alpaca Order Status
            ↓
    TARK Execution Status
            ↓
    TARK Position Status
    """

    normalized_status = str(
        order_status
    ).upper()


    # ------------------------------------------------------
    # DEFAULT
    # ------------------------------------------------------

    position_status = "NO_POSITION"

    position_decision = "NOT_APPLICABLE"


    # ------------------------------------------------------
    # ACTIVE ORDER STATES
    # ------------------------------------------------------

    if normalized_status in (

        "SUBMITTED",

        "ACCEPTED",

        "NEW",

        "PENDING_NEW",

        "PENDING_REPLACE",

        "REPLACED",

    ):

        position_status = "PENDING_FILL"

        position_decision = "PENDING"


    # ------------------------------------------------------
    # PARTIAL FILL
    # ------------------------------------------------------

    elif normalized_status in (

        "PARTIALLY_FILLED",

        "PARTIAL",

    ):

        position_status = "PARTIAL"

        position_decision = "PENDING"


    # ------------------------------------------------------
    # FILLED
    # ------------------------------------------------------

    elif normalized_status == "FILLED":

        position_status = "OPEN"

        position_decision = "PENDING"


    # ------------------------------------------------------
    # TERMINAL ORDER STATES
    # ------------------------------------------------------

    elif normalized_status in (

        "CANCELED",

        "CANCELLED",

        "REJECTED",

        "EXPIRED",

    ):

        position_status = "NO_POSITION"

        position_decision = "NOT_APPLICABLE"


    # ------------------------------------------------------
    # BUILD UPDATE
    # ------------------------------------------------------

    updates = {

        "execution_status":
            normalized_status,

        "position_status":
            position_status,

        "position_decision":
            position_decision,

    }


    # ------------------------------------------------------
    # SAVE LATEST ORDER DATA
    # ------------------------------------------------------

    if order_data:

        updates["order_status_data"] = (
            order_data
        )


    return self.update_trade(

        trade_id,

        updates,
    )

    # ==========================================================
    # RECORD EXIT EXECUTION
    # ==========================================================

    def record_exit_execution(
        self,
        trade_id: str,
        exit_execution: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        return self.update_trade(
            trade_id,
            {
                "exit_execution": exit_execution,
            },
        )


    # ==========================================================
    # MARK CLOSED
    # ==========================================================

    def mark_closed(
        self,
        trade_id: str,
        exit_execution: Dict[str, Any],
        realized_pnl: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Optional[Dict[str, Any]]:

        return self.update_trade(

            trade_id,

            {

                "position_status": "CLOSED",

                "position_decision": "EXIT",

                "exit_execution": exit_execution,

                "realized_pnl":
                    realized_pnl or {},

                "closed_at": self._now(),
            },
        )