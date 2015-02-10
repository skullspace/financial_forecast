#!/usr/bin/env python

from __future__ import print_function
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import gnucashxml
import csv


DATE = 'Date'
ASSETS = 'Assets'
LIABILITIES = 'Liabilities'
CAPITAL = 'Capital'
DUES = 'Dues'
DONATIONS = 'Donations'
FOOD_DONATIONS =  'Food donations'
MEMBERS = 'Members'
DONATING_MEMBERS = 'Donating members'
EXPENSES = 'Expenses'
FOOD_EXPENSES = 'Food expenses'
PROJECTED_CAPITAL = 'Projected capital'
PROJECTED_DUES = 'Projected dues'
PROJECTED_DONATIONS = 'Projected donations'
PROJECTED_MEMBERS = 'Projected members'
PROJECTED_DONATING_MEMBERS = 'Projected donating members'
PROJECTED_FOOD_DONATIONS = 'Projected food donations'
PROJECTED_FOOD_EXPENSES = 'Projected food expenses'
CAPITAL_TARGET = 'Target balance (3 month buffer)'
FOOD_PROFIT = 'Food profit'
PROJECTED_FOOD_PROFIT = 'Projected food profit'

MONTH_START_DAY = 5

EXEMPT_EXPENSE_ACCOUNTS = ["Anti-social 10-04", "Hacker Jeopardy Ron's Revenge", "Groceries"]


def main():
    filename = sys.argv[1]
    book = gnucashxml.from_filename(filename)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if today.day < MONTH_START_DAY:
        today -= relativedelta(months=+1)
    delta = relativedelta(months=+6)
    start = today - delta
    end = today + delta

    history = []

    for month in report_days(start, today):
        print(month)
        assets = get_assets_on_date(book, month)
        liabilities = get_liability_on_date(book, month)
        capital = assets + liabilities
        dues = get_dues_for_month(book, month)
        donations = get_donations_for_month(book, month)
        food_donations = get_food_donations_for_month(book, month)
        members = get_paying_members(book, month)
        donating_members = get_donating_members(book, month)
        expenses = get_expenses_for_month(book, month)
        food_expenses = get_food_expenses_for_month(book, month)

        print("Total assets: ", assets)
        print("Total liability: ", liabilities)
        print("Available capital: ", capital)
        print("Dues collected last month: ", dues)
        print("Dues paying members: ", members)
        print("Regular donations collected last month: ", donations)
        print("Regularly donating members: ", donating_members)
        print("Food donations: ", food_donations)
        print("Total expected income: ", (dues + donations + food_donations))
        print("Expenses: ", expenses)
        print("Food expenses: ", food_expenses)

        history.append({
            DATE: month,
            ASSETS: assets,
            LIABILITIES: liabilities,
            CAPITAL: capital,
            DUES: dues,
            DONATIONS: donations,
            FOOD_DONATIONS: food_donations,
            MEMBERS: members,
            DONATING_MEMBERS: donating_members,
            EXPENSES: expenses,
            FOOD_EXPENSES: food_expenses,
            CAPITAL_TARGET: expenses * -3,
            FOOD_PROFIT: food_donations + food_expenses,
        })

        print()

    income = get_projected_income(history)
    expenses = get_projected_expenses(history) - get_historical_rent_expenses_average(book, start, today)

    print("Projected income: ", income)
    print("Projected expenses: ", expenses, " (plus monthly rent amount)")

    food_income = get_projected_food_income(history)
    food_expenses = get_projected_food_expenses(history)

    history[-1][PROJECTED_CAPITAL] = history[-1][CAPITAL]
    history[-1][PROJECTED_DUES] = history[-1][DUES]
    history[-1][PROJECTED_DONATIONS] = history[-1][DONATIONS]
    history[-1][PROJECTED_MEMBERS] = history[-1][MEMBERS]
    history[-1][PROJECTED_DONATING_MEMBERS] = history[-1][DONATING_MEMBERS]

    for month in report_days(today, end):
        print(month)

        history.append({
            DATE: month,
            PROJECTED_CAPITAL: history[-1][PROJECTED_CAPITAL] + income + expenses + get_rent_expenses_for_month(book, month),
            PROJECTED_DUES: history[-1][PROJECTED_DUES],
            PROJECTED_DONATIONS: history[-1][PROJECTED_DONATIONS],
            PROJECTED_MEMBERS: history[-1][PROJECTED_MEMBERS],
            PROJECTED_DONATING_MEMBERS: history[-1][PROJECTED_DONATING_MEMBERS],
            PROJECTED_FOOD_DONATIONS: food_income,
            PROJECTED_FOOD_EXPENSES: food_expenses,
            CAPITAL_TARGET: (expenses + get_rent_expenses_for_month(book, month)) * -3,
            FOOD_PROFIT: food_income + food_expenses,
        })

    with open('foobar.csv', 'wb') as csvfile:
        fieldnames = [
            DATE,
            ASSETS,
            LIABILITIES,
            PROJECTED_CAPITAL,
            CAPITAL,
            PROJECTED_DUES,
            DUES,
            PROJECTED_DONATIONS,
            DONATIONS,
            PROJECTED_MEMBERS,
            MEMBERS,
            PROJECTED_DONATING_MEMBERS,
            DONATING_MEMBERS,
            EXPENSES,
            PROJECTED_FOOD_DONATIONS,
            FOOD_DONATIONS,
            PROJECTED_FOOD_EXPENSES,
            FOOD_EXPENSES,
            CAPITAL_TARGET,
            FOOD_PROFIT,
        ]



        writer = csv.DictWriter(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames)

        writer.writeheader()
        for history_item in history:
            writer.writerow(history_item)


