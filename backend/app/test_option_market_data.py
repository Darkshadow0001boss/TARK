import json

from app.brokers.option_market_data import get_option_quote


def main():

    symbol = "QQQ260903P00709000"

    quote = get_option_quote(symbol)

    print(json.dumps(quote, indent=2))


if __name__ == "__main__":
    main()