#!/usr/bin/env python3

import os, sys
import subprocess
import base64
import sqlite3
import hashlib
import pyotp
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

key_length = 16
openvpn_path = os.path.join('/','etc','openvpn')


def getSecretFromCryptedFile(username: str, password: str) -> str:
    decrypted_data = ''

    if len(password) < key_length:
        key = password + '\0' * (key_length - len(password))

    try:
        with open(os.path.join(openvpn_path, 'users', f'{username}.crypted'), 'rb') as f:
            nonce = f.read(key_length)
            tag = f.read(key_length)
            ciphertext = f.read()
        cipher = AES.new(key.encode(), AES.MODE_EAX, nonce=nonce)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag).decode().split()[0]
    except FileNotFoundError:
        pass

    return decrypted_data


def checkUserPassword(username: str, password: str) -> bool:
    # username and password match
    ret = False

    try:
        # Connect to the database
        conn = sqlite3.connect(dbfilenem)

    except sqlite3.OperationalError:
        print(f"*** ERROR: cannot access to the {dbfilenem} database!")
        sys.exit(1)

    # Create a cursor object
    cursor = conn.cursor()

    try:
        # Execute a SELECT statement to retrieve data from the users table
        cursor.execute(
            '''
            SELECT salt1, salt2, hash, is_active
            FROM users
            WHERE username = ?
            ''', (username,))

        # Fetch the first row from the result set
        row = cursor.fetchone()

        # If a row is found, assign values to corresponding variables
        if row:
            salt1_value, salt2_value, hash_value, is_active_value = row
            if is_active_value:
                # Combine salt and password
                salted_password = salt1_value + password

                # Hash the salted password using SHA-256
                hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()

                # Combine salt and hashed
                salted_hash = salt2_value + hashed_password

                # Hash the salted password using SHA-256
                hashed_password = hashlib.sha256(salted_hash.encode()).hexdigest()

                if hashed_password == hash_value:
                    ret = True
            else:
                print("*** ERROR: user account's not active!")

    except sqlite3.OperationalError:
        print("*** ERROR: something gone wrong reading users table!")

    # Close the connection
    conn.close()

    return ret


if __name__ == "__main__":
    # name of the SQLite database
    dbfilenem = os.path.join(openvpn_path, 'users', 'users.db')
    if not os.path.exists(dbfilenem):
        print("*** ERROR: no database found!")
        sys.exit(1)

    # Check if exactly one parameter is provided
    if len(sys.argv) != 2:
        sys.exit(1)

    # Get the parameter
    file_path = sys.argv[1]

    # Check if the file with the user's input exists
    if not os.path.exists(file_path):
        sys.exit(1)

    # Open the file in read mode
    with open(file_path, 'r') as file:
        # Read the first line and save it to a variable
        username = file.readline().strip()

        # Read the second line and save it to another variable
        pass_and_otp = file.readline().strip()

    if pass_and_otp.startswith("SCRV1"):
        # Split the string by ":"
        parts = pass_and_otp.split(":")

        # get clean password
        password = base64.b64decode(parts[1]).decode()

        if not checkUserPassword(username, password):
            print("*** ERROR: username and password doesn't match!")

            # Not authenticated
            sys.exit(1)

        # get clean OTP
        pin = base64.b64decode(parts[2]).decode()
        if not pin.isdigit() or not (len(pin) == 6 or len(pin) == 8):
            print("*** ERROR: PIN is not a correct sequence of digit!")

            # Not authenticated
            sys.exit(1)

        user_filename = os.path.join(openvpn_path, 'users', f'{username}.crypted')
        if not os.path.exists(user_filename):
            print(f"***ERROR: username '{username}' doesn't exist!")

            # Not authenticated
            sys.exit(1)

        secret = getSecretFromCryptedFile(username, password)
        if not secret:
            print("***ERROR: username and password don't match!")
            sys.exit(1)

        # verify TOTP by secret and pin
        totp = pyotp.TOTP(secret)

        if totp.verify(pin):
            # Get the current Unix timestamp without the decimal part
            unix_timestamp = int(datetime.now().timestamp())

            try:
                # Connect to the database
                conn = sqlite3.connect(dbfilenem)

            except sqlite3.OperationalError:
                print(f"*** ERROR: cannot access to the {dbfilenem} database!")
                sys.exit(1)

            # Create a cursor object
            cursor = conn.cursor()

            try:
                # Execute a SELECT statement to retrieve data from the users table
                cursor.execute('''
                    UPDATE users
                    SET last_access_timestamp = ?
                    WHERE username = ?
                    ''', (unix_timestamp, username,))

                # Commit the transaction
                conn.commit()

            except sqlite3.OperationalError:
                print("*** ERROR: something gone wrong updating users table!")
                sys.exit(1)

            # Close the connection
            conn.close()

            # Authenticated
            sys.exit(0)

        else:
            # Not authenticated
            sys.exit(1)
    else:
        # Not authenticated
        sys.exit(1)
