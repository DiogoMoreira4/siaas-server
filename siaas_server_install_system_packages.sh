#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

cd ${SCRIPT_DIR}

apt-get update
apt-get install -y python3 python3-pip python3-venv git mongodb

sed -i 's|bind_ip[[:space:]]*=[[:space:]]*127.0.0.1|bind_ip = 0.0.0.0|g' /etc/mongodb.conf
systemctl restart mongodb
systemctl enable mongodb

ln -fs ${SCRIPT_DIR}/siaas_server_run.sh /usr/local/bin/
ln -fs ${SCRIPT_DIR}/siaas_server_kill.sh /usr/local/bin/
