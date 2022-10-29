import ipaddress
import math
import pprint
import logging
import uuid
import os
import sys
import re
import json
from copy import copy
from datetime import datetime, timedelta
from pymongo import MongoClient
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


def merge_module_dicts(modules=""):
    """
    Grabs all DB files from the module list and concatenate them
    Returns an empty dict if it fails
    """
    merged_dict = {}
    for module in modules.split(','):
        module = module.lstrip().rstrip()
        try:
            module_dict = read_from_local_file(
                os.path.join(sys.path[0], 'var/'+str(module)+'.db'))
            if module_dict != None:
                next_dict_to_merge = {}
                next_dict_to_merge[module] = module_dict
                merged_dict = dict(
                    list(merged_dict.items())+list(next_dict_to_merge.items()))
        except:
            logger.warning("Couldn't merge dict: " +
                           str(next_dict_to_merge))
    return merged_dict


def get_config_from_configs_db(local_dict=os.path.join(sys.path[0], 'var/config.db'), config_name=None, convert_to_string=True):
    """
    Reads a configuration value from the configs db
    If the intput is "None" it returns an entire dict with all the values. Returns an empty dict if there are no configs
    If the input is a specific config key, it returns the value for that config key. Returns None if the config key does not exist
    """
    if config_name == None:

        logger.debug("Getting configuration dictionary from local DB ...")
        config_dict = read_from_local_file(
            local_dict)
        if len(config_dict or '') > 0:
            out_dict = {}
            for k in config_dict.keys():
                if convert_to_string:
                    out_dict[k] = str(config_dict[k])
                else:
                    out_dict[k] = config_dict[k]
            return config_dict

        logger.error("Couldn't get configuration dictionary from local DB.")
        return {}

    else:

        logger.debug("Getting configuration value '" +
                     config_name+"' from local DB ...")
        config_dict = read_from_local_file(
            local_dict)
        if len(config_dict or '') > 0:
            if config_name in config_dict.keys():
                value = config_dict[config_name]
                if convert_to_string:
                    value = str(value)
                return config_dict[config_name]

        logger.debug("Couldn't get configuration named '" +
                     config_name+"' from local DB. Maybe it doesn't exist.")
        return None


def write_config_db_from_conf_file(conf_file=os.path.join(sys.path[0], 'conf/siaas_server.cnf'), output=os.path.join(sys.path[0], 'var/config.db')):
    """
    Writes the configuration DB (dict) from the config file. If the file is empty or does not exist, returns False
    It will strip all characters after '#', and then strip the spaces from the beginning or end of the resulting string. If the resulting string is empty, it will ignore it
    Then, it will grab the string before the first "=" as the config key, and after it as the actual value
    The config key has its spaces removed from beginning or end, and all " and ' are removed.
    The actual value is just stripped of spaces from the beginning and the end
    Writes the resulting dict in the DB file of config.db. This means it will return True if things go fine, or False if it fails
    """

    logger.debug("Writing configuration local DB, from local file: "+conf_file)

    config_dict = {}
    pattern = "^[A-Za-z0-9_-]*$"

    local_conf_file = read_from_local_file(conf_file)
    if len(local_conf_file or '') == 0:
        return False

    for line in local_conf_file.splitlines():
        try:
            line_uncommented = line.split('#')[0].rstrip().lstrip()
            if len(line_uncommented) == 0:
                continue
            config_name = line_uncommented.split("=", 1)[0].rstrip().lstrip()
            if not bool(re.match(pattern, config_name)):
                raise
            config_value = line_uncommented.split("=", 1)[1].rstrip().lstrip()
            config_dict[config_name] = config_value
        except:
            logger.warning(
                "Invalid line from local configuration file was ignored: "+str(line))
            continue

    return write_to_local_file(output, dict(sorted(config_dict.items())))


