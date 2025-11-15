"""
Authentication service implementation.

This module provides business logic for user authentication operations,
coordinating between the user repository and authentication requirements.
"""

import logging
from typing import Optional

from application.repositories.user_repository import UserRepository
from application.utils.exceptions import DatabaseConnectionError
from application.models import User

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Service for handling user authentication operations.

    This service encapsulates authentication business logic and coordinates
    between the user repository and the authentication system.
    """

    def __init__(self, user_repository: UserRepository):
        """
        Initialize the authentication service.

        Args:
            user_repository: Repository for user data access
        """
        self.user_repository = user_repository

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.

        Args:
            username: The username to authenticate
            password: The plain text password to verify

        Returns:
            User object if authentication succeeds, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            user_data = self.user_repository.authenticate(username, password)

            if user_data:
                logger.info(f"User {username} authenticated successfully")
                return User(user_data["_id"])
            else:
                logger.warning(f"Failed authentication attempt for user {username}")
                return None

        except DatabaseConnectionError as e:
            logger.error(f"Database error during authentication for user {username}: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error during authentication for user {username}: {str(e)}")
            raise DatabaseConnectionError(f"Authentication failed: {str(e)}")

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by username.

        Args:
            username: The username to retrieve

        Returns:
            User object if found, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            user_data = self.user_repository.find_by_username(username)

            if user_data:
                return User(user_data["_id"])
            else:
                return None

        except DatabaseConnectionError as e:
            logger.error(f"Database error retrieving user {username}: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error retrieving user {username}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to retrieve user: {str(e)}")

    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists.

        Args:
            username: The username to check

        Returns:
            True if user exists, False otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            return self.user_repository.username_exists(username)
        except DatabaseConnectionError as e:
            logger.error(f"Database error checking if user {username} exists: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking if user {username} exists: {str(e)}")
            raise DatabaseConnectionError(f"Failed to check user existence: {str(e)}")
