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
        pass
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
        pass
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