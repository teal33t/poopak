"""
Crawler configuration module.

This module is deprecated. Please use application.config.settings instead.

This module provides backward compatibility by exposing configuration values
from the centralized settings module as module-level variables.
"""

from typing import Dict

from application.config import settings
from application.config.constants import (
    CONNECTION_TIMEOUT,
    FOLLOWLOCATION,
    HTTP_BAD_REQUEST,
    HTTP_CREATED,
    HTTP_FORBIDDEN,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NOT_FOUND,
    HTTP_OK,
    HTTP_STATUS_DESCRIPTIONS,
    HTTP_UNAUTHORIZED,
    MAX_TRY_COUNT,
    REQUEST_TIMEOUT,
    SPLASH_HOST,
    SPLASH_PORT,
)

# Backward compatibility - expose settings as module-level variables
localhost: str = settings.LOCALHOST
mongodb_uri: str = settings.mongodb_uri
tor_pool_url: str = settings.TOR_POOL_URL
tor_pool_port: int = settings.TOR_POOL_PORT
redis_uri: str = settings.redis_uri

# Splash configuration (from constants)
splash_host: str = SPLASH_HOST
splash_port: int = SPLASH_PORT

# Request configuration (from constants)
max_try_count: int = MAX_TRY_COUNT

# Screenshot path
SCR_PATH: str = settings.SCREENSHOT_UPLOAD_DIR

# HTTP status code descriptions (from constants)
http_codes: Dict[int, str] = HTTP_STATUS_DESCRIPTIONS


def get_splash_uri(url):
    """
    Construct Splash service URI for rendering.

    Args:
        url: URL to render

    Returns:
        Splash service URI
    """
    return "http://%s:%d/render.png?url=%s&proxy=socks5://%s:%d" % (
        splash_host,
        splash_port,
        url,
        tor_pool_url,
        tor_pool_port,
    )


def get_save_path(filename):
    """
    Get screenshot save path.

    Args:
        filename: Base filename

    Returns:
        Full path for screenshot file
    """
    return "%s%s.png" % (SCR_PATH, filename)
