import siaas_aux
import logging
import os
import sys
import pprint
import time
from datetime import datetime
from copy import copy

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    log_level = logging.INFO
    logging.basicConfig(
        format='%(asctime)s %(levelname)-5s %(filename)s [%(threadName)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_level)

    if os.geteuid() != 0:
        print("You need to be root to run this script!", file=sys.stderr)
        sys.exit(1)

    print('\nThis script is being directly run, so it will just read data from the DB!\n')

    MONGO_USER = "siaas"
    MONGO_PWD = "siaas"
    MONGO_HOST = "127.0.0.1"
    MONGO_PORT = "27017"
    MONGO_DB = "siaas"
    MONGO_COLLECTION = "siaas"

    config = {
        "datatransfer_loop_interval_sec": 45,
        "disable_portscanner": "false",
        "silent_mode": "false"
    }

    config_2 = {
        "datatransfer_loop_interval_sec": 30,
        "disable_portscanner": "false",
        "silent_mode": "false"
    }


    bc_config = {
        "datatransfer_loop_interval_sec": 120,
        "disable_portscanner": "true",
        "ignore_neighborhood": "",
        "silent_mode": "true",
        "testing_a_dict": { "oi": 123 }
    }

    #config = {}
    #config_2 = {}
    #bc_config = {}

    agent_uid = "0924aa8b-6dc9-4fec-9716-d1601fc8b6c6"
    agent_uid_2 = "L1HF89B0091"

    # Create some configs for the agents (testing)

    collection = siaas_aux.connect_mongodb_collection(
        MONGO_USER, MONGO_PWD, MONGO_HOST+":"+MONGO_PORT, MONGO_DB, MONGO_COLLECTION)

    siaas_aux.create_or_update_agent_configs(collection, agent_uid, config)
    siaas_aux.create_or_update_agent_configs(collection, agent_uid_2, config_2)
    siaas_aux.create_or_update_agent_configs(
        collection, "ffffffff-ffff-ffff-ffff-ffffffffffff", bc_config)

    siaas_uid = siaas_aux.get_or_create_unique_system_id()
    #siaas_uid = "00000000-0000-0000-0000-000000000000" # hack to show data from all servers

    results = siaas_aux.read_mongodb_collection(collection, siaas_uid)

    results = siaas_aux.get_dict_current_agent_data(collection, agent_uid=agent_uid+","+agent_uid_2, module="neighborhood")
    #results = siaas_aux.get_dict_current_agent_data(collection)
    #results = siaas_aux.get_dict_active_agents(collection)


    results = siaas_aux.get_dict_current_agent_configs(collection, agent_uid=agent_uid, merge_broadcast=0)
    #results = siaas_aux.get_dict_current_agent_configs(collection, include_broadcast=True)

    #results = siaas_aux.get_dict_historical_agent_data(collection, days=1)
    #results = siaas_aux.get_dict_historical_agent_data(collection, agent_uid=agent_uid)

    #siaas_aux.delete_all_records_older_than(collection, scope=None, agent_uid=agent_uid, days=-1)
    #results = siaas_aux.get_dict_current_agent_configs(collection, agent_uid=agent_uid, merge_broadcast=0)
    results = siaas_aux.get_dict_historical_agent_data(collection, agent_uid=agent_uid)

    if results != None:
        pprint.pprint(results)
        #for doc in results:
            # print('\n'+str(pprint.pformat(doc)))
            #print('\n'+str(doc))

    print('\nAll done. Bye!\n')

