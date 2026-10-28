"""Shared JSON persistence so the CLI and the web UI see the same data."""
import json
import os

from expense_manager import ExpenseManager

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "netsettle_data.json"
)


def save(manager, path=DATA_FILE):
    data = {
        "members": sorted(manager.members),
        "expenses": [
            {
                "payer": e["payer"],
                "amount": e["amount"],
                "description": e["description"],
                "category": e["category"],
                "participants": e["participants"],
            }
            for e in manager.expenses
        ],
    }
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
    os.replace(tmp_path, path)  # atomic: never leaves a half-written file


def load(path=DATA_FILE):
    """Rebuild an ExpenseManager by replaying the saved records."""
    manager = ExpenseManager()
    if not os.path.exists(path):
        return manager
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        for name in data["members"]:
            manager.add_member(name)
        for e in data["expenses"]:
            manager.add_expense(
                e["payer"], e["amount"], e["description"],
                e["category"], e["participants"],
            )
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Could not read saved data: {error}")
    return manager
