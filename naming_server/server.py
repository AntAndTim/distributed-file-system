import json
import logging
import random
from os import environ
from threading import Thread
from typing import List

import redis
import requests
from flask import Flask, request, make_response, abort, jsonify

from naming_server.models import Server, Encoder
from naming_server.scheduler import Scheduler

LOG = logging.getLogger('NamingServer')
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.FileHandler('naming_server.log'))
LOG.addHandler(logging.StreamHandler())

ACTIVE_SERVERS: List[Server] = []


def check_server_liveness():
    for server in ACTIVE_SERVERS:
        try:
            ping(server)
        except:
            ACTIVE_SERVERS.remove(server)
            LOG.info(f'Server {server} disconnected.')


SCHEDULER = Scheduler(check_server_liveness, ())

app = Flask(__name__)
app.logger = LOG
app.json_encoder = Encoder

REDIS_CONNECTOR = redis.StrictRedis(host=environ['REDIS_HOST'], port=environ['REDIS_PORT'], db=0)


@app.route('/files/<path:path_to_file>', methods=['GET'])
def download(path_to_file: str):
    urls = find_file(path_to_file)
    if len(urls) == 0:
        return 'SERVERS ARE UNAVAILABLE'
    get = requests.get(get_random_element(urls))
    if get.status_code != 200:
        abort(get.status_code)
    response = make_response(get.content)
    response.headers.set('Content-Disposition', 'attachment')
    return response


@app.route('/files/<path:path_to_file>', methods=['POST'])
def upload(path_to_file: str):
    urls = upload_file(path_to_file)
    for url in urls:
        requests.post(url, data=request.data)
    REDIS_CONNECTOR.set(path_to_file, str(ACTIVE_SERVERS))
    return jsonify('OK')


@app.route('/files/<path:path_to_file>', methods=['DELETE'])
def delete(path_to_file: str):
    urls = find_file(path_to_file)
    for url in urls:
        requests.delete(url)
    REDIS_CONNECTOR.delete(path_to_file)
    return jsonify('OK')


@app.route('/server', methods=['POST'])
def add_server():
    server_json = request.get_json(True)
    server = Server(server_json["address"], server_json["port"])
    ACTIVE_SERVERS.append(server)

    Thread(target=prepare_server, args=(server,)).start()
    return jsonify(server)


def prepare_server(server):
    with app.app_context():
        while True:
            try:
                ping(server)
            except:
                continue
            break
        response = requests.get(f'http://{server.address}:{server.port}/reset')
        if response.status_code != 200:
            raise Exception("Could not reset server")
        if len(ACTIVE_SERVERS) > 1:
            server_from = get_random_element(ACTIVE_SERVERS)
            requests.post(f'http://{server_from.address}:{server_from.port}/replicate', json=str(server))


@app.route('/initialize', methods=['GET'])
def initialize():
    result = {}
    for server in ACTIVE_SERVERS:
        response = requests.get(f'http://{server.address}:{server.port}/reset')
        result[str(server)] = response.text
    return jsonify(result)


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


def find_file(path_to_file):
    possible_servers = json.loads(REDIS_CONNECTOR.get(path_to_file))
    servers: List[Server] = []
    for server in possible_servers:
        servers.append(Server(server["address"], server["port"]))

    links = []
    for server in servers:
        try:
            ping(server)
            links.append(f'http://{server.address}:{server.port}/{path_to_file}')
        except:
            servers.remove(server)

    REDIS_CONNECTOR.set(path_to_file, str(servers))
    return links


def ping(server: Server):
    requests.get(f'http://{server.address}:{server.port}/ping')


def upload_file(path_to_file):
    global ACTIVE_SERVERS
    links = []
    for server in ACTIVE_SERVERS:
        try:
            ping(server)
            links.append(f'http://{server.address}:{server.port}/{path_to_file}')
        except:
            ACTIVE_SERVERS.pop(server)

    REDIS_CONNECTOR.set(path_to_file, str(ACTIVE_SERVERS))
    return links


def get_random_element(a_list):
    return a_list[int(random.uniform(0, len(a_list)))]


if __name__ == '__main__':
    SCHEDULER.start()
    app.run(host="0.0.0.0", port=80)
