"""
Base repository pattern implementation.

This module provides an abstract base class for all repositories,
defining common CRUD operations interface.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    Abstract base repository class for data access operations.

    Provides a consistent interface for CRUD operations across all repositories.
    Concrete repository classes should inherit from this class and implement
    the abstract methods.

    Attributes:
        database: MongoDB database instance
        collection_name: Name of the MongoDB collection
        collection: MongoDB collection instance
    """

    def __init__(self, database: Database, collection_name: str):
        """
        Initialize the base repository.

        Args:
            database: MongoDB database instance
            collection_name: Name of the collection to operate on
        """
        self.database = database
        self.collection_name = collection_name
        self.collection: Collection = database[collection_name]
        logger.debug(f"Initialized {self.__class__.__name__} for collection '{collection_name}'")

    @abstractmethod
    def find_by_id(self, id: Any) -> Optional[Dict[str, Any]]:
        """
        Find a document by its ID.

        Args:
            id: The document ID (can be ObjectId or string)

        Returns:
            Document dictionary if found, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        pass

    @abstractmethod
    def find_all(self, filter: Optional[Dict[str, Any]] = None, skip: int = 0, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Find all documents matching the filter.

        Args:
            filter: MongoDB query filter (None for all documents)
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (0 for no limit)

        Returns:
            List of document dictionaries

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> str:
        """
        Create a new document.

        Args:
            data: Document data to insert

        Returns:
            ID of the created document as string

        Raises:
            ValidationError: If data validation fails
            DatabaseConnectionError: If database operation fails
        """
        pass

    @abstractmethod
    def update(self, id: Any, data: Dict[str, Any]) -> bool:
        """
        Update an existing document.

        Args:
            id: The document ID to update
            data: Fields to update

        Returns:
            True if document was updated, False otherwise

        Raises:
            DocumentNotFoundError: If document with given ID doesn't exist
            DatabaseConnectionError: If database operation fails
        """
        pass

    @abstractmethod
    def delete(self, id: Any) -> bool:
        """
        Delete a document by its ID.

        Args:
            id: The document ID to delete

        Returns:
            True if document was deleted, False otherwise

        Raises:
            DocumentNotFoundError: If document with given ID doesn't exist
            DatabaseConnectionError: If database operation fails
        """
        pass

    @abstractmethod
    def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching the filter.

        Args:
            filter: MongoDB query filter (None for all documents)

        Returns:
            Number of documents matching the filter

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        pass

    def exists(self, filter: Dict[str, Any]) -> bool:
        """
        Check if any document matches the filter.

        Args:
            filter: MongoDB query filter

        Returns:
            True if at least one document matches, False otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        return self.count(filter) > 0
