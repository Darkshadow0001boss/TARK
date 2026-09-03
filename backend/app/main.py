from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.brokers.alpaca_client import (
    get_trading_client,
)

from app.data.market_data import (
    get_daily_bars,
    get_hourly_bars,
    get_15m_bars,
)

from app.engines.quant_features import (
    calculate_features,
)

from app.engines.opportunity import (
    evaluate_opportunity,
)

from app.services.tark_orchestrator import (
    TarkOrchestrator,
)

from app.services.market_scanner import (
    MarketScanner,
)

from app.services.autonomous_trader import (
    AutonomousTrader,
)

from app.services.trade_registry import (
    TradeRegistry,
)

from app.services.position_manager import (
    PositionManager,
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="TARK",

    description=(
        "Reason Before Risk — "
        "Autonomous AI-Powered Options Trading Agent"
    ),

    version="0.2.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tark-7pf.pages.dev",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "name": "TARK",

        "message": "Reason Before Risk",

        "status": "running",

        "version": "0.2.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check():

    return {

        "status": "healthy",
    }


# ============================================================
# ACCOUNT
# ============================================================

@app.get("/account")
def get_account():

    """
    Retrieve Alpaca account information.
    """

    try:

        client = get_trading_client()

        account = client.get_account()

        return {

            "status": str(
                account.status
            ),

            "portfolio_value": str(
                account.portfolio_value
            ),

            "equity": str(
                account.equity
            ),

            "buying_power": str(
                account.buying_power
            ),

            "cash": str(
                account.cash
            ),
        }

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Unable to connect to Alpaca: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# MARKET DATA
# ============================================================

@app.get("/market/{symbol}")
def get_market(symbol: str):

    """
    Retrieve recent daily market bars.
    """

    try:

        symbol = symbol.upper()

        bars = get_daily_bars(
            symbol
        )

        data = []

        for bar in bars.data.get(
            symbol,
            [],
        ):

            data.append(
                {

                    "timestamp":
                        bar.timestamp.isoformat(),

                    "open":
                        bar.open,

                    "high":
                        bar.high,

                    "low":
                        bar.low,

                    "close":
                        bar.close,

                    "volume":
                        bar.volume,
                }
            )

        return {

            "symbol": symbol,

            "bars": data,

            "count": len(data),
        }

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Unable to retrieve market data: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# MARKET SCAN
# ============================================================

@app.get("/scan")
def scan_market():

    """
    Scan the predefined TARK market universe
    and return detected candidates.
    """

    try:

        scanner = MarketScanner()

        result = scanner.scan()

        return result

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail={

                "message":
                    "Market scan failed",

                "error":
                    str(exc),
            },
        )


# ============================================================
# FEATURES
# ============================================================

@app.get("/features/{symbol}")
def get_features(symbol: str):

    """
    Calculate TARK quantitative features.
    """

    try:

        symbol = symbol.upper()

        bars_response = (
            get_daily_bars(symbol)
        )

        bars = bars_response.data.get(
            symbol,
            [],
        )

        features = calculate_features(
            bars
        )

        return {

            "symbol": symbol,

            "features": features,
        }

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Unable to calculate features: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# OPPORTUNITY ENGINE
# ============================================================

