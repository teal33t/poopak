"""
Screenshot capture module.

This module provides functions for capturing screenshots of web pages
using the Splash rendering service.
"""

import logging

from homura import download

from .config_crawler import get_save_path, get_splash_uri

logger = logging.getLogger(__name__)


def get_screenshot(url: str, filename: str) -> bool:
    """
    Capture a screenshot of a web page.

    Uses the Splash rendering service to capture a PNG screenshot of the
    specified URL through Tor proxy.

    Args:
        url: The URL to capture
        filename: Base filename for the screenshot (without extension)

    Returns:
        True if screenshot was captured successfully, False otherwise
    """
    try:
        splash_uri = get_splash_uri(url)
        save_path = get_save_path(filename)
        download(url=splash_uri, path=save_path)
        logger.info(f"Screenshot captured for {url} at {save_path}")
        return True
    except IOError as e:
        logger.error(f"File I/O error capturing screenshot for {url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error capturing screenshot for {url}: {str(e)}")
        return False
