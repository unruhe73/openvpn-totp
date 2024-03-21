#!/bin/bash

read active_config < config/active_config
if [ $? -ne 0 ];
then
  echo "***ERROR: no configuration available!"
  exit 1
fi

if [ ! -d "config/$active_config" ];
then
  echo "***ERROR: no active configuration found!"
  exit 1
fi

. config/$active_config/environment

EASY_RSA_VERSION="3.1.7"
EASY_RSA="EasyRSA-$EASY_RSA_VERSION"
EASY_RSA_PATH="$PWD/$EASY_RSA"
CLIENT="$PWD/openvpn/client"
USERS="$PWD/openvpn/users"
PKI_DIR="$EASY_RSA_PATH/pki"
CRTFILE="$1.crt"
KEYFILE="$1.key"

if [ -z "$1" ];
then
  echo "***ERROR: I need a certificate name to create as parameter!"
  exit 1
fi

if [ ! -d $PKI_DIR ];
then
  echo "***ERROR: no PKI found: try to generate a CA and then retry!"
  exit 1
fi

mkdir -p $CLIENT
mkdir -p $USERS
FILENAME="$CLIENT/$1.ovpn"

if [ -f "$FILENAME" ];
then
  echo "il file gia' esiste"
  exit 2
fi

cd $EASY_RSA_PATH
./easyrsa gen-req $1 nopass
./easyrsa sign-req client $1

echo "client" > $FILENAME
echo "dev tun" >> $FILENAME
echo "proto $OPENVPN_PROTO" >> $FILENAME
echo "remote $OPENVPN_REMOTE_SERVER $OPENVPN_REMOTE_PORT" >> $FILENAME

echo "<ca>" >> $FILENAME

cd $PKI_DIR
awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/' ca.crt >> $FILENAME
echo "</ca>" >> $FILENAME

echo "" >> $FILENAME
echo "<cert>" >> $FILENAME
cd issued

awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/' $CRTFILE >> $FILENAME
echo "</cert>" >> $FILENAME

echo "" >> $FILENAME
echo "<key>" >> $FILENAME
cd ../private
cat $KEYFILE >> $FILENAME
echo "</key>" >> $FILENAME
echo "" >> $FILENAME

echo "cipher AES-256-GCM" >> $FILENAME
echo "" >> $FILENAME
echo "# added remote-cert-tls" >> $FILENAME
echo "remote-cert-tls server" >> $FILENAME
echo "" >> $FILENAME
echo "auth SHA512" >> $FILENAME
echo "auth-nocache" >> $FILENAME
echo "tls-version-min 1.2" >> $FILENAME
echo "tls-cipher TLS-DHE-RSA-WITH-AES-256-GCM-SHA384:TLS-DHE-RSA-WITH-AES-256-CBC-SHA256:TLS-DHE-RSA-WITH-AES-128-GCM-SHA256:TLS-DHE-RSA-WITH-AES-128-CBC-SHA256" >> $FILENAME
echo "resolv-retry infinite" >> $FILENAME
echo "nobind" >> $FILENAME
echo "persist-key" >> $FILENAME
echo "persist-tun" >> $FILENAME
echo "mute-replay-warnings" >> $FILENAME
echo "connect-retry 120" >> $FILENAME
echo "verb 4" >> $FILENAME
echo "auth-user-pass" >> $FILENAME
echo "static-challenge \"Please enter authenticator PIN:\" 0" >> $FILENAME

echo "file generato: $FILENAME"
