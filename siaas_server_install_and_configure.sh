#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )
THIS_HOST=$(hostname -f | tr '[:upper:]' '[:lower:]')

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

if [ $# -ge 1 ]; then
  MONGO_VERSION=${1}
else
  MONGO_VERSION="6.0"
fi

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

cd ${SCRIPT_DIR}

# MONGODB REPO CONFIGURATION
apt-get update
apt-get install -y curl gnupg lsb-release || exit 1
repo_component="main" && [[ `lsb_release -is | tr '[:upper:]' '[:lower:]'` == "ubuntu" ]] && repo_component="multiverse" # if Ubuntu use the multiverse component
#curl --insecure -fsSL https://www.mongodb.org/static/pgp/server-${MONGO_VERSION}.asc | apt-key add - # apt-key is deprecated
curl --insecure -fsSL https://pgp.mongodb.com/server-${MONGO_VERSION}.asc | gpg -o /usr/share/keyrings/mongodb-server-${MONGO_VERSION}.gpg --dearmor --yes
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-${MONGO_VERSION}.gpg ] https://repo.mongodb.org/apt/`lsb_release -is | tr '[:upper:]' '[:lower:]'` `lsb_release -cs | tr '[:upper:]' '[:lower:]'`/mongodb-org/${MONGO_VERSION} ${repo_component}" | tee /etc/apt/sources.list.d/mongodb-org-siaas.list

# INSTALL PACKAGES
apt-get update
apt-get install -y python3 python3-pip python3-venv git apache2 mongodb-org=${MONGO_VERSION}.* openssl dmidecode ca-certificates || { rm -f /etc/apt/sources.list.d/mongodb-org-siaas.list; exit 1; }
systemctl daemon-reload

# SSL CONFIGURATION WITH SELF-SIGNED CERTS
[ ! -f "./ssl/siaas.crt" ] && ./siaas_server_generate_ssl_certs.sh # generate new self-signed certs on first run
cp -p ./ssl/siaas.crt /etc/ssl/certs/
chown root:root /etc/ssl/certs/siaas.crt
chmod 644 /etc/ssl/certs/siaas.crt
cp -p ./ssl/siaas.key /etc/ssl/private/
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
chown root:www-data /etc/apache2/.htpasswd
chmod 640 /etc/apache2/.htpasswd
cat << EOF | tee /etc/apache2/sites-available/siaas.conf
<VirtualHost *:80>

  ServerName ${THIS_HOST}
  ServerAlias siaas

  # Workaround against: https://github.com/scottie1984/swagger-ui-express/issues/183
  RewriteEngine on
  RewriteRule ^/docs(.*) http://%{HTTP_HOST}/api\$0
  RewriteRule ^/static(.*) http://%{HTTP_HOST}/api\$0

  ProxyPreserveHost On
  ProxyPass "/api" http://127.0.0.1:5000
  ProxyPassReverse "/api" http://127.0.0.1:5000

  <Location "/api">
    Order deny,allow
    Deny from all
    # IP access allowed
    Allow from 127.0.0.1
    AuthType Basic
    AuthName "Restricted Area"
    AuthUserFile /etc/apache2/.htpasswd
    # Satisfy Any will allow either IP or authentication; Satisfy All will enforce both IP and authentication
    Satisfy Any
    Require valid-user
  </Location>

  CustomLog \${APACHE_LOG_DIR}/siaas_access.log combined
  ErrorLog \${APACHE_LOG_DIR}/siaas_error.log

</VirtualHost>
EOF
cat << EOF | tee /etc/apache2/sites-available/siaas-ssl.conf
<VirtualHost *:80>

  ServerName ${THIS_HOST}
  ServerAlias siaas

  RewriteEngine On
  RewriteRule ^(.*)$ https://%{HTTP_HOST}\$1 [R=301,L]

</VirtualHost>

<VirtualHost *:443>

  ServerName ${THIS_HOST}
  ServerAlias siaas

  SSLEngine On
  SSLCertificateFile /etc/ssl/certs/siaas.crt
  SSLCertificateKeyFile /etc/ssl/private/siaas.key

  # Workaround against: https://github.com/scottie1984/swagger-ui-express/issues/183
  RewriteEngine on
  RewriteRule ^/docs(.*) https://%{HTTP_HOST}/api\$0
  RewriteRule ^/static(.*) https://%{HTTP_HOST}/api\$0

  ProxyPreserveHost On
  ProxyPass "/api" http://127.0.0.1:5000
  ProxyPassReverse "/api" http://127.0.0.1:5000

  <Location "/api">
    Order deny,allow
    Deny from all
    # IP access allowed
    Allow from 127.0.0.1
    AuthType Basic
    AuthName "Restricted Area"
    AuthUserFile /etc/apache2/.htpasswd
    # Satisfy Any will allow either IP or authentication; Satisfy All will enforce both IP and authentication
    Satisfy Any
    Require valid-user
  </Location>

  CustomLog \${APACHE_LOG_DIR}/siaas_access.log combined
  ErrorLog \${APACHE_LOG_DIR}/siaas_error.log

</VirtualHost>
EOF
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
mongo_shell="mongosh" && which ${mongo_shell} > /dev/null || mongo_shell="mongo" # fallback to the older mongo shell binary, if the new one is not found
#sed -i 's|bindIp[[:space:]]*:[[:space:]]*127.0.0.1|bindIp: 0.0.0.0|g' /etc/mongod.conf # open DB to the world (only for testing purposes
systemctl restart mongod
systemctl enable mongod
sleep 5 && ${mongo_shell} --quiet --eval 'Mongo().getDBNames()' | grep siaas || ./siaas_server_initialize_mongodb.sh # initialize the MongoDB SIAAS DB if it doesn't exist

# SERVICE CONFIGURATION
cp -n conf/siaas_server.cnf.orig conf/siaas_server.cnf
chmod o-rwx conf/siaas_server.cnf
ln -fsT ${SCRIPT_DIR}/log /var/log/siaas-server
cat << EOF | tee /etc/systemd/system/siaas-server.service
[Unit]
Description=SIAAS Server
Requires=mongod.service
Wants=apache2.service
After=mongod.service apache2.service

[Service]
ExecStart=${SCRIPT_DIR}/siaas_server_run.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable siaas-server

# INITIALIZE
#sudo rm -rf ${SCRIPT_DIR}/venv
${SCRIPT_DIR}/siaas_server_venv_setup.sh

echo -e "\nSIAAS Server will be started on boot.\n\nTo start (or restart) manually right now: sudo systemctl [start/restart] siaas-server\n"
