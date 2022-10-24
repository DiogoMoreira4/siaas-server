from __main__ import app, get_db_collection
from flask import jsonify, request, abort
import siaas_aux
import json
import os
import sys

app.config['JSON_AS_ASCII'] = False


@app.route('/', strict_slashes=False)
@app.route('/index', strict_slashes=False)
def index():
    siaas = {
        'name': 'Sistema Inteligente para Automação de Auditorias de Segurança',
        'module': 'Server',
        'author': 'João Pedro Seara',
        'supervisor': 'Carlos Serrão'
    }
    return jsonify(
        {
            'status': 'success',
            'total_entries': len(siaas),
            'time': siaas_aux.get_now_utc_str(),
            'output': siaas
        }
    )


@app.route('/siaas-server', methods=['GET'], strict_slashes=False)
def siaas_server():
    module = request.args.get('module', default='*', type=str)
    all_existing_modules = "config,neighborhood,platform,portscanner"
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
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str(),
            'output': output
        }
    )


@app.route('/siaas-server/agents', methods = ['GET'], strict_slashes=False)
def agents():
    collection = get_db_collection()
    output = siaas_aux.get_dict_active_agents(collection)
    return jsonify(
        {
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str(),
            'output': output
        }
    )

@app.route('/siaas-server/agents/data', methods = ['GET'], strict_slashes=False)
def agents_data():
    module = request.args.get('module', default='*', type=str)
    all_existing_modules = "config,neighborhood,platform,portscanner"
    for m in module.split(','):
        if m.lstrip().rstrip() == "*":
            module = all_existing_modules
    collection = get_db_collection()
    output = siaas_aux.get_dict_current_agent_data(collection, module=module)
    return jsonify(
        {
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str(),
            'output': output
        }
    )

@app.route('/siaas-server/agents/data/<agent_uid>', methods = ['GET','POST'], strict_slashes=False)
def agents_data_id(agent_uid):
    if request.method == 'GET':
        module = request.args.get('module', default='*', type=str)
        for m in module.split(','):
            if m.lstrip().rstrip() == "*":
                module = None
        collection = get_db_collection()
        output = siaas_aux.get_dict_current_agent_data(collection, agent_uid=agent_uid, module=module)
    if request.method == 'POST':
        pass
    # TODO: POST - AGENT UPLOAD LATEST DATA
    return jsonify(
        {
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str(),
            'output': output
        }
    )

@app.route('/siaas-server/agents/configs', methods = ['GET'], strict_slashes=False)
def agents_configs():
    collection = get_db_collection()
    output = siaas_aux.get_dict_current_agent_configs(collection, include_broadcast=True)
    return jsonify(
        {
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str(),
            'output': output
        }
    )

@app.route('/siaas-server/agents/configs/<agent_uid>', methods = ['GET'], strict_slashes=False)
def agents_configs_id(agent_uid):
    if request.method == 'GET':
        collection = get_db_collection()
        output = siaas_aux.get_dict_current_agent_configs(collection, agent_uid=agent_uid, include_broadcast=False)
    if request.method == 'POST':
        pass
    # TODO: POST - SERVER POST LATEST CONFIGS
    return jsonify(
        {
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str(),
            'output': output
        }
    )

@app.route('/siaas-server/agents/historical', methods = ['GET'], strict_slashes=False)
def agents_historical():
    module = request.args.get('module', default='*', type=str)
    limit_outputs = request.args.get('limit', default=10, type=int)
    all_existing_modules = "config,neighborhood,platform,portscanner"
    for m in module.split(','):
        if m.lstrip().rstrip() == "*":
            module = None
    collection = get_db_collection()
    if limit_outputs <= 0:
        output={}
    else:
        output = siaas_aux.get_dict_historical_agent_data(collection, module=module, limit_outputs=limit_outputs)
    return jsonify(
        {
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str(),
            'output': output
        }
    )

@app.route('/siaas-server/agents/historical/<agent_uid>', methods = ['GET'], strict_slashes=False)
def agents_historical_id(agent_uid):
    module = request.args.get('module', default='*', type=str)
    limit_outputs = request.args.get('limit', default=10, type=int)
    for m in module.split(','):
        if m.lstrip().rstrip() == "*":
            module = None
    collection = get_db_collection()
    if limit_outputs <= 0:
        output={}
    else:
        output = siaas_aux.get_dict_historical_agent_data(collection, agent_uid=agent_uid, module=module, limit_outputs=limit_outputs)
    return jsonify(
        {
            'status': 'success',
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str(),
            'output': output
        }
    )