@app.get("/opportunity/{symbol}")
def get_opportunity(symbol: str):

    """
    Evaluate a TARK trading opportunity.
    """

    try:

        symbol = symbol.upper()

        hourly_response = (
            get_hourly_bars(symbol)
        )

        entry_response = (
            get_15m_bars(symbol)
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

        hourly_features = (
            calculate_features(
                hourly_bars
            )
        )

        entry_features = (
            calculate_features(
                entry_bars
            )
        )

        opportunity = (
            evaluate_opportunity(

                symbol=symbol,

                hourly_features=
                    hourly_features,

                entry_features=
                    entry_features,
            )
        )

        return {

            "symbol": symbol,

            "hourly_features":
                hourly_features,

            "entry_features":
                entry_features,

            "opportunity":
                opportunity,
        }

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Unable to evaluate opportunity: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# FULL TARK ANALYSIS
# ============================================================

@app.get("/analyze/{symbol}")
def analyze_symbol(symbol: str):

    """
    Run the complete TARK decision pipeline.

    The completed decision is also persisted
    in the backend Trade Registry.
    """

    try:

        symbol = symbol.upper()


        # --------------------------------------------------
        # GET MARKET DATA
        # --------------------------------------------------

        hourly_response = (
            get_hourly_bars(symbol)
        )

        entry_response = (
            get_15m_bars(symbol)
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


        # --------------------------------------------------
        # VALIDATE DATA
        # --------------------------------------------------

        if not hourly_bars:

            raise HTTPException(

                status_code=404,

                detail=(
                    "No hourly market data "
                    f"found for {symbol}"
                ),
            )


        if not entry_bars:

            raise HTTPException(

                status_code=404,

                detail=(
                    "No 15-minute market data "
                    f"found for {symbol}"
                ),
            )


        # --------------------------------------------------
        # CALCULATE FEATURES
        # --------------------------------------------------

        hourly_features = (
            calculate_features(
                hourly_bars
            )
        )

        entry_features = (
            calculate_features(
                entry_bars
            )
        )


        # --------------------------------------------------
        # RUN TARK
        # --------------------------------------------------

        orchestrator = (
            TarkOrchestrator()
        )

        result = (
            orchestrator.analyze(

                symbol=symbol,

                hourly_features=
                    hourly_features,

                entry_features=
                    entry_features,
            )
        )


        # --------------------------------------------------
        # RECORD DECISION
        # --------------------------------------------------

        registry = TradeRegistry()

        registry_record = (
            registry.record_decision(

                result=result,

                mode="MANUAL",
            )
        )


        # --------------------------------------------------
        # RETURN
        # --------------------------------------------------

        return {

            "symbol": symbol,

            "pipeline": {

                "hourly_features":
                    hourly_features,

                "entry_features":
                    entry_features,
            },

            "result": result,

            "registry_id":
                registry_record["id"],
        }


    except HTTPException:

        raise


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail={

                "message":
                    "TARK analysis failed",

                "error":
                    str(exc),
            },
        )


# ============================================================
# AUTONOMOUS TARK
# ============================================================

@app.get("/autonomous")
def run_autonomous_tark():

    """
    Run TARK in autonomous mode.

    Workflow:

    Market Scan
        ↓
    Candidate Selection
        ↓
    TARK Decision Pipeline
        ↓
    Risk Governance
        ↓
    Execution / Simulation
        ↓
    Trade Registry
    """

    try:

        trader = AutonomousTrader()

        autonomous_result = trader.run()


        # --------------------------------------------------
        # NORMALIZE DECISION
        # --------------------------------------------------

        decision = (
            autonomous_result.get("result")
            or {
                "symbol": autonomous_result.get(
                    "selected_symbol"
                ),

                "status": autonomous_result.get(
                    "status",
                    "WAIT",
                ),

                "stage": "AUTONOMOUS_SCAN",

                "message": autonomous_result.get(
                    "message"
                ),

                "opportunity": {},

                "thesis": {},

                "fragility": {},

                "contracts": {},

                "pricing": {},

                "risk": {},

                "execution": {},
            }
        )


        # --------------------------------------------------
        # RECORD
        # --------------------------------------------------

        registry = TradeRegistry()

        registry_record = (

            registry.record_decision(

                result=decision,

                mode="AUTONOMOUS",

                autonomous_data={

                    "selected_symbol":
                        autonomous_result.get(
                            "selected_symbol"
                        ),

                    "scan_summary":
                        autonomous_result.get(
                            "scan_summary"
                        ),

                    "scanned_count":
                        autonomous_result.get(
                            "scan_summary",
                            {},
                        ).get(
                            "scanned_count"
                        ),

                    "candidate_count":
                        autonomous_result.get(
                            "scan_summary",
                            {},
                        ).get(
                            "candidate_count"
                        ),
                },
            )
        )


        return {

            **autonomous_result,

            "registry_id":
                registry_record["id"],
        }


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail={

                "message":
                    "Autonomous TARK execution failed",

                "error":
                    str(exc),
            },
        )   

# ============================================================
# TARK TRADE HISTORY
# ============================================================

@app.get("/trades")
def get_trades(
    limit: int = 50,
):

    """
    Retrieve persisted TARK decisions and trades.
    """

    try:

        registry = TradeRegistry()

        trades = registry.get_all(
            limit=limit
        )

        return {

            "count": len(trades),

            "trades": trades,
        }

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail={
                "message":
                    "Unable to retrieve TARK trades",

                "error":
                    str(exc),
            },
        )


# ============================================================
# SINGLE TARK TRADE
# ============================================================

@app.get("/trades/{trade_id}")
def get_trade(
    trade_id: str,
):

    """
    Retrieve a single TARK decision.
    """

    try:

        registry = TradeRegistry()

        trade = registry.get_trade(
            trade_id
        )

        if not trade:

            raise HTTPException(

                status_code=404,

                detail="TARK trade not found",
            )

        return trade

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail={

                "message":
                    "Unable to retrieve TARK trade",

                "error":
                    str(exc),
            },
        )


# ============================================================
# ACTIVE POSITIONS
# ============================================================

@app.get("/positions")
def get_positions():

    """
    Retrieve positions currently managed by TARK.

    Includes:

    - OPEN Alpaca positions
    - SIMULATED dry-run positions
    """

    try:

        registry = TradeRegistry()

        positions = (
            registry
            .get_manageable_positions()
        )

        return {

            "count": len(
                positions
            ),

            "positions":
                positions,
        }

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail={

                "message":
                    "Unable to retrieve positions",

                "error":
                    str(exc),
            },
        )


