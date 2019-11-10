import requests
from flask import Flask, request, make_response, abort

app = Flask(__name__)

server_list = []


def find_file(path_to_file):
    url = f'http://{server_list[0]["address"]}:{server_list[0]["port"]}/{path_to_file}'
    return url


@app.route('/files/<path:path_to_file>', methods=['GET'])
def download(path_to_file: str):
    url = find_file(path_to_file)
    get = requests.get(url)
    if get.status_code != 200:
        abort(get.status_code)
    response = make_response(get.content)
    response.headers.set('Content-Disposition', 'attachment')
    return response


@app.route('/files/<path:path_to_file>', methods=['POST'])
def upload(path_to_file: str):
    url = find_file(path_to_file)
    requests.post(url, data=request.data)
    return 'OK'


@app.route('/files/<path:path_to_file>', methods=['DELETE'])
def delete(path_to_file: str):
    url = find_file(path_to_file)
    requests.delete(url)
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
    app.run()
