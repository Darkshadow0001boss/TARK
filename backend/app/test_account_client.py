import json

from app.brokers.account_client import get_account_snapshot


def main():

    account = get_account_snapshot()

    print(json.dumps(account, indent=2))


if __name__ == "__main__":
    main()