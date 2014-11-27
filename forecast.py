#!/usr/bin/env python

from __future__ import print_function
import sys
from datetime import datetime, timedelta
#import getpass
import gnucashxml
import csv

def main():
    filename = sys.argv[1]
    book = gnucashxml.from_filename(filename)

#    username = raw_input("Username: ")
#    password = getpass.getpass()
#
#    print(username, ":", password)
#
#
#
#    import gdata.docs.service
#
#    # Create a client class which will make HTTP requests with Google Docs server.
#    client = gdata.docs.service.DocsService()
#    # Authenticate using your Google Docs email address and password.
#    client.ClientLogin('admin@lists.skullspace.ca', '2014Directors')
#
#    # Query the server for an Atom feed containing a list of your documents.
#    documents_feed = client.GetDocumentListFeed()
#    # Loop through the feed and extract each document entry.
#    for document_entry in documents_feed.entry:
#        # Display the title of the document on the command line.
#        print(document_entry.title.text)
#
#    return
#
#
#
#
#

    assets = book.find_account("Current Assets")

    asset_total = 0
    for account in assets.children:
        if account.name != "Prepaid Rent":
            asset_total += sum(split.value for split in account.splits)

    liabilities = book.find_account("Active Members")

    liability_total = sum(split.value for split in liabilities.get_all_splits())

    today = datetime.now()
    first_of_month = datetime(today.year, today.month, 1)

    member_dues = book.find_account("Member Dues")
    dues = 0
    members = 0
    for split in member_dues.get_all_splits():
        if split.transaction.date.replace(tzinfo=None) >= first_of_month:
            dues += split.value
            members += len(split.transaction.splits) - 1

    member_donations = book.find_account("Regular donations")
    donations = 0
    donating_members = 0
    for split in member_donations.get_all_splits():
        if split.transaction.date.replace(tzinfo=None) >= first_of_month:
            donations += split.value
            donating_members += len(split.transaction.splits) - 1

    print("Total assets: ", asset_total)
    print("Total liability: ", liability_total)
    print("Available capital: ", asset_total + liability_total)
    dues *= -1
    print("Dues collected last month: ", dues)
    print("Dues paying members: ", members)
    donations *= -1
    print("Regular donations collected last month: ", donations)
    print("Regularly donating members: ", donating_members)
    print("Total expected income: ", (dues + donations))

    with open('foobar.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Total assets', 'Total liability', 'Available capital', 'Dues collected last month', 'Dues paying members', 'Regular donations collected last month', 'Regularly donating members', 'Total expected income'])
        writer.writerow([asset_total, liability_total, asset_total + liability_total, dues, members, donations, donating_members, dues + donations])

if __name__ == "__main__":
    main()
