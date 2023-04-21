#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )
THIS_HOST=$(hostname -f | tr '[:upper:]' '[:lower:]')

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

mongo_shell="mongosh" && which ${mongo_shell} > /dev/null || mongo_shell="mongo" # fallback to the older mongo shell binary, if the new one is not found

cd ${SCRIPT_DIR}

systemctl stop siaas-server

# REPOS
rm -f /etc/apt/sources.list.d/mongodb-org-siaas.list
apt clean

# SSL CONFIGURATION WITH SELF-SIGNED CERTS
rm -f /etc/ssl/certs/siaas.crt
rm -f /etc/ssl/private/siaas.key
cd /etc/ssl/certs
for f in `find . -type l`; do [ `readlink $f` == siaas.crt ] && rm -f $f; done;
cd -

# APACHE CONFIGURATIONS
rm -f /etc/apache2/.htpasswd
rm -f /etc/apache2/sites-enabled/siaas.conf
rm -f /etc/apache2/sites-enabled/siaas-ssl.conf
rm -f /etc/apache2/sites-available/siaas.conf
rm -f /etc/apache2/sites-available/siaas-ssl.conf
sudo systemctl reload apache2

# SERVICE CONFIGURATION
rm -f /var/log/siaas-server
rm -f /etc/systemd/system/siaas-server.service
systemctl daemon-reload

echo -e "\nSIAAS Server service and configurations were removed from the system.\n\nThe MongoDB SIAAS DB was kept intact. To remove it manually: \n\n \
 sudo ${mongo_shell} siaas --eval 'db.siaas.dropIndexes()'\n \
 sudo ${mongo_shell} siaas --eval 'db.dropAllUsers()'\n \
 sudo ${mongo_shell} siaas --eval 'db.dropAllRoles()'\n \
 sudo ${mongo_shell} siaas --eval 'db.dropDatabase()'\n"
