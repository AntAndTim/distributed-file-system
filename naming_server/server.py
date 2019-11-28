import json
import random
from os import environ

import redis
import requests
from flask import Flask, request, make_response, abort

app = Flask(__name__)

server_list = []
r = redis.StrictRedis(host=environ['REDIS_HOST'], port=environ['REDIS_PORT'], db=0)


def find_file(path_to_file):
    servers = json.loads(r.get(path_to_file))
    links = []
    for server in servers:
        links.append(f'http://{server["address"]}:{server["port"]}/{path_to_file}')
    return links


def upload_file(path_to_file):
    links = []
    for server in server_list:
        links.append(f'http://{server["address"]}:{server["port"]}/{path_to_file}')
    return links


def sort_server_list(list_of_servers):
    return sorted(list_of_servers, key=lambda x: x.space, reverse=True)


@app.route('/files/<path:path_to_file>', methods=['GET'])
def download(path_to_file: str):
    urls = find_file(path_to_file)
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
    r.set(path_to_file, server_list_to_string())
    return 'OK'


def server_list_to_string():
    out = "["
    for server in server_list:
        out += '{' + f'"address": "{server["address"]}", "port": {server["port"]}' + "},"
    out += "]"
    return out.replace(',]', ']')


@app.route('/files/<path:path_to_file>', methods=['DELETE'])
def delete(path_to_file: str):
    urls = find_file(path_to_file)
    for url in urls:
        requests.delete(url)
    r.delete(path_to_file)
    return 'OK'


@app.route('/server', methods=['POST'])
def add_server():
    server_data = request.get_json(True)
    server_list.append(server_data)
    return 'OK'


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
