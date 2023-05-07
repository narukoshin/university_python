#!/usr/bin/python3

import sqlite3
import re
import os

# To convert string to real date format
import datetime

class main:
    conn    = None
    db      = None
    file    = None
    dbfile  = "database.db"
    '''
        Declaring variables and reading files.
    '''
    def __init__(self):
        # creating tables
        self.create_db()
        # reading the file/-s
        self.file = open("mbox.txt", "r")
        # getting the contents
        self.contents()
        # loading data from the database
        self.load_data()
    '''
        Creates and prepares database for the further actions.
        A database connection is created here that is keeped alive.
    '''
    def create_db(self):
        if self.conn is None:
            if not os.path.isfile(self.dbfile):
                print("Creating tables, please take a coffee...")
            # connecting to the database
            self.conn = sqlite3.connect(self.dbfile)
            self.db   = self.conn.cursor()
            # creating the tables
            #self.db.execute("CREATE TABLE IF NOT EXISTS domains (id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT)")
            self.db.execute("CREATE TABLE IF NOT EXISTS emails (id INTEGER PRIMARY KEY AUTOINCREMENT, email_address TEXT, domain_name TEXT, date TEXT, added_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(domain_name) REFERENCES domains(domain_name))")
            self.db.execute("CREATE TABLE IF NOT EXISTS domains (id INTEGER PRIMARY KEY AUTOINCREMENT, domain_name TEXT, added_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
            self.db.execute("CREATE TABLE IF NOT EXISTS spam_levels (id INTEGER PRIMARY KEY AUTOINCREMENT, spam_confidence INTEGER, email TEXT, added_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(email) REFERENCES emails(email_address))")
            self.conn.commit()
   
    '''
        Converting the date from one format to another.

        @param string date
        @return string  converted date
    '''
    def date_format(self, date):
        format1 = "^[A-Z][a-z]{2}, \d{1,2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2} [-+]\d{4}$"
        format2 = "^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [-+]\d{4} \([A-Z][a-z]{2}, \d{2} [A-Z][a-z]{2} \d{4}\)$"

        if re.match(format1, date):
            old_date = datetime.datetime.strptime(date.strip(), "%a, %d %b %Y %H:%M:%S %z")
            return old_date.strftime('%A, %Y-%m-%d %H:%M:%S')

        elif re.match(format2, date):
            old_date = datetime.datetime.strptime(date.strip()[:30], '%Y-%m-%d %H:%M:%S %z (%a')
            return old_date.strftime('%A, %Y-%m-%d %H:%M:%S')
    
    '''
        Inserting email, domain and date in the database

        @param string email     An email
        @param string domain    Domain name of the email
        @param string date      The date
    '''
    def insert_email(self, email, domain, date):
        self.insert_domain(domain)
        # Checking if there isn't data with the same domain name to avoid duplicates.
        stmt = self.db.execute(f"SELECT email_address FROM emails WHERE email_address = '{email}' LIMIT 1;")
        results = stmt.fetchone()
        # If there's no data in the table, adding a new entry.
        if not results:
            self.db.execute(f"INSERT INTO emails (email_address, domain_name, date) VALUES('{email}', '{domain}', '{date}')")
            self.conn.commit()
    '''
        Inserting domain name in the database

        @param string domain    Domain name of the email
    '''
    def insert_domain(self, domain):
        # Checking if there isn't data with the same domain name to avoid duplicates.
        stmt = self.db.execute(f"SELECT domain_name FROM domains WHERE domain_name = '{domain}' LIMIT 1;")
        results = stmt.fetchone()
        # If there's no data in the table, adding a new entry.
        if not results:
            self.db.execute(f"INSERT INTO domains (domain_name) VALUES('{domain}')")
            self.conn.commit()
    '''
        Inserting spam confidence in the database

        @param string email
        @param float spam_confidence
    '''
    def insert_spamconfidence(self, email, spam_confidence):
        # Checking if there isn't data with the same email to avoid duplicates.
        stmt = self.db.execute(f"SELECT email FROM spam_levels WHERE email = '{email}' LIMIT 1;")
        results = stmt.fetchone()
        # If there's no data in the table, adding a new entry.
        if not results:
            self.db.execute(f"INSERT INTO spam_levels (spam_confidence, email) VALUES('{spam_confidence}', '{email}')")
            self.conn.commit()
    '''
        Reading the necessary contents from the file and adding them to the array.
        It checks if there's no duplication in the arrays and later, it calls methods to insert data in database.
    '''
    def contents(self):
        if self.file is not None:
            # reading the file contents
            contents = self.file.readlines()
            # declaring variables for storing data
            emails              = []
            domains             = []
            spam_confidences    = []
            dates               = []
            # iterating trough the file/-s
            # Because we are reading every line
            # We need to mark a border from - to
            # This is because to make sure that the data is valid for the specific email
            notDuplicate = False
            for line in contents:
                if "from:" in line.lower():
                    # getting emails
                    email = re.search("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", line).group()
                    # checking if the email is not already in the list
                    # if the email is not in the list, adding it.
                    if not email in emails:
                        emails.append(email)
                        # setting, that this is not a duplicate.
                        notDuplicate = True
                    else:
                        # email duplication found, skipping...
                        continue
                    # getting domain of the email
                    domain = email.split("@")[1]
                    domains.append(domain)
                # Looking for the date and looking if we are in the same border
                # ..where we found an email
                if "date:" in line.lower() and notDuplicate:
                    # getting the date
                    date = self.date_format(line[6:])
                    if date in dates:
                        continue
                    dates.append(date)
                    notDuplicate = False
                # Looking for the spam confidence and looking if we are in the same border
                # ..where we found an email
                if "x-dspam-confidence" in line.lower() and notDuplicate:
                    spam_confidences.append(line.lower()[20:].replace("\n", ""))          
            # Printing a message that we are inserting the data.
            print("Inserting data in the database...")
            for email, domain, date, spam_confidence in zip(emails, domains, dates, spam_confidences):
                # Connecting all the data together
                self.insert_email(email, domain, date)
                self.insert_spamconfidence(email, spam_confidence)
    '''
        This function will print out a list of available domains to choose.
    '''
    def list_domains(self):
        stmt = self.db.execute("SELECT domain_name FROM domains;")
        domains = stmt.fetchall()
        for domain in domains:
            print(f"- {domain[0]}")
        return domains
    '''
        When a user received a list of available domains...
            user can input the domain to load more info from the database about the specific domain.
    '''
    def choose_domain(self, domains_list):
        # asking user to input the domain name
        try:
            domain = input("Please choose a domain from the list: ")
        except KeyboardInterrupt:
            # printing a message that user existed the application
            print("User exist.")
        # Checking of the domain user entered exists
        found = False
        for d in domains_list:
            if domain in d[0]:
                found = True
        if not found:
            print("We can't find your selected domain")
            return False
        return domain
        
    '''
        Getting the info from the database

        @param string domain_name   Domain name of the email
    '''
    def print_data(self, domain_name):
        stmt = self.db.execute(f"""
            SELECT DISTINCT e.date, e.email_address, sp.spam_confidence
            FROM emails e
            JOIN domains d ON e.domain_name = d.domain_name
            JOIN spam_levels sp ON e.email_address = sp.email
            WHERE e.domain_name = '{domain_name}' AND (e.date LIKE '%Friday%' OR e.date LIKE '%Saturday%')
            ORDER BY e.date;
        """)
        data = stmt.fetchall()
        if not data:
            print("There's no emails, sorry")
            return
        for d in data:
            print("Day of Week: " + d[0].split(",")[0])
            print("Domain name: " + domain_name)
            print("Email Address: " + d[1])
            print("SPAM Confidence: " + str(d[2]))
        
    '''
        Last step of the app where we are loading lal the data from the database
    '''
    def load_data(self):
        print("Loading data, please wait...")
        print("List of unique domains:")
        domains = self.list_domains()
        # Asking uesr to input the domain and checking if the domain is in the list.
        if domain := self.choose_domain(domains):
            # if the domain exists, we are loading more info about the specific domain.
            self.print_data(domain)

# Main function
main()
