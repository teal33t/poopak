import os

from rq import Worker, Queue, Connection
from redis import Redis
from urllib.parse import urlparse
from worker_config import redis_uri

listen = ['default']
redis_url = os.getenv('REDISTOGO_URL', redis_uri)

url = urlparse(redis_url)
conn = Redis(host=url.hostname, port=url.port, db=0)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()