import configparser
import os

import requests

config = configparser.ConfigParser()
config.read('client.ini')
HOST = config["DEFAULT"]["host"]
PORT = config["DEFAULT"]["port"]

current_directory = ''


def file_query(query):
    return f'http://{HOST}:{PORT}/files/{query}'


def query(query):
    return f'http://{HOST}:{PORT}/{query}'


# Commands section
# -----------------------------------

def initialize() -> requests.Response:
    return requests.get(query('initialize'))


def create_file(path_to_file):
    if current_directory != '':
        requests.post(file_query(f'{current_directory}/{path_to_file}'))
    else:
        requests.post(file_query(os.path.basename(path_to_file)))


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


def info_file():
    pass


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
        elif command in commands:
            commands[command]()
        else:
            print(f'There is no command `{command}`! Type `help` for the list of available commands')
