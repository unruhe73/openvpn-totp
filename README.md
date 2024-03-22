**OpenVPN TOTP**

This is a possible way to setup an openvpn server with user, password and TOTP code to connect to the VPN.

**Starting**

The first thing to do is to install the OpenVPN software, than a Certification Authorithy is needed. This because it has to sign the OpenVPN server certificate and the client certificates too.

But before this you have to compile a configuration. There is a **config** directory and into it you have the file **active_config** and the subdirectory **default**. The content of the **active_config** file is *default*. This content specify that into **config** directory you have another directory called exactly as it: **default**, where there are the VPN configuration files. You can have more configurations but in the current state development you can use just one of it and you have to specify which one into the **active_config** file that is the **active** configuration. If you want manage more configurations you have to clone more times the whole project in more directories. In the next software releases this could be managed in the same project directory with all certificates of the different configuration.

in the **active** configuration directory you're going to find the following files:

`environment
openvpn_users
routes
server.conf
users.csv
vars
vpn_configuration.json
`

Now here you are the files.

**environment**

`OPENVPN_REMOTE_SERVER="192.168.192.168"

OPENVPN_REMOTE_PORT="7890"

OPENVPN_PROTO="udp"

OPENVPN_NETWORK="192.168.254.0"

OPENVPN_NETMASK="255.255.255.0"`

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

**vpn_configuration.json**

In this file you have some more configuration. You can find the SMTP server parameters. You don't need them if you don't want to send emails using the script. The **totp** section defines the data you're going to specify when the QR code to scan and add to an Authenticator app is generated. It's needed. I suggest to let unchanged the **config** section. With the *default* configuration you're going to have an **openvpn** directory to copy to the server as it is, except for the **openvpn/client** one where you have to *OVPN* files, the client files to use to connect to the VPN, but you need just to send the ZIP file to the user. The ZIP file's containing the *OVPN* file and the *PDF* file containing the credential to access to the VPN: username, password and QR code. The *ZIP* and *PDF* file is protected from a password. The same password. More details later.

**Creating the CA and server and client certificates**

In the software you get from here you can proceed to create the CA and the server certificate and configuration executing the **create_server_and_ca_certs.sh** bash script and then execute the **generate_single_client_cert.py** Python script to create single client certificate specifying the username. Suppose you have just one user of the VPN and the username is *myuser*, than you have to execute:

`./create_server_and_ca_certs.sh

./generate_single_client_cert.py myuser`

But you can also insert all the usernames you need in the **config/default/openvpn_users** file and execute just the bash script **create_all_certs.sh**:

`./create_all_certs.sh`

After you executed the scripts you're getting the following directory:

`openvpn
users_file`

The first one contains the server configuration and the users file needed to be moved on the server. The subdirectory **users** into **openvpn** contains the users sqlite database and the crypted secret that generate the OTP code. Each user secret file is cpyptted using users password. No password is stored in the database. The information stored use a double salt storing.

The passoword is transformed according this formula:

`hash(salt2 + hash(salt1 + password))
`

where *salt1* and *salt2* are random Fermat keys.