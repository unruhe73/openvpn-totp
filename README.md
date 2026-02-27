[![GitHub license](https://img.shields.io/badge/license-AGPL-blue)](https://github.com/unruhe73/openvpn-totp/blob/main/LICENSE)
[![Made with Python 3](https://img.shields.io/badge/python-3.x-powered)](https://www.python.org/)


# OpenVPN TOTP

This is a possible way to setup an openvpn server with user, password and TOTP code to connect to the VPN.

# Starting

The first thing to do is to install the OpenVPN software, then a Certification Authorithy is needed. This because you need to sign the OpenVPN server certificate and then the client certificates for the users.

Before to proceed, you have to put down a configuration. There is a **config** directory and into it you have the file **active_config** and the subdirectory **default**. The content of the **active_config** file is *default*. This content specify that into **config** directory you have another directory called exactly as it: **default**, where there are the VPN configuration files. You can have more configurations but in the current state development you can use just one of it and you have to specify which one into the **active_config** file that is the **active** configuration. If you want manage more configurations you have to clone more times the whole project in more directories. In the next software releases this could be managed in the same project directory with all certificates of the different configuration.

in the **active** configuration directory you're going to find the following files:

    environment
    openvpn_users
    routes
    server.conf
    users.csv
    vars
    vpn_configuration.json

Now here you are the files.

**environment**

    OPENVPN_REMOTE_SERVER="192.168.192.168"
    OPENVPN_REMOTE_PORT="7890"
    OPENVPN_PROTO="udp"
    OPENVPN_NETWORK="192.168.254.0"
    OPENVPN_NETMASK="255.255.255.0"

In this file you can define the IP address of the remote server needed to the clients, the port and the protocol. The protocol has to be *udp* or *tcp*.
OPENVPN_NETWORK and OPENVPN_NETMASK is the OpenVPN network and netmask that is the network needed to the VPN to work. Avoid it conflict with your router and local LAN network.

**openvpn_users**

In this file you have the username list. This is useful if you know exactly the users of your VPN.

**routes**

In this file you have to specify the routes for your VPN: users connecting to the VPN which networks can reach.

**server.conf**

In this file you have the OpenVPN server configuration that's going to be merged with **routes** and **environment** files.

**users.csv**

In this file you can associate, in a CSV format, username with real name and email of the users. This is not really necessary, but if you specify this information you can auto generate and send emails with the information to access to the VPN to the users you specify. The `sent_email` field tells if the email has been sent or not. If the value is **0** than the email will be sent if you're going to execute the send email python script, if it's **1** no email for this user.

**vars**

In this file you define the data of the Certification Authority and how many days the CA is valid and after how many days a client certificate's expiring.
Here what need to be customized:

    set_var EASYRSA_REQ_COUNTRY     "NATION"
    set_var EASYRSA_REQ_PROVINCE    "Nation"
    set_var EASYRSA_REQ_CITY        "DefaultCity"
    set_var EASYRSA_REQ_ORG         "Default Certificate Authority"
    set_var EASYRSA_REQ_CN          "Default CA"
    set_var EASYRSA_REQ_EMAIL       "default@example.com"
    set_var EASYRSA_REQ_OU          "Default Techadmin EASY CA"
    set_var EASYRSA_KEY_SIZE        2048
    set_var EASYRSA_ALGO            rsa
    set_var EASYRSA_CA_EXPIRE       7500
    set_var EASYRSA_CERT_EXPIRE     1095
    set_var EASYRSA_NS_COMMENT      "Default Certificate Authority"

In this configuration certificates use a 2048 RSA key, CA expires in 20 years (7500 days) and the generated certificates (client and server) expires in 3 years (1095 days).

**vpn_configuration.json**

In this file you have some more configuration. You can find the SMTP server parameters. You don't need them if you don't want to send emails using the script. The **totp** section defines the data you're going to specify when the QR code to scan and add to an Authenticator app is generated. It's needed. I suggest to let unchanged the **config** section. With the *default* configuration you're going to have an **openvpn** directory to copy to the server as it is, except for the **openvpn/client** one where you have to *OVPN* files, the client files to use to connect to the VPN, but you need just to send the ZIP file to the user. The ZIP file's containing the *OVPN* file and the *PDF* file containing the credential to access to the VPN: username, password and QR code. The *ZIP* and *PDF* file is protected from a password. The same password. More details later.

# Creating the CA and server and client certificates

In the software you get from here you can proceed to create the CA and the server certificate and configuration executing the **create_server_and_ca_certs.sh** bash script and then execute the **generate_single_client_cert.py** Python script to create single client certificate specifying the username. Suppose you have just one user of the VPN and the username is *myuser*, than you have to execute:

    ./create_server_and_ca_certs.sh
    ./generate_single_client_cert.py myuser

But you can also insert all the usernames you need in the **config/default/openvpn_users** file and execute just the bash script **create_all_certs.sh**:

    ./create_all_certs.sh

After you executed the scripts you're getting the following directory:

    openvpn
    users_file

The first one contains the server configuration and the users file needed to be moved on the server. The subdirectory **users** into **openvpn** contains the users sqlite database and the crypted secret that generate the OTP code. Each user secret file is cpyptted using users password. No password is stored in the database. The information stored use a double salt storing.

The passoword is transformed according this formula:

    hash(salt2 + hash(salt1 + password))

where *salt1* and *salt2* are random Fermat keys. Only if the user inser the correct password than the conversion matches the data into the database.

Once certificates has been created you have to look for files to send to the users into the **users_file**. In this directory you're getting two subdirectories:

`zip` and `pdf`

If you didn't configure the *mail* session into the file **vpn_configuration.json** and you won't use the `send_email.py` python script but you want to send an e-mail from your favourite e-mail client you need to get the ZIP and PDF password from the file **pdf_passwords_users_files.txt** into the **pdf** directory and send just the ZIP related file to the user. The ZIP file is, of course, into the **zip** directory.

Anyway, also if you use the `send_email.py` python script (after you configured correctly mail parameters into the file **vpn_configuration.json**) to send the e-mail, the user's not getting the password to open the ZIP and PDF file, so you need to contact him or her and send them the password on a different channel, or writing a e-mail with your e-mail client later.

Of course, you have to keep all these data away from the server. Execute all these commands in a Linux Desktop client.

# The required Python libraries

For the openvpn *server* you need to install the following Python libraries:

    pyotp
    pycryptodome
    sqlite3

For the Linux *client* you need:

    csv
    cryptography
    pexpect
    pillow
    pycryptodome
    pyotp
    pypdf
    reportlab
    sqlite3

And the **google-authenticator** application installed.

# openvpn server on Linux

Into **/etc/openvpn/server** directory you're going to have the following files on the openvpn server:

    ca.crt
    dh.pem
    openvpn-server.crt
    openvpn-server.key
    server.conf

Into the **/etc/openvpn/users** directory you're going to have the following files on the openvpn server:

    users.db
    myuser.crypted

Into the **/etc/openvpn** directory you're going to have the following file on the openvpn server:

    totp_verify.py

If you're using **FreeBSD** copy **totp_verify.freebsd.py** into **/usr/local/etc/openvpn** and rename it as **totp_verify.py** and fix also the **server.conf** file paths, use:

    ca /usr/local/etc/openvpn/server/ca.crt
    cert /usr/local/etc/openvpn/server/openvpn-server.crt
    key /usr/local/etc/openvpn/server/openvpn-server.key
    dh /usr/local/etc/openvpn/server/dh.pem

in place of:

    ca /etc/openvpn/server/ca.crt
    cert /etc/openvpn/server/openvpn-server.crt
    key /etc/openvpn/server/openvpn-server.key
    dh /etc/openvpn/server/dh.pem


# The sqlite databse of users.db

The database stores some information about the username into the users table. Here you are the SQL:

    CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT,
       creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        username TEXT UNIQUE,
        salt1 TEXT,
        salt2 TEXT,
        hash TEXT,
        is_active INTEGER,
        disactived_timestamp TIMESTAMP DEFAULT 0,
        last_access_timestamp TIMESTAMP DEFAULT 0)

when a user's created, into `users.db` is stored its username, the creation Unix timestamp, it's created 2 salts (*salt1* and *salt2*) to store hashed form of the converted password according to the formula:

    hash(salt2 + hash(salt1 + password))

So no clear and ho hashed password is stored into it.

The `is_active` field is set to **1** and indicate the username is active, if you set it to **0** you're disabling its access to the VPN, `disactived_timestamp` indicate Unix timestamp of its disactivation date and time. You can disactivate a user using the UserManagement Python class contained into the file `user_management_class.py` or updating directly the *users.db* file by sqlite application.

When a user access to the VPN the `last_access_timestamp` field is upadated to the current Unix timestamp. As default the *disactived* and *last_access* are set to **0**. If `last_access_timestamp` field is **0**, than a user with that username never connected or maybe he/she tried to connect but with wrong credentials and then never get the VPN access.

# How a user has to connect to the openVPN server

He/she has to unzip the file using the password. Import the *OVPN* file into its OpenVPN GUI application, open the PDF file using the same ZIP password, scan the QR code with Twilio Authy or Google Authenticator or similars. Use the username, password and OTP code generated by the Authenticator app after the connection started.
