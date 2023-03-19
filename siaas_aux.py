# Intelligent System for Automation of Security Audits (SIAAS)
# Server - Auxiliary functions
# By João Pedro Seara, 2023

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
    Grabs all local DBs (dicts) from the module list and concatenates them
    Returns False if it fails
    """
    merged_dict = {}
    for module in sorted(set(modules.lower().split(','))):
        module = module.strip()
        try:
            module_dict = read_from_local_file(
                os.path.join(sys.path[0], 'var/'+str(module)+'.db'))
            if module_dict != None:
                next_dict_to_merge = {}
                next_dict_to_merge[module] = module_dict
                merged_dict = dict(
                    list(merged_dict.items())+list(next_dict_to_merge.items()))
        except:
            logger.error("Couldn't merge dict: " +
                         str(next_dict_to_merge))
            return False

    return merged_dict


def merge_configs_from_upstream(local_dict=os.path.join(sys.path[0], 'var/config_local.db'), output=os.path.join(sys.path[0], 'var/config.db'), upstream_dict={}):
    """
    Merges the upstream configs to the local configs, after removing protected configurations from the upstream configs
    If the config disappears from the server, it reverts to the local config
    In case of errors, no changes are made
    """
    local_config_dict = {}
    merged_config_dict = {}
    delta_dict = {}
    protected_configs = ["log_level", "mongo_collection", "mongo_db", "mongo_host", "mongo_port", "mongo_pwd", "mongo_user"]
    try:
        local_config_dict = get_config_from_configs_db(local_dict=local_dict)
        if type(upstream_dict) is not dict:
            raise TypeError("Upstream configs are invalid.")
        for p in protected_configs: # remove any protected configs from upstream dict
            for k in upstream_dict.copy().keys():
                if p.lower().strip() == k.lower().strip():
                    del(upstream_dict[k])
        if len(upstream_dict) > 0:
            merged_config_dict = dict(
                list(local_config_dict.items())+list(upstream_dict.items()))
            logger.debug(
                "The following configurations are being applied/overwritten from the server: "+str(upstream_dict))
        else:
            merged_config_dict = dict(
                list(local_config_dict.items()))
            logger.debug(
                "No configurations were found in the upstream dict. Using local configurations only.")
    except:
        logger.error(
            "Could not merge configurations from the upstream dict. Not doing any changes.")
        return False

    return write_to_local_file(output, dict(sorted(merged_config_dict.items(), key=lambda x: x[0].casefold() if len(x or "") > 0 else None)))


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
    The config key has its spaces removed from beginning or end, and all " and ' are removed
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
            line_uncommented = line.split('#')[0].strip()
            if len(line_uncommented) == 0:
                continue
            config_name = line_uncommented.split("=", 1)[0].strip()
            if not bool(re.match(pattern, config_name)):
                raise ValueError("Invalid character in config key.")
            config_value = line_uncommented.split("=", 1)[1].strip()
            config_dict[config_name] = config_value
        except:
            logger.warning(
                "Invalid line from local configuration file was ignored: "+str(line))
            continue

    return write_to_local_file(output, dict(sorted(config_dict.items(), key=lambda x: x[0].casefold() if len(x or "") > 0 else None)))


def get_dict_current_server_configs(collection):
    """
    Reads server configs from the Mongo DB collection
    Returns a list of records. Returns False if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    out_dict = {}
    try:
        cursor = collection.find(
            {'$and': [{"payload": {'$exists': True}}, {
                "scope": "server_configs"}, {"destiny": "server"}]}
        ).sort('_id', -1).limit(1)
        results = list(cursor)
    except Exception as e:
        logger.error("Can't read data from the DB server: "+str(e))
        return False

    for r in results:
        try:
            if r["destiny"] == "server":
                out_dict = r["payload"]
                out_dict = dict(sorted(
                    out_dict.items(), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))
        except:
            logger.debug(
                "Ignoring invalid entry when grabbing server configs.")

    return out_dict


