import siaas_aux
import logging
import os
import sys
import pprint
import time
from datetime import datetime
from copy import copy

logger = logging.getLogger(__name__)

def delete_historical_data(db_collection=None, days_to_keep=365):

    logger.info("Performing historical database cleanup, keeping last "+str(days_to_keep)+" days ...")
    deleted_count = siaas_aux.delete_all_records_older_than(db_collection, scope="agent_data", agent_uid=None, days_to_keep=days_to_keep)
    if deleted_count:
       logger.info("DB cleanup finished. "+str(deleted_count)+" records deleted.")
       return True
    else:
       logger.error("DB could not be cleaned up. This might result in an eventual disk exhaustion in the server!")
       return False

def loop():

    # Generate global variables from the configuration file
    config_dict = siaas_aux.get_config_from_configs_db(convert_to_string=True)
    MONGO_USER=None
    MONGO_PWD=None
    MONGO_HOST=None
    MONGO_PORT=None
    MONGO_DB=None
    MONGO_COLLECTION=None
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

    if len(MONGO_PORT or '') > 0:
       mongo_host_port = MONGO_HOST+":"+MONGO_PORT
    else:
       mongo_host_port = MONGO_HOST
    db_collection = siaas_aux.connect_mongodb_collection(
          MONGO_USER, MONGO_PWD, mongo_host_port, MONGO_DB, MONGO_COLLECTION)

    run=True
    if db_collection == None:
            logger.error("No valid DB collection received. No DB maintenance will be performed.")
            run=False

    while run:

        logger.debug("Loop running ...")

        try:
            days_to_keep = int(siaas_aux.get_config_from_configs_db(config_name="dbmaintenance_historical_days_to_keep"))
        except:
            logger.debug("The number of days to keep in the database is not configured or is invalid. Defaulting to 10 years.")
            days_to_keep = 3650

        delete_historical_data(db_collection, days_to_keep)

        # Sleep before next loop
        try:
            sleep_time = int(siaas_aux.get_config_from_configs_db(
                config_name="dbmaintenance_loop_interval_sec"))
            logger.debug("Sleeping for "+str(sleep_time) +
                         " seconds before next loop ...")
            time.sleep(sleep_time)
        except:
            logger.debug(
                "The interval loop time is not configured or is invalid. Sleeping now for 60 seconds by default ...")
            time.sleep(60)


if __name__ == "__main__":

    log_level = logging.INFO
    logging.basicConfig(
        format='%(asctime)s %(levelname)-5s %(filename)s [%(threadName)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_level)

    if os.geteuid() != 0:
        print("You need to be root to run this script!", file=sys.stderr)
        sys.exit(1)

    print('\nThis script is being directly run, so it will just read data from the DB!\n')

    siaas_uid = siaas_aux.get_or_create_unique_system_id()
    #siaas_uid = "00000000-0000-0000-0000-000000000000" # hack to show data from all agents

    MONGO_USER = "siaas"
    MONGO_PWD = "siaas"
    MONGO_HOST = "127.0.0.1"
    MONGO_PORT = "27017"
    MONGO_DB = "siaas"
    MONGO_COLLECTION = "siaas"

    try:
        collection = siaas_aux.connect_mongodb_collection(
            MONGO_USER, MONGO_PWD, MONGO_HOST+":"+MONGO_PORT, MONGO_DB, MONGO_COLLECTION)
    except:
        print("Can't connect to DB!")
        sys.exit(1)

    logger.info("Cleaning up the DB ...")

    if delete_historical_data(collection, days_to_keep=3650):
        logger.info("All OK!")
    else:
        logger.info("Error detected.")

    print('\nAll done. Bye!\n')
