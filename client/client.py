import configparser
import os
import re

import requests

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


# Commands section
# -----------------------------------

def initialize() -> requests.Response:
    return requests.get(common_query('initialize'))


def create_file(file_name: str, path_to_file: str):
    file_name = file_name.strip()
    path_to_file = path_to_file.strip()
    if path_to_file == './':
        if current_directory == '':
            slash = ''
        else:
            slash = '/'
        requests.post(file_query(f'{current_directory.lstrip("/")}{slash}{file_name.lstrip("/")}'), data=b'')
    else:
        if path_to_file == '':
            slash = ''
        else:
            slash = '/'
        requests.post(file_query(f'{path_to_file.lstrip("/")}{slash}{file_name.lstrip("/")}'))


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
    path_to_file = path_to_file.strip()
    if path_to_file.startswith('./'):
        if current_directory == '':
            slash = ''
        else:
            slash = '/'
        return requests.get(info_query(f'{current_directory.lstrip("/")}{slash}{path_to_file.lstrip("./")}'),
                            data=b'').text
    else:
        return requests.get(info_query(f'{path_to_file.lstrip("/")}')).text


def copy_file():
    pass


def move_file():
    pass


def open_directory(path_to_directory):
    global current_directory
    current_directory = path_to_directory


def read_directory():
    pass


def make_directory(path_to_directory):
    requests.post(file_query(path_to_directory))


def delete_directory():
    pass


# -----------------------------------
# End of commands section

commands = {
    '': print
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
        elif re.compile(r'stat(.+)').search(command) is not None:
            path = re.compile(r'stat(.+)').search(command).group(1)
            print(info_file(path))
        elif command in commands:
            commands[command]()
        else:
            print(f'There is no command `{command}`! Type `help` for the list of available commands')
