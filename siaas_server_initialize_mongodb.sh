#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

#mongo --eval 'db.runCommand({ connectionStatus: 1 })'
#echo "show dbs" | mongo

mongo siaas --eval 'db.dropAllUsers()'
mongo siaas --eval 'db.dropAllRoles()'
mongo siaas --eval 'db.dropDatabase()'

mongo siaas --eval 'db.createUser({"user":"siaas", "pwd": "siaas", roles:[{"role":"userAdmin","db":"siaas"}]})'
mongo siaas --eval 'db.getUsers()'

#mongo -u siaas -p siaas 127.0.0.1/siaas --eval 'db.siaas_test_collection.insert({"siaas_test_key":"siaas_test_value"})'
#mongo -u siaas -p siaas 127.0.0.1/siaas --eval 'db.getCollectionNames()'
#mongo -u siaas -p siaas 127.0.0.1/siaas --eval 'Mongo().getDBNames()'
#mongo -u siaas -p siaas 127.0.0.1/siaas --eval 'db.siaas_test_collection.drop()'
