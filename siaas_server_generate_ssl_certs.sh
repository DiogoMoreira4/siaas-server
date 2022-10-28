#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

cd ${SCRIPT_DIR}

SSL_DIR=${SCRIPT_DIR}/ssl
mkdir -p ${SSL_DIR}

cd ${SSL_DIR}
mkdir -p certs
openssl req -nodes -newkey rsa:2048 -keyout ./certs/siaas.key -out ./certs/siaas.csr -config ./siaas.cnf
openssl x509 -in ./certs/siaas.csr -out ./certs/siaas.crt -req -signkey ./certs/siaas.key -extfile ./siaas.cnf -extensions v3_req -days 3650
chmod 644 ./certs/*
cd -

echo -e "\nFiles siaas.crt and siaas.key can now be used in Apache configuration.\nFile siiaas.crt should be used in the agent as the 'ssl_ca_bundle' config.\n"
