import configparser
import os
import shutil
from os.path import expanduser

import requests
from flask import Flask, send_from_directory, request

FILE_STORAGE_PATH = f'{expanduser("~")}/files'

app = Flask(__name__)


@app.route('/<path:path_to_file>', methods=['GET'])
def download(path_to_file: str):
    return send_from_directory(FILE_STORAGE_PATH, path_to_file, as_attachment=True)


@app.route('/ping', methods=['GET'])
def ping():
    return 'OK'


@app.route('/<path:path_to_file>', methods=['POST'])
def upload(path_to_file: str):
    path_to_file = f'{FILE_STORAGE_PATH}/{path_to_file}'
    directory = path_to_file[:path_to_file.rfind('/')]
    if not os.path.exists(directory):
        os.mkdir(directory)
    file = open(path_to_file, 'wb')
    file.write(request.data)
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
    data = requests.get('http://checkip.dyndns.com/').text
    requests.post(url=f'http://{config["DEFAULT"]["host"]}:{config["DEFAULT"]["port"]}/server', json={
        "address": 'localhost',
    # TODO: replace with re.compile(REDIS_CONNECTOR'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)
        "port": 8080
    })
    app.run(host='0.0.0.0', port=8080)
