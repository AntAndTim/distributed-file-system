import json
import random
from os import environ
from typing import List

import redis
import requests
from flask import Flask, request, make_response, abort, jsonify

from naming_server.models import Server, Encoder

app = Flask(__name__)
app.json_encoder = Encoder

ACTIVE_SERVERS: List[Server] = []
REDIS_CONNECTOR = redis.StrictRedis(host=environ['REDIS_HOST'], port=environ['REDIS_PORT'], db=0)


def find_file(path_to_file):
    possible_servers = json.loads(REDIS_CONNECTOR.get(path_to_file))
    servers: List[Server] = []
    for server in possible_servers:
        servers.append(Server(server["address"], server["port"]))

    links = []
    for server in servers:
        try:
            requests.get(f'http://{server.address}:{server.port}/ping')
            links.append(f'http://{server.address}:{server.port}/{path_to_file}')
        except:
            servers.remove(server)

    REDIS_CONNECTOR.set(path_to_file, str(servers))
    return links


def upload_file(path_to_file):
    global ACTIVE_SERVERS
    links = []
    for server in ACTIVE_SERVERS:
        try:
            requests.get(f'http://{server.address}:{server.port}/ping')
            links.append(f'http://{server.address}:{server.port}/{path_to_file}')
        except:
            ACTIVE_SERVERS.remove(server)

    REDIS_CONNECTOR.set(path_to_file, str(ACTIVE_SERVERS))
    return links


@app.route('/files/<path:path_to_file>', methods=['GET'])
def download(path_to_file: str):
    urls = find_file(path_to_file)
    if len(urls) == 0:
        return 'SERVERS ARE UNAVAILABLE'
    get = requests.get(urls[int(random.uniform(0, len(urls)))])
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
    return jsonify(server)


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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
