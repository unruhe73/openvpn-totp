#!/usr/bin/env python3

import csv, os, sys
from email_sender_class import EmailSender
from vpn_configuration_class import VpnConfiguration


if __name__ == "__main__":
    vpn_config = VpnConfiguration()
    mail = EmailSender(vpn_config.getSmtpServerHost(), vpn_config.getSmtpServerPort())
    mail.setSenderName(vpn_config.getSenderName())
    mail.setSenderEmail(vpn_config.getSenderEmail())
    mail.setSenderPassword(input(f"email password for {mail.getSenderEmail()}: "))

    with open(os.path.join(vpn_config.getConfigDirectory(), 'users.csv'), 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for username, name, email, sent_email in reader:
            if sent_email == "0":
                print(f"Sending email to {name}")

                # Send email
                mail.setReceiverName(name)
                mail.setReceiverEmail(email)
                vpn_config.setReceiverName(name)
                mail.setSubject(vpn_config.getEmailSubject())
                mail.setBody(vpn_config.getEmailBody())
                if not vpn_config.canSendEmail():
                    print('***ERROR: your mail configuration is incomplete, I cannot send e-mails!')
                    sys.exit(1)

                mail.attachFile(vpn_config.getZipFilenameFullPath(username))
                mail.sendEmail()