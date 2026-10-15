
import json
import csv
import re
from pathlib import Path
from datetime import date, datetime
import calendar
import math
import os

# ---------- FILE SETTINGS ----------
BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"

DEFAULT_CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Entertainment"
]


# ---------- JSON HELPERS ----------
def load_json(file_path, default):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        print(f"Warning: {file_path.name} is invalid. Using default data.")
        return default


def save_json(file_path, data):
    """Save JSON safely by writing a temporary file before replacing the old one."""
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False, allow_nan=False)
        os.replace(temp_path, file_path)
    except (OSError, TypeError, ValueError) as error:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass
        print(f"Could not save {file_path.name}: {error}")


def valid_amount(value):
    """Return a usable numeric amount, or 0 for malformed legacy data."""
    try:
        amount = float(value)
        return amount if math.isfinite(amount) else 0.0
    except (TypeError, ValueError):
        return 0.0


# ---------- USER MANAGEMENT ----------
users = load_json(USERS_FILE, ["Rakshit"])
if not isinstance(users, list) or any(not isinstance(user, str) for user in users):
    print("Warning: users.json has an invalid format. Using the default user list.")
    users = ["Rakshit"]

if not any(user.lower() == "rakshit" for user in users):
    users.insert(0, "Rakshit")
    save_json(USERS_FILE, users)


def get_user_files(username):
    if username.lower() == "rakshit":
        expense_file = BASE_DIR / "expenses.json"
        category_file = BASE_DIR / "categories.json"
    else:
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", username)
        expense_file = BASE_DIR / f"expenses_{safe_name}.json"
        category_file = BASE_DIR / f"categories_{safe_name}.json"

    return expense_file, category_file


def choose_user():
    while True:
        print("\n===== EXPENSE TRACKER =====")
        print("===== SELECT USER =====")

        for i, username in enumerate(users, start=1):
            print(f"{i}. {username}")

        print(f"{len(users) + 1}. Add New User")
        print("0. Exit")

        choice = input("Choose user: ").strip()

        if not choice.isdigit():
            print("Please enter a valid number!")
            continue

        choice = int(choice)

        if choice == 0:
            return None

        elif 1 <= choice <= len(users):
            return users[choice - 1]

        elif choice == len(users) + 1:
            new_user = input("Enter new user's name: ").strip()

            if not new_user:
                print("Name cannot be empty!")
            elif any(
                username.lower() == new_user.lower()
                for username in users
            ):
                print("This user already exists!")
            else:
                users.append(new_user)
                save_json(USERS_FILE, users)
                print(f"User '{new_user}' created successfully!")
                return new_user

        else:
            print("Invalid choice!")


# ---------- CATEGORY MANAGEMENT ----------
def add_new_category(categories, category_file):
    new_category = input("Enter new category name: ").strip()

    if not new_category:
        print("Category name cannot be empty!")
    elif new_category.lower() in [c.lower() for c in categories]:
        print("This category already exists!")
    else:
        categories.append(new_category)
        save_json(category_file, categories)
        print("Category added and saved successfully!")


# ---------- DISPLAY EXPENSES ----------
def show_expenses(expenses):
    if not expenses:
        print("No expenses added yet.")
        return

    for i, item in enumerate(expenses, start=1):
        print(f"\nExpense {i}")
        print("Category:", item.get("category", "Uncategorized"))
        print(f"Amount: ₹{valid_amount(item.get('amount', 0)):.2f}")
        print("Description:", item.get("description", ""))
        print("Date:", item.get("date", "Not recorded"))


