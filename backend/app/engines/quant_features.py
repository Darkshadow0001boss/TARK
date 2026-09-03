import pandas as pd


def calculate_features(bars) -> dict:
    """
    Convert market bars into a compact set of quantitative
    features used by TARK's trading strategy.
    """

    if not bars:
        raise ValueError("No market bars available")

    data = []

    for bar in bars:
        data.append(
            {
                "timestamp": bar.timestamp,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
        )

    df = pd.DataFrame(data)

    if len(df) < 50:
        raise ValueError(
            f"Insufficient market data. Need at least 50 bars, got {len(df)}."
        )

    # Ensure chronological order.
    df = df.sort_values("timestamp").reset_index(drop=True)

    # EMA
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()

    # RSI (14)
    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # ATR (14)
    previous_close = df["close"].shift(1)

    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    df["atr_14"] = true_range.rolling(window=14).mean()

    # Volume ratio
    # Calculate the average using only completed bars with meaningful volume.
    volume_series = df["volume"].replace(0, pd.NA)

    df["volume_average_20"] = (
        volume_series.rolling(window=20, min_periods=5).mean()
    )

    df["volume_ratio"] = (
        df["volume"] / df["volume_average_20"]
    )

    # Use the most recent bar with valid calculated features.
    valid_df = df.dropna(
        subset=[
            "ema_20",
            "ema_50",
            "rsi_14",
            "atr_14",
            "volume_ratio",
        ]
    )

    # Ignore bars with zero volume.
    valid_df = valid_df[valid_df["volume"] > 0]

    if valid_df.empty:
        raise ValueError("No valid completed market bars available")

    latest = valid_df.iloc[-1]

    return {
        "timestamp": latest["timestamp"].isoformat(),
        "close": round(float(latest["close"]), 2),
        "ema_20": round(float(latest["ema_20"]), 2),
        "ema_50": round(float(latest["ema_50"]), 2),
        "rsi_14": round(float(latest["rsi_14"]), 2),
        "atr_14": round(float(latest["atr_14"]), 2),
        "volume_ratio": round(float(latest["volume_ratio"]), 2),
    }