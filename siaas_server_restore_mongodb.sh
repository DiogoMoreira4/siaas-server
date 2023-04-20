#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

if [ $# -lt 1 ]; then
  BACKUP_FILE=`ls -rt siaas_db_backup_* 2> /dev/null | tail -1`
else
  BACKUP_FILE=${1}
fi

stat ${BACKUP_FILE} 2> /dev/null

mongorestore --nsInclude=siaas.* --drop --archive=${BACKUP_FILE}
