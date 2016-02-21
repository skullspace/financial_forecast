#!/usr/bin/env python

from __future__ import print_function
import sys
import gnucashxml
import getopt
import csv
import re


DATE = 'Date'
MEMBERS = 'Members'
DONATING_MEMBERS = 'Donating members'

NAME = 'Name'
EMAIL = 'Email address'
ACCOUNT_BALANCE = 'Account balance'
MEMBERSHIP_TYPE = 'Membership type'


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "a:b:c:")
    except getopt.GetoptError:
        print("argument error")
        sys.exit(2)

    filename = args[0]
    book = gnucashxml.from_filename(filename)

    active_members = []

    active_member_accounts = book.find_account("Active Members")
    for account in active_member_accounts.find_account("Full Members").children:
        member = Member(account)
        active_members.append(member)

    for account in active_member_accounts.find_account("Student Members").children:
        member = StudentMember(account)
        active_members.append(member)

    with open('members.csv', 'wb') as csvfile:
        fieldnames = [
            NAME,
            EMAIL,
            MEMBERSHIP_TYPE,
            ACCOUNT_BALANCE,
        ]

        writer = csv.DictWriter(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames)

        writer.writeheader()

        for member in active_members:
            writer.writerow({
                NAME: member.name(),
                EMAIL: member.email(),
                MEMBERSHIP_TYPE: member.type(),
                ACCOUNT_BALANCE: member.effective_balance()
            })
            print(member.name(), "has a balance of", "$" + str(member.effective_balance()), "   ", member.email())

            if member.email() == None:
                print("ERROR:", member.name(), "does not have an email address on record")


class Member(object):
    monthy_dues = 40
    membership_type = "Regular"

    def __init__(self, account):
        self.account = account

    def type(self):
        return self.membership_type

    def name(self):
        return self.account.name

    def balance(self):
        return sum((-1 * split.value) for split in self.account.splits)

    def effective_balance(self):
        return self.balance() - self.monthy_dues

    def email(self):
        email = re.search("[^@ ]+@[^@ ]+\.[^@ ]+", self.account.description)
        if email is None:
            return None
        else:
            return email.group()


class StudentMember(Member):
    monthy_dues = 20
    membership_type = "Student"


if __name__ == "__main__":
    main(sys.argv[1:])
