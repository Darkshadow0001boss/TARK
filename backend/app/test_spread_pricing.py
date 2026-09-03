import json

from app.engines.spread_pricing import calculate_spread_pricing


def main():

    result = calculate_spread_pricing(
        long_symbol="QQQ260903P00709000",
        short_symbol="QQQ260903P00704000",
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()