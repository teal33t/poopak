"""
Data storage module for crawler operations.

This module provides a simplified interface for crawler data operations
using the repository pattern. It wraps DocumentRepository to provide
backward-compatible methods for legacy crawler code.
"""

import logging

from application.infrastructure.database import get_database
from application.repositories.document_repository import DocumentRepository
from application.utils.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class DataStorage:
    """
    Data storage interface for crawler operations.

    Uses DocumentRepository to interact with the database, eliminating
    direct MongoDB client usage and duplicate connection code.
    """

    def __init__(self):
        """Initialize DataStorage with DocumentRepository."""
        database = get_database()
        self.repository = DocumentRepository(database)

    def is_url_exist(self, url):
        """
        Check if a URL exists in the database.

        Args:
            url: URL to check

        Returns:
            True if URL exists, False otherwise
        """
        try:
            return self.repository.url_exists(url)
        except DatabaseConnectionError as e:
            logger.error(f"Database error checking if URL exists {url}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking if URL exists {url}: {str(e)}")
            return False

    def add_crawled_url(self, data):
        """
        Add a new crawled URL to the database.

        Args:
            data: Document data to insert

        Returns:
            ID of the created document
        """
        return self.repository.create(data)

    def update_crawled_url(self, url, data):
        """
        Update an existing crawled URL.

        Args:
            url: URL of the document to update
            data: Fields to update

        Returns:
            True if update was successful
        """
        try:
            self.repository.update_by_url(url, data)
            logger.info(f"Updated crawled URL: {url}")
            return True
        except DatabaseConnectionError as e:
            logger.error(f"Database error updating URL {url}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating URL {url}: {str(e)}")
            return False

    def get_document_by_url(self, url):
        """
        Get a document by its URL.

        Args:
            url: URL to search for

        Returns:
            Document dictionary if found, None otherwise
        """
        try:
            return self.repository.find_by_url(url)
        except DatabaseConnectionError as e:
            logger.error(f"Database error retrieving document by URL {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving document by URL {url}: {str(e)}")
            return None
