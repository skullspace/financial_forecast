#!/usr/bin/env python

from __future__ import print_function
import sys
from datetime import datetime#, timedelta
import calendar
#import getpass
import gnucashxml
import csv

def main():
    filename = sys.argv[1]
    book = gnucashxml.from_filename(filename)

    start = datetime(2014, 4, 22)
    end = datetime(2014, 11, 25)

    history = []

    for month in monthrange(start, end):
        print(month)
        assets = get_assets_on_date(book, month)
        liabilities = get_liability_on_date(book, month)
        capital = assets + liabilities
        dues = get_dues_for_month(book, month)
        donations = get_donations_for_month(book, month)
        members = get_paying_members(book, month)
        donating_members = get_donating_members(book, month)

        print("Total assets: ", assets)
        print("Total liability: ", liabilities)
        print("Available capital: ", capital)
        print("Dues collected last month: ", dues)
        print("Dues paying members: ", members)
        print("Regular donations collected last month: ", donations)
        print("Regularly donating members: ", donating_members)
        print("Total expected income: ", (dues + donations))

        history.append({
            'month': month,
            'assets': assets,
            'liabilities': liabilities,
            'capital': capital,
            'dues': dues,
            'donations': donations,
            'members': members,
            'donating_members': donating_members,
        })

        print()

    with open('foobar.csv', 'wb') as csvfile:
        fieldnames = ['month', 'assets', 'liabilities', 'capital', 'dues', 'donations', 'members', 'donating_members']
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
    year = date.year - 1/12
    day = min(date.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day)


def monthrange(start_date, end_date):
    for month in range(start_date.month, end_date.month):
        yield datetime(2014, month + 1, 4)

if __name__ == "__main__":
    main()
