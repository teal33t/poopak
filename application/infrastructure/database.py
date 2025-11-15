"""
Database connection factory for MongoDB.

This module provides a singleton pattern for MongoDB client management
with connection pooling configuration.
"""

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

from application.config import Settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Singleton database connection manager for MongoDB.

    Provides thread-safe MongoDB client instances with connection pooling.
    Uses lazy initialization to defer connection until first use.
    """

    _instance: Optional["DatabaseConnection"] = None
    _client: Optional[MongoClient] = None
    _settings: Optional[Settings] = None

    def __new__(cls, settings: Settings = None):
        """
        Create or return existing singleton instance.

        Args:
            settings: Configuration settings for database connection

        Returns:
            DatabaseConnection singleton instance
        """
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self, settings: Settings = None):
        """
        Initialize database connection manager.

        Args:
            settings: Configuration settings for database connection
        """
        if settings is not None:
            self._settings = settings
        elif self._settings is None:
            from application.config import settings as default_settings

            self._settings = default_settings

    def get_client(self) -> MongoClient:
        """
        Get MongoDB client instance.

        Creates client on first call (lazy initialization) and reuses
        the same client for subsequent calls. PyMongo handles connection
        pooling automatically.

        Returns:
            MongoClient instance

        Raises:
            Exception: If connection to MongoDB fails
        """
        if self._client is None:
            try:
                logger.info(f"Connecting to MongoDB at {self._settings.MONGODB_HOST}:{self._settings.MONGODB_PORT}")
                self._client = MongoClient(
                    host=self._settings.MONGODB_HOST,
                    port=self._settings.MONGODB_PORT,
                    username=self._settings.MONGODB_USERNAME,
                    password=self._settings.MONGODB_PASSWORD,
                    maxPoolSize=50,
                    minPoolSize=10,
                    serverSelectionTimeoutMS=5000,
                )
                # Test connection
                self._client.admin.command("ping")
                logger.info("Successfully connected to MongoDB")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {str(e)}")
                raise

        return self._client

    def get_database(self) -> Database:
        """
        Get database instance.

        Returns:
            Database instance for the configured database name

        Raises:
            Exception: If connection to MongoDB fails
        """
        client = self.get_client()
        return client[self._settings.MONGODB_DATABASE]

    def close(self) -> None:
        """
        Close MongoDB client connection.

        Should be called when shutting down the application to properly
        release resources.
        """
        if self._client is not None:
            logger.info("Closing MongoDB connection")
            self._client.close()
            self._client = None


def get_database(settings: Settings = None) -> Database:
    """
    Factory function to get database instance.

    Convenience function that creates a DatabaseConnection and returns
    the database instance.

    Args:
        settings: Optional configuration settings

    Returns:
        Database instance

    Raises:
        Exception: If connection to MongoDB fails
    """
    connection = DatabaseConnection(settings)
    return connection.get_database()
