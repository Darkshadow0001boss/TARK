from http.client import HTTPException
import time

from app.config import TARK_DRY_RUN

from app.engines.opportunity import (
    evaluate_opportunity,
)

from app.engines.fragility import (
    calculate_fragility,
)

from app.options.contract_selector import (
    select_option_spread,
)

from app.engines.spread_pricing import (
    calculate_spread_pricing,
)

from app.risk.risk_governor import (
    RiskGovernor,
)

from app.brokers.account_client import (
    get_account_snapshot,
)

from app.ai.gemini_provider import (
    GeminiProvider,
)

from app.agents.thesis_agent import (
    ThesisAgent,
)

from app.execution.order_executor import (
    OrderExecutor,
)

from app.services.trade_registry import (
    TradeRegistry,
)

from app.agents.fallback_thesis import (
    FallbackThesisAgent,
)

class TarkOrchestrator:

    """
    TARK Core Decision Pipeline.

    Workflow:

    Opportunity
        ↓
    AI Thesis
        ↓
    Fragility
        ↓
    Options Selection
        ↓
    Live Pricing
        ↓
    Risk Governance
        ↓
    Execution
    """

    def __init__(
        self,
        dry_run: bool = TARK_DRY_RUN,
    ):

        self.dry_run = dry_run

        self.ai_provider = GeminiProvider()

        self.thesis_agent = ThesisAgent(
            self.ai_provider
        )

        self.risk_governor = RiskGovernor()

        self.order_executor = OrderExecutor(
            dry_run=self.dry_run
        )

        self.registry = TradeRegistry()

        self.fallback_thesis_agent = (
            FallbackThesisAgent()
        )


    # ======================================================
    # ANALYZE
    # ======================================================

    def analyze(
        self,
        symbol: str,
        hourly_features: dict,
        entry_features: dict,
        execute: bool = False,
    ) -> dict:

        symbol = symbol.upper()


        # ==================================================
        # STEP 1 — OPPORTUNITY ENGINE
        # ==================================================

        opportunity = evaluate_opportunity(

            symbol=symbol,

            hourly_features=hourly_features,

            entry_features=entry_features,
        )


        # --------------------------------------------------
        # NO OPPORTUNITY
        # --------------------------------------------------

        if opportunity.get("action") == "WAIT":

            return {

                "symbol": symbol,

                "status": "WAIT",

                "stage": "OPPORTUNITY_ENGINE",

                "opportunity": opportunity,

                "thesis": {},

                "fragility": {},

                "contracts": {},

                "pricing": {},

                "risk": {},

                "execution": {},

                "message": (
                    "No sufficiently aligned trading "
                    "opportunity detected."
                ),
            }


        # ==================================================
        # STEP 2 — AI THESIS
        # ==================================================

        # ==================================================
        # STEP 2 — AI THESIS
        #
        # External AI is preferred, but TARK must remain
        # operational if the provider is unavailable.
        # ==================================================

        try:

            thesis = self.thesis_agent.analyze(

                symbol=symbol,

                opportunity=opportunity,

                hourly_features=hourly_features,

                entry_features=entry_features,
            )


            thesis_source = "GEMINI"


        except Exception as exc:

            thesis = (

                self.fallback_thesis_agent.analyze(

                    symbol=symbol,

                    opportunity=opportunity,

                    hourly_features=hourly_features,

                    entry_features=entry_features,
                )

            )


            thesis_source = (
                "DETERMINISTIC_FALLBACK"
            )


            thesis["ai_error"] = str(exc)


                # ==================================================
                # STEP 3 — FRAGILITY ENGINE
                # ==================================================

        fragility = calculate_fragility(

                    hourly_features=hourly_features,

                    entry_features=entry_features,

                    opportunity=opportunity,

                    thesis=thesis,
                )


        # ==================================================
        # STEP 4 — FRAGILITY GATE
        # ==================================================

        if fragility.get("decision") == "ABSTAIN":

            return {

                "symbol": symbol,

                "status": "ABSTAIN",

                "stage": "FRAGILITY_ENGINE",

                "opportunity": opportunity,

                "thesis": thesis,

                "fragility": fragility,

                "contracts": {},

                "pricing": {},

                "risk": {},

                "execution": {},

                "message": (
                    "Trade candidate rejected due to "
                    "high structural fragility."
                ),
            }


        # ==================================================
        # STEP 5 — OPTIONS CONTRACT SELECTION
        # ==================================================

        underlying_price = float(
            entry_features["close"]
        )

        contracts = select_option_spread(

            symbol=symbol,

            strategy=opportunity["strategy"],

            underlying_price=underlying_price,
        )


        # ==================================================
        # STEP 6 — LIVE SPREAD PRICING
        # ==================================================

        pricing = calculate_spread_pricing(

            long_symbol=(
                contracts["long_leg"]["symbol"]
            ),

            short_symbol=(
                contracts["short_leg"]["symbol"]
            ),
        )


        # ==================================================
        # STEP 7 — ACCOUNT STATE
        # ==================================================

        account = get_account_snapshot()


        # ==================================================
        # STEP 8 — PORTFOLIO STATE
        # ==================================================

        portfolio_state = (
            self._get_portfolio_state()
        )
        if (
            portfolio_state["start_of_day_equity"]
            <= 0
        ):

            portfolio_state[
                "start_of_day_equity"
            ] = float(
                account["equity"]
            )

        # ==================================================
        # STEP 9 — PROPOSED POSITION
        # ==================================================

        proposed_position = {

            "net_debit":
                pricing["estimated_debit"],

            "contracts":
                5,
        }


        # ==================================================
        # STEP 10 — RISK GOVERNOR
        # ==================================================

        risk = self.risk_governor.evaluate(

            decision=fragility["decision"],

            symbol=symbol,

            strategy=opportunity["strategy"],

            account_equity=float(
                account["equity"]
            ),

            start_of_day_equity=float(
                portfolio_state[
                    "start_of_day_equity"
                ]
            ),

            buying_power=float(
                account["buying_power"]
            ),

            open_positions=(
                portfolio_state[
                    "open_positions"
                ]
            ),

            daily_realized_pnl=float(
                portfolio_state[
                    "daily_realized_pnl"
                ]
            ),

            new_entries_today=int(
                portfolio_state[
                    "new_entries_today"
                ]
            ),

            proposed_position=proposed_position,
        )


        # ==================================================
        # STEP 11 — RISK GATE
        # ==================================================

        if risk.get("status") != "APPROVED":

            return {

                "symbol": symbol,

                "status":
                    risk.get(
                        "status",
                        "REJECTED",
                    ),

                "stage":
                    "RISK_GOVERNOR",

                "opportunity":
                    opportunity,

                "thesis":
                    thesis,

                "fragility":
                    fragility,

                "contracts":
                    contracts,

                "pricing":
                    pricing,

                "risk":
                    risk,

                "execution":
                    {},

                "message":
                    "Trade was not approved by "
                    "the Risk Governor.",
            }


        # ==================================================
        # STEP 12 — BUILD EXECUTION TRADE
        # ==================================================

        trade = {

            "strategy":
                contracts["strategy"],

            "symbol":
                contracts["symbol"],

            "expiration_date":
                contracts["expiration_date"],

            "long_leg":
                contracts["long_leg"],

            "short_leg":
                contracts["short_leg"],

            "limit_price":
                pricing["estimated_debit"],
        }

        # ==================================================
        # STEP 13 — EXECUTION
        #
        # Execution is explicitly controlled by the caller.
        # Analysis endpoints must never submit orders.
        # ==================================================

        if execute:

            execution = self.order_executor.execute(

                trade=trade,

                risk_result=risk,
            )

        else:

            execution = {

                "status": "READY_FOR_EXECUTION",

                "message": (
                    "Trade passed all TARK decision and risk "
                    "gates but has not been submitted."
                ),

                "trade": trade,
            }


        # ==================================================
        # STEP 14 — COMPLETE
        # ==================================================

        return {

            "symbol":
                symbol,

            "status":
                execution.get(
                    "status",
                    "COMPLETED",
                ),

            "stage":
                "EXECUTION_COMPLETE",

            "opportunity":
                opportunity,

            "thesis":
                thesis,

            "fragility":
                fragility,

            "contracts":
                contracts,

            "pricing":
                pricing,

            "risk":
                risk,

            "execution":
                execution,

            "execution_mode": (
                "NOT_EXECUTED"
                if not execute
                else (
                    "DRY_RUN"
                    if self.dry_run
                    else "PAPER"
                )
            ),

            "message":
                execution.get(
                    "message",
                    "TARK pipeline completed.",
                ),
        }


    # ======================================================
    # PORTFOLIO STATE
    # ======================================================

    def _get_portfolio_state(
            self,
       ) -> dict:

            """
            Build the portfolio state required by the
            Risk Governor from persisted TARK trades.

            Active positions are normalized into the
            structure expected by RiskGovernor.
            """

            trades = self.registry.get_all()

            active_statuses = (
                "OPEN",
                "SIMULATED",
            )

            # ==================================================
            # ACTIVE POSITIONS
            # ==================================================

            manageable_positions = []

            for trade in trades:

                if (
                    trade.get("position_status")
                    not in active_statuses
                ):
                    continue

                risk = trade.get("risk") or {}

                maximum_loss = risk.get(
                    "proposed_max_loss"
                )

                # Fail closed by preserving None if
                # risk data is missing. RiskGovernor will reject.
                manageable_positions.append(
                    {
                        "trade_id": trade.get("id"),

                        "symbol": trade.get("symbol"),

                        "strategy": trade.get("strategy"),

                        "position_status": trade.get(
                            "position_status"
                        ),

                        "maximum_loss": (
                            float(maximum_loss)
                            if maximum_loss is not None
                            else None
                        ),
                    }
                )

            # ==================================================
            # NEW ENTRIES TODAY
            #
            # MVP approximation.
            # ==================================================

            new_entries_today = len(
                manageable_positions
            )

            # ==================================================
            # START OF DAY EQUITY
            # ==================================================

            start_of_day_equity = 0.0

            for trade in reversed(trades):

                risk = trade.get("risk") or {}

                equity = risk.get(
                    "start_of_day_equity"
                )

                if equity:

                    start_of_day_equity = float(
                        equity
                    )

                    break

            return {

                "open_positions":
                    manageable_positions,

                "daily_realized_pnl":
                    0.0,

                "new_entries_today":
                    new_entries_today,

                "start_of_day_equity":
                    start_of_day_equity,
    }