def upload_agent_data(collection, agent_uid=None, data_dict={}):
    """
    Receives a dict with agent data, validates it, and calls the mongodb insertion function to insert it
    Returns True if all OK; False if NOK
    """

    if type(data_dict) is not dict:
        logger.error(
            "No valid data dict received. No data was uploaded.")
        return False

    if not validate_string_key(agent_uid):
        logger.error("Agent UID is not valid. No data was uploaded.")
        return False

    for k in data_dict.keys():
        if not validate_string_key(k):
            logger.error("Data dict is not valid. No data was uploaded.")
            return False

    # Creating a new dict with a date object and date transfer direction so we can easily filter it and order entries in MongoDB

    # MongoDB fields in SIAAS data model are:
    # _id - (Auto-generated by Mongo)
    # scope - What type of content there's in this entry
    # origin - Creator of this entry
    # destiny - Intended destiny
    # payload - Data payload
    # timestamp - Data object with creation timestamp of the record

    complete_dict = {}
    complete_dict["scope"] = "agent_data"
    complete_dict["origin"] = "agent_"+agent_uid
    complete_dict["destiny"] = "*"
    complete_dict["payload"] = data_dict
    complete_dict["timestamp"] = get_now_utc_obj()

    return insert_in_mongodb_collection(collection, complete_dict)


def create_or_update_agent_configs(collection, agent_uid=None, config_dict={}):
    """
    Receives a dict with agent configs, validates it, and calls the mongodb insertion function to insert it
    Returns True if all OK; False if NOK
    """

    if type(config_dict) is not dict:
        logger.error(
            "No valid configuration dict received. No data was uploaded.")
        return False

    if "#" in str(config_dict):
        logger.error(
            "Detected invalid character '#' in the input configuration dict keys or values. No data was uploaded.")
        return False

    if not validate_string_key(agent_uid):
        logger.error("Agent UID is not valid. No data was uploaded.")
        return False

    for k in config_dict.keys():
        if not validate_string_key(k):
            logger.error("Data dict is not valid. No data was uploaded.")
            return False

    siaas_uid = get_or_create_unique_system_id()

    # Creating a new dict with a date object and date transfer direction so we can easily filter it and order entries in MongoDB

    # MongoDB fields in SIAAS data model are:
    # _id - (Auto-generated by Mongo)
    # scope - What type of content there's in this entry
    # origin - Creator of this entry
    # destiny - Intended destiny
    # payload - Data payload
    # timestamp - Data object with creation timestamp of the record

    complete_dict = {}
    complete_dict["scope"] = "agent_configs"
    complete_dict["origin"] = "server_"+siaas_uid
    complete_dict["destiny"] = "agent_"+agent_uid
    complete_dict["payload"] = dict(sorted(config_dict.items()))
    complete_dict["timestamp"] = get_now_utc_obj()

    return create_or_update_in_mongodb_collection(collection, complete_dict)


def read_mongodb_collection(collection, siaas_uid="00000000-0000-0000-0000-000000000000"):
    """
    Reads data from the Mongo DB collection
    If the UID is "nil" it will return all records. Else, it will return records only for the inputted UID
    Returns a list of records. Returns None if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    try:

        if(siaas_uid == "00000000-0000-0000-0000-000000000000"):
            cursor = collection.find({"payload": {'$exists': True}}).sort(
                '_id', -1).limit(15)  # show everything
        else:
            cursor = collection.find({'$and': [{"payload": {'$exists': True}}, {'$or': [{"origin": "server_"+siaas_uid}, {"destiny": {'$in': [
                                     "server_"+siaas_uid, "server_ffffffff-ffff-ffff-ffff-ffffffffffff"]}}]}]}).sort('_id', -1).limit(15)  # destinated or originated to/from the server

        results = list(cursor)
        for doc in results:
            logger.debug("Record read: "+str(doc))
        return results
    except Exception as e:
        logger.error("Can't read data from the DB server: "+str(e))
        return None


def get_dict_active_agents(collection):
    """
    Reads a list of active agents
    Returns a list of records. Returns empty dict if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    out_dict = {}

    try:
        if "timestamp" not in str(list(collection.index_information())):
            collection.create_index("timestamp", unique=False)
        cursor = collection.aggregate([
            {"$match": {"origin": {"$regex": "^agent_"}}},
            {"$sort": {"timestamp": 1}},
            {"$group": {"_id": {"origin": "$origin"}, "origin": {
                "$last": "$origin"}, "timestamp": {"$last": "$timestamp"}}}
        ])
        results = list(cursor)
    except Exception as e:
        logger.error("Can't read data from the DB server: "+str(e))
        return out_dict

    for r in results:
        try:
            uid = r["origin"].split("_", 1)[1]
            out_dict[uid] = {}
            out_dict[uid]["last_seen"] = r["timestamp"].strftime(
                '%Y-%m-%dT%H:%M:%SZ')
        except:
            logger.debug(
                "Ignoring invalid entry when grabbing active agents data.")

    return out_dict


