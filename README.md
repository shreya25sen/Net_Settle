# Net_Settle
# Net-Settle: Automated Group Expense & Debt Minimiser

A command-line application that tracks shared group expenses and works out a small set of payments that settles everyone up.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Interface](https://img.shields.io/badge/Interface-CLI-lightgrey)
![Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen)

---

## Problem Statement

In multi-user group environments (shared student housing, group travel, freelance business partnerships), settling shared expenses by hand leads to many transactions, peer-to-peer tracking errors, and avoidable transaction fees.

For example, if Person A owes Person B ₹500 and Person B owes Person C ₹500, the group has two separate transactions, when a single ₹500 payment from A to C settles everything.

## Solution

Net-Settle models a group as a financial network. Users are vertices and debts are directed, weighted edges. The app records every shared expense, computes each member's **net balance**, and runs a **greedy optimisation algorithm** that cuts the number of peer-to-peer transfers needed to clear all debts.

## Features

- Add group members and record shared expenses (payer, amount, description, category, participants)
- Split each expense equally among the chosen participants
- Exact money handling: all amounts are stored as whole **paise** using Python's `Decimal`, so there are no floating-point errors
- Uneven splits are handled fairly: leftover paise are distributed one at a time to the first participants
- View full expense history and each member's net balance (who owes, who should receive)
- Compute a minimised set of settlement transfers
- Estimate total transaction fees from a per-transfer fee
- Export a CSV report with balances, settlements, and expense history
- Input validation with clear error messages (empty names, duplicate members, unregistered payers, invalid amounts, and so on)

## How It Works

1. **Record expenses.** For each expense, the payer is credited the full amount and each participant is debited their share. Each member's net balance is the total they paid minus their total share.
2. **Build the graph.** Each participant's share is also stored as a directed edge (participant → payer) in an adjacency list, preserving the original debt structure.
3. **Separate debtors and creditors.** Members with a negative balance are debtors. Members with a positive balance are creditors.
4. **Greedy matching with heaps.** Two heaps (`heapq`) hold the debtors and creditors. Repeatedly:
   - pop the largest debtor and the largest creditor,
   - settle `min(debt, credit)` between them,
   - push back whichever side still has a remaining balance.
5. **Output.** The result is a list of `from → to : amount` payments.

A zero-sum check runs first: if balances do not add up to zero, the engine raises an error instead of returning wrong settlements.

**Complexity:** O(n log n) for n members. The greedy method produces at most n − 1 transfers, and each transfer fully clears at least one person, which is usually close to the minimum. Finding the *provably* minimum number of transfers is NP-hard in general, so greedy is the standard practical approach.

### Example

| Member | Net balance |
|--------|-------------|
| A | owes ₹500 |
| B | settled |
| C | should receive ₹500 |

Recommended settlement: `A pays C: Rs. 500.00` (1 transfer instead of 2).

## Project Structure

```
Net_Settle/
├── main.py                # CLI menu, command-line flags, program entry point
├── expense_manager.py     # Members, expenses, balances, debt graph, money helpers
├── settlement.py          # SettlementEngine: heap-based debt minimisation + fee estimate
├── storage.py             # JSON save/load shared by the CLI and the web UI
├── server.py              # Local web server and JSON API 
├── ui/
│   └── index.html         # Browser front end served by server.py
├── reports.py             # CSV report export
├── settlement_report.csv  # Sample generated report
└── netsettle_data.json    # Saved data 
```

| File | Responsibility |
|------|----------------|
| `main.py` | Menu loop, user input, and wiring the modules together |
| `expense_manager.py` | `ExpenseManager` class, `money_to_paise()`, `format_money()` |
| `settlement.py` | `SettlementEngine.minimise_transfers()` and `estimate_fees()` |
| `reports.py` | `export_report()` writes the CSV |

## Getting Started

### Prerequisites

- Python 3.8 or newer
- No external packages are required (standard library only: `decimal`, `heapq`, `csv`)

### Installation and Run

```bash
git clone https://github.com/shreya25sen/Net_Settle.git
cd Net_Settle
python main.py
```

### Menu

```
1. Add group member
2. Record a shared expense
3. View expense history
4. View net balances
5. Calculate settlements
6. Export CSV report
7. Open web UI
8. Exit
```

## Sample Session

```
==========================================
          NET-SETTLE
 Smart Group Expense & Debt Minimiser
==========================================

Choose an option: 1
Member name: arya
...
Choose an option: 2
Who paid? shreya
Total expense in Rs.: 2093
Expense description: food
Category (food, travel, rent, etc.): food
Who shared this expense? Enter names separated by commas: arya, shreya, maher

Choose an option: 5

--- Recommended Settlements ---
arya pays shreya: Rs. 697.67
maher pays shreya: Rs. 697.66
Total transfers: 2
```

## Sample Report

Option 6 writes `settlement_report.csv` with three sections:

```
NET-SETTLE REPORT

GROUP BALANCES
Member,Balance,Status
arya,Rs. -697.67,Needs to pay
shreya,"Rs. 1,395.33",Should receive

RECOMMENDED SETTLEMENTS
From,To,Amount
arya,shreya,Rs. 697.67
maher,shreya,Rs. 697.66

EXPENSE HISTORY
Description,Category,Payer,Amount,Participants
food,food,shreya,"Rs. 2,093.00","arya, shreya, maher"
```

## Tech Stack

- **Language:** Python 3
- **Data structures:** hash sets and dictionaries, adjacency-list graph, min-heaps (`heapq`)
- **Concepts:** graph modelling, greedy algorithms, fixed-point money arithmetic

## Possible Improvements

- Unequal or percentage-based splits
- Persistent storage (JSON or SQLite) so data survives between runs
- Expense editing and deletion
- Category-wise spending summaries
- Unit tests for the settlement engine
- A GUI or web front end

## Author

**Shreya Sen** — [@shreya25sen](https://github.com/shreya25sen)