# ---------- DAILY AND MONTHLY REPORTS ----------
def show_date_reports(expenses, categories):
    while True:
        print("\n===== DAILY & MONTHLY REPORTS =====")
        print("1. Today's Summary")
        print("2. Summary for a Specific Date")
        print("3. Monthly Summary")
        print("4. Back to Main Menu")

        choice = input("Choose report: ").strip()

        if choice == "4":
            break

        # Select the date or month
        if choice == "1":
            selected_date = date.today().isoformat()
            report_type = "day"

        elif choice == "2":
            selected_date = input(
                "Enter date (YYYY-MM-DD): "
            ).strip()

            try:
                datetime.strptime(selected_date, "%Y-%m-%d")
            except ValueError:
                print("Invalid date! Please use YYYY-MM-DD.")
                continue

            report_type = "day"

        elif choice == "3":
            selected_date = input(
                "Enter month (YYYY-MM), e.g. 2026-10: "
            ).strip()

            try:
                datetime.strptime(selected_date, "%Y-%m")
            except ValueError:
                print("Invalid month! Please use YYYY-MM.")
                continue

            report_type = "month"

        else:
            print("Invalid choice! Select 1 to 4.")
            continue

        # Filter expenses for the selected date or month
        matching_expenses = []

        for item in expenses:
            expense_date = item.get("date", "")

            if report_type == "day":
                if expense_date == selected_date:
                    matching_expenses.append(item)

            elif report_type == "month":
                if expense_date.startswith(selected_date + "-"):
                    matching_expenses.append(item)

        print("\n===== REPORT =====")

        if report_type == "day":
            print("Date:", selected_date)
        else:
            year, month = map(int, selected_date.split("-"))
            print(
                "Month:",
                calendar.month_name[month],
                year
            )

        if not matching_expenses:
            print("No recorded expenses for this period.")
            continue

        total = sum(
            valid_amount(item.get("amount", 0)) for item in matching_expenses
        )

        print(f"Total expenses: ₹{total:.2f}")
        print(f"Number of expenses: {len(matching_expenses)}")

        print("\nCategory-wise breakdown:")

        for category in categories:
            category_total = sum(
                valid_amount(item.get("amount", 0))
                for item in matching_expenses
                if item.get("category") == category
            )

            if category_total > 0:
                print(f"{category}: ₹{category_total:.2f}")

        print("\nExpenses in this period:")

        for item in matching_expenses:
            print(
                f"{item.get('date', 'Not recorded')} | "
                f"{item.get('category', 'Uncategorized')} | "
                f"₹{valid_amount(item.get('amount', 0)):.2f} | "
                f"{item.get('description', '')}"
            )



# ---------- SEARCH EXPENSE ----------
def search_expenses(expenses):
    print("\n===== SEARCH EXPENSES =====")
    if not expenses:
        print("No expenses available to search.")
        return

    query = input(
        "Search by category, description, date, or amount: "
    ).strip().lower()

    if not query:
        print("Search text cannot be empty!")
        return

    matches = []
    for index, item in enumerate(expenses, start=1):
        searchable_text = " ".join([
            str(item.get("category", "")),
            str(item.get("description", "")),
            str(item.get("date", "")),
            str(item.get("amount", ""))
        ]).lower()

        if query in searchable_text:
            matches.append((index, item))

    if not matches:
        print("No matching expenses found.")
        return

    print(f"\nFound {len(matches)} matching expense(s):")
    for index, item in matches:
        print(
            f"\nExpense #{index} | {item.get('date', 'Not recorded')} | "
            f"{item.get('category', 'Uncategorized')} | "
            f"₹{valid_amount(item.get('amount', 0)):.2f} | "
            f"{item.get('description', '')}"
        )


