"""
Repository layer for data access.

This package contains repository classes that abstract database operations
and provide a clean interface for data access throughout the application.
"""

from .base_repository import BaseRepository
from .document_repository import DocumentRepository
from .user_repository import UserRepository

__all__ = ["BaseRepository", "DocumentRepository", "UserRepository"]
