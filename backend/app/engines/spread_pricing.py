from app.brokers.option_market_data import get_option_quote


def calculate_spread_pricing(
    long_symbol: str,
    short_symbol: str,
) -> dict:
    """
    Calculate pricing information for a debit options spread.

    Opening:
        Buy long leg at ask
        Sell short leg at bid

    Closing:
        Sell long leg at bid
        Buy short leg at ask

    Also calculates midpoint values for marking P&L.
    """

    long_quote = get_option_quote(long_symbol)
    short_quote = get_option_quote(short_symbol)

    long_bid = float(long_quote["bid_price"])
    long_ask = float(long_quote["ask_price"])

    short_bid = float(short_quote["bid_price"])
    short_ask = float(short_quote["ask_price"])

    # ======================================================
    # MID PRICES
    # ======================================================

    long_mid = round(
        (long_bid + long_ask) / 2,
        2,
    )

    short_mid = round(
        (short_bid + short_ask) / 2,
        2,
    )

    # ======================================================
    # OPENING DEBIT
    #
    # Buy long at ask
    # Sell short at bid
    # ======================================================

    estimated_debit = round(
        long_ask - short_bid,
        2,
    )

    # ======================================================
    # MIDPOINT SPREAD VALUE
    #
    # Used for unrealized P&L marking.
    # ======================================================

    estimated_mid_debit = round(
        long_mid - short_mid,
        2,
    )

    # ======================================================
    # EXECUTABLE EXIT CREDIT
    #
    # Sell long at bid
    # Buy short at ask
    # ======================================================

    estimated_exit_credit = round(
        long_bid - short_ask,
        2,
    )

    return {
        "long_leg": {
            "symbol": long_symbol,
            "bid": long_bid,
            "ask": long_ask,
            "mid": long_mid,
        },

        "short_leg": {
            "symbol": short_symbol,
            "bid": short_bid,
            "ask": short_ask,
            "mid": short_mid,
        },

        # Opening estimate
        "estimated_debit": max(
            estimated_debit,
            0.0,
        ),

        # Mark-to-market estimate
        "estimated_mid_debit": max(
            estimated_mid_debit,
            0.0,
        ),

        # Conservative executable close estimate
        "estimated_exit_credit": max(
            estimated_exit_credit,
            0.0,
        ),
    }