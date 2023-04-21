#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

now=`date +%Y%m%d%H%M%S`

if [ $# -lt 1 ]; then
  BACKUP_FILE=siaas_db_backup_${now}
else
  BACKUP_FILE=${1}
fi

mongodump --db=siaas --archive=${BACKUP_FILE}

echo -e "\nBackup file information:\n"
stat ${BACKUP_FILE}