# ---------- UPDATE EXPENSE ----------
def update_expense(expenses, categories, save_expenses):
    print("\n===== UPDATE EXPENSE =====")
    if not expenses:
        print("No expenses available to update.")
        return

    show_expenses(expenses)
    choice = input(
        "\nEnter expense number to update (0 to cancel): "
    ).strip()

    if not choice.isdigit():
        print("Please enter a valid number!")
        return

    index = int(choice)
    if index == 0:
        print("Update cancelled.")
        return
    if not 1 <= index <= len(expenses):
        print("Expense number does not exist!")
        return

    item = expenses[index - 1]
    print("Press Enter to keep the current value.")

    print(f"Current category: {item.get('category', '')}")
    for number, category in enumerate(categories, start=1):
        print(f"{number}. {category}")
    category_input = input("New category number (Enter to keep): ").strip()

    new_category = item.get("category", categories[0] if categories else "Other")
    if category_input:
        if not category_input.isdigit():
            print("Invalid category number. Update cancelled.")
            return
        category_number = int(category_input)
        if not 1 <= category_number <= len(categories):
            print("Invalid category number. Update cancelled.")
            return
        new_category = categories[category_number - 1]

    current_amount = item.get("amount", 0)
    amount_input = input(
        f"New amount (current ₹{current_amount:.2f}): "
    ).strip()
    new_amount = current_amount
    if amount_input:
        try:
            new_amount = float(amount_input)
            if not math.isfinite(new_amount) or new_amount <= 0:
                print("Amount must be a finite number greater than zero. Update cancelled.")
                return
        except ValueError:
            print("Invalid amount. Update cancelled.")
            return

    current_description = item.get("description", "")
    description_input = input(
        f"New description (current: {current_description}): "
    ).strip()
    new_description = description_input if description_input else current_description

    current_date = item.get("date", date.today().isoformat())
    date_input = input(
        f"New date YYYY-MM-DD (current: {current_date}): "
    ).strip()
    new_date = current_date
    if date_input:
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            new_date = date_input
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD. Update cancelled.")
            return

    item["category"] = new_category
    item["amount"] = new_amount
    item["description"] = new_description
    item["date"] = new_date
    save_expenses()
    print("Expense updated and saved successfully!")


# ---------- MONTHLY BUDGET ----------
def manage_monthly_budget(expenses, budget_file):
    budgets = load_json(budget_file, {})
    current_month = date.today().strftime("%Y-%m")

    print("\n===== MONTHLY BUDGET =====")
    print(f"Current month: {current_month}")
    print("1. Set/update a monthly budget")
    print("2. View a month's budget status")
    choice = input("Choose an option: ").strip()

    if choice == "1":
        month = input(
            f"Enter month (YYYY-MM, Enter for {current_month}): "
        ).strip()
        if not month:
            month = current_month
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            print("Invalid month. Use YYYY-MM.")
            return

        try:
            amount = float(input("Enter budget amount (₹): "))
            if not math.isfinite(amount) or amount <= 0:
                print("Budget must be a finite number greater than zero.")
                return
        except ValueError:
            print("Please enter a valid amount.")
            return

        budgets[month] = amount
        save_json(budget_file, budgets)
        print(f"Budget for {month} saved: ₹{amount:.2f}")

    elif choice == "2":
        month = input(
            f"Enter month to view (YYYY-MM, Enter for {current_month}): "
        ).strip()
        if not month:
            month = current_month
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            print("Invalid month. Use YYYY-MM.")
            return

        budget = budgets.get(month)
        month_expenses = [
            item for item in expenses
            if str(item.get("date", "")).startswith(month + "-")
        ]
        spent = sum(valid_amount(item.get("amount", 0)) for item in month_expenses)

        print(f"\nBudget report for {month}")
        if budget is None:
            print("No budget has been set for this month.")
            print(f"Total spent: ₹{spent:.2f}")
            return

        remaining = budget - spent
        print(f"Budget limit: ₹{budget:.2f}")
        print(f"Total spent: ₹{spent:.2f}")
        if remaining >= 0:
            print(f"Remaining budget: ₹{remaining:.2f}")
            if remaining == 0:
                print("You have reached your budget limit.")
        else:
            print(f"Budget exceeded by: ₹{abs(remaining):.2f}")
            print("WARNING: You have crossed your monthly budget!")

    else:
        print("Invalid choice!")