def create_or_update_server_configs(collection, config_dict={}):
    """
    Receives a dict with server configs, validates it, and calls the mongodb insertion function to insert it
    Returns True if all OK; False if NOK
    """

    logger.info("Server configs received and now being uploaded to the DB ...")

    if type(config_dict) is not dict:
        logger.error(
            "No valid server configuration dict received. No server configs were uploaded.")
        return False

    if "#" in str(config_dict):
        logger.error(
            "Detected invalid character '#' in the input server configuration dict keys or values. No server configs were uploaded.")
        return False

    for k in config_dict.keys():
        if not validate_string_key(k):
            logger.error("Server configurations dict has an invalid key: " +
                         k+". No server configs were uploaded.")
            return False

    # Turn all keys to lowercase, also ignore "nickname" and "description" if the target is broadcast:
    corrected_config_dict = {}
    for k in config_dict.keys():
        formatted_key = k.lower().strip()
        corrected_config_dict[formatted_key] = config_dict[k]

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
    complete_dict["scope"] = "server_configs"
    complete_dict["origin"] = "server_"+siaas_uid.lower()
    complete_dict["destiny"] = "server"
    complete_dict["payload"] = dict(sorted(corrected_config_dict.items(
    ), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))
    complete_dict["timestamp"] = get_now_utc_obj()

    result = create_or_update_in_mongodb_collection(collection, complete_dict)

    logger.info("Server configs upload to the DB finished.")

    return result


def upload_agent_data(collection, agent_uid=None, data_dict={}):
    """
    Receives a dict with agent data, validates it, and calls the mongodb insertion function to insert it
    Returns True if all OK; False if NOK
    """

    logger.info(
        "Agent data received and now being uploaded to the DB ["+str(agent_uid)+"] ...")

    if type(data_dict) is not dict:
        logger.error(
            "No valid agent data dict received. No agent data was uploaded.")
        return False

    for k in data_dict.keys():
        if not validate_string_key(k):
            logger.error("Agent data dict has an invalid key: " +
                         k+". No agent data was uploaded.")
            return False

    if not validate_string_key(agent_uid):
        logger.error("Agent UID '"+uid +
                     "' is not valid. No agent data was uploaded.")
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
    complete_dict["origin"] = "agent_"+agent_uid.lower()
    complete_dict["destiny"] = "server"
    complete_dict["payload"] = data_dict
    complete_dict["timestamp"] = get_now_utc_obj()

    result = insert_in_mongodb_collection(collection, complete_dict)

    logger.info("Agent data upload to the DB finished ["+str(agent_uid)+"].")

    return result


def create_or_update_agent_configs(collection, agent_uid=None, config_dict={}):
    """
    Receives a dict with agent configs, validates it, and calls the mongodb insertion function to insert it
    Returns True if all OK; False if NOK
    """

    logger.info(
        "Agent configs received and now being uploaded to the DB ["+str(agent_uid)+"] ...")

    if type(config_dict) is not dict:
        logger.error(
            "No valid agent configuration dict received. No agent configs were uploaded.")
        return False

    if "#" in str(config_dict):
        logger.error(
            "Detected invalid character '#' in the input agent configuration dict keys or values. No agent configs were uploaded.")
        return False

    for k in config_dict.keys():
        if not validate_string_key(k):
            logger.error("Agent configurations dict has an invalid key: " +
                         k+". No agent configs were uploaded.")
            return False

    # Turn all keys to lowercase, also ignore "nickname" and "description" if the target is broadcast:
    corrected_config_dict = {}
    for k in config_dict.keys():
        formatted_key = k.lower().strip()
        if (formatted_key == "nickname" or formatted_key == "description") and agent_uid == "ffffffff-ffff-ffff-ffff-ffffffffffff":
            logger.warning("Ignoring '"+formatted_key +
                           "' key from broadcast configuration insertion.")
            continue
        corrected_config_dict[formatted_key] = config_dict[k]

    siaas_uid = get_or_create_unique_system_id()

    result = True
    for u in agent_uid.split(','):
        uid = u.strip()

        if not validate_string_key(uid):
            logger.error("Agent UID '"+uid +
                         "' is not valid. No agent configs were uploaded.")
            result = False
            continue

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
        complete_dict["origin"] = "server_"+siaas_uid.lower()
        complete_dict["destiny"] = "agent_"+uid.lower()
        complete_dict["payload"] = dict(sorted(corrected_config_dict.items(
        ), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))
        complete_dict["timestamp"] = get_now_utc_obj()

        if not create_or_update_in_mongodb_collection(collection, complete_dict):
            result = False

    logger.info(
        "Agent configs upload to the DB finished ["+str(agent_uid)+"].")

    return result


