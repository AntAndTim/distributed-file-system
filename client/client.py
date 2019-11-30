import configparser
import os

import requests

config = configparser.ConfigParser()
config.read('client.ini')
host = config["DEFAULT"]["host"]
port = config["DEFAULT"]["port"]

current_directory = ''


def initialize():
    pass


def create_file(path_to_file):
    if current_directory != '':
        requests.post(f'http://{host}:{port}/files/{current_directory}/{path_to_file}')
    else:
        requests.post(f'http://{host}:{port}/files/{os.path.basename(path_to_file)}')


def write_file(path_to_file):
    data = open(path_to_file, 'rb').read()

    if current_directory != '':
        requests.post(f'http://{host}:{port}/files/{current_directory}/{os.path.basename(path_to_file)}', data=data)
    else:
        requests.post(f'http://{host}:{port}/files/{os.path.basename(path_to_file)}', data=data)


def delete_file(path_to_file):
    if current_directory != '':
        requests.delete(f'http://{host}:{port}/files/{current_directory}/{os.path.basename(path_to_file)}')
    else:
        requests.delete(f'http://{host}:{port}/files/{os.path.basename(path_to_file)}')


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
    requests.post(f'http://{host}:{port}/files/{path_to_directory}')


def delete_directory():
    pass


while True:
    print('please write command')
    command = input()

    if command == 'create file':
        print('write system path to file')
        path_to_file = input()
        create_file(path_to_file)

    if command == 'write file':
        print('write system path to file')
        path_to_file = input()
        write_file(path_to_file)

    if command == 'open directory':
        print('write directory')
        path_to_directory = input()
        open_directory(path_to_directory)
