"""
Domain models for the application.

This module provides domain model classes for the web crawler application.
Models are lightweight data containers with type safety.
"""

from .user import User
from .document import CrawledDocument

__all__ = ['User', 'CrawledDocument']
