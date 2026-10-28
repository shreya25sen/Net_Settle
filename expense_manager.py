from decimal import Decimal, InvalidOperation


def money_to_paise(value):
    """Convert a rupee amount into whole paise."""
    try:
        amount = Decimal(value.strip())
        if not amount.is_finite() or amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        paise = amount * 100
        if paise != paise.to_integral_value():
            raise ValueError("Use at most two decimal places.")
        return int(paise)
    except InvalidOperation:
        raise ValueError("Enter a valid monetary amount.")


def format_money(paise):
    """Display paise as Indian rupees."""
    rupees = Decimal(paise) / 100
    return f"Rs. {rupees:,.2f}"


class ExpenseManager:
    def __init__(self):
        self.members = set()
        self.balances = {}
        self.expenses = []
        self.graph = {}

    def add_member(self, name):
        name = name.strip()
        if not name:
            raise ValueError("Name cannot be empty.")
        if name in self.members:
            raise ValueError("This member already exists.")
        self.members.add(name)
        self.balances[name] = 0
        self.graph[name] = []

    def add_expense(self, payer, amount_paise,
                    description, category, participants):
        if payer not in self.members:
            raise ValueError("The payer is not registered.")
        if amount_paise <= 0:
            raise ValueError("Amount must be positive.")
        participants = list(dict.fromkeys(participants))
        if not participants:
            raise ValueError("Select at least one participant.")
        if any(person not in self.members for person in participants):
            raise ValueError("Every participant must be registered.")
        if not description.strip() or not category.strip():
            raise ValueError("Description and category are required.")

        # Divide the expense in whole paise. Any remainder is
        # assigned one paise at a time to the first participants.
        base_share, remainder = divmod(
            amount_paise, len(participants)
        )
        shares = {}
        for index, person in enumerate(participants):
            shares[person] = base_share + (
                1 if index < remainder else 0
            )

        # The payer initially paid the entire expense.
        self.balances[payer] += amount_paise
        for person, share in shares.items():
            self.balances[person] -= share
            # Store original debt edges, excluding self-loops.
            if person != payer:
                self.graph[person].append(
                    (payer, share)
                )

        self.expenses.append({
            "payer": payer,
            "amount": amount_paise,
            "description": description.strip(),
            "category": category.strip(),
            "participants": participants.copy(),
            "shares": shares.copy()
        })

    def show_expenses(self):
        print("\n--- Expense History ---")
        if not self.expenses:
            print("No expenses recorded.")
            return
        for index, expense in enumerate(self.expenses, start=1):
            print(
                f"{index}. {expense['description']} "
                f"| {expense['category']} "
                f"| Paid by: {expense['payer']} "
                f"| {format_money(expense['amount'])}"
            )
            print("   Participants:", ", ".join(
                expense["participants"]
            ))

    def show_balances(self):
        print("\n--- Net Balances ---")
        for name in sorted(self.members):
            balance = self.balances[name]
            if balance < 0:
                status = f"Owes {format_money(-balance)}"
            elif balance > 0:
                status = f"Should receive {format_money(balance)}"
            else:
                status = "Settled"
            print(f"{name}: {status}")

    def total_expense(self):
        return sum(
            expense["amount"] for expense in self.expenses
        )
