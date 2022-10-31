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
    if output:
        status = "success"
    else:
        status = "failure"
        output = {}
    try:
        output["config"]["mongo_pwd"] = '*' * \
            len(output["config"]["mongo_pwd"])
    except:
        pass
    try:
        output["config"]["api_pwd"] = '*' * \
            len(output["config"]["api_pwd"])
    except:
        pass
    return jsonify(
        {
            'output': output,
            'status': status,
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )


@app.route('/siaas-server/agents', methods=['GET'], strict_slashes=False)
def agents():
    collection = get_db_collection()
    output = siaas_aux.get_dict_active_agents(collection)
    if output:
        status = "success"
    else:
        status = "failure"
        output = {}
    return jsonify(
        {
            'output': output,
            'status': status,
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )


@app.route('/siaas-server/agents/data', methods=['GET'], strict_slashes=False)
def agents_data():
    module = request.args.get('module', default='*', type=str)
    for m in module.split(','):
        if m.lstrip().rstrip() == "*":
            module = None
    collection = get_db_collection()
    output = siaas_aux.get_dict_current_agent_data(collection, module=module)
    if output:
        status = "success"
    else:
        status = "failure"
        output = {}
    return jsonify(
        {
            'output': output,
            'status': status,
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )


@app.route('/siaas-server/agents/data/<agent_uid>', methods=['GET', 'POST', 'DELETE'], strict_slashes=False)
def agents_data_id(agent_uid):
    collection = get_db_collection()
    if request.method == 'GET':
        module = request.args.get('module', default='*', type=str)
        for m in module.split(','):
            if m.lstrip().rstrip() == "*":
                module = None
        output = siaas_aux.get_dict_current_agent_data(
            collection, agent_uid=agent_uid, module=module)
        if output:
            status = "success"
        else:
            status = "failure"
            output = {}
        return jsonify(
            {
                'output': output,
                'status': status,
                'total_entries': len(output),
                'time': siaas_aux.get_now_utc_str()
            }
        )
    if request.method == 'POST':
        content = request.json
        output = siaas_aux.upload_agent_data(
            collection, agent_uid=agent_uid, data_dict=content)
        if output:
            status = "success"
        else:
            status = "failure"
        return jsonify(
            {
                'status': status,
                'time': siaas_aux.get_now_utc_str()
            }
        )
    if request.method == 'DELETE':
        days = request.args.get('days', default=0, type=int)
        output = siaas_aux.delete_all_records_older_than(
            collection, scope="agent_data", agent_uid=agent_uid, days_to_keep=days)
        if output:
            status = "success"
            count_deleted = int(output)
        else:
            status = "failure"
            count_deleted = 0
        return jsonify(
            {
                'deleted_count': count_deleted,
                'status': status,
                'time': siaas_aux.get_now_utc_str()
            }
        )


@app.route('/siaas-server/agents/configs', methods=['GET'], strict_slashes=False)
def agents_configs():
    collection = get_db_collection()
    merge_broadcast = request.args.get('merge_broadcast', default=0, type=int)
    output = siaas_aux.get_dict_current_agent_configs(
        collection, merge_broadcast=merge_broadcast)
    if output:
        status = "success"
    else:
        status = "failure"
        output = {}
    return jsonify(
        {
            'output': output,
            'status': status,
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )


@app.route('/siaas-server/agents/configs/<agent_uid>', methods=['GET', 'POST', 'DELETE'], strict_slashes=False)
def agents_configs_id(agent_uid):
    collection = get_db_collection()
    if request.method == 'GET':
        merge_broadcast = request.args.get(
            'merge_broadcast', default=0, type=int)
        output = siaas_aux.get_dict_current_agent_configs(
            collection, agent_uid=agent_uid, merge_broadcast=merge_broadcast)
        if output:
            status = "success"
        else:
            status = "failure"
            output = {}
        return jsonify(
            {
                'output': output,
                'status': status,
                'total_entries': len(output),
                'time': siaas_aux.get_now_utc_str()
            }
        )
    if request.method == 'POST':
        content = request.json
        output = siaas_aux.create_or_update_agent_configs(
            collection, agent_uid=agent_uid, config_dict=content)
        if output:
            status = "success"
        else:
            status = "failure"
        return jsonify(
            {
                'status': status,
                'time': siaas_aux.get_now_utc_str()
            }
        )
    if request.method == 'DELETE':
        output = siaas_aux.delete_all_records_older_than(
            collection, scope="agent_configs", agent_uid=agent_uid, days_to_keep=0)
        if output:
            status = "success"
            count_deleted = int(output)
        else:
            status = "failure"
            count_deleted = 0
        return jsonify(
            {
                'deleted_count': count_deleted,
                'status': status,
                'time': siaas_aux.get_now_utc_str()
            }
        )


@app.route('/siaas-server/agents/history', methods=['GET'], strict_slashes=False)
def agents_history():
    module = request.args.get('module', default='*', type=str)
    limit_outputs = request.args.get('limit', default=0, type=int) # 0 equates to having no output limit (as per MongoDB spec)
    days = request.args.get('days', default=365, type=int)
    sort_by = request.args.get('sort', default="date", type=str)
    older_first = request.args.get('older', default=0, type=int)
    for m in module.split(','):
        if m.lstrip().rstrip() == "*":
            module = None
    collection = get_db_collection()
    if limit_outputs < 0:
        limit_outputs = 0 # a negative value makes MongoDB behave differently. Let's avoid that
    output = siaas_aux.get_dict_history_agent_data(
        collection, module=module, limit_outputs=limit_outputs, days=days, sort_by=sort_by, older_first=older_first)
    if output:
        status = "success"
    else:
        status = "failure"
        output = {}
    return jsonify(
        {
            'output': output,
            'status': status,
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )


@app.route('/siaas-server/agents/history/<agent_uid>', methods=['GET'], strict_slashes=False)
def agents_history_id(agent_uid):
    module = request.args.get('module', default='*', type=str)
    limit_outputs = request.args.get('limit', default=0, type=int) # 0 equates to having no output limit (as per MongoDB spec)
    days = request.args.get('days', default=365, type=int)
    sort_by = request.args.get('sort', default="date", type=str)
    older_first = request.args.get('older', default=0, type=int)
    for m in module.split(','):
            module = None
    collection = get_db_collection()
    if limit_outputs < 0:
        limit_outputs = 0 # a negative value makes MongoDB behave differently. Let's avoid that
    output = siaas_aux.get_dict_history_agent_data(
        collection, agent_uid=agent_uid, module=module, limit_outputs=limit_outputs, days=days, sort_by=sort_by, older_first=older_first)
    if output:
        status = "success"
    else:
        status = "failure"
        output = {}
    return jsonify(
        {
            'output': output,
            'status': status,
            'total_entries': len(output),
            'time': siaas_aux.get_now_utc_str()
        }
    )
