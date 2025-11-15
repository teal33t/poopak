"""
User domain model.

This module provides the User model for authentication and user management.
"""

from typing import Optional


class User:
    """
    User model for authentication.
    
    Represents a user in the system with authentication capabilities.
    This is a lightweight model used primarily for Flask-Login integration.
    
    Attributes:
        username: The unique username for the user
    """

    def __init__(self, username: str) -> None:
        """
        Initialize a User instance.
        
        Args:
            username: The unique username for the user
        """
        self.username = username

    def is_authenticated(self) -> bool:
        """
        Check if the user is authenticated.
        
        Returns:
            True if the user is authenticated
        """
        return True

    def is_active(self) -> bool:
        """
        Check if the user account is active.
        
        Returns:
            True if the user account is active
        """
        return True

    def is_anonymous(self) -> bool:
        """
        Check if the user is anonymous.
        
        Returns:
            False as this represents an authenticated user
        """
        return False

    def get_id(self) -> str:
        """
        Get the user's unique identifier.
        
        Returns:
            The username as the unique identifier
        """
        return self.username

    def __repr__(self) -> str:
        """
        Get string representation of the user.
        
        Returns:
            String representation showing the username
        """
        return f"<User(username='{self.username}')>"

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another user.
        
        Args:
            other: Another object to compare with
            
        Returns:
            True if both users have the same username
        """
        if not isinstance(other, User):
            return False
        return self.username == other.username

    def __hash__(self) -> int:
        """
        Get hash of the user.
        
        Returns:
            Hash based on username
        """
        return hash(self.username)
