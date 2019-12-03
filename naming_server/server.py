import datetime
import json
import logging
import random
from json import JSONEncoder
from os import environ
from threading import Thread
from time import sleep
from typing import List, Any, Optional

import redis
import requests
from flask import Flask, request, make_response, abort, jsonify
from requests import Response
from requests.adapters import TimeoutSauce, HTTPAdapter
from urllib3 import Retry


def requests_retry_session(
        retries=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
        session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class DefaultTimeout(TimeoutSauce):
    def __init__(self, *args, **kwargs):
        if kwargs['connect'] is None:
            kwargs['connect'] = 2
        if kwargs['read'] is None:
            kwargs['read'] = 2
        super(DefaultTimeout, self).__init__(*args, **kwargs)


requests.adapters.TimeoutSauce = DefaultTimeout


class Scheduler(Thread):

    def __init__(self, target, args: tuple, second=5, daemon: Optional[bool] = ...) -> None:

        super().__init__(daemon=daemon)
        self.args = args
        self.target = target
        self.second = second
        self._init_update()

    def _init_update(self) -> None:
        self.update_time = datetime.datetime.today() + datetime.timedelta(seconds=self.second)

    def run(self) -> None:
        while True:
            time_to_sleep = (self.update_time - datetime.datetime.today()).seconds
            while time_to_sleep > 0:
                sleep(time_to_sleep)
                time_to_sleep = (self.update_time - datetime.datetime.today()).seconds
            Thread(target=self.target, args=self.args).run()
            sleep(1)  # Is used to prevent target to run several times during update_time == today()
            self._init_update()


class Server:
    def __init__(self, address: str, port: int) -> None:
        super().__init__()
        self.address = address
        self.port = port

    def __str__(self) -> str:
        return '{' + f'"address":"{self.address}", "port":{self.port}' + '}'

    def __repr__(self) -> str:
        return '{' + f'"address":"{self.address}", "port":{self.port}' + '}'

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Server):
            return self.address == o.address and self.port == o.port
        return False

    def __hash__(self) -> int:
        return hash((self.address, self.port))


class Encoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Server):
            return str(obj)
        return JSONEncoder.default(self, obj)


LOG = logging.getLogger('NamingServer')
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.FileHandler('naming_server.log'))
LOG.addHandler(logging.StreamHandler())

ACTIVE_SERVERS: List[Server] = []


def check_server_liveness():
    global ACTIVE_SERVERS
    unique_servers = set(ACTIVE_SERVERS)  # handling duplicates
    ACTIVE_SERVERS = list(unique_servers)
    for server in ACTIVE_SERVERS:
        try:
            ping(server)
        except requests.ConnectionError:
            ACTIVE_SERVERS.remove(server)
            LOG.info(f'Server {server} disconnected.')


SCHEDULER = Scheduler(check_server_liveness, ())

app = Flask(__name__)
app.logger = LOG
app.json_encoder = Encoder

REDIS_CONNECTOR = redis.StrictRedis(host=environ['REDIS_HOST'], port=environ['REDIS_PORT'], db=0)


# Util methods section
# -----------------------------------
def construct_query(server: Server, query: str) -> str:
    return f'http://{server.address}:{server.port}/{query}'


def reset(server: Server) -> Response:
    return requests_retry_session().get(construct_query(server, 'reset'))


def ping(server: Server):
    requests_retry_session().get(construct_query(server, 'ping'))


def get_random_element(a_list: List[Any]) -> Any:
    return a_list[int(random.uniform(0, len(a_list)))]


# -----------------------------------
# End of util methods section


# File managing section
# -----------------------------------

@app.route('/files/<path:path_to_file>', methods=['GET'])
def download(path_to_file: str):
    urls = _find_file_location(path_to_file)
    if len(urls) == 0:
        return 'SERVERS ARE UNAVAILABLE'
    get = requests_retry_session().get(get_random_element(urls))
    if get.status_code != 200:
        abort(get.status_code)
    response = make_response(get.content)
    response.headers.set('Content-Disposition', 'attachment')
    return response


@app.route('/files/<path:path_to_file>', methods=['POST'])
def upload(path_to_file: str):
    is_directory = request.args.get('dir')
    for server in ACTIVE_SERVERS:
        try:
            requests_retry_session().post(construct_query(server, path_to_file + f'?dir={is_directory}'),
                                          data=request.data)
        except requests.ConnectionError:
            ACTIVE_SERVERS.remove(server)
    REDIS_CONNECTOR.set(path_to_file, str(ACTIVE_SERVERS))
    return jsonify('OK')


@app.route('/files/<path:path_to_file>', methods=['DELETE'])
def delete(path_to_file: str):
    is_directory = request.args.get('dir')
    urls = _find_file_location(path_to_file)
    for url in urls:
        requests_retry_session().delete(url + f'?dir={is_directory}')
    REDIS_CONNECTOR.delete(path_to_file)
    return jsonify('OK')


@app.route('/files/info/<path:path_to_file>', methods=['GET'])
def info(path_to_file: str):
    urls = _find_file_location(path_to_file, True)
    if len(urls) == 0:
        return requests_retry_session().get(
            construct_query(get_random_element(ACTIVE_SERVERS), f'info/{path_to_file}')).text
    get = requests_retry_session().get(get_random_element(urls))
    if get.status_code != 200:
        abort(get.status_code)
    return get.content


# -----------------------------------
# End of file managing section


# This method is called by a file server starting, so he can be found by this server

# The real preparation of file server for storing data is in prepare_server method, as we need to send answer to file
# server to prevent deadlocking
@app.route('/server', methods=['POST'])
def add_server():
    server_json = request.get_json(True)
    server = Server(server_json["address"], server_json["port"])
    ACTIVE_SERVERS.append(server)

    Thread(target=prepare_server, args=(server,)).start()
    return jsonify(server)


# Wipes the file server and then fill it with data from other server alive
# TODO: maybe add some checksum checking for finding, if file server really replicated
def prepare_server(server):
    with app.app_context():
        while True:
            try:
                ping(server)
            except requests.ConnectionError:
                continue
            break
        response = reset(server)
        if response.status_code != 200:
            raise Exception("Could not reset server")
        replicas = ACTIVE_SERVERS.copy()
        replicas.remove(server)
        if len(ACTIVE_SERVERS) > 1:
            server_from = get_random_element(replicas)
            requests_retry_session().post(construct_query(server_from, 'replicate'), data=str(server))


# User for wiping all file servers
@app.route('/initialize', methods=['GET'])
def initialize():
    result = {}
    for server in ACTIVE_SERVERS:
        response = reset(server)
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


def _find_file_location(path_to_file, info=False) -> List[str]:
    if path_to_file == './':
        servers: List[Server] = ACTIVE_SERVERS
    else:
        paths = REDIS_CONNECTOR.get(path_to_file)
        if paths is None:
            return []
        possible_servers: List[dict] = json.loads(paths)
        servers: List[Server] = [Server(server["address"], server["port"]) for server in possible_servers]

    links: List[str] = []
    for server in servers:
        try:
            ping(server)
            if info:
                links.append(f'{construct_query(server, "info")}/{path_to_file}')
            else:
                links.append(construct_query(server, path_to_file))
        except requests.ConnectionError:
            servers.remove(server)

    REDIS_CONNECTOR.set(path_to_file, str(servers))
    return links


if __name__ == '__main__':
    SCHEDULER.start()
    app.run(host="0.0.0.0", port=80)
