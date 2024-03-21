#!/usr/bin/env python3

import email, smtplib, ssl
import csv, os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    def __init__(self, smtp_server: str, smtp_port: int) -> None:
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.filenames = []
        self.subject = ''
        self.body = ''
        self.sender_name = ''
        self.sender_email = ''
        self.password = ''
        self.receiver_name = ''
        self.receiver_email = ''


    def setSenderName(self, sender_name: str) -> None:
        self.sender_name = sender_name


    def getSenderName(self) -> str:
        return self.sender_name


    def setSenderEmail(self, sender_email: str) -> None:
        self.sender_email = sender_email


    def getSenderEmail(self) -> str:
        return self.sender_email


    def setSenderPassword(self, password: str) -> None:
        self.password = password


    def setReceiverName(self, receiver_name: str) -> None:
        self.receiver_name = receiver_name


    def getReceiverName(self) -> str:
        return self.receiver_name


    def setReceiverEmail(self, receiver_email: str) -> None:
        self.receiver_email = receiver_email


    def getReceiverEmail(self) -> str:
        return self.receiver_email


    def setSubject(self, subject: str) -> None:
        self.subject = subject


    def getSubject(self) -> str:
        return self.subject


    def setBody(self, body: str) -> None:
        self.body = body


    def getBody(self) -> str:
        return self.body


    def attachFile(self, filename: str) -> bool:
        if not filename:
            print("I need the attachement file!")
            return False

        if not os.path.exists(filename):
            print(f"file {filename} doesn't exist!")
            return False
        self.filenames = [ filename ]

        return True


    def attachFiles(self, filenames: []) -> bool:
        ret = False
        for item in filenames:
            if not os.path.exists(item):
                print(f"file {item} doesn't exist, removed!")
            else:
                ret = True
                self.filenames.append(item)

        return ret


    def removeAllAttachments(self) -> None:
        self.filenames.clear()


    def sendEmail(self) -> bool:
        sent = False

        if not self.sender_name:
            print("I don't know the name of the person I have to send email to!")
            return sent

        if not self.filenames:
            print("I need the attachement file!")
            return sent
        
        if not self.subject:
            print("***ERROR: no subject email available!")
            return sent

        if not self.body:
            print("***ERROR: no body message available!")
            return sent

        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = f'{self.sender_name} <{self.sender_email}>'
        message["To"] = f'{self.receiver_name} <{self.receiver_email}>'
        message["Subject"] = self.subject
        message["Bcc"] = f'{self.sender_name} <{self.sender_email}>'

        # Add body to email
        message.attach(MIMEText(self.body, "plain"))

        for filename in self.filenames:
            # Open PDF file in binary mode
            with open(filename, "rb") as attachment:
                # Add file as application/octet-stream
                # Email client can usually download this automatically as attachment
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            # Encode file in ASCII characters to send by email    
            encoders.encode_base64(part)

            # Add header as key/value pair to attachment part
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(filename)}",
            )

            # Add attachment to message and convert message to string
            message.attach(part)
        text = message.as_string()

        # Log in to server using secure context and send email
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, [self.receiver_email, self.sender_email], text)
                sent = True

        except smtplib.SMTPSenderRefused:
            print(f'***ERROR: Address {self.sender_email} refused by {self.smtp_server}!')

        except smtplib.SMTPRecipientsRefused:
            print('***ERROR: All recipient refused!')

        except smtplib.SMTPDataError:
            print('***ERROR: The SMTP server refused to accept the message data!')

        except smtplib.SMTPConnectError:
            print('***ERROR: Error occurred during establishment of a connection with the server.')

        except smtplib.SMTPHeloError:
            print('***ERROR: The server refused our HELO message.')

        except smtplib.SMTPNotSupportedError:
            print('***ERROR: The command or option attempted is not supported by the server.')

        except smtplib.SMTPAuthenticationError:
            print("***ERROR: SMTP authentication went wrong. Most probably the server didn’t accept the username/password combination provided.")

        except smtplib.SMTPException:
            print('***ERROR: Mail server generic exception!')

        except smtplib.SMTPServerDisconnected:
            print(f'***ERROR: Server {self.smtp_server} unexpectedly disconnected!')

        except smtplib.SMTPResponseException:
            print('***ERROR: Mail server got some kind of error!')

        return sent