def get_assets_on_date(book, date):
    assets = book.find_account("Current Assets")

    asset_total = 0
    for account in assets.children:
        if account.name != "Prepaid Rent":
            asset_total += sum(split.value for split in account.splits if split.transaction.date.replace(tzinfo=None) <= date)

    return asset_total


def get_liability_on_date(book, date):
    liabilities = book.find_account("Active Members")
    liability_total = sum(split.value for split in liabilities.get_all_splits() if split.transaction.date.replace(tzinfo=None) <= date)

    liabilities = book.find_account("Former Members")
    liability_total += sum(split.value for split in liabilities.get_all_splits() if split.transaction.date.replace(tzinfo=None) <= date)

    return liability_total


def get_dues_for_month(book, month_end):
    end_date = month_end
    start_date = subtract_month(month_end)

    member_dues = book.find_account("Member Dues")
    dues = 0
    for split in member_dues.get_all_splits():
        if start_date < split.transaction.date.replace(tzinfo=None) <= end_date:
            dues += split.value

    return dues * -1


def get_paying_members(book, month_end):
    end_date = month_end
    start_date = subtract_month(month_end)

    member_dues = book.find_account("Member Dues")
    members = 0
    for split in member_dues.get_all_splits():
        if start_date < split.transaction.date.replace(tzinfo=None) <= end_date:
            members += len(split.transaction.splits) - 1

    return members


def get_donations_for_month(book, month_end):
    end_date = month_end
    start_date = subtract_month(month_end)

    member_donations = book.find_account("Regular donations")
    donations = 0
    for split in member_donations.get_all_splits():
        if start_date < split.transaction.date.replace(tzinfo=None) <= end_date:
            donations += split.value

    return donations * -1


def get_expenses_for_month(book, month_end):
    end_date = month_end
    start_date = subtract_month(month_end)

    expense_accounts = book.find_account("Expenses")
    expenses = 0
    for account in expense_accounts.children:
        if account.name not in EXEMPT_EXPENSE_ACCOUNTS:
            for split in account.get_all_splits():
                if start_date < split.transaction.date.replace(tzinfo=None) <= end_date:
                    expenses += split.value

    return expenses * -1


def get_rent_expenses_for_month(book, month_end):
    end_date = month_end
    start_date = subtract_month(month_end)

    expense_accounts = book.find_account("Expenses")
    expenses = 0
    for account in expense_accounts.children:
        if account.name == "Rent":
            for split in account.splits:
                if start_date < split.transaction.date.replace(tzinfo=None) <= end_date:
                    expenses += split.value

    return expenses * -1


def get_historical_rent_expenses_average(book, start, today):
    rent = 0
    months = 0
    for month in report_days(start, today):
        rent += get_rent_expenses_for_month(book, month)
        months += 1

    return rent / months


def get_food_expenses_for_month(book, month_end):
    end_date = month_end
    start_date = subtract_month(month_end)

    expense_accounts = book.find_account("Groceries")
    expenses = 0
    for split in expense_accounts.get_all_splits():
        if start_date < split.transaction.date.replace(tzinfo=None) <= end_date:
            expenses += split.value

    return expenses * -1


def get_food_donations_for_month(book, month_end):
    end_date = month_end
    start_date = subtract_month(month_end)

    food_donations = book.find_account("Food and Drink Donations")
    donations = 0
    for split in food_donations.get_all_splits():
        if start_date < split.transaction.date.replace(tzinfo=None) <= end_date:
            donations += split.value

    return donations * -1


def get_donating_members(book, month_end):
    end_date = month_end
    start_date = subtract_month(month_end)

    member_dues = book.find_account("Regular donations")
    members = 0
    for split in member_dues.get_all_splits():
        if start_date < split.transaction.date.replace(tzinfo=None) <= end_date:
            members += len(split.transaction.splits) - 1

    return members


def subtract_month(date):
    month = date.month - 2
    month = month % 12 + 1
    year = date.year
    if month > date.month:
        year = date.year - 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day)


def report_days(start_date, end_date):
    delta = relativedelta(months=+1)
    d = start_date.replace(day=MONTH_START_DAY)
    while d < end_date.replace(day=MONTH_START_DAY):
        d += delta
        yield d


def get_projected_income(history):
    return history[-1][DUES] + history[-1][DONATIONS]


def get_projected_expenses(history):
    expenses = 0
    for data_point in history:
        expenses += data_point[EXPENSES]

    return expenses / len(history)


def get_projected_food_income(history):
    income = 0
    for data_point in history:
        income += data_point[FOOD_DONATIONS]

    return income / len(history)


def get_projected_food_expenses(history):
    expenses = 0
    for data_point in history:
        expenses += data_point[FOOD_EXPENSES]

    return expenses / len(history)


if __name__ == "__main__":
    main()
