import json

with open("expenses.json", "r") as file:
    expenses = json.load(file)

print(expenses)