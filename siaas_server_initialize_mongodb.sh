#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

mongo_shell="mongosh" && which ${mongo_shell} > /dev/null || mongo_shell="mongo" # fallback to the older mongo shell binary, if the new one is not found

echo "Initializing SIAAS database (also dropping existing, if any) ..."

#${mongo_shell} --quiet --eval 'db.runCommand({ connectionStatus: 1 })'
#${mongo_shell} --quiet --eval 'Mongo().getDBNames()'
#echo "show dbs" | ${mongo_shell} --quiet

${mongo_shell} --quiet siaas --eval 'db.siaas.dropIndexes()' 2> /dev/null
${mongo_shell} --quiet siaas --eval 'db.dropAllUsers()'
${mongo_shell} --quiet siaas --eval 'db.dropAllRoles()'
${mongo_shell} --quiet siaas --eval 'db.dropDatabase()'

${mongo_shell} --quiet siaas --eval 'db.createUser({"user":"siaas", "pwd": "siaas", roles:[{"role":"userAdmin","db":"siaas"}]})'
${mongo_shell} --quiet siaas --eval 'db.getUsers()'

#${mongo_shell} --quiet -u siaas -p siaas 127.0.0.1/siaas --eval 'db.siaas_test_collection.insertOne({"siaas_test_key":"siaas_test_value"})'
#${mongo_shell} --quiet -u siaas -p siaas 127.0.0.1/siaas --eval 'db.getCollectionNames()'
#${mongo_shell} --quiet -u siaas -p siaas 127.0.0.1/siaas --eval 'db.siaas_test_collection.drop()'
