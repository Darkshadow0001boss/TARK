from datetime import date, timedelta
from typing import Dict, List

from alpaca.trading.enums import ContractType
from alpaca.trading.requests import GetOptionContractsRequest

from app.brokers.options_client import get_options_client


def get_nearest_expiration(
    contracts: List,
    minimum_days: int = 1,
) -> date:
    """
    Select the nearest available expiration that is at least
    minimum_days away.
    """

    today = date.today()

    valid_expirations = sorted(
        {
            contract.expiration_date
            for contract in contracts
            if (contract.expiration_date - today).days >= minimum_days
        }
    )

    if not valid_expirations:
        raise ValueError(
            "No suitable option expiration found"
        )

    return valid_expirations[0]


def get_contracts(
    symbol: str,
    contract_type: ContractType,
    minimum_days: int = 1,
    maximum_days: int = 7,
) -> List:
    """
    Retrieve option contracts for a symbol.
    """

    client = get_options_client()

    today = date.today()

    request = GetOptionContractsRequest(
        underlying_symbols=[symbol],
        expiration_date_gte=today + timedelta(days=minimum_days),
        expiration_date_lte=today + timedelta(days=maximum_days),
        type=contract_type,
        limit=1000,
    )

    response = client.get_option_contracts(request)

    return response.option_contracts


def find_nearest_strike(
    contracts: List,
    target_price: float,
):
    """
    Find the contract with strike closest to target_price.
    """

    if not contracts:
        raise ValueError("No contracts available")

    return min(
        contracts,
        key=lambda contract: abs(
            float(contract.strike_price) - target_price
        ),
    )


def select_bull_call_spread(
    symbol: str,
    underlying_price: float,
    spread_width: float = 5.0,
) -> Dict:
    """
    Select an ATM bull call spread.

    Long call:
        Strike closest to current price.

    Short call:
        Strike above the long call.
    """

    contracts = get_contracts(
        symbol=symbol,
        contract_type=ContractType.CALL,
    )

    expiration = get_nearest_expiration(contracts)

    contracts = [
        contract
        for contract in contracts
        if contract.expiration_date == expiration
    ]

    long_call = find_nearest_strike(
        contracts,
        underlying_price,
    )

    long_strike = float(long_call.strike_price)

    short_call = find_nearest_strike(
        contracts,
        long_strike + spread_width,
    )

    return {
        "strategy": "BULL_CALL_SPREAD",
        "symbol": symbol,
        "expiration_date": str(expiration),
        "long_leg": {
            "symbol": long_call.symbol,
            "strike": float(long_call.strike_price),
            "side": "BUY",
            "type": "CALL",
        },
        "short_leg": {
            "symbol": short_call.symbol,
            "strike": float(short_call.strike_price),
            "side": "SELL",
            "type": "CALL",
        },
    }


def select_bear_put_spread(
    symbol: str,
    underlying_price: float,
    spread_width: float = 5.0,
) -> Dict:
    """
    Select an ATM bear put spread.

    Long put:
        Strike closest to current price.

    Short put:
        Strike below the long put.
    """

    contracts = get_contracts(
        symbol=symbol,
        contract_type=ContractType.PUT,
    )

    expiration = get_nearest_expiration(contracts)

    contracts = [
        contract
        for contract in contracts
        if contract.expiration_date == expiration
    ]

    long_put = find_nearest_strike(
        contracts,
        underlying_price,
    )

    long_strike = float(long_put.strike_price)

    short_put = find_nearest_strike(
        contracts,
        long_strike - spread_width,
    )

    return {
        "strategy": "BEAR_PUT_SPREAD",
        "symbol": symbol,
        "expiration_date": str(expiration),
        "long_leg": {
            "symbol": long_put.symbol,
            "strike": float(long_put.strike_price),
            "side": "BUY",
            "type": "PUT",
        },
        "short_leg": {
            "symbol": short_put.symbol,
            "strike": float(short_put.strike_price),
            "side": "SELL",
            "type": "PUT",
        },
    }


def select_option_spread(
    symbol: str,
    strategy: str,
    underlying_price: float,
) -> Dict:
    """
    Main entry point for the TARK option contract selector.
    """

    if strategy == "BULL_CALL_SPREAD":
        return select_bull_call_spread(
            symbol=symbol,
            underlying_price=underlying_price,
        )

    if strategy == "BEAR_PUT_SPREAD":
        return select_bear_put_spread(
            symbol=symbol,
            underlying_price=underlying_price,
        )

    raise ValueError(
        f"Unsupported strategy: {strategy}"
    )