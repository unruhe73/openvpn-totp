#!/usr/bin/env python3

import os, sys
import sqlite3
import hashlib
import random
import string
from datetime import datetime
from cryptography.fernet import Fernet


class UserManagement:
    def __init__(self):
        self.password_size = 10
        self.minimun_password_size = 5
        self.base_path = ''


    def generatePassword(self, pass_size: int = 0) -> str:
        if pass_size < self.minimun_password_size:
            pass_size = self.password_size

        # Define the characters to choose from
        characters = string.ascii_letters + string.digits

        # Generate a sequence of password_size random characters
        password = ''.join(random.choice(characters) for _ in range(pass_size))

        return password


    def setDatabasePath(self, base_path: str) -> None:
        # Assign path and name of the SQLite database
        filename = 'users.db'
        self.base_path = base_path
        self.dbfilename = os.path.join(base_path, filename)


    def getDatabaseFilePath(self):
        return self.dbfilename


    def createDatabase(self) -> bool:
        ret = False

        os.makedirs(self.base_path, exist_ok = True)

        try:
            # Connect to the database (or create it if it doesn't exist)
            conn = sqlite3.connect(self.dbfilename)

        except sqlite3.OperationalError:
            print(f"*** ERROR: cannot access to the {self.dbfilename} database!")
            sys.exit(1)

        # Create a cursor object
        cursor = conn.cursor()

        try:
            # Create a table
            cursor.execute('''CREATE TABLE users
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 username TEXT UNIQUE,
                 salt1 TEXT,
                 salt2 TEXT,
                 hash TEXT,
                 is_active INTEGER,
                 disactived_timestamp TIMESTAMP DEFAULT 0,
                 last_access_timestamp TIMESTAMP DEFAULT 0)''')

            # Commit the transaction
            conn.commit()

            # Operation successful
            print("*** DONE: database created successful")
            ret = True

        except sqlite3.OperationalError:
            try:
                # Execute a SELECT statement to retrieve data from the users table
                cursor.execute("SELECT id, creation_timestamp, username, salt1, salt2, hash, is_active, disactived_timestamp, last_access_timestamp FROM users")

                # Commit the transaction
                conn.commit()

            except sqlite3.OperationalError:
                print("*** ERROR: I cannot find the correct user table!")
                sys.exit(1)

        # Close the connection
        conn.close()

        return ret


    def addUser(self, username: str, password: str = "") -> (bool, str):
        ret = False

        try:
            # Connect to the database
            conn = sqlite3.connect(self.dbfilename)

        except sqlite3.OperationalError:
            print(f"*** ERROR: cannot access to the {self.dbfilename} database!")
            sys.exit(1)

        # Create a cursor object
        cursor = conn.cursor()

        # Generate a secure key salt using Fernet
        salt1 = Fernet.generate_key().decode()

        if not password:
            # Generate a sequence of password_size random characters
            password = self.generatePassword()

        # Combine salt and password
        salted_password = salt1 + password

        # Hash the salted password using SHA-256
        hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()

        # Generate a secure key salt using Fernet
        salt2 = Fernet.generate_key().decode()

        # Combine salt and hashed
        salted_hash = salt2 + hashed_password

        # Hash the salted hash using SHA-256
        hashed_password = hashlib.sha256(salted_hash.encode()).hexdigest()

        # Get the current Unix timestamp without the decimal part
        creation_timestamp = int(datetime.now().timestamp())

        # Define the data to insert
        data_to_insert = {
            'creation_timestamp': creation_timestamp,
            'username': username,
            'salt1': salt1,
            'salt2': salt2,
            'hash': hashed_password,
            'is_active': 1
        }

        try:
            # Insert data into the table
            cursor.execute('''INSERT INTO users (creation_timestamp, username, salt1, salt2, hash, is_active) VALUES (:creation_timestamp, :username, :salt1, :salt2, :hash, :is_active)''', data_to_insert)

            # Commit the transaction
            conn.commit()

            # Operation successful
            print(f"*** DONE: added user '{username}'")
            ret = True

            # output the password
            print(f"Here the password for the user '{username}': {password}")

        except sqlite3.IntegrityError:
            print(f"*** ERROR: user '{username}' is already into the database!")
            ret = False

        # Close the connection
        conn.close()

        return ret, password


    def showUsernameData(self, username: str) -> None:
        try:
            # Connect to the database
            conn = sqlite3.connect(self.dbfilename)

        except sqlite3.OperationalError:
            print(f"*** ERROR: cannot access to the {self.dbfilename} database!")
            sys.exit(1)

        # Create a cursor object
        cursor = conn.cursor()

        try:
            # Execute a SELECT statement to retrieve data from the users table
            cursor.execute('''SELECT * FROM users WHERE username = ?''', (username,))

            # Fetch the first row from the result set
            row = cursor.fetchone()

            # If a row is found, assign values to corresponding variables
            if row:
                id_value, creation_timestamp_value, username_value, salt1_value, salt2_value, hash_value, is_active_value, disactived_timestamp_value, last_access_timestamp_value = row

                # Convert timestamp to datetime object
                dt_object = datetime.fromtimestamp(creation_timestamp_value)

                # Convert datetime object to a readable date and time string
                readable_creation_datetime = dt_object.strftime('%d %B %Y %H:%M:%S')
                
                # Convert timestamp to datetime object
                dt_object = datetime.fromtimestamp(disactived_timestamp_value)

                # Convert datetime object to a readable date and time string
                readable_disactived_datetime = dt_object.strftime('%d %B %Y %H:%M:%S')

                # Convert timestamp to datetime object
                dt_object = datetime.fromtimestamp(last_access_timestamp_value)

                # Convert datetime object to a readable date and time string
                readable_last_access_datetime = dt_object.strftime('%d %B %Y %H:%M:%S')

                # Print the values or use them as needed
                print("ID:", id_value)
                print(f"Creation timestamp: {creation_timestamp_value}: {readable_creation_datetime}")
                print("Username:", username_value)
                print("Salt1:", salt1_value)
                print("Salt2:", salt2_value)
                print("Hash:", hash_value)
                print("Is active:", is_active_value)
                if disactived_timestamp_value == 0:
                    print(f"Disactived timestamp: never happened")
                else:
                    print(f"Disactived  timestamp: {disactived_timestamp_value}: {readable_disactived_datetime}")
                if last_access_timestamp_value == 0:
                    print(f"Last access timestamp: never happened")
                else:
                    print(f"Last access timestamp: {last_access_timestamp_value}: {readable_last_access_datetime}")
            else:
                print(f"*** ERROR: No user found with username '{username}'!")

        except sqlite3.OperationalError:
            print("*** ERROR: something gone wrong reading users table!")

        # Close the connection
        conn.close()


    def resetUserPassword(self, username: str, password: str = "") -> (bool, str):
        ret = False

        try:
            # Connect to the database
            conn = sqlite3.connect(self.dbfilename)

        except sqlite3.OperationalError:
            print(f"*** ERROR: cannot access to the {self.dbfilename} database!")
            sys.exit(1)

        # Create a cursor object
        cursor = conn.cursor()

        try:
            # Execute a SELECT statement to retrieve data from the users table
            cursor.execute('''SELECT id FROM users WHERE username = ?''', (username,))

            # Fetch the first row from the result set
            row = cursor.fetchone()

            # If a row is found, assign values to corresponding variables
            if row:
                id_value = row

                # generate a secure key salt using Fernet
                salt1 = Fernet.generate_key().decode()

                if not password:
                    # Generate a sequence of password_size random characters
                    password = self.generatePassword()

                # Combine salt and password
                salted_password = salt1 + password

                # Hash the salted password using SHA-256
                hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()

                # Generate a secure key salt using Fernet
                salt2 = Fernet.generate_key().decode()

                # Combine salt and hashed
                salted_hash = salt2 + hashed_password

                # Hash the salted hash using SHA-256
                hashed_password = hashlib.sha256(salted_hash.encode()).hexdigest()

                try:
                    # Execute the UPDATE statement
                    cursor.execute('''UPDATE users SET salt1 = ?, salt2 = ?, hash = ?, is_active = 1 WHERE id = ?''',
                        (salt1, salt2, hashed_password, id_value[0]))

                    # Commit the transaction
                    conn.commit()

                    # Operation successful
                    print(f"*** DONE: Replaced password for user '{username}'")
                    ret = True

                    # output the new password
                    print(f"Here the NEW password for the username '{username}': '{password}'")

                except sqlite3.OperationalError:
                    print("*** ERROR: something gone wrong updating users table!")
                    sys.exit(1)

            else:
                print(f"*** ERROR: No user found with username '{username}'!")

        except sqlite3.OperationalError:
            print("*** ERROR: something gone wrong reading users table!")

        # Close the connection
        conn.close()

        return ret, password


    def disactiveUser(self, username: str) -> bool:
        ret = False

        # Get the current Unix timestamp without the decimal part
        disactived_timestamp = int(datetime.now().timestamp())

        try:
            # Connect to the database
            conn = sqlite3.connect(self.dbfilename)

        except sqlite3.OperationalError:
            print(f"*** ERROR: cannot access to the {self.dbfilename} database!")
            sys.exit(1)

        # Create a cursor object
        cursor = conn.cursor()

        try:
            # Execute a SELECT statement to retrieve data from the users table
            cursor.execute('''SELECT id FROM users WHERE username = ?''', (username,))

            # Fetch the first row from the result set
            row = cursor.fetchone()

            # If a row is found, assign values to corresponding variables
            if row:
                id_value = row

                try:
                    # Execute the UPDATE statement
                    cursor.execute('''UPDATE users SET is_active = 0, disactived_timestamp = ? WHERE id = ?''',
                        (disactived_timestamp, id_value[0]))

                    # Commit the transaction
                    conn.commit()

                    # Operation successful
                    print(f"*** DONE: Disactivated user '{username}'")
                    ret = True

                except sqlite3.OperationalError:
                    print("*** ERROR: something gone wrong updating users table!")
                    sys.exit(1)

            else:
                print(f"*** ERROR: No user found with username '{username}'!")

        except sqlite3.OperationalError:
            print("*** ERROR: something gone wrong reading users table!")

        # Close the connection
        conn.close()

        return ret


    def resetDatabase(self):
        # Delete the database file
        os.remove(self.dbfilename)

        # create again the database
        self.createDatabase()
