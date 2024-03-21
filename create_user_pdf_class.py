#!/usr/bin/env python3

import os, sys
import subprocess
import string
import random
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pypdf import PdfWriter, PdfReader
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from vpn_configuration_class import VpnConfiguration


class CreateUserPDF:
    def __init__(self, vpn_name:str, vpn_issuer: str, pdf_directory: str):
        self.up_margin = 30
        self.left_margin = 30
        self.line_spacing = 20
        self.pdf_encryption_password = ''
        self.username = ''
        self.username_password = ''
        self.qr_code_image_path = ''
        self.pdf_filename_path = ''
        self.secret = ''
        self.emergency_scratch_codes = []
        self.pdf_directory = pdf_directory
        self.can_replace = False
        self.password_size = 10
        self.key_length = 16
        self.minimun_password_size = 5
        self.vpn_name = vpn_name
        self.vpn_issuer = vpn_issuer
        self.vpn_config = VpnConfiguration()
        self.dbfilename = os.path.join(self.vpn_config.getUsersDirectory(), 'users.db')


    def encryptSecretFile(self, key: str, input_file: str, output_file:str) -> None:
        if len(key) < self.key_length:
            key = key + '\0' * (self.key_length - len(key))
        cipher = AES.new(key.encode(), AES.MODE_EAX)
        with open(input_file, 'rb') as f:
            data = f.read()
        ciphertext, tag = cipher.encrypt_and_digest(data)
        with open(output_file, 'wb') as f:
            f.write(cipher.nonce)
            f.write(tag)
            f.write(ciphertext)


    def getPdfFilenamePath(self) -> str:
        return self.pdf_filename_path


    def setVpnName(self, name: str) -> None:
        self.vpn_name = name


    def getVpnName(self) -> str:
        return self.vpn_name


    def generatePassword(self, pass_size: int = 0) -> str:
        if pass_size < self.minimun_password_size:
            pass_size = self.password_size

        # Define the characters to choose from
        characters = string.ascii_letters + string.digits

        # Generate a sequence of password_size random characters
        password = ''.join(random.choice(characters) for _ in range(pass_size))

        return password


    def pdfEncryptionPassword(self) -> str:
        return self.pdf_encryption_password


    def setCanReplace(self, can_replace: bool = False):
        self.can_replace = can_replace


    def setMargins(self, up_margin: int = 30, left_margin: int = 30, line_spacing: int = 20) -> None:
        self.up_margin = up_margin
        self.left_margin = left_margin
        self.line_spacing = line_spacing


    def setPdfPassword(self, password: str = "") -> None:
        self.pdf_encryption_password = password


    def setTitle(self, title: str = "") -> None:
        self.title = title


    def setUsernamePassword(self, username: str, password: str) -> None:
        if username:
            self.username = username
            self.username_password = password
            self.setOutputDirectory(self.pdf_directory)
        else:
            print('*** ERROR: username *NOT* defined')
            sys.exit(1)


    def setOutputDirectory(self, directory: str) -> None:
        if self.username:
            if directory:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    self.output_directory = os.path.abspath(directory)
                else:
                    if os.path.isdir(directory):
                        self.output_directory = os.path.abspath(directory)
                    else:
                        print(f"*** ERROR: {directory} exists already but it's not a directory")
                        sys.exit(1)
            else:
                self.output_directory = ""

            self.base_pdf_directory = self.output_directory

            self.output_directory = os.path.join(self.output_directory, f"{self.username}")
            if not os.path.exists(self.output_directory) or self.can_replace:
                os.makedirs(self.output_directory, exist_ok = True)
                self.qr_code_image_path = os.path.join(self.output_directory, f"{self.username}_qr_code.png")
                self.pdf_filename_path = os.path.join(self.output_directory, f"{self.username}_{self.vpn_name}_vpn.pdf")
            else:
                print(f"*** ERROR: '{self.username}' has already its secret and its PDF file!")
                sys.exit(1)
        else:
            print("*** ERROR: username is empty!")
            sys.exit(1)


    def getBasePathDirectory(self) -> str:
        return self.base_pdf_directory


    def usernameCreationDate(self) -> str:
        if not self.dbfilename:
            print("*** ERROR: I need a valid database filename!")
            sys.exit(1)

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
            cursor.execute('''SELECT creation_timestamp FROM users WHERE username = ?''', (self.username,))

            # Fetch the first row from the result set
            row = cursor.fetchone()

            # If a row is found, assign values to corresponding variables
            if row:
                creation_timestamp_value = row[0]

                # Convert timestamp to datetime object
                dt_object = datetime.fromtimestamp(creation_timestamp_value)

                # Convert datetime object to a readable date and time string
                readable_creation_datetime = dt_object.strftime('%d %B %Y %H:%M:%S')

            else:
                print(f"*** ERROR: No user found with username '{self.username}'!")
                sys.exit(1)

        except sqlite3.OperationalError:
            print("*** ERROR: something gone wrong reading users table!")
            sys.exit(1)

        # Close the connection
        conn.close()

        return readable_creation_datetime


    def getSecretAndEmergencyScratchCodes(self) -> None:
        output_file = os.path.join(self.output_directory, f"{self.username}.google_authenticator")
        cmd = f"google-authenticator -i {self.vpn_issuer} -s {output_file} -e 5 -C"

        # Open subprocess and communicate with it
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        # Send inputs to the subprocess
        inputs = b"y\ny\ny\nn\ny\n"
        process.stdin.write(inputs)
        process.stdin.flush()

        # Read the output from the subprocess
        output, _ = process.communicate()

        # Decode the output
        output = output.decode()

        # Look for the text and get the next 10 lines
        secret_key = ""
        phrase = "Your new secret key is: "

        if phrase in output:
            index = output.index(phrase) + len(phrase)
            this_and_next_7_lines = output[index:].split('\n')[0:8]  # Get this and the next 12 lines after the text
            trimmed_lines = [line.strip() for line in this_and_next_7_lines]
            self.secret = trimmed_lines[0]
            self.emergency_scratch_codes = trimmed_lines[3:8]
            texts = "Your emergency scratch codes are:\n"
            texts += '\n'.join(self.emergency_scratch_codes)

        print(f'* Crypting {output_file} into {self.vpn_config.getUsersDirectory()} with {self.username_password} key.')
        self.encryptSecretFile(
          self.username_password, output_file,
          os.path.join(f'{self.vpn_config.getUsersDirectory()}',f'{self.username}.crypted'))
        #shutil.copy2(f'{self.username}.crypted', self.vpn_config.getUsersDirectory())


    def createQrFile(self, access: str, issuer: str) -> None:
        png_file = os.path.join(self.output_directory, f"{self.username}_qr_code.png")
        cmd = f'qrencode -s 4 -o {png_file} "otpauth://totp/{access}?secret={self.secret}&issuer={issuer}"'

        # Execute the command
        subprocess.run(cmd, shell=True)


    def encryptPDF(self, password: str = "") -> None:
        # create a PdfWriter object 
        out = PdfWriter() 

        # Open our PDF file with the PdfReader 
        file = PdfReader(self.pdf_filename_path) 

        # Get number of pages in original file 
        num = len(file.pages)

        # Add title to the document
        out.add_metadata({"/Title": self.title})
        out.add_metadata({"/Author": "Python Create User PDF Class"})

        # Iterate through every page of the original 
        # file and add it to our new file. 
        for idx in range(num): 
            # Get the page at index idx 
            page = file.pages[idx]

            # Add it to the output file 
            out.add_page(page) 

        if not password:
            if not self.pdf_encryption_password:
                # Generate a sequence of password_size random characters
                password = self.generatePassword()
                self.pdf_encryption_password = password
            else:
                password = self.pdf_encryption_password
        else:
            self.pdf_encryption_password = password
            
        # Encrypt the new file with the entered password 
        out.encrypt(password)
        print(f"'{self.pdf_filename_path}' encrypted with '{password}' password")

        # Open a new file "myfile_encrypted.pdf" 
        with open(self.pdf_filename_path, "wb") as f: 
            # Write our encrypted PDF to this file 
            out.write(f)


    def createPdfWithImageAndText(self, with_backup_codes: bool = False) -> bool:
        if not self.username:
            return False

        # Open the image to get its size
        with Image.open(self.qr_code_image_path) as img:
            img_width, img_height = img.size

        # Create a canvas with A4 page size
        c = canvas.Canvas(self.pdf_filename_path, pagesize=A4)

        # Calculate position to center the image horizontally
        img_x = (A4[0] - img_width) / 2

        text_before_image = f"Here you are your VPN account.\n    * username: {self.username}\n    * password: {self.username_password}\nAccount created in date and time: {self.usernameCreationDate()}.\nHere you are your QR code to scan with an Authenticator App.\nTry Twilio Authy, Google Authenticator or similars."

        if with_backup_codes:
            text_after_image = "Your emergency scratch codes are:\n"
            for code in self.emergency_scratch_codes:
                text_after_image += f"  {code}\n"

        # Calculate y position for text before image
        text_before_image_lines = text_before_image.split('\n')
        text_before_image_y = A4[1] - self.up_margin

        # Draw text before image
        for line in text_before_image_lines:
            c.drawString(self.left_margin, text_before_image_y, line)
            text_before_image_y -= self.line_spacing  # Adjust line spacing as needed

        # Draw the image
        c.drawImage(self.qr_code_image_path, img_x, text_before_image_y - img_height, width=img_width, height=img_height)

        if with_backup_codes:
            # Calculate y position for text after image
            text_after_image_lines = text_after_image.split('\n')
            text_after_image_y = text_before_image_y - img_height - self.line_spacing

            # Draw text after image
            for line in text_after_image_lines:
                c.drawString(self.left_margin, text_after_image_y, line)
                text_after_image_y -= self.line_spacing  # Adjust line spacing as needed

        # Save the canvas
        c.save()

        # Encrypt the PDF
        self.encryptPDF(self.pdf_encryption_password)

        return True
