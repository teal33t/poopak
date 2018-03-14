import os

from rq import Worker, Queue, Connection
from redis import Redis
from urllib.parse import urlparse


local_dev = False

if local_dev:
    mongodb_uri = "mongodb://%s:%s@localhost:27017/crawler" % ("admin", "54nn4n")
    redis_uri = 'redis://localhost:6379'
else:
    mongodb_uri = "mongodb://%s:%s@mongodb:27017/crawler" % ("admin", "54nn4n")
    redis_uri = 'redis://redis:6379'


listen = ['default']
redis_url = os.getenv('REDISTOGO_URL', redis_uri)

url = urlparse(redis_url)
conn = Redis(host=url.hostname, port=url.port, db=0)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()