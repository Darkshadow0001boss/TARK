import json

from app.options.contract_selector import select_option_spread


def main():

    result = select_option_spread(
        symbol="QQQ",
        strategy="BEAR_PUT_SPREAD",
        underlying_price=708.82,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()