import redis
from flask_script import Server, Manager
from rq import Connection, Worker
from web import app
from settings import redis_url

from redis import Redis
from urllib.parse import urlparse


manager = Manager(app)
manager.add_command(
    'runserver',
    Server(use_debugger=True, use_reloader=True))

# there are 4 workers

@manager.command
def run_panel_worker():
    url = urlparse(redis_url)
    redis_connection = Redis(host=url.hostname, port=url.port, db=0)  # db 0 is for panel worker
    with Connection(redis_connection):
        worker = Worker(app.config['QUEUES'])
        worker.work()


@manager.command
def run_app_worker():
    url = urlparse(redis_url)
    redis_connection = Redis(host=url.hostname, port=url.port, db=1)  # db 1 is for app worker
    with Connection(redis_connection):
        worker = Worker(app.config['QUEUES'])
        worker.work()


@manager.command
def run_detector_worker():
    url = urlparse(redis_url)
    redis_connection = Redis(host=url.hostname, port=url.port, db=2)  # db 2 is for detector worker
    with Connection(redis_connection):
        worker = Worker(app.config['QUEUES'])
        worker.work()


@manager.command
def run_crawler_worker():
    url = urlparse(redis_url)
    redis_connection = Redis(host=url.hostname, port=url.port, db=3)  # db 3 is for crawler worker
    with Connection(redis_connection):
        worker = Worker(app.config['QUEUES'])
        worker.work()


if __name__ == '__main__':
    manager.run()