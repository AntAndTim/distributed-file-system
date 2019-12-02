import configparser
import json
import os
import shutil
from datetime import datetime
from os import DirEntry
from os.path import expanduser

import requests
from flask import Flask, send_from_directory, request, abort, jsonify

from common.models import Server

FILE_STORAGE_PATH = f'{expanduser("~")}/files/'

app = Flask(__name__)


@app.route('/<path:path_to_file>', methods=['GET'])
def download(path_to_file: str):
    return send_from_directory(FILE_STORAGE_PATH, path_to_file, as_attachment=True)


@app.route('/ping', methods=['GET'])
def ping():
    return 'OK'


@app.route('/info/<path:path_to_file>', methods=['GET'])
def info(path_to_file: str):
    if os.path.isdir(f'{FILE_STORAGE_PATH}{path_to_file}'):
        return jsonify(os.listdir(f'{FILE_STORAGE_PATH}{path_to_file}'))
    if '/' in path_to_file:
        scan_path = f'{FILE_STORAGE_PATH}{path_to_file[:path_to_file.rfind("/")]}'
        file_name = path_to_file[path_to_file.rfind('/') + 1]
    else:
        scan_path = FILE_STORAGE_PATH
        file_name = path_to_file
    with os.scandir(scan_path) as dir_entries:
        for entry in dir_entries:
            if entry.name == file_name:
                return jsonify(get_file_info(entry))
    return abort(404)


def get_file_info(entry: DirEntry):
    os.stat(entry.path)
    stat = entry.stat()
    return {
        'size': stat[6],
        'lastAccessed': datetime.fromtimestamp(stat[7]).strftime("%A, %B %d, %Y %I:%M:%S"),
        'lastModified': datetime.fromtimestamp(stat[8]).strftime("%A, %B %d, %Y %I:%M:%S"),
    }


@app.route('/<path:path_to_file>', methods=['POST'])
def upload(path_to_file: str):
    path_to_file = f'{FILE_STORAGE_PATH}{path_to_file}'
    is_directory = request.args.get('dir')
    if is_directory == '1':
        os.makedirs(path_to_file)
        return "OK"
    directory = path_to_file[:path_to_file.rfind('/')]
    if not os.path.exists(directory):
        os.makedirs(directory)
    file = open(path_to_file, 'wb')
    file.write(request.data)
    return 'OK'


@app.route('/replicate', methods=['POST'])
def replicate():
    server_json = json.loads(request.data)
    server = Server(server_json['address'], server_json['port'])

    files_to_send = []
    for address, dirs, files in os.walk(FILE_STORAGE_PATH):
        for file in files:
            relative_folder = address.replace(FILE_STORAGE_PATH, '')
            if relative_folder != '':
                relative_folder += '/'
            files_to_send.append(relative_folder + file)
    for file in files_to_send:
        requests.post(f'http://{server.address}:{server.port}/{file}', data=request.data)
    return 'OK'


@app.route('/<path:path_to_file>', methods=['DELETE'])
def delete(path_to_file: str):
    path_to_file = f'{FILE_STORAGE_PATH}/{path_to_file}'
    os.remove(path_to_file)
    return 'OK'


@app.route('/reset', methods=['GET'])
def reset():
    recreate_storage()
    total, used, free = shutil.disk_usage("/")
    return f'{free * 1e-9}Gb'


def recreate_storage():
    shutil.rmtree(FILE_STORAGE_PATH)
    os.mkdir(FILE_STORAGE_PATH)


if __name__ == '__main__':
    if not os.path.exists(FILE_STORAGE_PATH):
        os.mkdir(FILE_STORAGE_PATH)
    else:
        recreate_storage()
    config = configparser.ConfigParser()
    config.read('file_server.ini')
    ip = requests.get('http://checkip.dyndns.com/').text
    host = config["DEFAULT"]["host"]
    port = config["DEFAULT"]["port"]
    requests.post(url=f'http://{host}:{port}/server', json={
        "address": 'localhost',  # re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(ip).group(1)
        "port": 8080
    })
    app.run(host='0.0.0.0', port=8080)
