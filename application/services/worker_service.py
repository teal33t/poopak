"""
Worker service for managing RQ worker operations.

This module provides the WorkerService class that encapsulates common worker
initialization and execution logic, eliminating code duplication in manage.py.
"""

import logging
from typing import Optional

from redis import Redis
from rq import Connection, Worker

from application.config import Settings
from application.config.constants import QUEUE_HIGH_PRIORITY
from application.infrastructure.queue import WorkerType

logger = logging.getLogger(__name__)


class WorkerService:
    """
    Service for managing RQ worker operations.

    Provides a centralized way to start workers with proper configuration
    and error handling, eliminating duplicate worker initialization code.
    """

    def __init__(self, settings: Settings = None):
        """
        Initialize the worker service.

        Args:
            settings: Application configuration settings
        """
        if settings is None:
            from application.config import settings as default_settings

            settings = default_settings

        self._settings = settings
        logger.info("WorkerService initialized")

    def start_worker(self, worker_type: WorkerType, queue_name: str = QUEUE_HIGH_PRIORITY) -> None:
        """
        Start an RQ worker for the specified worker type.

        This method creates a Redis connection for the specified worker type,
        initializes an RQ Worker, and starts processing jobs from the queue.

        Args:
            worker_type: Type of worker to start (PANEL, APP, DETECTOR, or CRAWLER)
            queue_name: Name of the queue to process (default: "high")

        Raises:
            ValueError: If worker_type is not a valid WorkerType
            Exception: If worker initialization or execution fails
        """
        if not isinstance(worker_type, WorkerType):
            raise ValueError(f"Invalid worker type: {worker_type}")

        try:
            # Get the Redis database number for this worker type
            db_number = worker_type.value

            logger.info(f"Starting {worker_type.name} worker on queue '{queue_name}' " f"(db={db_number})")

            # Create Redis connection for this worker type
            redis_connection = Redis(
                host=self._settings.REDIS_HOST,
                port=self._settings.REDIS_PORT,
                db=db_number,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            redis_connection.ping()
            logger.info(f"Successfully connected to Redis for {worker_type.name} worker")

            # Start worker with connection context
            with Connection(redis_connection):
                worker = Worker(queue_name)
                logger.info(f"{worker_type.name} worker started, processing jobs...")
                worker.work()

        except Exception as e:
            logger.error(f"Failed to start {worker_type.name} worker: {str(e)}", exc_info=True)
            raise

    def start_panel_worker(self, queue_name: str = QUEUE_HIGH_PRIORITY) -> None:
        """
        Start the panel worker.

        Args:
            queue_name: Name of the queue to process (default: "high")
        """
        self.start_worker(WorkerType.PANEL, queue_name)

    def start_app_worker(self, queue_name: str = QUEUE_HIGH_PRIORITY) -> None:
        """
        Start the app worker.

        Args:
            queue_name: Name of the queue to process (default: "high")
        """
        self.start_worker(WorkerType.APP, queue_name)

    def start_detector_worker(self, queue_name: str = QUEUE_HIGH_PRIORITY) -> None:
        """
        Start the detector worker.

        Args:
            queue_name: Name of the queue to process (default: "high")
        """
        self.start_worker(WorkerType.DETECTOR, queue_name)

    def start_crawler_worker(self, queue_name: str = QUEUE_HIGH_PRIORITY) -> None:
        """
        Start the crawler worker.

        Args:
            queue_name: Name of the queue to process (default: "high")
        """
        self.start_worker(WorkerType.CRAWLER, queue_name)
