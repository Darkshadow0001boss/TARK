import json

from app.brokers.position_client import get_open_positions


def main():

    positions = get_open_positions()

    print(f"Number of open positions: {len(positions)}")
    print()

    print(json.dumps(positions, indent=2))


if __name__ == "__main__":
    main()