def get_dict_active_agents(collection, sort_by="date"):
    """
    Reads a list of active agents. Returns nickname and description if they exist in configs DB
    Returns a list of records. Returns False if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    out_dict = {}

    try:
        cursor = collection.aggregate([
            {"$match": {"origin": {"$regex": "^agent_"}}},
            {"$group": {"_id": {"origin": "$origin"}, "origin": {
                "$last": "$origin"}, "timestamp": {"$last": "$timestamp"}}},
            {"$sort": {"timestamp": -1}}
        ])
        results = list(cursor)
    except Exception as e:
        logger.error("Can't read data from the DB server: "+str(e))
        return False

    for r in results:
        try:
            uid = r["origin"].split("_", 1)[1]
            out_dict[uid] = {}
            try:
                out_dict[uid]["nickname"] = str(get_dict_current_agent_configs(
                    collection, agent_uid=uid, merge_broadcast=False)[uid]["nickname"])
            except:
                pass
            try:
                out_dict[uid]["description"] = str(get_dict_current_agent_configs(
                    collection, agent_uid=uid, merge_broadcast=False)[uid]["description"])
            except:
                pass
            out_dict[uid]["last_seen"] = r["timestamp"].strftime(
                '%Y-%m-%dT%H:%M:%SZ')
        except:
            logger.debug(
                "Ignoring invalid entry when grabbing active agents data.")

    if sort_by == "agent":
        out_dict = dict(sorted(
            out_dict.items(), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))

    return out_dict


def get_dict_history_agent_data(collection, agent_uid=None, module=None, limit_outputs=99999, days=99999, sort_by="date", older_first=False, hide_empty=False):
    """
    Reads historical agent data from the Mongo DB collection
    We can select a list of agents and modules to display
    We can sort, select a day limit, limit outputs, order by older records first, and hide empty records
    Returns a list of records. Returns False if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    out_dict = {}

    if sort_by.lower() == "agent":
        sort_field = "origin"
    else:
        sort_field = "_id"

    if older_first:
        id_sort_type = 1
    else:
        id_sort_type = -1

    if agent_uid == None:
        try:
            if(int(limit_outputs) < 0):
                limit_outputs = 0
            last_d = datetime.utcnow() - timedelta(days=int(days))
            cursor = collection.find(
                {'$and': [{"payload": {'$exists': True}}, {"scope": "agent_data"}, {"timestamp": {"$gte": last_d}}
                          ]}
            ).sort('_id', id_sort_type).limit(int(limit_outputs))
            results = list(cursor)
        except Exception as e:
            logger.error("Can't read data from the DB server: "+str(e))
            return False

    else:
        results = []
        agent_list = []
        for u in agent_uid.split(','):
            agent_list.append("agent_"+u.strip().lower())
        try:
            if(int(limit_outputs) < 0):
                limit_outputs = 0
            last_d = datetime.utcnow() - timedelta(days=int(days))
            cursor = collection.find(
                {'$and': [{"payload": {'$exists': True}}, {"scope": "agent_data"}, {
                    "timestamp": {"$gte": last_d}}, {"origin": {'$in': agent_list}}]}
            ).sort('_id', id_sort_type).limit(int(limit_outputs))
            results = results+list(cursor)
        except Exception as e:
            logger.error("Can't read data from the DB server: "+str(e))
            return False

    if sort_field == "origin":
        for r in results:
            try:
                if r["origin"].startswith("agent_"):
                    uid = r["origin"].split("_", 1)[1]
                    timestamp = r["timestamp"].strftime('%Y-%m-%dT%H:%M:%SZ')
                    if uid not in out_dict.keys():
                        out_dict[uid] = {}
                    if module == None:
                        out_dict[uid][timestamp] = r["payload"]
                    else:
                        out_dict[uid][timestamp] = {}
                        for m in sorted(set(module.lower().split(','))):
                            mod = m.strip()
                            if mod in r["payload"].keys():
                                out_dict[uid][timestamp][mod] = r["payload"][mod]
                    if hide_empty:
                        for k in list(out_dict[uid][timestamp].keys()):
                            if len(out_dict[uid][timestamp][k]) == 0:
                                out_dict[uid][timestamp].pop(k, None)
                        if len(out_dict[uid][timestamp]) == 0:
                            out_dict[uid].pop(timestamp, None)
            except:
                logger.debug(
                    "Ignoring invalid entry when grabbing agent data.")
        out_dict = dict(sorted(
            out_dict.items(), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))

    else:
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
                        for m in sorted(set(module.lower().split(','))):
                            mod = m.strip()
                            if mod in r["payload"].keys():
                                out_dict[timestamp][uid][mod] = r["payload"][mod]
                    out_dict[timestamp] = dict(sorted(out_dict[timestamp].items(
                    ), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))
                    if hide_empty:
                        for k in list(out_dict[timestamp][uid].keys()):
                            if len(out_dict[timestamp][uid][k]) == 0:
                                out_dict[timestamp][uid].pop(k, None)
                        if len(out_dict[timestamp][uid]) == 0:
                            out_dict[timestamp].pop(uid, None)
            except:
                logger.debug(
                    "Ignoring invalid entry when grabbing agent data.")

    if hide_empty:
        for k in list(out_dict.keys()):
            if len(out_dict[k]) == 0:
                out_dict.pop(k, None)

    return out_dict


