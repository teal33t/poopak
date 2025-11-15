"""
Queue connection factory for Redis and RQ.

This module provides a factory for creating Redis connections and RQ queues
with type-safe worker identification.
"""

import logging
from enum import Enum
from typing import Optional

from redis import Redis
from rq import Queue

from application.config import Settings

logger = logging.getLogger(__name__)


class WorkerType(Enum):
    """
    Enum for type-safe worker identification.

    Each worker type corresponds to a specific Redis database number
    for isolation of queue operations.
    """

    PANEL = 0
    APP = 1
    DETECTOR = 2
    CRAWLER = 3


class QueueFactory:
    """
    Factory for creating Redis connections and RQ queues.

    Provides centralized queue management with type-safe worker identification
    and eliminates duplicate Redis connection code.
    """

    def __init__(self, settings: Settings = None):
        """
        Initialize queue factory.

        Args:
            settings: Configuration settings for Redis connections
        """
        if settings is None:
            from application.config import settings as default_settings

            settings = default_settings

        self._settings = settings
        self._connections: dict[WorkerType, Optional[Redis]] = {
            WorkerType.PANEL: None,
            WorkerType.APP: None,
            WorkerType.DETECTOR: None,
            WorkerType.CRAWLER: None,
        }

    def get_connection(self, worker_type: WorkerType) -> Redis:
        """
        Get Redis connection for specified worker type.

        Creates connection on first call for each worker type and reuses
        the same connection for subsequent calls.

        Args:
            worker_type: Type of worker (PANEL, APP, DETECTOR, or CRAWLER)

        Returns:
            Redis connection instance

        Raises:
            ValueError: If worker_type is not a valid WorkerType
            Exception: If connection to Redis fails
        """
        if not isinstance(worker_type, WorkerType):
            raise ValueError(f"Invalid worker type: {worker_type}")

        if self._connections[worker_type] is None:
            try:
                db_number = worker_type.value
                logger.info(f"Creating Redis connection for {worker_type.name} worker (db={db_number})")

                self._connections[worker_type] = Redis(
                    host=self._settings.REDIS_HOST,
                    port=self._settings.REDIS_PORT,
                    db=db_number,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )

                # Test connection
                self._connections[worker_type].ping()
                logger.info(f"Successfully connected to Redis for {worker_type.name} worker")

            except Exception as e:
                logger.error(f"Failed to connect to Redis for {worker_type.name} worker: {str(e)}")
                raise

        return self._connections[worker_type]

    def get_queue(self, worker_type: WorkerType, queue_name: str = "high") -> Queue:
        """
        Get RQ queue for specified worker type.

        Creates a queue instance using the Redis connection for the
        specified worker type.

        Args:
            worker_type: Type of worker (PANEL, APP, DETECTOR, or CRAWLER)
            queue_name: Name of the queue (default: "high")

        Returns:
            RQ Queue instance

        Raises:
            ValueError: If worker_type is not a valid WorkerType
            Exception: If connection to Redis fails
        """
        connection = self.get_connection(worker_type)
        logger.debug(f"Creating queue '{queue_name}' for {worker_type.name} worker")
        return Queue(queue_name, connection=connection)

    def close_all(self) -> None:
        """
        Close all Redis connections.

        Should be called when shutting down the application to properly
        release resources.
        """
        for worker_type, connection in self._connections.items():
            if connection is not None:
                logger.info(f"Closing Redis connection for {worker_type.name} worker")
                connection.close()
                self._connections[worker_type] = None
