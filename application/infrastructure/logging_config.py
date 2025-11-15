"""
Logging configuration for the web crawler application.

This module provides centralized logging setup with rotating file handlers
and consistent formatters.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def configure_logging(
    app=None,
    log_level: int = logging.INFO,
    log_file: str = "logs/app.log",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 3,
) -> None:
    """
    Configure application logging with rotating file handler.

    Sets up logging with both file and console handlers. File handler uses
    rotation to prevent log files from growing too large.

    Args:
        app: Flask application instance (optional)
        log_level: Logging level (default: INFO)
        log_file: Path to log file (default: 'logs/app.log')
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 3)
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Configure file handler with rotation
    file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # If Flask app is provided, configure app logger
    if app is not None:
        app.logger.handlers.clear()
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(log_level)
        app.logger.info("Logging configured for Flask application")

    logging.info(f"Logging configured: level={logging.getLevelName(log_level)}, file={log_file}")


def get_logger(name: str, log_level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__ of the module)
        log_level: Optional logging level override

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    if log_level is not None:
        logger.setLevel(log_level)

    return logger
