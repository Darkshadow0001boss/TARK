from app.data.market_data import (
    get_hourly_bars,
    get_15m_bars,
)

from app.engines.quant_features import calculate_features
from app.engines.opportunity import evaluate_opportunity


class MarketScanner:

    """
    TARK Autonomous Market Scanner.

    Scans a predefined universe of liquid,
    options-friendly symbols and identifies
    valid trading candidates.
    """

    WATCHLIST = [
        "SPY",
        "QQQ",
        "IWM",
        "AAPL",
        "MSFT",
        "NVDA",
        "AMD",
        "TSLA",
    ]

    def scan(self) -> dict:

        results = []
        candidates = []

        for symbol in self.WATCHLIST:

            try:

                # ------------------------------------------
                # MARKET DATA
                # ------------------------------------------

                hourly_response = get_hourly_bars(symbol)

                entry_response = get_15m_bars(symbol)

                hourly_bars = hourly_response.data.get(
                    symbol,
                    [],
                )

                entry_bars = entry_response.data.get(
                    symbol,
                    [],
                )

                # ------------------------------------------
                # VALIDATE DATA
                # ------------------------------------------

                if not hourly_bars or not entry_bars:

                    results.append(
                        {
                            "symbol": symbol,
                            "status": "NO_DATA",
                        }
                    )

                    continue

                # ------------------------------------------
                # FEATURES
                # ------------------------------------------

                hourly_features = calculate_features(
                    hourly_bars
                )

                entry_features = calculate_features(
                    entry_bars
                )

                # ------------------------------------------
                # OPPORTUNITY ENGINE
                # ------------------------------------------

                opportunity = evaluate_opportunity(
                    symbol=symbol,
                    hourly_features=hourly_features,
                    entry_features=entry_features,
                )

                scan_result = {
                    "symbol": symbol,

                    "direction":
                        opportunity.get(
                            "direction"
                        ),

                    "action":
                        opportunity.get(
                            "action"
                        ),

                    "strategy":
                        opportunity.get(
                            "strategy"
                        ),

                    "reasons":
                        opportunity.get(
                            "reasons",
                            []
                        ),

                    # Keep these internally so the
                    # orchestrator can use the winner
                    "hourly_features":
                        hourly_features,

                    "entry_features":
                        entry_features,
                }

                results.append(
                    scan_result
                )

                # ------------------------------------------
                # SAVE VALID CANDIDATES
                # ------------------------------------------

                if opportunity.get(
                    "action"
                ) == "CANDIDATE":

                    candidates.append(
                        scan_result
                    )

            except Exception as exc:

                results.append(
                    {
                        "symbol": symbol,
                        "status": "ERROR",
                        "error": str(exc),
                    }
                )

        return {
            "watchlist": self.WATCHLIST,

            "scanned_count":
                len(self.WATCHLIST),

            "candidate_count":
                len(candidates),

            "candidates":
                candidates,

            "results":
                results,
        }