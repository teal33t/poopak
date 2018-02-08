from web import app

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5050, debug=True)
#

import redis
from flask_script import Server, Manager
from rq import Connection, Worker
from redis import Redis
from urllib.parse import urlparse
# from uwsgi import app

import os
manager = Manager(app)

@manager.command
def runserver():
    app.run(host="0.0.0.0",
            port=5050,
            debug=True)

RQ_QUEUES = {
    'default': {
         'HOST': 'localhost',
         'PORT': '6379',
         'URL': os.getenv('REDISTOGO_URL', 'redis://redis:6379'),  # If you're
         'DB': 0,
         'DEFAULT_TIMEOUT': 480,
     }
}

@manager.command
def runworker():
    # redis_url = app.config['REDIS_URL']
    # redis_connection = redis.from_url(redis_url)
    redis_url = os.getenv('REDISTOGO_URL', 'redis://redis:6379')

    # conn = redis.from_url(redis_url)
    url = urlparse(redis_url)
    conn = Redis(host=url.hostname, port=url.port, db=0)
    with Connection(conn):
        worker = Worker(RQ_QUEUES)
        worker.work()


if __name__ == '__main__':
    manager.run()