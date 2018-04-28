from redis import Redis
from urllib.parse import urlparse
from .config_crawler import redis_uri

url = urlparse(redis_uri)
redis_connection = Redis(host=url.hostname, port=url.port, db=3)  # db 3 is for crawler worker
