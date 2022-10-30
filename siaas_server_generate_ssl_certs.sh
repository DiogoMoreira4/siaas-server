#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )
THIS_HOST=$(hostname -f | tr '[:upper:]' '[:lower:]')

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

cd ${SCRIPT_DIR}

SSL_DIR=${SCRIPT_DIR}/ssl
mkdir -p ${SSL_DIR}

cd ${SSL_DIR}

cat << EOF | sudo tee siaas.cnf
[ req ]
default_bits = 4096
distinguished_name = req_distinguished_name
req_extensions = v3_req
x509_extensions = v3_req
prompt = no
[ req_distinguished_name ]
countryName = PT
stateOrProvinceName = Lisbon
localityName = Lisbon
organizationName = ISCTE
organizationalUnitName = METI
commonName = ${THIS_HOST}
#emailAddress = ""
[ v3_req ]
subjectAltName = @alt_names
[alt_names]
DNS.1 = ${THIS_HOST}
DNS.2 = siaas
EOF

openssl req -nodes -newkey rsa:2048 -keyout siaas.key -out siaas.csr -config siaas.cnf
openssl x509 -in siaas.csr -out siaas.crt -req -signkey siaas.key -extfile siaas.cnf -extensions v3_req -days 3650
chmod 644 *.crt
chmod 644 *.csr
chmod 644 *.key

cd -

echo -e "\nCerts placed inside: ${SCRIPT_DIR}/ssl\n\nFiles siaas.crt and siaas.key can now be used in Apache configuration;\nFile siaas.crt should be used in the agent as the 'api_ssl_ca_bundle' config.\n"
