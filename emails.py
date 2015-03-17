#!/usr/bin/env python

from __future__ import print_function
import sys
from datetime import date
#from dateutil.relativedelta import relativedelta
import calendar
import gnucashxml
import getopt
import re
import imaplib
import email.message
import time
import getpass


DATE = 'Date'
MEMBERS = 'Members'
DONATING_MEMBERS = 'Donating members'


def main(argv):
    now = date.today()

    try:
        opts, args = getopt.getopt(argv, "a:b:c:")
    except getopt.GetoptError:
        print("argument error")
        sys.exit(2)

    email_user = raw_input("Gmail username: ")
    email_pass = getpass.getpass("Gmail password: ")

    filename = args[0]
    book = gnucashxml.from_filename(filename)

#    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
#    if today.day < MONTH_START_DAY:
#        today -= relativedelta(months=+1)

    active_members = []

    active_member_accounts = book.find_account("Active Members")
    for account in active_member_accounts.find_account("Full Members").children:
        member = Member(account)
        active_members.append(member)

    for account in active_member_accounts.find_account("Student Members").children:
        member = StudentMember(account)
        active_members.append(member)

    for member in active_members:
        if member.effective_balance() < 0:
            print(member.name(), "has a balance of", member.effective_balance(), "   ", member.email())

            if member.email() == None:
                print("ERROR:", member.name(), "does not have an email address on record")

            else:
                gmail = imaplib.IMAP4_SSL('imap.gmail.com', port = 993)
                gmail.login(email_user, email_pass)
                gmail.select('[Gmail]/Drafts')

                msg = email.message.Message()
                msg['Subject'] = 'SkullSpace Dues'
                msg['To'] = member.email()
                msg['CC'] = 'admin@skullspace.ca'
                msg.set_payload('Hello ' + member.name() + ',\n\nAccording to our records, your account balance is currently $' + str(member.effective_balance()) + '. Dues for the month of ' + calendar.month_name[now.month % 12 + 1] + ' were due on ' + calendar.month_name[now.month] + ' 15th. If you believe there is an issue with this record, please let us know.\n\nThank you,\n\n- Your SkullSpace Board of Directors')

                gmail.append("[Gmail]/Drafts",
                            '',
                            imaplib.Time2Internaldate(time.time()),
                            str(msg))
        #balance = member.balance()
        #spacer1 = " " * (34 - len(member.name()))
        #spacer2 = " " * (6 - len(str(balance)))
        #print("Account", member.type(), ":", member.name(), spacer1, "Balance:", balance, spacer2, "Effective bal:", member.effective_balance(), "email:", member.email())



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