# ============================================================
# POSITION MANAGEMENT
# ============================================================

@app.post("/positions/manage")
def manage_positions():

    """
    Run TARK Position Manager.

    For every active TARK position:

    1. Fetch fresh market data
    2. Recalculate features
    3. Re-evaluate opportunity
    4. Recalculate fragility
    5. Validate the original thesis
    6. Decide HOLD or EXIT
    """

    try:

        manager = PositionManager(
            dry_run=True
        )

        result = (
            manager.manage_all()
        )

        return result

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail={

                "message":
                    "Position management failed",

                "error":
                    str(exc),
            },
        )

    # ============================================================
# TARK PORTFOLIO SUMMARY
# ============================================================

# ============================================================
# TARK PORTFOLIO INTELLIGENCE
# ============================================================

@app.get("/portfolio/summary")
def get_portfolio_summary():

    """
    Return TARK portfolio intelligence.

    Includes:

    - Active positions
    - Closed positions
    - Unrealized P&L
    - Realized P&L
    - Total P&L
    - Winning trades
    - Losing trades
    - Win rate
    """

    try:

        registry = TradeRegistry()

        trades = registry.get_all()


        # ====================================================
        # POSITION GROUPS
        # ====================================================

        active_positions = [

            trade

            for trade in trades

            if trade.get(
                "position_status"
            )

            in (

                "OPEN",

                "SIMULATED",
            )
        ]


        closed_positions = [

            trade

            for trade in trades

            if trade.get(
                "position_status"
            )

            == "CLOSED"
        ]


        # ====================================================
        # UNREALIZED P&L
        # ====================================================

        total_unrealized_pnl = 0.0

        positions_with_pnl = 0


        for position in active_positions:

            history = position.get(
                "position_history",
                [],
            )


            if not history:

                continue


            latest = history[-1]


            details = latest.get(
                "details",
                {},
            )


            pnl = details.get(
                "pnl",
                {},
            )


            if pnl.get("available"):

                total_unrealized_pnl += float(

                    pnl.get(
                        "unrealized_pnl",
                        0,
                    )

                )


                positions_with_pnl += 1


        # ====================================================
        # REALIZED P&L
        # ====================================================

        total_realized_pnl = 0.0

        winning_trades = 0

        losing_trades = 0

        breakeven_trades = 0

        closed_positions_with_pnl = 0


        for position in closed_positions:

            realized_pnl = position.get(
                "realized_pnl",
                {},
            )


            if not realized_pnl.get(
                "available"
            ):

                continue


            pnl_value = float(

                realized_pnl.get(
                    "realized_pnl",
                    0,
                )

            )


            total_realized_pnl += pnl_value

            closed_positions_with_pnl += 1


            if pnl_value > 0:

                winning_trades += 1


            elif pnl_value < 0:

                losing_trades += 1


            else:

                breakeven_trades += 1


        # ====================================================
        # WIN RATE
        # ====================================================

        completed_trades = (

            winning_trades
            + losing_trades

        )


        if completed_trades > 0:

            win_rate = (

                winning_trades
                / completed_trades

            ) * 100


        else:

            win_rate = 0.0


        # ====================================================
        # TOTAL P&L
        # ====================================================

        total_pnl = (

            total_unrealized_pnl
            + total_realized_pnl

        )


        # ====================================================
        # RETURN
        # ====================================================

        return {

            # -----------------------------------------------
            # RECORDS
            # -----------------------------------------------

            "total_records":
                len(trades),


            # -----------------------------------------------
            # POSITIONS
            # -----------------------------------------------

            "active_positions":
                len(active_positions),

            "closed_positions":
                len(closed_positions),


            # -----------------------------------------------
            # UNREALIZED
            # -----------------------------------------------

            "positions_with_unrealized_pnl":
                positions_with_pnl,

            "total_unrealized_pnl":
                round(
                    total_unrealized_pnl,
                    2,
                ),


            # -----------------------------------------------
            # REALIZED
            # -----------------------------------------------

            "closed_positions_with_realized_pnl":
                closed_positions_with_pnl,

            "total_realized_pnl":
                round(
                    total_realized_pnl,
                    2,
                ),


            # -----------------------------------------------
            # TOTAL
            # -----------------------------------------------

            "total_pnl":
                round(
                    total_pnl,
                    2,
                ),


            # -----------------------------------------------
            # PERFORMANCE
            # -----------------------------------------------

            "winning_trades":
                winning_trades,

            "losing_trades":
                losing_trades,

            "breakeven_trades":
                breakeven_trades,

            "completed_trades":
                completed_trades,

            "win_rate":
                round(
                    win_rate,
                    2,
                ),
        }


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail={

                "message":
                    "Unable to calculate portfolio summary",

                "error":
                    str(exc),
            },
        )