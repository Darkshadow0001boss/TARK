from app.services.market_scanner import (
    MarketScanner,
)

from app.services.tark_orchestrator import (
    TarkOrchestrator,
)

from app.services.position_manager import (
    PositionManager,
)

class AutonomousTrader:

    """
    TARK Autonomous Trading Controller.

    Responsibilities:

    1. Scan the market watchlist
    2. Identify valid candidates
    3. Rank candidates
    4. Select strongest candidate
    5. Run complete TARK pipeline
    """


    def __init__(self):

        self.scanner = MarketScanner()

        self.orchestrator = TarkOrchestrator()

        self.position_manager = PositionManager()


    # ======================================================
    # MAIN AUTONOMOUS WORKFLOW
    # ======================================================

    def run(self) -> dict:

        # ==================================================
        # STEP 1 — MANAGE EXISTING POSITIONS
        # ==================================================

        position_management = (
            self.position_manager.manage_all()
        )

        # ==================================================
        # STEP 1 — SCAN MARKET
        # ==================================================
        scan_result = self.scanner.scan()


        candidates = scan_result.get(

            "candidates",

            [],

        )


        scanned_count = scan_result.get(

            "scanned_count",

            0,

        )


        # ==================================================
        # STEP 2 — NO OPPORTUNITY
        # ==================================================

        if not candidates:


            return {

                "mode":
                    "AUTONOMOUS",

                "status":
                    "WAIT",

                "selected_symbol":
                    None,

                "scan_summary": {

                    "scanned_count":
                        scanned_count,

                    "candidate_count":
                        0,

                },

                "message": (

                    "TARK scanned the market universe "
                    "but found no sufficiently aligned "
                    "trading opportunities."

                ),

                "scan":
                    scan_result,


                # IMPORTANT:
                # Frontend always expects data.result

                "result": {

                    "status":
                        "WAIT",

                    "stage":
                        "OPPORTUNITY",

                    "message": (

                        "No sufficiently aligned "
                        "opportunity was found."

                    ),

                },

            }


        # ==================================================
        # STEP 3 — SELECT BEST CANDIDATE
        # ==================================================

        best_candidate = self.select_best_candidate(
            candidates
        )


        symbol = best_candidate.get(
            "symbol"
        )


        if not symbol:

            raise ValueError(
                "Selected candidate has no symbol"
            )


        # ==================================================
        # STEP 4 — RUN FULL TARK PIPELINE
        # ==================================================

        analysis = self.orchestrator.analyze(

            symbol=symbol,

            hourly_features=best_candidate.get(

                "hourly_features",

                {},

            ),

            entry_features=best_candidate.get(

                "entry_features",

                {},

            ),

        )


        # ==================================================
        # STEP 5 — NORMALIZED RESPONSE
        # ==================================================

        return {

            "mode":
                "AUTONOMOUS",

            "status":

                analysis.get(

                    "status",

                    "COMPLETED",

                ),

            "selected_symbol":
                symbol,


            "scan_summary": {

                "scanned_count":
                    scanned_count,

                "candidate_count":
                    len(candidates),

            },


            "selected_candidate": {

                "symbol":
                    symbol,

                "direction":

                    best_candidate.get(

                        "direction",

                        "NEUTRAL",

                    ),

            },


            "scan":
                scan_result,


            # IMPORTANT:
            # Same result structure as manual analysis

            "result":
                analysis,

        }


    # ======================================================
    # CANDIDATE RANKING
    # ======================================================

    def select_best_candidate(
        self,
        candidates: list,
    ) -> dict:

        """
        Rank candidates and return the strongest one.

        Ranking factors:

        - Volume confirmation
        - Trend strength
        - Directional momentum
        """


        def score(candidate):


            hourly = candidate.get(

                "hourly_features",

                {},

            )


            entry = candidate.get(

                "entry_features",

                {},

            )


            direction = candidate.get(

                "direction",

                "NEUTRAL",

            )


            # ==============================================
            # VOLUME SCORE
            # ==============================================

            volume_score = (

                float(
                    hourly.get(
                        "volume_ratio",
                        0,
                    ) or 0
                )

                +

                float(
                    entry.get(
                        "volume_ratio",
                        0,
                    ) or 0
                )

            )


            # ==============================================
            # TREND SCORE
            # ==============================================

            hourly_ema_20 = float(

                hourly.get(
                    "ema_20",
                    0,
                ) or 0

            )


            hourly_ema_50 = float(

                hourly.get(
                    "ema_50",
                    0,
                ) or 0

            )


            entry_ema_20 = float(

                entry.get(
                    "ema_20",
                    0,
                ) or 0

            )


            entry_ema_50 = float(

                entry.get(
                    "ema_50",
                    0,
                ) or 0

            )


            hourly_trend_strength = abs(

                hourly_ema_20

                -

                hourly_ema_50

            )


            entry_trend_strength = abs(

                entry_ema_20

                -

                entry_ema_50

            )


            trend_score = (

                hourly_trend_strength

                +

                entry_trend_strength

            )


            # ==============================================
            # MOMENTUM SCORE
            # ==============================================

            rsi = float(

                entry.get(
                    "rsi_14",
                    50,
                ) or 50

            )


            if direction == "BULLISH":

                momentum_score = max(

                    rsi - 50,

                    0,

                )


            elif direction == "BEARISH":

                momentum_score = max(

                    50 - rsi,

                    0,

                )


            else:

                momentum_score = 0


            # ==============================================
            # FINAL SCORE
            # ==============================================

            final_score = (

                volume_score * 10

                +

                trend_score

                +

                momentum_score

            )


            return final_score


        # ==================================================
        # RANK CANDIDATES
        # ==================================================

        ranked_candidates = sorted(

            candidates,

            key=score,

            reverse=True,

        )


        return ranked_candidates[0]