def get_dict_current_agent_data(collection, agent_uid=None, module=None):
    """
    Reads agent data from the Mongo DB collection
    We can select a list of agents and modules to display
    Returns a list of records. Returns False if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    out_dict = {}

    if agent_uid == None:
        try:
            cursor = collection.aggregate([
                {"$match": {
                    '$and': [{"origin": {"$regex": "^agent_"}}, {"scope": "agent_data"}]}},
                {"$group": {"_id": {"origin": "$origin"}, "scope": {"$last": "$scope"}, "origin": {"$last": "$origin"}, "destiny": {
                    "$last": "$destiny"}, "payload": {"$last": "$payload"}, "timestamp": {"$last": "$timestamp"}}},
                {"$sort": {"origin": 1}}
            ])
            results = list(cursor)
        except Exception as e:
            logger.error("Can't read data from the DB server: "+str(e))
            return False

    else:
        results = []
        for u in agent_uid.split(','):
            uid = u.strip().lower()
            try:
                cursor = collection.find(
                    {'$and': [{"payload": {'$exists': True}}, {
                        "scope": "agent_data"}, {"origin": "agent_"+uid}]}
                ).sort('_id', -1).limit(1)
                results = results+list(cursor)
            except Exception as e:
                logger.error("Can't read data from the DB server: "+str(e))
                return False

    for r in results:
        try:
            if r["origin"].startswith("agent_"):
                uid = r["origin"].split("_", 1)[1]
                if module == None:
                    out_dict[uid] = r["payload"]
                else:
                    out_dict[uid] = {}
                    for m in sorted(set(module.lower().split(','))):
                        mod = m.strip()
                        if mod in r["payload"].keys():
                            out_dict[uid][mod] = r["payload"][mod]
        except:
            logger.debug("Ignoring invalid entry when grabbing agent data.")

    out_dict = dict(sorted(
        out_dict.items(), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))

    return out_dict


def get_dict_current_agent_configs(collection, agent_uid=None, merge_broadcast=False):
    """
    Reads agent configs from the Mongo DB collection
    We can select a list of agents and modules to display
    Returns a list of records. Returns False if data can't be read
    """
    logger.debug("Reading data from the DB server ...")
    out_dict = {}

    if agent_uid == None:
        try:
            cursor = collection.aggregate([
                {"$match": {'$and': [{"destiny": {"$regex": "^agent_"}}, {
                    "scope": "agent_configs"}]}},
                {"$group": {"_id": {"destiny": "$destiny"}, "scope": {"$last": "$scope"}, "origin": {"$last": "$origin"}, "destiny": {
                    "$last": "$destiny"}, "payload": {"$last": "$payload"}, "timestamp": {"$last": "$timestamp"}}},
                {"$sort": {"destiny": 1}}
            ])
            results = list(cursor)
        except Exception as e:
            logger.error("Can't read data from the DB server: "+str(e))
            return False

    else:
        results = []
        for u in agent_uid.split(','):
            uid = u.strip().lower()
            try:
                cursor = collection.find(
                    {'$and': [{"payload": {'$exists': True}}, {
                        "scope": "agent_configs"}, {"destiny": "agent_"+uid}]}
                ).sort('_id', -1).limit(1)
                results = results+list(cursor)
            except Exception as e:
                logger.error("Can't read data from the DB server: "+str(e))
                return False

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
            return False

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
                out_dict[uid] = dict(sorted(out_dict[uid].items(
                ), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))
        except:
            logger.debug("Ignoring invalid entry when grabbing agent configs.")

    # We have to make sure that even if the agent UID doesn't exist in the config DB, we return the broadcast values if merge_broadcast is on
    if merge_broadcast and len(agent_uid or '') > 0:
        for u in agent_uid.split(','):
            try:
                uid = u.strip().lower()
                if uid not in out_dict.keys():
                    if len(results_bc) > 0:
                        out_dict[uid] = results_bc[0]["payload"]
                        out_dict[uid] = dict(sorted(out_dict[uid].items(
                        ), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))
            except:
                logger.debug(
                    "Ignoring invalid entry when grabbing agent configs.")

    out_dict = dict(sorted(
        out_dict.items(), key=lambda x: x[0].casefold() if len(x or "") > 0 else None))

    return out_dict


def delete_all_records_older_than(collection, scope=None, agent_uid=None, days_to_keep=99999):
    """
    Delete records older than n-days
    We can select a list of agent_uuids or scope, else it will pick all scopes and all records
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
            agent_list.append("agent_"+u.strip().lower())
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

    return count


