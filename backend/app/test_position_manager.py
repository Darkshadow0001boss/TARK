import json

from app.engines.position_evaluator import evaluate_position


def print_result(title: str, result: dict):
    print("\n" + title)
    print("-" * 50)
    print(json.dumps(result, indent=2))


# Scenario 1: Position is healthy
healthy = evaluate_position(
    entry_debit=1.68,
    current_debit=1.85,
)

print_result("HEALTHY POSITION", healthy)


# Scenario 2: Profit target reached
profit = evaluate_position(
    entry_debit=1.68,
    current_debit=2.60,
)

print_result("PROFIT TARGET", profit)


# Scenario 3: Stop loss triggered
loss = evaluate_position(
    entry_debit=1.68,
    current_debit=0.75,
)

print_result("STOP LOSS", loss)


# Scenario 4: Thesis invalidated
invalidated = evaluate_position(
    entry_debit=1.68,
    current_debit=1.75,
    thesis_invalidated=True,
)

print_result("THESIS INVALIDATED", invalidated)