import random

import redis

from file_container.server import FileServer

r = redis.StrictRedis(host='localhost', port=6379, db=0)
r.set('foo', 'bar')
print(r.get('foo'))


def find_file(file_path):
    if r.exists(file_path):
        first_server = r.get(file_path).decode().split(';')[0]
        return FileServer(first_server).download(file_path)


def create_file(file_path):
    file_server = random.uniform(0, 5)
    r.set(file_path, f'{file_server};')
