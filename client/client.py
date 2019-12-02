import configparser
import os
import re

import requests
from requests import Response

config = configparser.ConfigParser()
config.read('client.ini')
HOST = config["DEFAULT"]["host"]
PORT = config["DEFAULT"]["port"]

current_directory = ''


def info_query(query):
    return f'http://{HOST}:{PORT}/files/info/{query}'


def file_query(query):
    return f'http://{HOST}:{PORT}/files/{query}'


def common_query(query):
    return f'http://{HOST}:{PORT}/{query}'


def make_request(request_function, args):
    result: Response = request_function(args)
    if result.status_code == 404 or '404 Not Found' in result.text:
        return 'No result found'
    elif result.status_code == 500:
        return 'Some error occurred'
    else:
        return result.text


def get_path(some_path: str):
    if some_path.startswith('./'):
        if current_directory == '':
            slash = ''
        else:
            slash = '/'
        return f'{current_directory.lstrip("/")}{slash}{some_path.lstrip("./")}'
    else:
        return some_path.lstrip("/")


# Commands section
# -----------------------------------

def initialize() -> requests.Response:
    return requests.get(common_query('initialize'))


def create_file(file_name: str, path_to_file: str):
    final_path = get_path(path_to_file + '/' + file_name)
    requests.post(file_query(final_path), data=b'')


def write_file(path_to_file):
    data = open(path_to_file, 'rb').read()

    if current_directory != '':
        requests.post(file_query(f'{current_directory}/{os.path.basename(path_to_file)}'), data=data)
    else:
        requests.post(file_query(os.path.basename(path_to_file)), data=data)


def delete_file(path_to_file):
    if current_directory != '':
        requests.delete(file_query(f'{current_directory}/{os.path.basename(path_to_file)}'))
    else:
        requests.delete(file_query(os.path.basename(path_to_file)))


def info_file(path_to_file: str):
    path_to_file = get_path(path_to_file.strip())
    return make_request(requests.get, info_query(path_to_file))


def copy_file(file_from: str, file_to: str):
    file_from = get_path(file_from.strip())
    file_to = get_path(file_to.strip())

    request = make_request(requests.get, info_query(file_from))
    if (request == 'No result found') or (request == 'Some error occurred'):
        return request
    else:
        file = requests.get(file_query(file_from)).content
        requests.post(file_query(file_to), data=file)
        return 'OK'


def move_file(file_from: str, file_to: str):
    file_from = get_path(file_from.strip())
    file_to = get_path(file_to.strip())

    request = make_request(requests.get, info_query(file_from))
    if (request == 'No result found') or (request == 'Some error occurred'):
        return request
    else:
        file = requests.get(file_query(file_from)).content
        requests.delete(file_query(file_from))
        requests.post(file_query(file_to), data=file)
        return 'OK'


def open_directory(path_to_directory):
    global current_directory
    if path_to_directory == '..':
        if '/' in current_directory:
            path_to_directory = current_directory[:current_directory.rfind('/')]
        else:
            current_directory = ''
            return 'OK'

    request = make_request(requests.get, info_query(path_to_directory))
    if (request == 'No result found') or (request == 'Some error occurred'):
        return request
    current_directory = path_to_directory
    return 'OK'


def read_directory():
    if current_directory == '':
        return make_request(requests.get, info_query('./'))
    return make_request(requests.get, info_query(get_path(current_directory)))


def make_directory(path_to_directory: str):
    return requests.post(file_query(path_to_directory + f'?dir=1')).text


def delete_directory(path_to_directory: str):
    return requests.delete(file_query(path_to_directory + f'?dir=1')).text


# -----------------------------------
# End of commands section

commands = {
    'ls': read_directory
}

if __name__ == '__main__':
    print('Client for DFS started!')
    try:
        print(initialize().text)
    except requests.ConnectionError:
        print(f'DFS is not running on host `{HOST}:{PORT}`. Please, check your configuration.')
        print('Exiting...')
        exit(0)

    print('DFS is running and ready to use, good luck :)')
    print()
    print('Please, type in the command. Type `help` for the list of available commands')

    while True:
        command = input()

        if command == 'help':
            print(commands)
        elif re.compile(r'(.+)>(.+)').search(command) is not None:
            name, path = re.compile(r'(.+)>(.+)').search(command).groups()
            create_file(name, path)
        elif re.compile(r'stat (.+)').search(command) is not None:
            path = re.compile(r'stat (.+)').search(command).group(1)
            print(info_file(path))
        elif re.compile(r'cp (.+) (.+)').search(command) is not None:
            what, where = re.compile(r'cp (.+) (.+)').search(command).groups()
            print(copy_file(what, where))
        elif re.compile(r'mv (.+) (.+)').search(command) is not None:
            what, where = re.compile(r'mv (.+) (.+)').search(command).groups()
            print(move_file(what, where))
        elif re.compile(r'cd (.+)').search(command) is not None:
            directory = re.compile(r'cd (.+)').search(command).group(1)
            print(open_directory(directory))
            print(f'Current directory: {current_directory}')
        elif re.compile(r'mkdir (.+)').search(command) is not None:
            directory = re.compile(r'mkdir (.+)').search(command).group(1)
            print(make_directory(directory))
        elif re.compile(r'rmdir (.+)').search(command) is not None:
            directory = re.compile(r'rmdir (.+)').search(command).group(1)
            print(delete_directory(directory))
        elif command in commands:
            print(commands[command]())
        else:
            print(f'There is no command `{command}`! Type `help` for the list of available commands')
