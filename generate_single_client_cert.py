#!/usr/bin/env python3

import os, sys
import subprocess
import pexpect
import glob
import shutil
from user_management_class import UserManagement
from create_user_pdf_class import CreateUserPDF
from vpn_configuration_class import VpnConfiguration


def add_user_to_the_vpn(username: str) -> ():
    os.makedirs(vpn_config.getUsersDirectory(), exist_ok = True)

    # It's going to return the directory path where you'll find users' PDF
    # And random password used to crypt the PDF file
    ret = ()

    # Create the client username certificate
    command = f"./create-client-cert-conf.sh {username}"

    # Execute the command
    process = subprocess.Popen(command, shell=True)

    # Wait for the command to complete
    process.wait()

    # Get the exit code
    exit_code = process.returncode

    if exit_code == 0:
        um = UserManagement()
        um.setDatabasePath(base_path = vpn_config.getUsersDirectory())
        um.createDatabase()
        result, username_password = um.addUser(username)

        # If user has been added
        if result:
            print(f"* producing PDF with credentials for {username}...")
            um.showUsernameData(username)
            pdf_title = vpn_config.getPdfTitle()
            access_name = vpn_config.getAccessName()
            issuer_name = vpn_config.getIssuerName()
            pdf_directory = vpn_config.getPdfDirectory()
            filename_prefix = vpn_config.getFilenamePrefix()

            cupdf = CreateUserPDF(filename_prefix, issuer_name, pdf_directory)
            cupdf.setMargins()
            cupdf.setTitle(pdf_title)
            cupdf.setUsernamePassword(username, username_password)
            cupdf.getSecretAndEmergencyScratchCodes()
            cupdf.createQrFile(access_name, issuer_name)
            cupdf.createPdfWithImageAndText()
            ret = (cupdf.getPdfFilenamePath(), cupdf.getBasePathDirectory(), cupdf.pdfEncryptionPassword())
    else:
        print("***ERROR: failed to create client certificates!")
        sys.exit(1)

    return ret


def compress_and_encrypt_zip_file(file_to_zip: str, output_zip: str, password:str) -> None:
    # Construct the command
    command = f"zip -e -j {output_zip} {file_to_zip}"

    # Spawn the process
    process = pexpect.spawn(command)

    # Expect the first prompt for the password
    process.expect('Enter password:')

    # Send the password
    process.sendline(password)

    # Expect the second prompt for the password confirmation
    process.expect('Verify password:')

    # Send the password again for verification
    process.sendline(password)

    # Wait for the process to finish
    process.wait()

    # Check if there were any errors
    if process.exitstatus != 0:
        print(f"***ERROR: file {output_zip}: {process.before.decode()}")
    else:
        print(f"Zip operation successful. I wrote: {output_zip}")


if __name__ == "__main__":
    # Check if exactly one parameter is provided
    if len(sys.argv) != 2:
        print("*** ERROR: it's needed just the username as only parameter!")
        sys.exit(1)

    # Get the parameter
    username = sys.argv[1]

    # Get the VPN configuration
    vpn_config = VpnConfiguration()

    print(f"********** user to manage: '{username}'")
    pdf_filename, pdf_directory, password = add_user_to_the_vpn(username)
    pdf_passwords_users_files = os.path.join(pdf_directory, 'pdf_passwords_users_files.txt')
    with open(pdf_passwords_users_files, 'a') as f:
        f.write(f'{username}\t\t{password}\n')

    ovpn_filename = vpn_config.getOvpnFilenameFullPath(username)
    file_to_zip = f'{ovpn_filename} {pdf_filename}'
    output_zip = vpn_config.getZipFilenameFullPath(username)
    compress_and_encrypt_zip_file(file_to_zip, output_zip, password)
    shutil.copy2('totp_verify.py', vpn_config.getConfigureBaseDirectory())