def get_dict_history_agent_data(collection, agent_uid=None, module=None, limit_outputs=99999, days=99999):
    """
    Reads historical agent data from the Mongo DB collection
    We can select a list of agents and modules to display
    Returns a list of records. Returns empty dict if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    out_dict = {}

    if agent_uid == None:
        try:
            last_d = datetime.utcnow() - timedelta(days=int(days))
            cursor = collection.find(
                {'$and': [{"payload": {'$exists': True}}, {"scope": "agent_data"}, {"timestamp": {"$gte": last_d}}
                          ]}
            ).sort('_id', -1).limit(int(limit_outputs))
            results = list(cursor)
        except Exception as e:
            logger.error("Can't read data from the DB server: "+str(e))
            return out_dict

    else:
        results = []
        agent_list = []
        for u in agent_uid.split(','):
            agent_list.append("agent_"+u.lstrip().rstrip())
        try:
            last_d = datetime.utcnow() - timedelta(days=int(days))
            cursor = collection.find(
                {'$and': [{"payload": {'$exists': True}}, {"scope": "agent_data"}, {
                    "timestamp": {"$gte": last_d}}, {"origin": {'$in': agent_list}}]}
            ).sort('_id', -1).limit(int(limit_outputs))
            results = results+list(cursor)
        except Exception as e:
            logger.error("Can't read data from the DB server: "+str(e))

    for r in results:
        try:
            if r["origin"].startswith("agent_"):
                uid = r["origin"].split("_", 1)[1]
                timestamp = r["timestamp"].strftime('%Y-%m-%dT%H:%M:%SZ')
                if timestamp not in out_dict.keys():
                    out_dict[timestamp] = {}
                if module == None:
                    out_dict[timestamp][uid] = r["payload"]
                else:
                    out_dict[timestamp][uid] = {}
                    for m in module.split(','):
                        mod = m.lstrip().rstrip()
                        if mod in r["payload"].keys():
                            out_dict[timestamp][uid][mod] = r["payload"][mod]
        except:
            logger.debug("Ignoring invalid entry when grabbing agent data.")

    return out_dict


def get_dict_current_agent_data(collection, agent_uid=None, module=None):
    """
    Reads agent data from the Mongo DB collection
    We can select a list of agents and modules to display
    Returns a list of records. Returns empty dict if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    out_dict = {}

    if agent_uid == None:
        try:
            if "timestamp" not in str(list(collection.index_information())):
                collection.create_index("timestamp", unique=False)
            cursor = collection.aggregate([
                {"$match": {
                    '$and': [{"origin": {"$regex": "^agent_"}}, {"scope": "agent_data"}]}},
                {"$sort": {"timestamp": 1}},
                {"$group": {"_id": {"origin": "$origin"}, "scope": {"$last": "$scope"}, "origin": {"$last": "$origin"}, "destiny": {
                    "$last": "$destiny"}, "payload": {"$last": "$payload"}, "timestamp": {"$last": "$timestamp"}}}
            ])
            results = list(cursor)
        except Exception as e:
            logger.error("Can't read data from the DB server: "+str(e))
            return out_dict

    else:
        results = []
        for u in agent_uid.split(','):
            uid = u.lstrip().rstrip()
            try:
                cursor = collection.find(
                    {'$and': [{"payload": {'$exists': True}}, {
                        "scope": "agent_data"}, {"origin": "agent_"+uid}]}
                ).sort('_id', -1).limit(1)
                results = results+list(cursor)
            except Exception as e:
                logger.error("Can't read data from the DB server: "+str(e))

    for r in results:
        try:
            if r["origin"].startswith("agent_"):
                uid = r["origin"].split("_", 1)[1]
                if module == None:
                    out_dict[uid] = r["payload"]
                else:
                    out_dict[uid] = {}
                    for m in module.split(','):
                        mod = m.lstrip().rstrip()
                        if mod in r["payload"].keys():
                            out_dict[uid][mod] = r["payload"][mod]
        except:
            logger.debug("Ignoring invalid entry when grabbing agent data.")

    return out_dict


