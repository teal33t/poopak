"""
Worker connector module for crawler.

This module provides a pre-configured Redis connection for the crawler worker.
"""

from redis import Redis

from application.config import settings

# Create Redis connection for crawler worker
redis_connection: Redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB_CRAWLER)
