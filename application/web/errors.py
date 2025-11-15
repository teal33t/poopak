"""
Error handlers and error handling utilities for the web application.

This module provides comprehensive error handling including custom error handlers,
error logging with context, and error tracking utilities.
"""

import logging
import traceback
from typing import Any, Dict, Optional, Tuple

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

from application.config.constants import (
    HTTP_BAD_REQUEST,
    HTTP_FORBIDDEN,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NOT_FOUND,
    HTTP_UNAUTHORIZED,
)
from application.utils.exceptions import (
    ApplicationError,
    CrawlerError,
    DatabaseConnectionError,
    DetectionError,
    DocumentNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class ErrorContext:
    """
    Context information for error logging and tracking.

    Captures request context and additional metadata for comprehensive
    error tracking and debugging.
    """

    def __init__(
        self,
        error: Exception,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize error context.

        Args:
            error: The exception that occurred
            endpoint: The endpoint where the error occurred
            user_id: The ID of the user who encountered the error
            additional_data: Additional context data
        """
        self.error = error
        self.error_type = type(error).__name__
        self.error_message = str(error)
        self.endpoint = endpoint or (request.endpoint if request else None)
        self.user_id = user_id
        self.additional_data = additional_data or {}

        # Capture request context if available
        if request:
            self.method = request.method
            self.url = request.url
            self.remote_addr = request.remote_addr
            self.user_agent = request.user_agent.string if request.user_agent else None
        else:
            self.method = None
            self.url = None
            self.remote_addr = None
            self.user_agent = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error context to dictionary for logging.

        Returns:
            Dictionary containing all error context information
        """
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "endpoint": self.endpoint,
            "method": self.method,
            "url": self.url,
            "remote_addr": self.remote_addr,
            "user_agent": self.user_agent,
            "user_id": self.user_id,
            "additional_data": self.additional_data,
        }

    def log(self, level: int = logging.ERROR) -> None:
        """
        Log the error with full context.

        Args:
            level: Logging level (default: ERROR)
        """
        context_dict = self.to_dict()
        logger.log(
            level,
            f"Error occurred: {self.error_type} - {self.error_message}",
            extra={"error_context": context_dict},
            exc_info=True,
        )


def log_error_with_context(
    error: Exception,
    endpoint: Optional[str] = None,
    user_id: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR,
) -> None:
    """
    Log an error with full context information.

    Args:
        error: The exception that occurred
        endpoint: The endpoint where the error occurred
        user_id: The ID of the user who encountered the error
        additional_data: Additional context data
        level: Logging level (default: ERROR)
    """
    error_context = ErrorContext(error, endpoint, user_id, additional_data)
    error_context.log(level)


def get_error_response(
    error: Exception,
    status_code: int,
    title: str,
    description: str,
    log_context: bool = True,
) -> Tuple[str, int]:
    """
    Generate a standardized error response.

    Args:
        error: The exception that occurred
        status_code: HTTP status code to return
        title: Error title for display
        description: Error description for display
        log_context: Whether to log the error with context (default: True)

    Returns:
        Tuple of (rendered template, status code)
    """
    if log_context:
        log_error_with_context(error)

    from .search.forms import SearchForm

    search_form = SearchForm()

    return (
        render_template(
            "error.html",
            title=title,
            code=str(status_code),
            description=description,
            search_form=search_form,
        ),
        status_code,
    )


def register_error_handlers(app: Flask) -> None:
    """
    Register comprehensive error handlers for the application.

    Handles both HTTP exceptions and application-specific exceptions
    with proper logging, user feedback, and status codes.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError) -> Tuple[str, int]:
        """
        Handle CSRF token errors.

        Args:
            e: CSRF error exception

        Returns:
            Tuple of (rendered template, status code)
        """
        logger.warning(f"CSRF error: {str(e)}", extra={"url": request.url if request else None})

        return get_error_response(
            e,
            HTTP_UNAUTHORIZED,
            "Session Expired",
            "Your form session has expired. Please refresh the page and try again.",
            log_context=False,  # Already logged above
        )

    @app.errorhandler(400)
    def handle_bad_request(e: Exception) -> Tuple[str, int]:
        """
        Handle 400 Bad Request errors.

        Args:
            e: Exception that caused the error

        Returns:
            Tuple of (rendered template, status code)
        """
        return get_error_response(
            e,
            HTTP_BAD_REQUEST,
            "Bad Request",
            "The request could not be understood or was missing required parameters.",
        )

    @app.errorhandler(401)
    def handle_unauthorized(e: Exception) -> Tuple[str, int]:
        """
        Handle 401 Unauthorized errors.

        Args:
            e: Exception that caused the error

        Returns:
            Tuple of (rendered template, status code)
        """
        return get_error_response(
            e,
            HTTP_UNAUTHORIZED,
            "Unauthorized",
            "You must be logged in to access this resource.",
        )

    @app.errorhandler(403)
    def handle_forbidden(e: Exception) -> Tuple[str, int]:
        """
        Handle 403 Forbidden errors.

        Args:
            e: Exception that caused the error

        Returns:
            Tuple of (rendered template, status code)
        """
        logger.warning(f"403 Forbidden: {request.url if request else 'unknown URL'}")
        
        from .search.forms import SearchForm
        search_form = SearchForm()
        
        return (
            render_template("errors/403.html", search_form=search_form),
            HTTP_FORBIDDEN,
        )

    @app.errorhandler(404)
    def handle_not_found(e: Exception) -> Tuple[str, int]:
        """
        Handle 404 Not Found errors.

        Args:
            e: Exception that caused the error

        Returns:
            Tuple of (rendered template, status code)
        """
        logger.info(f"404 error: {request.url if request else 'unknown URL'}")

        from .search.forms import SearchForm
        search_form = SearchForm()
        
        return (
            render_template("errors/404.html", search_form=search_form),
            HTTP_NOT_FOUND,
        )

    @app.errorhandler(500)
    def handle_internal_error(e: Exception) -> Tuple[str, int]:
        """
        Handle 500 Internal Server errors.

        Args:
            e: Exception that caused the error

        Returns:
            Tuple of (rendered template, status code)
        """
        log_error_with_context(e)
        
        # Track error in production monitoring
        if hasattr(app, "error_tracker"):
            app.error_tracker.capture_exception(e, level="error")
        
        from .search.forms import SearchForm
        search_form = SearchForm()
        
        return (
            render_template("errors/500.html", search_form=search_form),
            HTTP_INTERNAL_SERVER_ERROR,
        )

    @app.errorhandler(DocumentNotFoundError)
    def handle_document_not_found(e: DocumentNotFoundError) -> Tuple[str, int]:
        """
        Handle DocumentNotFoundError exceptions.

        Args:
            e: DocumentNotFoundError exception

        Returns:
            Tuple of (rendered template, status code)
        """
        logger.warning(f"Document not found: {str(e)}")

        return get_error_response(
            e,
            HTTP_NOT_FOUND,
            "Document Not Found",
            "The requested document could not be found.",
            log_context=False,  # Already logged above
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError) -> Tuple[str, int]:
        """
        Handle ValidationError exceptions.

        Args:
            e: ValidationError exception

        Returns:
            Tuple of (rendered template, status code)
        """
        logger.warning(f"Validation error: {str(e)}")

        return get_error_response(
            e,
            HTTP_BAD_REQUEST,
            "Validation Error",
            f"Invalid input: {str(e)}",
            log_context=False,  # Already logged above
        )

    @app.errorhandler(DatabaseConnectionError)
    def handle_database_error(e: DatabaseConnectionError) -> Tuple[str, int]:
        """
        Handle DatabaseConnectionError exceptions.

        Args:
            e: DatabaseConnectionError exception

        Returns:
            Tuple of (rendered template, status code)
        """
        # Track critical database errors
        if hasattr(app, "error_tracker"):
            app.error_tracker.capture_exception(e, level="error")
        
        return get_error_response(
            e,
            HTTP_INTERNAL_SERVER_ERROR,
            "Database Error",
            "A database error occurred. Please try again later.",
        )

    @app.errorhandler(CrawlerError)
    def handle_crawler_error(e: CrawlerError) -> Tuple[str, int]:
        """
        Handle CrawlerError exceptions.

        Args:
            e: CrawlerError exception

        Returns:
            Tuple of (rendered template, status code)
        """
        return get_error_response(
            e,
            HTTP_INTERNAL_SERVER_ERROR,
            "Crawler Error",
            "An error occurred during crawling. Please try again later.",
        )

    @app.errorhandler(DetectionError)
    def handle_detection_error(e: DetectionError) -> Tuple[str, int]:
        """
        Handle DetectionError exceptions.

        Args:
            e: DetectionError exception

        Returns:
            Tuple of (rendered template, status code)
        """
        return get_error_response(
            e,
            HTTP_INTERNAL_SERVER_ERROR,
            "Detection Error",
            "An error occurred during detection. Please try again later.",
        )

    @app.errorhandler(ApplicationError)
    def handle_application_error(e: ApplicationError) -> Tuple[str, int]:
        """
        Handle generic ApplicationError exceptions.

        This is a catch-all for any custom application errors not
        handled by more specific handlers.

        Args:
            e: ApplicationError exception

        Returns:
            Tuple of (rendered template, status code)
        """
        return get_error_response(
            e,
            HTTP_INTERNAL_SERVER_ERROR,
            "Application Error",
            "An application error occurred. Please try again later.",
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(e: Exception) -> Tuple[str, int]:
        """
        Handle any unexpected exceptions.

        This is the final catch-all handler for any exceptions not
        handled by more specific handlers.

        Args:
            e: Exception that occurred

        Returns:
            Tuple of (rendered template, status code)
        """
        # Log the full traceback for unexpected errors
        logger.critical(
            f"Unexpected error: {type(e).__name__} - {str(e)}",
            exc_info=True,
            extra={
                "traceback": traceback.format_exc(),
                "url": request.url if request else None,
                "method": request.method if request else None,
            },
        )

        # Track unexpected errors in production
        if hasattr(app, "error_tracker"):
            context = {
                "traceback": traceback.format_exc(),
                "url": request.url if request else None,
                "method": request.method if request else None,
            }
            app.error_tracker.capture_exception(e, context=context, level="error")

        return get_error_response(
            e,
            HTTP_INTERNAL_SERVER_ERROR,
            "Unexpected Error",
            "An unexpected error occurred. Please try again later.",
            log_context=False,  # Already logged above with more detail
        )