def get_dict_current_agent_configs(collection, agent_uid=None, merge_broadcast=False):
    """
    Reads agent data from the Mongo DB collection
    We can select a list of agents and modules to display
    Returns a list of records. Returns empty dict if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    out_dict = {}

    if agent_uid == None:
        try:
            if "timestamp" not in str(list(collection.index_information())):
                collection.create_index("timestamp", unique=False)
            cursor = collection.aggregate([
                {"$match": {'$and': [{"destiny": {"$regex": "^agent_"}}, {
                    "scope": "agent_configs"}]}},
                {"$sort": {"timestamp": 1}},
                {"$group": {"_id": {"destiny": "$destiny"}, "scope": {"$last": "$scope"}, "origin": {"$last": "$origin"}, "destiny": {
                    "$last": "$destiny"}, "payload": {"$last": "$payload"}, "timestamp": {"$last": "$timestamp"}}}
            ])
            results = list(cursor)
        except Exception as e:
            logger.error("Can't read data from the DB server: "+str(e))

    else:
        results = []
        for u in agent_uid.split(','):
            uid = u.lstrip().rstrip()
            try:
                cursor = collection.find(
                    {'$and': [{"payload": {'$exists': True}}, {
                        "scope": "agent_configs"}, {"destiny": "agent_"+uid}]}
                ).sort('_id', -1).limit(1)
                results = results+list(cursor)
            except Exception as e:
                logger.error("Can't read data from the DB server: "+str(e))

    if merge_broadcast:
        results_bc = []
        try:
            cursor = collection.find(
                {'$and': [{"payload": {'$exists': True}}, {"scope": "agent_configs"}, {
                    "destiny": "agent_ffffffff-ffff-ffff-ffff-ffffffffffff"}]}
            ).sort('_id', -1).limit(1)
            results_bc = list(cursor)
        except Exception as e:
            logger.error("Can't read data from the DB server: "+str(e))

    for r in results:
        try:
            if r["destiny"].startswith("agent_"):
                uid = r["destiny"].split("_", 1)[1]
                if merge_broadcast:
                    if len(results_bc) > 0:
                        out_dict[uid] = dict(
                            list(results_bc[0]["payload"].items())+list(r["payload"].items()))
                    else:
                        out_dict[uid] = r["payload"]
                else:
                    out_dict[uid] = r["payload"]
                out_dict[uid] = dict(sorted(out_dict[uid].items()))
        except:
            logger.debug("Ignoring invalid entry when grabbing agent data.")

    # We have to make sure that even if the Agent UID doesn't exist in the config DB, we return the broadcast values if merge_broadcast is on
    if merge_broadcast and len(agent_uid or '') > 0:
        for u in agent_uid.split(','):
            try:
               uid = u.lstrip().rstrip()
               if uid not in out_dict.keys():
                   if len(results_bc) > 0:
                       out_dict[uid]=results_bc[0]["payload"]
                       out_dict[uid] = dict(sorted(out_dict[uid].items()))
            except:
               logger.debug("Ignoring invalid entry when grabbing agent data.")

    return out_dict


def delete_all_records_older_than(collection, scope=None, agent_uid=None, days_to_keep=99999):
    """
    Delete records older than n-days
    We can select a list of agent_uuids or scope, else it will pick all scopes and all agents
    Returns number of deleted records as a string, or False if error
    """
    logger.debug("Removing data from the DB server ...")
    out_dict = {}
    count = 0

    if agent_uid == None:
        try:
            last_d = datetime.utcnow() - timedelta(days=int(days_to_keep))
            if scope == None:
                c = collection.delete_many(
                    {'$and': [{"payload": {'$exists': True}}, {"timestamp": {"$lt": last_d}}
                              ]}
                )
                count += c.deleted_count
            else:
                c = collection.delete_many(
                    {'$and': [{"payload": {'$exists': True}}, {"scope": scope}, {"timestamp": {"$lt": last_d}}
                              ]}
                )
                count += c.deleted_count
        except Exception as e:
            logger.error("Can't delete data from the DB server: "+str(e))
            return False

    else:
        agent_list = []
        for u in agent_uid.split(','):
            agent_list.append("agent_"+u.lstrip().rstrip())
        try:
            last_d = datetime.utcnow() - timedelta(days=int(days_to_keep))
            if scope == None:
                c = collection.delete_many(
                    {'$and': [{"payload": {'$exists': True}}, {"timestamp": {"$lt": last_d}}, {
                        '$or': [{"destiny": {'$in': agent_list}}, {"origin": {'$in': agent_list}}]}]}
                )
                count += c.deleted_count
            else:
                c = collection.delete_many(
                    {'$and': [{"payload": {'$exists': True}}, {"scope": scope}, {"timestamp": {"$lt": last_d}}, {
                        '$or': [{"destiny": {'$in': agent_list}}, {"origin": {'$in': agent_list}}]}]}
                )
                count += c.deleted_count
        except Exception as e:
            logger.error("Can't delete data from the DB server: "+str(e))
            return False

    # equivalent to True, and also has the number of deleted documents in it
    return str(count)


def read_published_data_for_agents_mongodb(collection, siaas_uid="00000000-0000-0000-0000-000000000000", scope=None, include_broadcast=False, convert_to_string=False):
    """
    Reads data from the Mongo DB collection, specifically published by the server, for agents
    Returns a config dict. Returns an empty dict if anything failed
    """
    my_configs = {}
    broadcasted_configs = {}
    out_dict = {}
    logger.debug("Reading data from the DB server ...")
    try:
        if len(scope or '') > 0:
            cursor1 = collection.find({"payload": {'$exists': True}, "destiny": "agent_"+siaas_uid, "scope": scope}, {
                                      '_id': False, 'timestamp': False, 'origin': False, 'destiny': False, 'scope': False}).sort('_id', -1).limit(1)
        else:
            cursor1 = collection.find({"payload": {'$exists': True}, "destiny": "agent_"+siaas_uid}, {
                                      '_id': False, 'timestamp': False, 'origin': False, 'destiny': False, 'scope': False}).sort('_id', -1).limit(1)
        results1 = list(cursor1)
        for doc in results1:
            my_configs = doc["payload"]

        if len(scope or '') > 0:
            cursor2 = collection.find({"payload": {'$exists': True}, "destiny": "agent_"+"ffffffff-ffff-ffff-ffff-ffffffffffff", "scope": scope}, {
                                      '_id': False, 'timestamp': False, 'origin': False, 'destiny': False, 'scope': False}).sort('_id', -1).limit(1)
        else:
            cursor2 = collection.find({"payload": {'$exists': True}, "destiny": "agent_"+"ffffffff-ffff-ffff-ffff-ffffffffffff"}, {
                                      '_id': False, 'timestamp': False, 'origin': False, 'destiny': False, 'scope': False}).sort('_id', -1).limit(1)
        results2 = list(cursor2)
        for doc in results2:
            broadcasted_configs = doc["payload"]

        if include_broadcast:
            final_results = dict(
                list(broadcasted_configs.items())+list(my_configs.items()))  # configs directed to the agent have precedence over broadcasted ones
        else:
            final_results = my_configs

        for k in final_results.keys():
            if convert_to_string:
                out_dict[k] = str(final_results[k])
            else:
                out_dict[k] = final_results[k]

        logger.debug("Records read from the server: "+str(out_dict))
    except Exception as e:
        logger.error("Can't read data from the DB server: "+str(e))
    return out_dict


def insert_in_mongodb_collection(collection, data_to_insert):
    """
    Inserts data (usually a dict) into a said collection
    Returns True if all was OK. Returns False if the insertion failed
    """
    logger.debug("Inserting data in the DB server ...")
    try:
        logger.debug("All data that will now be written to the database:\n" +
                     pprint.pformat(data_to_insert))
        collection.insert_one(copy(data_to_insert))
        logger.debug("Data successfully uploaded to the DB server.")
        return True
    except Exception as e:
        logger.error("Can't upload data to the DB server: "+str(e))
        return False


def create_or_update_in_mongodb_collection(collection, data_to_insert):
    """
    Creates or updates an object with data
    Returns 1 if all was OK. Returns -1 if the insertion failed
    """
    logger.info("Inserting data in the DB server ...")
    try:
        logger.debug("All data that will now be written to the database:\n" +
                     pprint.pformat(data_to_insert))
        data = copy(data_to_insert)
        collection.find_one_and_update(
            {'destiny': data["destiny"], 'scope': data["scope"]}, {'$set': data}, upsert=True)
        logger.info("Data successfully uploaded to the DB server.")
        return True
    except Exception as e:
        logger.error("Can't upload data to the DB server: "+str(e))
        return False


def connect_mongodb_collection(mongo_user="siaas", mongo_password="siaas", mongo_host="127.0.0.1:27017", mongo_db="siaas", mongo_collection="siaas"):
    """
    Set up a MongoDB collection connection based on the inputs
    Returns the collection obj if succeeded. Returns None if it failed
    """
    logger.debug("Connecting to the DB server at "+str(mongo_host)+" ...")
    try:
        uri = "mongodb://%s:%s@%s/%s" % (quote_plus(mongo_user),
                                         quote_plus(mongo_password), mongo_host, mongo_db)
        client = MongoClient(uri)
        db = client[mongo_db]
        collection = db[mongo_collection]
        logger.info(
            "Correctly configured the DB server connection to collection '"+mongo_collection+"'.")
        return collection
    except Exception as e:
        logger.error("Can't connect to the DB server: "+str(e))
        return None


def write_to_local_file(file_to_write, data_to_insert):
    """
    Writes data (usually a dict) to a local file, after converting it to a JSON format
    Returns True if all went OK
    Returns False if it failed
    """
    logger.debug("Inserting data to local file "+file_to_write+" ...")
    try:
        os.makedirs(os.path.dirname(os.path.join(
            sys.path[0], file_to_write)), exist_ok=True)
        logger.debug("All data that will now be written to the file:\n" +
                     pprint.pformat(data_to_insert))
        with open(file_to_write, 'w') as file:
            file.write(json.dumps(data_to_insert))
            logger.debug("Local file write ended successfully.")
            return True
    except Exception as e:
        logger.error(
            "There was an error while writing to the local file "+file_to_write+": "+str(e))
        return False


def read_from_local_file(file_to_read):
    """
    Reads data from local file and returns it
    It will return None if it failed
    """
    logger.debug("Reading from local file "+file_to_read+" ...")
    try:
        with open(file_to_read, 'r') as file:
            content = file.read()
            try:
                content = eval(content)
            except:
                pass
            return content
    except Exception as e:
        logger.error("There was an error reading from local file " +
                     file_to_read+": "+str(e))
        return None


def get_or_create_unique_system_id():
    """
    Reads the local UID file and returns it
    If this file does not exist or has no data, continues to generate an UID. If it has an invalid UID, it will return a nil UID
    Proceeds to try to generate an UID from local system data
    If this fails, generates a random one
    If all fails, returns a nil UID
    """
    logger.debug(
        "Searching for an existing UID and creating a new one if it doesn't exist ...")
    try:
        with open(os.path.join(sys.path[0], 'var/uid'), 'r') as file:
            content = file.read()
            if len(content or '') == 0:
                raise IOError(
                    "Nothing valid could be read from local UID file.")
            if content.split('\n')[0] == "ffffffff-ffff-ffff-ffff-ffffffffffff":
                logger.warning(
                    "Invalid ID, reserved for broadcast. Returning a nil UID.")
                return "00000000-0000-0000-0000-000000000000"
            logger.debug("Reusing existing UID: "+str(content))
            return content.split('\n')[0]
    except:
        pass
    logger.debug(
        "Existing UID not found. Creating a new one from system info ...")
    new_uid = ""
    try:
        with open("/sys/class/dmi/id/board_serial", 'r') as file:
            content = file.read()
            new_uid = content.split('\n')[0]
    except:
        pass
    if len(new_uid) == 0:
        try:
            with open("/sys/class/dmi/id/product_uuid", 'r') as file:
                content = file.read()
                new_uid = content.split('\n')[0]
        except:
            pass
    if len(new_uid) == 0:
        try:
            with open("/var/lib/dbus/machine-id", 'r') as file:
                content = file.read()
                new_uid = content.split('\n')[0]
        except:
            pass
    if len(new_uid) == 0:
        logger.warning(
            "Couldn't create a new UID from the system info. Creating a new one on-the-fly ...")
        try:
            new_uid = str(uuid.UUID(int=uuid.getnode()))
        except:
            logger.error(
                "There was an error while generating a new UID. Returning a nil UID.")
            return "00000000-0000-0000-0000-000000000000"
    try:
        os.makedirs(os.path.join(sys.path[0], 'var'), exist_ok=True)
        with open(os.path.join(sys.path[0], 'var/uid'), 'w') as file:
            file.write(new_uid)
            logger.debug("Wrote new UID to a local file: "+new_uid)
    except Exception as e:
        logger.error("There was an error while writing to the local UID file: " +
                     str(e)+". Returning a nil UID.")
        return "00000000-0000-0000-0000-000000000000"
    return new_uid


def validate_string_key(string):
    pattern = "^[A-Za-z0-9_-]*$"
    if type(string) is not str:
        logger.debug(
            "This data dict has a key which is not a string. No data was uploaded.")
        return False
    if len(string or '') == 0:
        logger.debug(
            "This data dict has an empty or invalid key. No data was uploaded.")
        return False
    if not bool(re.match(pattern, string)):
        logger.debug(
            "Invalid character detected in data dict keys. No data was uploaded.")
        return False
    return True


def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f} {unit}{suffix}"
        bytes /= factor


def get_now_utc_str():
    """
    Returns an ISO date string
    """
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def get_now_utc_obj():
    """
    Returns an ISO date obj
    """
    return datetime.strptime(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), '%Y-%m-%dT%H:%M:%SZ')


def get_ipv6_cidr(mask):
    """
    Returns the IPv6 short netmask from a long netmask input
    Returns None if inputted mask is not proper
    """
    bitCount = [0, 0x8000, 0xc000, 0xe000, 0xf000, 0xf800, 0xfc00, 0xfe00,
                0xff00, 0xff80, 0xffc0, 0xffe0, 0xfff0, 0xfff8, 0xfffc, 0xfffe, 0xffff]
    count = 0
    try:
        for w in mask.split(':'):
            if not w or int(w, 16) == 0:
                break
            count += bitCount.index(int(w, 16))
    except:
        return None
        logger.warning("Bad IPv6 netmask: "+mask)
    return count
