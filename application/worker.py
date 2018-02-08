import os

import redis
from rq import Worker, Queue, Connection
from redis import Redis
from urllib.parse import urlparse

listen = ['default']
redis_url = os.getenv('REDISTOGO_URL', 'redis://redis:6379')

# conn = redis.from_url(redis_url)
url = urlparse(redis_url)
conn = Redis(host=url.hostname, port=url.port, db=0)
#
# RQ_QUEUES = {
#     'default': {
#          'HOST': 'localhost',
#          'PORT': '6379',
#          'URL': os.getenv('REDISTOGO_URL', 'redis://redis:6379'),  # If you're
#          'DB': 0,
#          'DEFAULT_TIMEOUT': 480,
#      }
# }
#

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()