#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )
THIS_HOST=$(hostname -f | tr '[:upper:]' '[:lower:]')

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

cd ${SCRIPT_DIR}

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
systemctl stop siaas-server
rm -f /var/log/siaas-server
rm -f /etc/systemd/system/siaas-server.service
systemctl daemon-reload

echo -e "\nSIAAS Server service and configurations were removed from the system.\n\nThe MongoDB SIAAS DB was kept intact. To remove it manually: \n\n \
 sudo mongo siaas --eval 'db.dropAllUsers()'\n \
 sudo mongo siaas --eval 'db.dropAllRoles()'\n \
 sudo mongo siaas --eval 'db.dropDatabase()'\n"
