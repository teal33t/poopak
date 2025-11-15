"""
Queue instances for web application.

This module provides pre-configured queue instances for different worker types
using the QueueFactory for centralized connection management.
"""

from application.config import settings
from application.config.constants import QUEUE_HIGH_PRIORITY
from application.infrastructure.queue import QueueFactory, WorkerType

# Initialize queue factory with application settings
queue_factory = QueueFactory(settings)

# Create queues for each worker type using the factory
panel_q = queue_factory.get_queue(WorkerType.PANEL, QUEUE_HIGH_PRIORITY)
app_q = queue_factory.get_queue(WorkerType.APP, QUEUE_HIGH_PRIORITY)
detector_q = queue_factory.get_queue(WorkerType.DETECTOR, QUEUE_HIGH_PRIORITY)
crawler_q = queue_factory.get_queue(WorkerType.CRAWLER, QUEUE_HIGH_PRIORITY)
