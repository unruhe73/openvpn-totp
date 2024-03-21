#!/usr/bin/env python3

import os, sys
import json


class VpnConfiguration:
    def __init__(self, active_configuration: str = '') -> None:
        if not active_configuration:
            try:
                with open(os.path.join('config', 'active_config'), 'r') as f:
                    active_configuration = f.read().split()[0]
            except FileNotFoundError:
                print("***ERROR: active configuration file not found!")
                sys.exit(1)

        self.config_dir = os.path.join('config', active_configuration)
        self.pdf_title = ''
        self.access_name = ''
        self.issuer_name = ''
        self.filename_prefix = ''
        self.smtp_server_host = ''
        self.smtp_port = 0
        self.sender_name = ''
        self.sender_email = ''
        self.receiver_name = ''
        self.email_subject = ''
        self.email_body_template = ''
        self.email_body = ''
        self.can_create_users = False
        self.can_send_email = False
        self.config_base_dir = []
        self.config_users_dir = []
        self.config_ovpn_dir = []
        self.zip_dir = []
        self.pdf_dir = []
        filename = os.path.join(self.config_dir, 'vpn_configuration.json')
        if not os.path.exists(filename):
            print(f'***ERROR: cannot read configuration file {filename}!')
            sys.exit(1)
        with open(filename, 'r') as f:
            data = json.load(f)
            key_count = 0
            try:
                self.pdf_title = data['totp']['pdf_title']
                key_count += 1
            except KeyError:
                pass

            try:
                self.access_name = data['totp']['access_name']
                key_count += 1
            except KeyError:
                pass

            try:
                self.issuer_name = data['totp']['issuer_name']
                key_count += 1
            except KeyError:
                pass

            try:
                self.filename_prefix = data['totp']['filename_prefix'].replace(' ', '_')
                key_count += 1
            except KeyError:
                pass

            try:
                self.config_base_dir = data['config']['config_base_dir']
                if len(self.config_base_dir) > 0:
                    key_count += 1
                else:
                    print("***ERROR: configuration base directory is not defined!")
                    sys.exit(1)
            except KeyError:
                print("***ERROR: configuration base directory is not defined!")
                sys.exit(1)

            try:
                self.config_users_dir = data['config']['config_users_dir']
                if len(self.config_users_dir) > 0:
                    key_count += 1
                else:
                    print("***ERROR: users directory is not defined!")
                    sys.exit(1)
            except KeyError:
                print("***ERROR: users directory is not defined!")
                sys.exit(1)

            try:
                self.config_ovpn_dir = data['config']['config_ovpn_dir']
                if len(self.config_ovpn_dir) > 0:
                    key_count += 1
                else:
                    print("***ERROR: OVPN file directory is not defined!")
                    sys.exit(1)
            except KeyError:
                print("***ERROR: OVPN file directory is not defined!")
                sys.exit(1)

            try:
                self.zip_dir = data['config']['zip_dir']
                if len(self.zip_dir) > 0:
                    key_count += 1
                else:
                    print("***ERROR: ZIP file directory is not defined!")
                    sys.exit(1)
            except KeyError:
                print("***ERROR: ZIP file directory is not defined!")
                sys.exit(1)

            try:
                self.pdf_dir = data['config']['pdf_dir']
                if len(self.pdf_dir) > 0:
                    key_count += 1
                else:
                    print("***ERROR: PDF file directory is not defined!")
                    sys.exit(1)
            except KeyError:
                print("***ERROR: PDF file directory is not defined!")
                sys.exit(1)

            self.can_create_users = (key_count == 9)
            key_count = 0
            try:
                self.smtp_server_host = data['mail']['smtp_server']['host']
                key_count += 1
            except KeyError:
                pass

            try:
                self.smtp_port = data['mail']['smtp_server']['port']
                key_count += 1
            except KeyError:
                pass

            try:
                self.sender_name = data['mail']['sender']['name']
                key_count += 1
            except KeyError:
                pass

            try:
                self.sender_email = data['mail']['sender']['email']
                key_count += 1
            except KeyError:
                pass
            
            try:
                self.email_subject = data['mail']['email']['subject']
                key_count += 1
            except KeyError:
                pass

            try:
                self.email_body_template = data['mail']['email']['body_template']
                key_count += 1
            except KeyError:
                pass

            self.can_send_email = (key_count == 6)


    def getConfigDirectory(self) -> str:
        return self.config_dir


    def getPdfTitle(self) -> str:
        return self.pdf_title


    def getAccessName(self) -> str:
        return self.access_name


    def getIssuerName(self) -> str:
        return self.issuer_name


    def getFilenamePrefix(self) -> str:
        return self.filename_prefix


    def canCreateUsers(self) -> bool:
        return self.can_create_users


    def getSmtpServerHost(self) -> str:
        return self.smtp_server_host


    def getSmtpServerPort(self) -> int:
        return self.smtp_port


    def getSenderName(self) -> str:
        return self.sender_name


    def getSenderEmail(self) -> str:
        return self.sender_email


    def getEmailSubject(self) -> str:
        return self.email_subject


    def setReceiverName(self, name: str) -> None:
        self.receiver_name = name
        if self.email_body_template:
            if 'DESTINATARIO' in self.email_body_template:
                self.email_body = self.email_body_template.replace('DESTINATARIO', name)
            elif 'RECEIVER' in self.email_body_template:
                self.email_body = self.email_body_template.replace('RECEIVER', name)


    def getEmailBodyTemplate(self) -> str:
        return self.email_body_template


    def getEmailBody(self) -> str:
        return self.email_body


    def canSendEmail(self) -> bool:
        cond1 = len(self.receiver_name) > 0
        cond2 = len(self.email_subject) > 0
        cond3 = len(self.email_body) > 0

        return self.can_send_email and cond1 and cond2 and cond3


    def getConfigureBaseDirectory(self) -> str:
        path = ''
        for item in self.config_base_dir:
            path = os.path.join(path, item)
        os.makedirs(path, exist_ok = True)

        return path


    def getUsersDirectory(self) -> str:
        path = ''
        for item in self.config_users_dir:
            path = os.path.join(path, item)
        os.makedirs(path, exist_ok = True)

        return path


    def getDatabaseFilename(self) -> str:
        return os.path.join(self.getUsersDirectory(), 'users.db')


    def getOvpnDirectory(self) -> str:
        path = ''
        try:
            for item in self.config_ovpn_dir:
                path = os.path.join(path, item)
            os.makedirs(path, exist_ok = True)
        except KeyError:
            print("***ERROR: OVPN file directory is not defined!")
            sys.exit(1)

        return path


    def getOvpnFilename(self, username: str) -> str:
        return f'{username}.ovpn'


    def getOvpnFilenameFullPath(self, username: str) -> str:
        return os.path.join(self.getOvpnDirectory(), self.getOvpnFilename(username))


    def getZipDirectory(self) -> str:
        path = ''
        try:
            for item in self.zip_dir:
                path = os.path.join(path, item)
            os.makedirs(path, exist_ok = True)
        except KeyError:
            print("***ERROR: ZIP file directory is not defined!")
            sys.exit(1)

        return path


    def getZipFilenameFullPath(self, username: str) -> str:
        return os.path.join(self.getZipDirectory(), self.getZipFilename(username))


    def getZipFilename(self, username: str) -> str:
        return f'{username}_{self.getFilenamePrefix()}_vpn.zip'


    def getPdfDirectory(self) -> str:
        path = ''
        try:
            for item in self.pdf_dir:
                path = os.path.join(path, item)
            os.makedirs(path, exist_ok = True)
        except KeyError:
            print("***ERROR: PDF file directory is not defined!")
            sys.exit(1)

        return path


    def canCreateUsers(self) -> bool:
        return self.can_create_users


    def isVpnWellConfigurated(self) -> bool:
        return (self.can_create_users and self.can_send_email)