"""
User repository implementation.

This module provides data access methods for user operations including
authentication and user management.
"""

import logging
from typing import Any, Dict, List, Optional

from pymongo.database import Database
from werkzeug.security import check_password_hash, generate_password_hash

from application.utils.exceptions import DatabaseConnectionError, DocumentNotFoundError, ValidationError

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    Repository for user data access operations.

    Provides methods for user authentication, creation, and management.
    """

    def __init__(self, database: Database):
        """
        Initialize the user repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "users")

    def find_by_id(self, id: Any) -> Optional[Dict[str, Any]]:
        """
        Find a user by their ID (username).

        Args:
            id: The user ID (username)

        Returns:
            User dictionary if found, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            user = self.collection.find_one({"_id": id})
            logger.debug(f"Found user with ID {id}: {user is not None}")
            return user
        except Exception as e:
            logger.error(f"Error finding user by ID {id}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to find user: {str(e)}")

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by their username.

        Args:
            username: The username to search for

        Returns:
            User dictionary if found, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        return self.find_by_id(username)

    def find_all(self, filter: Optional[Dict[str, Any]] = None, skip: int = 0, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Find all users matching the filter.

        Args:
            filter: MongoDB query filter (None for all users)
            skip: Number of users to skip (for pagination)
            limit: Maximum number of users to return (0 for no limit)

        Returns:
            List of user dictionaries

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            filter_query = filter if filter else {}
            cursor = self.collection.find(filter_query)

            if skip > 0:
                cursor = cursor.skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)

            users = list(cursor)
            logger.debug(f"Found {len(users)} users")
            return users
        except Exception as e:
            logger.error(f"Error finding users: {str(e)}")
            raise DatabaseConnectionError(f"Failed to find users: {str(e)}")

    def create(self, data: Dict[str, Any]) -> str:
        """
        Create a new user.

        Args:
            data: User data to insert (must include '_id' as username and 'password')

        Returns:
            ID (username) of the created user

        Raises:
            ValidationError: If data validation fails
            DatabaseConnectionError: If database operation fails
        """
        try:
            if not data.get("_id"):
                raise ValidationError("User must have an _id (username)")
            if not data.get("password"):
                raise ValidationError("User must have a password")

            # Hash the password if it's not already hashed
            if not data["password"].startswith("pbkdf2:sha256"):
                data["password"] = generate_password_hash(data["password"], method="pbkdf2:sha256")

            result = self.collection.insert_one(data)
            user_id = str(result.inserted_id)
            logger.info(f"Created user with ID {user_id}")
            return user_id
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise DatabaseConnectionError(f"Failed to create user: {str(e)}")

    def update(self, id: Any, data: Dict[str, Any]) -> bool:
        """
        Update an existing user.

        Args:
            id: The user ID (username) to update
            data: Fields to update

        Returns:
            True if user was updated, False otherwise

        Raises:
            DocumentNotFoundError: If user with given ID doesn't exist
            DatabaseConnectionError: If database operation fails
        """
        try:
            # Hash password if it's being updated and not already hashed
            if "password" in data and not data["password"].startswith("pbkdf2:sha256"):
                data["password"] = generate_password_hash(data["password"], method="pbkdf2:sha256")

            result = self.collection.update_one({"_id": id}, {"$set": data}, upsert=False)

            if result.matched_count == 0:
                raise DocumentNotFoundError(f"User with ID {id} not found")

            logger.info(f"Updated user with ID {id}")
            return result.modified_count > 0
        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating user {id}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to update user: {str(e)}")

    def delete(self, id: Any) -> bool:
        """
        Delete a user by their ID.

        Args:
            id: The user ID (username) to delete

        Returns:
            True if user was deleted, False otherwise

        Raises:
            DocumentNotFoundError: If user with given ID doesn't exist
            DatabaseConnectionError: If database operation fails
        """
        try:
            result = self.collection.delete_one({"_id": id})

            if result.deleted_count == 0:
                raise DocumentNotFoundError(f"User with ID {id} not found")

            logger.info(f"Deleted user with ID {id}")
            return True
        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting user {id}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to delete user: {str(e)}")

    def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        """
        Count users matching the filter.

        Args:
            filter: MongoDB query filter (None for all users)

        Returns:
            Number of users matching the filter

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            filter_query = filter if filter else {}
            count = self.collection.count_documents(filter_query)
            logger.debug(f"Counted {count} users")
            return count
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}")
            raise DatabaseConnectionError(f"Failed to count users: {str(e)}")

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.

        Args:
            username: The username
            password: The plain text password to verify

        Returns:
            User dictionary if authentication succeeds, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            user = self.find_by_username(username)

            if not user:
                logger.debug(f"Authentication failed: user {username} not found")
                return None

            if self.validate_password(user["password"], password):
                logger.info(f"User {username} authenticated successfully")
                return user
            else:
                logger.debug(f"Authentication failed: invalid password for user {username}")
                return None
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to authenticate user: {str(e)}")

    @staticmethod
    def validate_password(password_hash: str, password: str) -> bool:
        """
        Validate a password against its hash.

        This method replaces the validate_login method from the User model,
        moving password validation logic to the repository layer.

        Args:
            password_hash: The hashed password from the database
            password: The plain text password to verify

        Returns:
            True if password is valid, False otherwise
        """
        try:
            return check_password_hash(password_hash, password)
        except Exception as e:
            logger.error(f"Error validating password: {str(e)}")
            return False

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain text password.

        Args:
            password: The plain text password to hash

        Returns:
            Hashed password string
        """
        return generate_password_hash(password, method="pbkdf2:sha256")

    def username_exists(self, username: str) -> bool:
        """
        Check if a username exists in the database.

        Args:
            username: The username to check

        Returns:
            True if username exists, False otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        return self.exists({"_id": username})
