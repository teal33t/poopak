from redis import Redis
from urllib.parse import urlparse
from .config import redis_uri
from rq import Queue

url = urlparse(redis_uri)
panel_connection = Redis(host=url.hostname, port=url.port, db=0)  # db 0 is for panel worker
app_connection = Redis(host=url.hostname, port=url.port, db=1)  # db 1 is for app worker
detector_connection = Redis(host=url.hostname, port=url.port, db=2)  # db 2 is for detector worker
crawler_connection = Redis(host=url.hostname, port=url.port, db=3)  # db 3 is for crawler worker


panel_q = Queue(name="high", connection=panel_connection)
app_q = Queue(name="high", connection=app_connection)
detector_q = Queue(name="high", connection=detector_connection)
crawler_q = Queue(name="high", connection=crawler_connection)