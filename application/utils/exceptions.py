"""
Custom exception classes for the application.

This module defines domain-specific exceptions used throughout the application
for better error handling and debugging.
"""


class ApplicationError(Exception):
    """
    Base exception for all application errors.

    All custom exceptions should inherit from this class to allow
    catching all application-specific errors with a single except clause.
    """

    pass


class DocumentNotFoundError(ApplicationError):
    """
    Raised when a requested document is not found in the database.

    This exception should be raised by repository methods when a document
    lookup by ID or URL returns no results.
    """

    pass


class CrawlerError(ApplicationError):
    """
    Raised when the crawler encounters an error during operation.

    This includes errors during URL fetching, parsing, or data extraction.
    """

    pass


class DatabaseConnectionError(ApplicationError):
    """
    Raised when database connection fails or is lost.

    This exception indicates issues with connecting to or communicating
    with the MongoDB database.
    """

    pass


class ValidationError(ApplicationError):
    """
    Raised when data validation fails.

    This exception should be raised when input data does not meet
    required validation criteria.
    """

    pass


class DetectionError(ApplicationError):
    """
    Raised when detection operations (EXIF, subject detection) fail.

    This exception indicates issues during detection job enqueueing
    or processing.
    """

    pass