# ---------- EXPORT EXPENSES TO CSV ----------
def export_expenses_csv(expenses, csv_file):
    print("\n===== EXPORT EXPENSES TO CSV =====")
    if not expenses:
        print("No expenses available to export.")
        return

    try:
        with open(csv_file, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["date", "category", "amount", "description"]
            )
            writer.writeheader()
            for item in expenses:
                writer.writerow({
                    "date": item.get("date", ""),
                    "category": item.get("category", ""),
                    "amount": item.get("amount", 0),
                    "description": item.get("description", "")
                })
        print(f"Export successful! CSV saved at:\n{csv_file}")
        print("You can open this file in Microsoft Excel.")
    except OSError as error:
        print(f"Could not export CSV: {error}")

# ---------- USER EXPENSE APP ----------
def run_expense_tracker(username):
    expense_file, category_file = get_user_files(username)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", username)
    if username.lower() == "rakshit":
        budget_file = BASE_DIR / "budget.json"
        csv_file = BASE_DIR / "expenses_export.csv"
    else:
        budget_file = BASE_DIR / f"budget_{safe_name}.json"
        csv_file = BASE_DIR / f"expenses_export_{safe_name}.csv"

    expenses = load_json(expense_file, [])
    if not isinstance(expenses, list) or any(not isinstance(item, dict) for item in expenses):
        print("Warning: expense data has an invalid format. Starting with an empty list in memory.")
        expenses = []

    categories = load_json(category_file, DEFAULT_CATEGORIES.copy())
    if not isinstance(categories, list) or any(not isinstance(item, str) for item in categories):
        print("Warning: category data has an invalid format. Using default categories in memory.")
        categories = DEFAULT_CATEGORIES.copy()

    if not category_file.exists():
        save_json(category_file, categories)

    def save_expenses():
        save_json(expense_file, expenses)

    print(f"\nWelcome, {username}!")

    while True:
        print(f"\n===== {username.upper()}'S EXPENSE TRACKER =====")
        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. View Summary")
        print("4. Manage Categories")
        print("5. Delete Expense")
        print("6. Switch User")
        print("7. Daily & Monthly Reports")
        print("8. Search Expense")
        print("9. Update Expense")
        print("10. Monthly Budget")
        print("11. Export to CSV")
        print("12. Exit Program")

        choice = input("Enter your choice: ").strip()

        # ---------- OPTION 1: ADD EXPENSE ----------
        if choice == "1":
            while True:
                print("\n===== ADD EXPENSE =====")

                for i, category in enumerate(categories, start=1):
                    print(f"{i}. {category}")

                print(f"{len(categories) + 1}. Add New Category")
                print(f"{len(categories) + 2}. Back to Main Menu")

                cat_choice = input("Select category: ").strip()

                if not cat_choice.isdigit():
                    print("Please enter a valid number!")
                    continue

                cat_choice = int(cat_choice)

                if 1 <= cat_choice <= len(categories):
                    category = categories[cat_choice - 1]

                    try:
                        amount = float(input("Enter amount (₹): "))

                        if not math.isfinite(amount) or amount <= 0:
                            print("Amount must be a finite number greater than zero!")
                            continue

                    except ValueError:
                        print("Please enter a valid amount!")
                        continue

                    description = input("Enter description: ").strip()

                    today = date.today().isoformat()
                    print(f"Today's date: {today}")

                    while True:
                        expense_date = input(
                            "Enter date (YYYY-MM-DD), "
                            "or press Enter for today: "
                        ).strip()

                        if expense_date == "":
                            expense_date = today
                            break

                        try:
                            datetime.strptime(
                                expense_date,
                                "%Y-%m-%d"
                            )
                            break
                        except ValueError:
                            print(
                                "Invalid date! Use YYYY-MM-DD, "
                                "for example 2026-10-15."
                            )

                    expenses.append({
                        "category": category,
                        "amount": amount,
                        "description": description,
                        "date": expense_date
                    })

                    save_expenses()
                    print("Expense added and saved successfully!")

                    again = input(
                        "Add another expense? (y/n): "
                    ).strip().lower()

                    if again != "y":
                        break

                elif cat_choice == len(categories) + 1:
                    add_new_category(categories, category_file)

                elif cat_choice == len(categories) + 2:
                    break

                else:
                    print("Invalid category choice!")

        # ---------- OPTION 2: VIEW EXPENSES ----------
        elif choice == "2":
            print("\n===== ALL EXPENSES =====")
            show_expenses(expenses)

        # ---------- OPTION 3: OVERALL SUMMARY ----------
        elif choice == "3":
            print("\n===== OVERALL EXPENSE SUMMARY =====")

            total = sum(valid_amount(item.get("amount", 0)) for item in expenses)
            print(f"Total expenses: ₹{total:.2f}")

            for category in categories:
                category_total = sum(
                    valid_amount(item.get("amount", 0))
                    for item in expenses
                    if item.get("category") == category
                )

                if category_total > 0:
                    print(f"{category}: ₹{category_total:.2f}")

            print(f"Number of expenses: {len(expenses)}")

        # ---------- OPTION 4: MANAGE CATEGORIES ----------
        elif choice == "4":
            while True:
                print("\n===== MANAGE CATEGORIES =====")

                for i, category in enumerate(categories, start=1):
                    print(f"{i}. {category}")

                print(f"{len(categories) + 1}. Add New Category")
                print(f"{len(categories) + 2}. Back to Main Menu")

                manage_choice = input("Enter your choice: ").strip()

                if not manage_choice.isdigit():
                    print("Please enter a valid number!")
                    continue

                manage_choice = int(manage_choice)

                if manage_choice == len(categories) + 1:
                    add_new_category(categories, category_file)

                elif manage_choice == len(categories) + 2:
                    break

                else:
                    print("Invalid choice!")

        # ---------- OPTION 5: DELETE EXPENSE ----------
        elif choice == "5":
            print("\n===== DELETE EXPENSE =====")

            if not expenses:
                print("No expenses available to delete.")
                continue

            show_expenses(expenses)

            delete_choice = input(
                "\nEnter expense number to delete (0 to cancel): "
            ).strip()

            if not delete_choice.isdigit():
                print("Please enter a valid number!")
                continue

            delete_choice = int(delete_choice)

            if delete_choice == 0:
                print("Deletion cancelled.")

            elif 1 <= delete_choice <= len(expenses):
                confirm = input(
                    "Are you sure? (y/n): "
                ).strip().lower()

                if confirm == "y":
                    deleted = expenses.pop(delete_choice - 1)
                    save_expenses()

                    print(
                        f"Deleted {deleted['category']} expense: "
                        f"₹{deleted['amount']:.2f}"
                    )
                    print("Expense deleted and saved successfully!")
                else:
                    print("Deletion cancelled!")

            else:
                print("Expense number does not exist!")

        # ---------- OPTION 6: SWITCH USER ----------
        elif choice == "6":
            print("Returning to user selection...")
            return "switch"

        # ---------- OPTION 7: DAILY & MONTHLY REPORTS ----------
        elif choice == "7":
            show_date_reports(expenses, categories)

        # ---------- OPTION 8: SEARCH EXPENSE ----------
        elif choice == "8":
            search_expenses(expenses)

        # ---------- OPTION 9: UPDATE EXPENSE ----------
        elif choice == "9":
            update_expense(expenses, categories, save_expenses)

        # ---------- OPTION 10: MONTHLY BUDGET ----------
        elif choice == "10":
            manage_monthly_budget(expenses, budget_file)

        # ---------- OPTION 11: EXPORT TO CSV ----------
        elif choice == "11":
            export_expenses_csv(expenses, csv_file)

        # ---------- OPTION 12: EXIT ----------
        elif choice == "12":
            print("Thank you for using Expense Tracker!")
            return "exit"

        else:
            print("Invalid choice! Please select a number from 1 to 12.")


# ---------- START PROGRAM ----------
while True:
    selected_user = choose_user()

    if selected_user is None:
        print("Goodbye!")
        break

    result = run_expense_tracker(selected_user)

    if result == "exit":
        break
