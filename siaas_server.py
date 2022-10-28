# SIAAS - Sistema Inteligente para Automação de Auditorias de Segurança
# By João Pedro Seara

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import uuid
from flask import Flask, jsonify, render_template
from multiprocessing import Process, Value, Manager, Lock
from waitress import serve

app = Flask(__name__)
logger = logging.getLogger(__name__)

SIAAS_VERSION = "0.0.1"
LOG_DIR = "log"

DB_COLLECTION_OBJ = None
def get_db_collection():
    return DB_COLLECTION_OBJ

if __name__ == "__main__":

    import siaas_aux
    import siaas_dbmaintenance
    import siaas_platform
    import siaas_routes

    print('\n')

    # No Windows can do ; - )
    if os.name != "posix":
        logger.critical(
            "\nThis program can only be run in Linux or Raspberry Pi. Exiting!\n")
        sys.exit(1)

    # Needs to be root
    if os.geteuid() != 0:
        logger.critical(
            "\nThis script must be run as root or using sudo!\n", file=sys.stderr)
        sys.exit(2)

    # Create local directories
    os.makedirs(os.path.join(sys.path[0], 'conf'), exist_ok=True)
    os.makedirs(os.path.join(sys.path[0], 'tmp'), exist_ok=True)
    os.makedirs(os.path.join(sys.path[0], 'var'), exist_ok=True)

    # Initializing local databases for configurations
    siaas_aux.write_to_local_file(
        os.path.join(sys.path[0], 'var/config.db'), {})

    # Read local configuration file and insert in local database
    siaas_aux.write_config_db_from_conf_file()

    # Get all values
    config_dict = siaas_aux.get_config_from_configs_db(convert_to_string=True)
    MONGO_USER = None
    MONGO_PWD = None
    MONGO_HOST = None
    MONGO_PORT = None
    MONGO_DB = None
    MONGO_COLLECTION = None
    for config_name in config_dict.keys():
        if config_name.upper() == "MONGO_USER":
            MONGO_USER = config_dict[config_name]
        if config_name.upper() == "MONGO_PWD":
            MONGO_PWD = config_dict[config_name]
        if config_name.upper() == "MONGO_HOST":
            MONGO_HOST = config_dict[config_name]
        if config_name.upper() == "MONGO_PORT":
            MONGO_PORT = config_dict[config_name]
        if config_name.upper() == "MONGO_DB":
            MONGO_DB = config_dict[config_name]
        if config_name.upper() == "MONGO_COLLECTION":
            MONGO_COLLECTION = config_dict[config_name]

    # Define logging level according to user config
    os.makedirs(os.path.join(sys.path[0], LOG_DIR), exist_ok=True)
    log_file = os.path.join(os.path.join(sys.path[0], LOG_DIR), "siaas-server.log")
    log_level = siaas_aux.get_config_from_configs_db(config_name="log_level")
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    try:
        logging.basicConfig(handlers=[RotatingFileHandler(os.path.join(sys.path[0], log_file), maxBytes=10240000, backupCount=5)],
                            format='%(asctime)s.%(msecs)03d %(levelname)-5s %(filename)s [%(processName)s|%(threadName)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=eval("logging."+log_level.upper()))
    except:
        logging.basicConfig(handlers=[RotatingFileHandler(os.path.join(sys.path[0], log_file), maxBytes=10240000, backupCount=5)],
                            format='%(asctime)s.%(msecs)03d %(levelname)-5s %(filename)s [%(processName)s|%(threadName)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

    # Grabbing a unique system ID before proceeding
    server_uid = siaas_aux.get_or_create_unique_system_id()
    if server_uid == "00000000-0000-0000-0000-000000000000":
        logger.critical(
            "\nCan't proceed without an unique system ID. Aborting !\n")
        sys.exit(3)

    # Create connection to MongoDB
    if len(MONGO_PORT or '') > 0:
        mongo_host_port = MONGO_HOST+":"+MONGO_PORT
    else:
        mongo_host_port = MONGO_HOST
    DB_COLLECTION_OBJ = siaas_aux.connect_mongodb_collection(
        MONGO_USER, MONGO_PWD, mongo_host_port, MONGO_DB, MONGO_COLLECTION)

    print("\nSIAAS Server v"+SIAAS_VERSION +
          " starting ["+server_uid+"]\n\nLogging to: "+os.path.join(sys.path[0], log_file)+"\n")
    logger.info("SIAAS Server v"+SIAAS_VERSION+" starting ["+server_uid+"]")

    # Main logic
    platform = Process(target=siaas_platform.loop, args=(SIAAS_VERSION,))
    dbmaintenance = Process(target=siaas_dbmaintenance.loop, args=())
    platform.start()
    dbmaintenance.start()
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port="5000")
    #serve(app, host="0.0.0.0", port="5000")
    platform.join()
    dbmaintenance.join()
