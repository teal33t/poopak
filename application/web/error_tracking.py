"""
Error tracking utilities for production environments.

This module provides utilities for tracking and reporting errors to external
monitoring services like Sentry, Rollbar, or custom logging systems.
"""

import logging
from typing import Any, Dict, Optional

from flask import Flask, request

logger = logging.getLogger(__name__)


class ErrorTracker:
    """
    Error tracking service for production monitoring.

    This class provides a unified interface for error tracking that can be
    integrated with various monitoring services.
    """

    def __init__(self, app: Optional[Flask] = None, enabled: bool = True):
        """
        Initialize error tracker.

        Args:
            app: Flask application instance (optional)
            enabled: Whether error tracking is enabled
        """
        self.enabled = enabled
        self.app = app
        self._sentry_enabled = False
        self._custom_handlers = []

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """
        Initialize error tracking for Flask application.

        Args:
            app: Flask application instance
        """
        self.app = app
        self.enabled = app.config.get("ERROR_TRACKING_ENABLED", False)

        # Initialize Sentry if configured
        sentry_dsn = app.config.get("SENTRY_DSN")
        if sentry_dsn and self.enabled:
            self._init_sentry(sentry_dsn, app)

        # Store tracker in app extensions
        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["error_tracker"] = self

    def _init_sentry(self, dsn: str, app: Flask) -> None:
        """
        Initialize Sentry error tracking.

        Args:
            dsn: Sentry DSN (Data Source Name)
            app: Flask application instance
        """
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration

            sentry_sdk.init(
                dsn=dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=app.config.get("SENTRY_TRACES_SAMPLE_RATE", 0.1),
                environment=app.config.get("ENVIRONMENT", "production"),
                release=app.config.get("APP_VERSION", "unknown"),
            )

            self._sentry_enabled = True
            logger.info("Sentry error tracking initialized")

        except ImportError:
            logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {str(e)}")

    def capture_exception(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: str = "error",
    ) -> None:
        """
        Capture an exception for tracking.

        Args:
            error: The exception to track
            context: Additional context information
            level: Error level (error, warning, info)
        """
        if not self.enabled:
            return

        # Capture with Sentry if enabled
        if self._sentry_enabled:
            self._capture_with_sentry(error, context, level)

        # Call custom handlers
        for handler in self._custom_handlers:
            try:
                handler(error, context, level)
            except Exception as e:
                logger.error(f"Error in custom error handler: {str(e)}")

    def _capture_with_sentry(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: str = "error",
    ) -> None:
        """
        Capture exception with Sentry.

        Args:
            error: The exception to track
            context: Additional context information
            level: Error level
        """
        try:
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                # Add context
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)

                # Add request context if available
                if request:
                    scope.set_context(
                        "request",
                        {
                            "url": request.url,
                            "method": request.method,
                            "headers": dict(request.headers),
                            "remote_addr": request.remote_addr,
                        },
                    )

                # Set level
                scope.level = level

                # Capture exception
                sentry_sdk.capture_exception(error)

        except Exception as e:
            logger.error(f"Failed to capture exception with Sentry: {str(e)}")

    def add_custom_handler(self, handler) -> None:
        """
        Add a custom error handler.

        The handler should be a callable that accepts (error, context, level).

        Args:
            handler: Callable error handler
        """
        self._custom_handlers.append(handler)

    def capture_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        level: str = "info",
    ) -> None:
        """
        Capture a message for tracking.

        Args:
            message: The message to track
            context: Additional context information
            level: Message level (error, warning, info)
        """
        if not self.enabled:
            return

        if self._sentry_enabled:
            try:
                import sentry_sdk

                with sentry_sdk.push_scope() as scope:
                    if context:
                        for key, value in context.items():
                            scope.set_context(key, value)

                    scope.level = level
                    sentry_sdk.capture_message(message)

            except Exception as e:
                logger.error(f"Failed to capture message with Sentry: {str(e)}")


# Global error tracker instance
error_tracker = ErrorTracker()


def init_error_tracking(app: Flask) -> ErrorTracker:
    """
    Initialize error tracking for the application.

    Args:
        app: Flask application instance

    Returns:
        Configured ErrorTracker instance
    """
    tracker = ErrorTracker(app)
    return tracker