def grab_vulns_from_agent_data_dict(agent_data_dict, target_host=None, report_type="vuln_only"):
    """
    Receives an agent data dict and returns a list of vulnerabilities, depending on report_type: 'all', 'vuln_only', 'exploit_vuln_only'
    Returns the vuln dict if all OK; Returns False if anything fails
    """
    if len(report_type or '') == 0:
        report_type = "vuln_only"

    new_dict = {}

    if report_type.lower() == "all":
        try:
            for a in agent_data_dict.keys():
                for b in agent_data_dict[a].keys():
                    if b == "portscanner":
                        for c in agent_data_dict[a][b].keys():
                            if len(target_host or '') > 0 and c not in target_host.split(','):
                                continue
                            if a not in new_dict.keys():
                                new_dict[a] = {}
                            if b not in new_dict[a].keys():
                                new_dict[a][b] = {}
                            new_dict[a][b][c] = agent_data_dict[a][b][c]
        except Exception as e:
            logger.error("Error generating new dict: "+str(e))
            return False
    else:
        try:
            for a in agent_data_dict.keys():
                for b in agent_data_dict[a].keys():
                    if b == "portscanner":
                        for c in agent_data_dict[a][b].keys():
                            if len(target_host or '') > 0 and c not in target_host.split(','):
                                continue
                            for d in agent_data_dict[a][b][c].keys():
                                if d == "last_check":
                                    if a not in new_dict.keys():
                                        new_dict[a] = {}
                                    if b not in new_dict[a].keys():
                                        new_dict[a][b] = {}
                                    if c not in new_dict[a][b].keys():
                                        new_dict[a][b][c] = {}
                                    new_dict[a][b][c]["last_check"] = agent_data_dict[a][b][c]["last_check"]
                                if d == "scanned_ports":
                                    for e in agent_data_dict[a][b][c][d].keys():
                                        for f in agent_data_dict[a][b][c][d][e].keys():
                                            if f == "scan_results":
                                                for g in agent_data_dict[a][b][c][d][e][f].keys():
                                                    for h in agent_data_dict[a][b][c][d][e][f][g].keys():
                                                        if "vulners" in h or "vulscan" in h:
                                                            if report_type.lower() == "exploit_vuln_only":
                                                                for i in agent_data_dict[a][b][c][d][e][f][g][h].keys():
                                                                    for j in agent_data_dict[a][b][c][d][e][f][g][h][i].keys():
                                                                        if "siaas_exploit_tag" in agent_data_dict[a][b][c][d][e][f][g][h][i][j]:
                                                                            if a not in new_dict.keys():
                                                                                new_dict[a] = {
                                                                                }
                                                                            if b not in new_dict[a].keys():
                                                                                new_dict[a][b] = {
                                                                                }
                                                                            if c not in new_dict[a][b].keys():
                                                                                new_dict[a][b][c] = {
                                                                                }
                                                                            if d not in new_dict[a][b][c].keys():
                                                                                new_dict[a][b][c][d] = {
                                                                                }
                                                                            if e not in new_dict[a][b][c][d].keys():
                                                                                new_dict[a][b][c][d][e] = {
                                                                                }
                                                                            if f not in new_dict[a][b][c][d][e].keys():
                                                                                new_dict[a][b][c][d][e][f] = {
                                                                                }
                                                                            if g not in new_dict[a][b][c][d][e][f].keys():
                                                                                new_dict[a][b][c][d][e][f][g] = {
                                                                                }
                                                                            if h not in new_dict[a][b][c][d][e][f][g].keys():
                                                                                new_dict[a][b][c][d][e][f][g][h] = {
                                                                                }
                                                                            if i not in new_dict[a][b][c][d][e][f][g][h].keys():
                                                                                new_dict[a][b][c][d][e][f][g][h][i] = {
                                                                                }
                                                                            new_dict[a][b][c][d][e][f][g][h][i][
                                                                                j] = agent_data_dict[a][b][c][d][e][f][g][h][i][j]
                                                            else:  # default to vuln_only
                                                                if a not in new_dict.keys():
                                                                    new_dict[a] = {
                                                                    }
                                                                if b not in new_dict[a].keys():
                                                                    new_dict[a][b] = {
                                                                    }
                                                                if c not in new_dict[a][b].keys():
                                                                    new_dict[a][b][c] = {
                                                                    }
                                                                if d not in new_dict[a][b][c].keys():
                                                                    new_dict[a][b][c][d] = {
                                                                    }
                                                                if e not in new_dict[a][b][c][d].keys():
                                                                    new_dict[a][b][c][d][e] = {
                                                                    }
                                                                if f not in new_dict[a][b][c][d][e].keys():
                                                                    new_dict[a][b][c][d][e][f] = {
                                                                    }
                                                                if g not in new_dict[a][b][c][d][e][f].keys():
                                                                    new_dict[a][b][c][d][e][f][g] = {
                                                                    }
                                                                new_dict[a][b][c][d][e][f][g][h] = agent_data_dict[a][b][c][d][e][f][g][h]
        except Exception as e:
            logger.error("Error generating new dict: "+str(e))
            return False

    return new_dict


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


