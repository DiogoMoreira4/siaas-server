# Intelligent System for Automation of Security Audits (SIAAS)
# Server
# By João Pedro Seara, 2022-2024

import os
import sys
import logging
import time
import multiprocessing_logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from multiprocessing import Process
from waitress import serve

app = Flask(__name__)
logger = logging.getLogger(__name__)

SIAAS_VERSION = "1.0.1"
LOG_DIR = "log"
API_PORT = 5000
SWAGGER_URL = "/docs"  # route for exposing Swagger UI
SWAGGER_JSON_URL = "/static/swagger_siaas_server.json"
SWAGGER_APP_NAME = "SIAAS Server"

DB_COLLECTION_OBJ = None
DB_ZAP_COLLECTION_OBJ = None


def get_db_collection():
    """
    Returns the MongoDB collection object
    """
    return DB_COLLECTION_OBJ

def get_db_collection_zap():
    """
    Returns the MongoDB ZAP collection object
    """
    return DB_ZAP_COLLECTION_OBJ

if __name__ == "__main__":

    import siaas_aux
    import siaas_dbmaintenance
    import siaas_mailer
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
            "\nThis script must be run as root or using sudo!\n")
        sys.exit(1)

    # Create local directories
    os.makedirs(os.path.join(sys.path[0], 'conf'), exist_ok=True)
    os.makedirs(os.path.join(sys.path[0], 'tmp'), exist_ok=True)
    os.makedirs(os.path.join(sys.path[0], 'var'), exist_ok=True)

    # Deleting any existing databases leftovers
    old_dbs = os.listdir(os.path.join(sys.path[0], 'var/'))
    for db in old_dbs:
        if db.endswith(".db"):
            os.remove(os.path.join(sys.path[0], 'var/'+db))

    # Initializing local databases for configurations
    siaas_aux.write_to_local_file(
        os.path.join(sys.path[0], 'var/config.db'), {})
    os.chmod(os.path.join(sys.path[0], 'var/config.db'), os.stat(
        os.path.join(sys.path[0], 'var/config.db')).st_mode & ~0o007)
    siaas_aux.write_to_local_file(os.path.join(
        sys.path[0], 'var/config_local.db'), {})
    os.chmod(os.path.join(sys.path[0], 'var/config_local.db'), os.stat(
        os.path.join(sys.path[0], 'var/config_local.db')).st_mode & ~0o007)

    # Read local configuration file and insert in local databases
    siaas_aux.write_config_db_from_conf_file(
        output=os.path.join(sys.path[0], 'var/config.db'))
    siaas_aux.write_config_db_from_conf_file(
        output=os.path.join(sys.path[0], 'var/config_local.db'))

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
        if config_name.upper() == "MONGO_ZAP_COLLECTION":
            MONGO_ZAP_COLLECTION = config_dict[config_name]

    # Define logging level according to user config
    os.makedirs(os.path.join(sys.path[0], LOG_DIR), exist_ok=True)
    log_file = os.path.join(os.path.join(
        sys.path[0], LOG_DIR), "siaas-server.log")
    log_level = siaas_aux.get_config_from_configs_db(config_name="log_level")
    log_max_bytes = 10240000
    log_backup_count = 3
    while len(logging.root.handlers) > 0:
        logging.root.removeHandler(logging.root.handlers[-1])
    try:
        logging.basicConfig(handlers=[RotatingFileHandler(os.path.join(sys.path[0], log_file), maxBytes=log_max_bytes, backupCount=log_backup_count)],
                            format='%(asctime)s.%(msecs)03d %(levelname)-5s %(filename)s [%(processName)s|%(threadName)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=eval("logging."+log_level.upper()))
    except:
        logging.basicConfig(handlers=[RotatingFileHandler(os.path.join(sys.path[0], log_file), maxBytes=log_max_bytes, backupCount=log_backup_count)],
                            format='%(asctime)s.%(msecs)03d %(levelname)-5s %(filename)s [%(processName)s|%(threadName)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
    multiprocessing_logging.install_mp_handler()

    # Grabbing a unique system ID before proceeding
    server_uid = siaas_aux.get_or_create_unique_system_id()
    if server_uid == "00000000-0000-0000-0000-000000000000":
        logger.critical(
            "Can't proceed without an unique system ID. Aborting !")
        sys.exit(1)

    # Create connection to MongoDB
    if len(MONGO_PORT or '') > 0:
        mongo_host_port = MONGO_HOST+":"+MONGO_PORT
    else:
        mongo_host_port = MONGO_HOST
    DB_COLLECTION_OBJ = siaas_aux.connect_mongodb_collection(MONGO_USER, MONGO_PWD, mongo_host_port, MONGO_DB, MONGO_COLLECTION)
    DB_ZAP_COLLECTION_OBJ = siaas_aux.connect_mongodb_collection(MONGO_USER, MONGO_PWD, mongo_host_port, MONGO_DB, MONGO_ZAP_COLLECTION)

    # Check if DB is alive
    if not siaas_aux.mongodb_ping(MONGO_USER, MONGO_PWD, mongo_host_port, MONGO_DB, MONGO_COLLECTION):
        logger.critical(
            "DB is down. Aborting !")
        sys.exit(1)

    # Merge upstream configs
    siaas_aux.merge_configs_from_upstream(
        upstream_dict=siaas_aux.get_dict_current_server_configs(DB_COLLECTION_OBJ))

    # Create MongoDB indexes
    DB_COLLECTION_OBJ.create_index(
        "origin", unique=False, name="agent_origin_index")
    DB_COLLECTION_OBJ.create_index(
        "destiny", unique=False, name="agent_destiny_index")
    DB_COLLECTION_OBJ.create_index(
        "timestamp", unique=False, name="agent_timestamp_index")

    print("\nSIAAS Server v"+SIAAS_VERSION +
          " starting ["+server_uid+"]\n\nLogging to: "+os.path.join(sys.path[0], log_file)+"\n")
    logger.info("SIAAS Server v"+SIAAS_VERSION+" starting ["+server_uid+"]")

    # Main logic

    platform = Process(target=siaas_platform.loop, args=(SIAAS_VERSION,))
    dbmaintenance = Process(target=siaas_dbmaintenance.loop, args=())
    mailer = Process(target=siaas_mailer.loop, args=())

    platform.start()
    dbmaintenance.start()
    mailer.start()

    # give the modules some time to start before launching the API
    time.sleep(5)
    app.register_blueprint(get_swaggerui_blueprint(SWAGGER_URL, SWAGGER_JSON_URL, config={
                           'app_name': SWAGGER_APP_NAME, 'validatorUrl': 'none'}), url_prefix=SWAGGER_URL)
    #app.run(debug=True, use_reloader=False, host="127.0.0.1", port=API_PORT)
    serve(app, host="127.0.0.1", port=API_PORT)

    platform.join()
    dbmaintenance.join()
    mailer.join()

    sys.exit(0)
