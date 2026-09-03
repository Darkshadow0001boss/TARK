def evaluate_position(
    entry_debit: float,
    current_debit: float,
    profit_target_pct: float = 50.0,
    stop_loss_pct: float = 50.0,
    thesis_invalidated: bool = False,
) -> dict:
    """
    Deterministically evaluate an open options spread position.

    For debit spreads:

    - Profit occurs when the spread value increases.
    - Loss occurs when the spread value decreases.
    """

    if entry_debit <= 0:
        raise ValueError("entry_debit must be greater than zero")

    # Percentage return on the spread
    pnl_pct = (
        (current_debit - entry_debit)
        / entry_debit
    ) * 100

    # 1. Thesis invalidation has highest priority
    if thesis_invalidated:
        return {
            "action": "EXIT",
            "reason": "THESIS_INVALIDATED",
            "entry_debit": entry_debit,
            "current_debit": current_debit,
            "pnl_percent": round(pnl_pct, 2),
        }

    # 2. Profit target
    if pnl_pct >= profit_target_pct:
        return {
            "action": "EXIT",
            "reason": "TAKE_PROFIT",
            "entry_debit": entry_debit,
            "current_debit": current_debit,
            "pnl_percent": round(pnl_pct, 2),
        }

    # 3. Stop loss
    if pnl_pct <= -stop_loss_pct:
        return {
            "action": "EXIT",
            "reason": "STOP_LOSS",
            "entry_debit": entry_debit,
            "current_debit": current_debit,
            "pnl_percent": round(pnl_pct, 2),
        }

    # Otherwise hold
    return {
        "action": "HOLD",
        "reason": "POSITION_HEALTHY",
        "entry_debit": entry_debit,
        "current_debit": current_debit,
        "pnl_percent": round(pnl_pct, 2),
    }