def insert_in_mongodb_collection(collection, data_to_insert):
    """
    Inserts data (usually a dict) into a said collection
    Returns True if all was OK. Returns False if the insertion failed
    """
    logger.debug("Inserting data in the DB server ...")
    try:
        logger.debug("All data that will now be inserted in the database:\n" +
                     pprint.pformat(data_to_insert, sort_dicts=False))
        collection.insert_one(copy(data_to_insert))
        logger.debug("Data successfully inserted in the DB server.")
        return True
    except Exception as e:
        logger.error("Can't insert data in the DB server: "+str(e))
        return False


def create_or_update_in_mongodb_collection(collection, data_to_insert):
    """
    Creates or updates an object with data
    Returns 1 if all was OK. Returns -1 if the insertion failed
    """
    logger.debug("Creating or updating data in the DB server ...")
    try:
        logger.debug("All data that will now be created or updated in the database:\n" +
                     pprint.pformat(data_to_insert, sort_dicts=False))
        data = copy(data_to_insert)
        collection.find_one_and_update(
            {'destiny': data["destiny"], 'scope': data["scope"]}, {'$set': data}, upsert=True)
        logger.debug("Data successfully created or updated in the DB server.")
        return True
    except Exception as e:
        logger.error("Can't create or update data to the DB server: "+str(e))
        return False


