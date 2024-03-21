#!/bin/bash

./create_server_and_ca_certs.sh

if [ $? -eq 0 ];
then
  ./generate_client_certs.py
fi