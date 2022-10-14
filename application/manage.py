import redis
import click
from rq import Connection, Worker

redis_url = redis_url = 'redis://redis:6379'


from redis import Redis
from urllib.parse import urlparse


@click.group()
def workers():
  pass

# there are 4 workers

@click.command(name='run_panel_worker')
def run_panel_worker():
    url = urlparse(redis_url)
    redis_connection = Redis(host=url.hostname, port=url.port, db=0)  # db 0 is for panel worker
    with Connection(redis_connection):
        worker = Worker('high')
        worker.work()


@click.command(name='run_app_worker')
def run_app_worker():
    url = urlparse(redis_url)
    redis_connection = Redis(host=url.hostname, port=url.port, db=1)  # db 1 is for app worker
    with Connection(redis_connection):
        worker = Worker('high')
        worker.work()


@click.command(name='run_detector_worker')
def run_detector_worker():
    url = urlparse(redis_url)
    redis_connection = Redis(host=url.hostname, port=url.port, db=2)  # db 2 is for detector worker
    with Connection(redis_connection):
        worker = Worker('high')
        worker.work()


@click.command(name='run_crawler_worker')
def run_crawler_worker():
    url = urlparse(redis_url)
    redis_connection = Redis(host=url.hostname, port=url.port, db=3)  # db 3 is for crawler worker
    with Connection(redis_connection):
        worker = Worker('high')
        worker.work()

workers.add_command(run_panel_worker)
workers.add_command(run_app_worker)
workers.add_command(run_detector_worker)
workers.add_command(run_crawler_worker)
 
if __name__ == '__main__':
    workers()