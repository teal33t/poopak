import os

from rq import Worker, Queue, Connection
from redis import Redis
from urllib.parse import urlparse

listen = ['default']
redis_url = os.getenv('REDISTOGO_URL', 'redis://redis:6379')

url = urlparse(redis_url)
conn = Redis(host=url.hostname, port=url.port, db=0)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()