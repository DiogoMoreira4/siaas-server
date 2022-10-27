#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

cd ${SCRIPT_DIR}

apt-get update
apt-get install -y python3 python3-pip python3-venv git mongodb apache2

# APACHE CONFIGURATION
apt-get install -y apache2
cat <<EOF | tee /etc/apache2/sites-available/siaas.conf
<VirtualHost *:80>

  ServerName siaas

  ProxyPreserveHost On
  ProxyPass "/api" http://127.0.0.1:5000
  ProxyPassReverse "/api" http://127.0.0.1:5000

  CustomLog /\${APACHE_LOG_DIR}/siaas-access.log combined
  ErrorLog /\${APACHE_LOG_DIR}/siaas-error.log

</VirtualHost>
EOF
cd /etc/apache2/sites-enabled/
ln -fs ../sites-available/siaas.conf
cd -
a2enmod rewrite
a2enmod ssl
a2enmod proxy
a2enmod proxy_http
a2enmod headers
rm -f /etc/apache2/sites-enabled/000-default.conf
rm -f /etc/apache2/sites-enabled/default-ssl.conf
systemctl restart apache2
systemctl enable apache2

# MONGO DB CONFIGURATION
#sed -i 's|bind_ip[[:space:]]*=[[:space:]]*127.0.0.1|bind_ip = 0.0.0.0|g' /etc/mongodb.conf
systemctl restart mongodb
systemctl enable mongodb

ln -fs ${SCRIPT_DIR}/siaas_server_run.sh /usr/local/bin/
ln -fs ${SCRIPT_DIR}/siaas_server_kill.sh /usr/local/bin/
