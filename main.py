import argparse

import storage
from expense_manager import ExpenseManager, money_to_paise, format_money
from settlement import SettlementEngine
from reports import export_report


def run_cli(app):
    print("=" * 42)
    print("          NET-SETTLE")
    print("  Smart Group Expense & Debt Minimiser")
    print("=" * 42)

    while True:
        # Reload from disk so changes made in the web UI show up here.
        try:
            app = storage.load()
        except ValueError as error:
            print("Warning:", error)

        print("\n1. Add group member")
        print("2. Record a shared expense")
        print("3. View expense history")
        print("4. View net balances")
        print("5. Calculate settlements")
        print("6. Export CSV report")
        print("7. Open web UI")
        print("8. Exit")

        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                name = input("Member name: ")
                app.add_member(name)
                storage.save(app)
                print(f"{name.strip()} added successfully.")

            elif choice == "2":
                if len(app.members) < 2:
                    print("Add at least two members first.")
                    continue

                payer = input("Who paid? ").strip()
                if payer not in app.members:
                    print("That payer is not registered.")
                    continue

                amount = money_to_paise(
                    input("Total expense in Rs.: ")
                )
                description = input("Expense description: ").strip()
                category = input(
                    "Category (food, travel, rent, etc.): "
                ).strip()

                print("Registered members:", ", ".join(
                    sorted(app.members)
                ))
                names = input(
                    "Who shared this expense? "
                    "Enter names separated by commas: "
                )
                participants = [
                    name.strip()
                    for name in names.split(",")
                    if name.strip()
                ]

                app.add_expense(
                    payer, amount, description, category, participants
                )
                storage.save(app)
                print("Expense recorded successfully!")

            elif choice == "3":
                app.show_expenses()

            elif choice == "4":
                app.show_balances()

            elif choice == "5":
                engine = SettlementEngine(app.balances)
                settlements = engine.minimise_transfers()

                print("\n--- Recommended Settlements ---")
                if not settlements:
                    print("Everyone is already settled.")
                else:
                    for payment in settlements:
                        print(
                            f"{payment['from']} pays "
                            f"{payment['to']}: "
                            f"{format_money(payment['amount'])}"
                        )

                fee_input = input(
                    "Estimated fee per transfer in Rs. "
                    "(press Enter for 0): "
                ).strip()
                fee = money_to_paise(fee_input) if fee_input else 0

                total_fees = engine.estimate_fees(settlements, fee)
                print(f"Total transfers: {len(settlements)}")
                print(f"Estimated total fees: {format_money(total_fees)}")
                print(
                    f"Total recorded expenses: "
                    f"{format_money(app.total_expense())}"
                )

            elif choice == "6":
                settlements = SettlementEngine(
                    app.balances
                ).minimise_transfers()
                export_report(app, settlements)

            elif choice == "7":
                import server
                server.run()  # blocks until Ctrl+C, then back to the menu

            elif choice == "8":
                print("Thank you for using Net-Settle!")
                break

            else:
                print("Please select a number from 1 to 8.")

        except ValueError as error:
            print("Could not complete that action:", error)
        except OSError as error:
            print("Could not save the data or report:", error)


def main():
    parser = argparse.ArgumentParser(
        description="Net-Settle: group expense & debt minimiser"
    )
    parser.add_argument(
        "--ui", action="store_true",
        help="start the web UI instead of the command-line menu",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="port for the web UI (default: 8000)",
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="do not open the browser automatically",
    )
    args = parser.parse_args()

    if args.ui:
        import server
        server.run(port=args.port, open_browser=not args.no_browser)
        return

    try:
        app = storage.load()
    except ValueError as error:
        print("Warning:", error)
        app = ExpenseManager()
    run_cli(app)


if __name__ == "__main__":
    main()
