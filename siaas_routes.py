from __main__ import app, get_db_collection
from flask import jsonify, request, abort
import siaas_aux
import json
import os
import sys

app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

@app.route('/', strict_slashes=False)
@app.route('/index', strict_slashes=False)
def index():
    output = {
        'name': 'Sistema Inteligente para Automação de Auditorias de Segurança',
        'module': 'Server',
        'author': 'João Pedro Seara',
        'supervisor': 'Carlos Serrão'
    }
    return jsonify(
        {
            'output': output,
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )


@app.route('/siaas-server', methods=['GET'], strict_slashes=False)
def siaas_server():
    module = request.args.get('module', default='*', type=str)
    all_existing_modules = "platform,neighborhood,portscanner,config"
    for m in module.split(','):
        if m.lstrip().rstrip() == "*":
            module = all_existing_modules
    output = siaas_aux.merge_module_dicts(module)
    try:
        output["config"]["mongo_pwd"] = '*' * \
            len(output["config"]["mongo_pwd"])
    except:
        pass

    return jsonify(
        {
            'output': output,
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )


@app.route('/siaas-server/agents', methods = ['GET'], strict_slashes=False)
def agents():
    collection = get_db_collection()
    output = siaas_aux.get_dict_active_agents(collection)
    return jsonify(
        {
            'output': output,
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )

@app.route('/siaas-server/agents/data', methods = ['GET'], strict_slashes=False)
def agents_data():
    module = request.args.get('module', default='*', type=str)
    for m in module.split(','):
        if m.lstrip().rstrip() == "*":
            module = None
    collection = get_db_collection()
    output = siaas_aux.get_dict_current_agent_data(collection, module=module)
    return jsonify(
        {
            'output': output,
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )

@app.route('/siaas-server/agents/data/<agent_uid>', methods = ['GET','POST','DELETE'], strict_slashes=False)
def agents_data_id(agent_uid):
    collection = get_db_collection()
    if request.method == 'GET':
        module = request.args.get('module', default='*', type=str)
        for m in module.split(','):
            if m.lstrip().rstrip() == "*":
                module = None
        output = siaas_aux.get_dict_current_agent_data(collection, agent_uid=agent_uid, module=module)
        return jsonify(
          {
            'output': output,
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
          }
        )
    if request.method == 'POST':
        test_dict={'platform': {'uid': '0924aa8b-6dc9-4fec-9716-d1601fc8b6c6', 'version': '0.0.1', 'system_info': {'cpu': {'percentage': '27.8 %', 'physical_cores': 4, 'total_cores': 4, 'current_freq': '1992.00 MHz'}, 'memory': {'percentage': '7.2 %', 'total': '7.77 GB', 'used': '320.58 MB', 'available': '7.21 GB', 'swap': {'percentage': '0.0 %', 'total': '4.00 GB', 'used': '0.00 B', 'free': '4.00 GB'}}, 'io': {'volumes': {'/dev/mapper/ubuntu--vg-ubuntu--lv': {'partition_mountpoint': '/', 'partition_fstype': 'ext4', 'usage': {'percentage': '36.3 %', 'total': '22.47 GB', 'used': '7.72 GB', 'free': '13.58 GB'}}, '/dev/vda2': {'partition_mountpoint': '/boot', 'partition_fstype': 'ext4', 'usage': {'percentage': '5.8 %', 'total': '1.90 GB', 'used': '105.74 MB', 'free': '1.68 GB'}}}, 'total_read': '795.70 MB', 'total_written': '3.63 GB'}, 'network': {'interfaces': {'enp1s0': ['192.168.122.172/24', '2a01:7c8:aab5:4cd::1/48'], 'enp7s0': ['192.168.123.1/24', '2a01:7c8:aab5:4cd::10/48']}, 'total_received': '1.07 GB', 'total_sent': '501.24 MB'}, 'last_boot': '2022-10-26T22:25:54Z'}, 'last_check': '2022-10-27T14:03:30Z'}, 'neighborhood': {}, 'portscanner': {}, 'config': {'datatransfer_loop_interval_sec': '120', 'log_level': 'debug', 'manual_hosts': '109.51.61.78,sapo.pt,google.com,focal62', 'mongo_collection': 'siaas', 'mongo_db': 'siaas', 'mongo_host': '192.168.122.172', 'mongo_port': '27017', 'mongo_pwd': 'siaas', 'mongo_user': 'siaas', 'neighborhood_arp_timeout_sec': '5', 'neighborhood_loop_interval_sec': '60', 'nmap_portscan_timeout_sec': '300', 'nmap_scripts': 'nmap-vulners,vulscan,vuln,http-csrf,http-sherlock,http-slowloris-attack,http-vmware-path-vuln,http-passwd,http-internal-ip-disclosure,http-vuln-cve2013-0156', 'nmap_sysinfo_timeout_sec': '600', 'platform_loop_interval_sec': '60', 'portscanner_loop_interval_sec': '60'}}
        output = siaas_aux.upload_agent_data(collection, agent_uid=agent_uid, data_dict=test_dict)
        if output:
           status="success"
        else:
           status="failure"
        return jsonify(
        {
            'status': status,
            'time': siaas_aux.get_now_utc_str()
        }
    )
    if request.method == 'DELETE':
        days = request.args.get('days', default=0, type=int)
        output = siaas_aux.delete_all_records_older_than(collection, scope="agent_data", agent_uid=agent_uid, days_to_keep=days)
        if output:
           status="success"
           count_deleted=int(output)
        else:
           status="failure"
           count_deleted=0
        return jsonify(
        {
            'deleted_count': count_deleted,
            'status': status,
            'time': siaas_aux.get_now_utc_str()
        }
    )

@app.route('/siaas-server/agents/configs', methods = ['GET'], strict_slashes=False)
def agents_configs():
    collection = get_db_collection()
    merge_broadcast = request.args.get('merge_broadcast', default=0, type=int)
    output = siaas_aux.get_dict_current_agent_configs(collection, merge_broadcast=merge_broadcast)
    return jsonify(
        {
            'output': output,
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )

@app.route('/siaas-server/agents/configs/<agent_uid>', methods = ['GET','POST','DELETE'], strict_slashes=False)
def agents_configs_id(agent_uid):
    collection = get_db_collection()
    if request.method == 'GET':
        merge_broadcast = request.args.get('merge_broadcast', default=0, type=int)
        output = siaas_aux.get_dict_current_agent_configs(collection, agent_uid=agent_uid, merge_broadcast=merge_broadcast)
        return jsonify(
          {
            'output': output,
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
          }
        )
    if request.method == 'POST':
        test_dict = {
        "datatransfer_loop_interval_sec": 45,
        "disable_portscanner": "false",
        "silent_mode": "false"
        }
        output = siaas_aux.create_or_update_agent_configs(collection, agent_uid=agent_uid, config_dict=test_dict)
        if output:
           status="success"
        else:
           status="failure"
        return jsonify(
        {
            'status': status,
            'time': siaas_aux.get_now_utc_str()
        }
    )
    if request.method == 'DELETE':
        output = siaas_aux.delete_all_records_older_than(collection, scope="agent_configs", agent_uid=agent_uid, days_to_keep=0)
        if output:
           status="success"
           count_deleted=int(output)
        else:
           status="failure"
           count_deleted=0
        return jsonify(
        {
            'deleted_count': count_deleted,
            'status': status,
            'time': siaas_aux.get_now_utc_str()
        }
    )

@app.route('/siaas-server/agents/historical', methods = ['GET'], strict_slashes=False)
def agents_historical():
    module = request.args.get('module', default='*', type=str)
    limit_outputs = request.args.get('limit', default=25, type=int)
    days = request.args.get('days', default=7, type=int)
    for m in module.split(','):
        if m.lstrip().rstrip() == "*":
            module = None
    collection = get_db_collection()
    if limit_outputs <= 0 or days <=0:
        output={}
    else:
        output = siaas_aux.get_dict_historical_agent_data(collection, module=module, limit_outputs=limit_outputs, days=days)
    return jsonify(
        {
            'output': output,
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )

@app.route('/siaas-server/agents/historical/<agent_uid>', methods = ['GET'], strict_slashes=False)
def agents_historical_id(agent_uid):
    module = request.args.get('module', default='*', type=str)
    limit_outputs = request.args.get('limit', default=25, type=int)
    days = request.args.get('days', default=7, type=int)
    for m in module.split(','):
        if m.lstrip().rstrip() == "*":
            module = None
    collection = get_db_collection()
    if limit_outputs <= 0 or days <=0:
        output={}
    else:
        output = siaas_aux.get_dict_historical_agent_data(collection, agent_uid=agent_uid, module=module, limit_outputs=limit_outputs, days=days)
    return jsonify(
        {
            'output': output,
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )
