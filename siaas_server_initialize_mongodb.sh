#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

echo "Initializing SIAAS database (also dropping existing, if any) ..."

#mongosh --quiet --eval 'db.runCommand({ connectionStatus: 1 })'
#mongosh --quiet --eval 'Mongo().getDBNames()'
#echo "show dbs" | mongosh --quiet

mongosh --quiet siaas --eval 'db.dropAllUsers()'
mongosh --quiet siaas --eval 'db.dropAllRoles()'
mongosh --quiet siaas --eval 'db.dropDatabase()'

mongosh --quiet siaas --eval 'db.createUser({"user":"siaas", "pwd": "siaas", roles:[{"role":"userAdmin","db":"siaas"}]})'
mongosh --quiet siaas --eval 'db.getUsers()'

#mongosh --quiet -u siaas -p siaas 127.0.0.1/siaas --eval 'db.siaas_test_collection.insertOne({"siaas_test_key":"siaas_test_value"})'
#mongosh --quiet -u siaas -p siaas 127.0.0.1/siaas --eval 'db.getCollectionNames()'
#mongosh --quiet -u siaas -p siaas 127.0.0.1/siaas --eval 'db.siaas_test_collection.drop()'