def mongodb_ping(mongo_user="siaas", mongo_password="siaas", mongo_host="127.0.0.1:27017", mongo_db="siaas", mongo_collection="siaas"):
    """
    Returns True if the DB is alive, False if otherwise
    """
    logger.debug("Pinging the DB server at "+str(mongo_host)+" ...")
    try:
        uri = "mongodb://%s:%s@%s/%s" % (quote_plus(mongo_user),
                                         quote_plus(mongo_password), mongo_host, mongo_db)
        client = MongoClient(uri)
        eval("client."+mongo_db+".command('ping')")
        logger.debug("DB replied to ping.")
        return True
    except:
        logger.debug("DB didn't reply to ping.")
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
        logger.debug(
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
                     pprint.pformat(data_to_insert, sort_dicts=False))
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
    If this file does not exist or has no data, tries to generate an UID. If it has an invalid UID, it will return a nil UID
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
            return content.split('\n')[0].lower()
    except:
        pass
    logger.debug(
        "Existing UID not found. Creating a new one from system info ...")
    new_uid = ""
    try:
        with open("/sys/firmware/devicetree/base/serial-number", 'r') as file:  # Raspberry Pi serial
            content = file.read()
            new_uid = str(content.split('\n')[0].strip(
            ).strip('\x00'))
    except:
        pass
    if len(new_uid or '') == 0 or new_uid.upper() == "N/A":
        try:
            with open("/sys/class/dmi/id/board_serial", 'r') as file:
                content = file.read()
                new_uid = str(content.split('\n')[0].strip(
                ).strip('\x00'))
        except:
            pass
    if len(new_uid or '') == 0 or new_uid.upper() == "N/A":
        try:
            with open("/sys/class/dmi/id/product_uuid", 'r') as file:
                content = file.read()
                new_uid = str(content.split('\n')[0].strip(
                ).strip('\x00'))
        except:
            pass
    # if len(new_uid or '') == 0 or new_uid.upper() == "N/A":
    #    try:
    #        with open("/var/lib/dbus/machine-id", 'r') as file:
    #            content = file.read()
    #            new_uid = str(content.split('\n')[0].strip().strip('\x00'))
    #    except:
    #        pass
    if len(new_uid or '') == 0 or new_uid.upper() == "N/A":
        logger.warning(
            "Couldn't create a new UID from the system info. Will create a new randomized UUID for this session only!")
        try:
            new_uid = "temp-"+str(uuid.UUID(int=uuid.getnode()))
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
                     str(e) + ". Returning a nil UID.")
        return "00000000-0000-0000-0000-000000000000"
    return new_uid.lower()


def validate_bool_string(input_string, default_output=False):
    """
    Validates string format and if it's not empty and returns a boolean
    """
    if type(default_output) is not bool:
        return None
    if default_output == False:
        if len(input_string or '') > 0:
            if input_string.lower() == "true":
                return True
        return False
    if default_output == True:
        if len(input_string or '') > 0:
            if input_string.lower() == "false":
                return False
        return True


def validate_string_key(string):
    """
    Validates the proper format of a string configuration key and returns a boolean
    """
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


def convert_sec_to_pretty_format(seconds):
    """
    Converts a number of seconds to a pretty day/hr/min/sec format
    """
    time = float(seconds)
    day = time // (24 * 3600)
    time = time % (24 * 3600)
    hour = time // 3600
    time %= 3600
    mins = time // 60
    time %= 60
    secs = time
    if day != 0:
        return "%d day %d hr %d min %d sec" % (day, hour, mins, secs)
    if hour != 0:
        return "%d hr %d min %d sec" % (hour, mins, secs)
    if mins != 0:
        return "%d min %d sec" % (mins, secs)
    else:
        return "%d sec" % (secs)


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
