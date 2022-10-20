#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "`readlink -f ${BASH_SOURCE[0]}`" )" &> /dev/null && pwd )

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root or using sudo!"
  exit 1
fi

cd ${SCRIPT_DIR}

if ! source ./venv/bin/activate 2> /dev/null
then
	python3 -m venv ./venv
	source ./venv/bin/activate
	pip3 install wheel==0.37.1
	pip3 install -r ./requirements.txt
fi

source ./venv/bin/activate
python3 -u ./siaas_server.py
