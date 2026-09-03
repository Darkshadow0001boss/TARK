from datetime import date, timedelta

from alpaca.trading.enums import ContractType
from alpaca.trading.requests import GetOptionContractsRequest

from app.brokers.options_client import get_options_client


def print_contracts(title, contracts, underlying_price):
    print()
    print(title)
    print("-" * 60)

    nearby = []

    for contract in contracts:
        strike = float(contract.strike_price)

        if abs(strike - underlying_price) <= 20:
            nearby.append(contract)

    print(f"Nearby contracts found: {len(nearby)}")
    print()

    for contract in nearby[:20]:
        print(
            {
                "symbol": contract.symbol,
                "expiration_date": str(contract.expiration_date),
                "strike_price": float(contract.strike_price),
                "type": str(contract.type),
            }
        )


def main():
    client = get_options_client()

    underlying_price = 708.82

    # CALL contracts
    call_request = GetOptionContractsRequest(
        underlying_symbols=["QQQ"],
        expiration_date_gte=date.today(),
        expiration_date_lte=date.today() + timedelta(days=30),
        type=ContractType.CALL,
        limit=1000,
    )

    call_response = client.get_option_contracts(call_request)

    print(f"Total CALL contracts returned: {len(call_response.option_contracts)}")

    print_contracts(
        "CALL CONTRACTS",
        call_response.option_contracts,
        underlying_price,
    )

    # PUT contracts
    put_request = GetOptionContractsRequest(
        underlying_symbols=["QQQ"],
        expiration_date_gte=date.today(),
        expiration_date_lte=date.today() + timedelta(days=30),
        type=ContractType.PUT,
        limit=1000,
    )

    put_response = client.get_option_contracts(put_request)

    print()
    print(f"Total PUT contracts returned: {len(put_response.option_contracts)}")

    print_contracts(
        "PUT CONTRACTS",
        put_response.option_contracts,
        underlying_price,
    )


if __name__ == "__main__":
    main()