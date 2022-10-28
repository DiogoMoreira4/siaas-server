#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

cd ${SCRIPT_DIR}

apt-get update
apt-get install -y python3 python3-pip python3-venv git mongodb apache2 openssl

# SSL CONFIGURATION
#./siaas_server_generate_ssl_certs.sh # only if we want to generate new certs
cp -p ./ssl/certs/siaas.crt /etc/ssl/certs/
chown root:root /etc/ssl/certs/siaas.crt
chmod 644 /etc/ssl/certs/siaas.crt
cp -p ./ssl/certs/siaas.key /etc/ssl/private/
chown root:root /etc/ssl/private/siaas.key
chmod 640 /etc/ssl/private/siaas.key
cd /etc/ssl/certs
for f in `find . -type l`; do [ `readlink $f` == siaas.crt ] && rm -f $f; done;
ln -fs siaas.crt `openssl x509 -hash -noout -in /etc/ssl/certs/siaas.crt`.0
cd -

# APACHE CONFIGURATIONS
APACHE_AUTH_PWD=siaas
echo $APACHE_AUTH_PWD > .siaas_apache_pwd
htpasswd -c -i /etc/apache2/.htpasswd siaas < .siaas_apache_pwd
rm -f .siaas_apache_pwd
sudo chown root:www-data /etc/apache2/.htpasswd
sudo chmod 640 /etc/apache2/.htpasswd
cp -f ./apache/*.conf /etc/apache2/sites-available/
cd /etc/apache2/sites-enabled/
rm -f 000-default.conf
rm -f default-ssl.conf
rm -f siaas*.conf
#ln -fs ../sites-available/siaas.conf # HTTP only (no HTTPS)
ln -fs ../sites-available/siaas-ssl.conf
cd -
a2enmod rewrite
a2enmod ssl
a2enmod proxy
a2enmod proxy_http
a2enmod headers
systemctl restart apache2
systemctl enable apache2

# MONGO DB CONFIGURATION
#sed -i 's|bind_ip[[:space:]]*=[[:space:]]*127.0.0.1|bind_ip = 0.0.0.0|g' /etc/mongodb.conf # Open DB to the world (only for testing purposes)
systemctl restart mongodb
systemctl enable mongodb
sleep 3 && ./siaas_server_initialize_mongodb.sh # initialize the SIAAS users in MongoDB (resets all databases as well!)

# SYSTEMD CONFIGURATION
ln -fs ${SCRIPT_DIR}/siaas_server_run.sh /usr/local/bin/
ln -fs ${SCRIPT_DIR}/siaas_server_kill.sh /usr/local/bin/
cat << EOF | sudo tee /etc/systemd/system/siaas-server.service
[Unit]
Description=SIAAS Server
[Service]
ExecStart=/usr/local/bin/siaas_server_run.sh
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable siaas-server
echo -e "\nSIAAS Server will be started on boot.\n\nTo start/stop manually: sudo systemctl start siaas-server\n"
