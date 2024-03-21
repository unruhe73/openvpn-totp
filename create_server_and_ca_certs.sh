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

#git clone https://github.com/OpenVPN/easy-rsa.git
#EASY_RSA_PATH="$PWD/easy-rsa/easyrsa3/"

EASY_RSA_VERSION="3.1.7"
EASY_RSA="EasyRSA-$EASY_RSA_VERSION"
EASY_RSA_PATH="$PWD/$EASY_RSA"
EASY_RSA_TGZ="$EASY_RSA.tgz"

SERVER="$PWD/openvpn/server"
CONFIG="$PWD/config/$active_config"

if [ ! -f $EASY_RSA_TGZ ];
then
  wget https://github.com/OpenVPN/easy-rsa/releases/download/v$EASY_RSA_VERSION/EasyRSA-$EASY_RSA_VERSION.tgz
fi

if [ $? -ne 0 ];
then
  echo "***ERROR: no EasyRSA $EASY_RSA_VERSION found!"
  exit 1
fi

rm -rf $EASY_RSA
tar xzf $EASY_RSA_TGZ
if [ $? -ne 0 ];
then
  echo "***ERROR: some issue to untar $EASY_RSA_TGZ"
  exit 1
fi

cp $CONFIG/vars $EASY_RSA_PATH
mkdir -p $SERVER

cd $EASY_RSA_PATH
./easyrsa init-pki
./easyrsa build-ca
./easyrsa gen-req openvpn-server nopass
./easyrsa sign-req server openvpn-server
./easyrsa gen-dh

if [ ! -f pki/ca.crt ];
then
  echo "***ERROR: PKI wasn't created!"
  exit 1
fi

cp -v pki/ca.crt pki/dh.pem pki/private/openvpn-server.key pki/issued/openvpn-server.crt $CONFIG/server.conf $SERVER
if [ $? -ne 0 ];
then
  echo "***ERROR: some issue with certs generation!"
  exit 1
fi

cd $SERVER
sed -i "s/OPENVPN_NETWORK/$OPENVPN_NETWORK/g" server.conf
sed -i "s/OPENVPN_NETMASK/$OPENVPN_NETMASK/g" server.conf
rm -f server.conf.new
while read line
do
  case "$line" in
    "ROUTES")
      cat $CONFIG/routes >> server.conf.new
      echo "" >> server.conf.new
      ;;
    *)
      echo "$line" >> server.conf.new
      ;;
  esac
done < server.conf
mv server.conf.new server.conf