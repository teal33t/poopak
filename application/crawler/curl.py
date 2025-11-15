"""
HTTP request module using pycurl.

This module provides functions for making HTTP requests through Tor proxy
using pycurl library for web crawling operations.
"""

import datetime
import io
import logging
from typing import Any, Dict, List

import pycurl

from application.config.constants import DEFAULT_USER_AGENT, HTTP_OK, HTTP_SERVICE_UNAVAILABLE, MAX_RETRY_SENTINEL

from .config_crawler import *

logger = logging.getLogger(__name__)


def get_headers() -> List[str]:
    """
    Get HTTP headers for requests.

    Returns:
        List of HTTP header strings including User-Agent and Connection headers
    """
    headers = ["Connection: close", "User-Agent: %s" % DEFAULT_USER_AGENT]
    return headers


def query(url: str) -> Dict[str, Any]:
    """
    Fetch a URL through Tor proxy using pycurl.

    Makes HTTP request to the specified URL through Tor SOCKS5 proxy with
    retry logic. Returns response data including HTML content and status code.

    Args:
        url: The URL to fetch

    Returns:
        Dictionary containing:
            - url: The requested URL
            - html: HTML content (only for 200 responses)
            - status: HTTP status code
            - seen_time: Timestamp when the request was made

    Note:
        Retries up to max_try_count times on pycurl errors.
        Returns status 503 if all retries fail.
    """

    output = io.BytesIO()
    seen_time = datetime.datetime.utcnow()

    try_count = 0
    resp = None

    while try_count < max_try_count:
        try:
            query = pycurl.Curl()
            query.setopt(pycurl.URL, url)
            query.setopt(pycurl.CONNECTTIMEOUT, CONNECTION_TIMEOUT)
            query.setopt(pycurl.TIMEOUT, REQUEST_TIMEOUT)
            query.setopt(pycurl.FOLLOWLOCATION, FOLLOWLOCATION)
            query.setopt(pycurl.HTTPHEADER, get_headers())
            query.setopt(pycurl.PROXY, tor_pool_url)
            query.setopt(pycurl.PROXYPORT, tor_pool_port)
            query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
            query.setopt(pycurl.WRITEFUNCTION, output.write)
            query.perform()

            http_code = query.getinfo(pycurl.HTTP_CODE)
            response = output.getvalue()
            html = response.decode("utf8")

            if http_code in http_codes:
                if http_code == HTTP_OK:
                    resp = {"url": url, "html": html, "status": http_code, "seen_time": seen_time}
                    logger.info(f"Successfully fetched {url} with status {http_code}")
                    try_count = MAX_RETRY_SENTINEL
                else:
                    resp = {"url": url, "status": http_code, "seen_time": seen_time}
                    logger.info(f"Fetched {url} with status {http_code}")
                    try_count = MAX_RETRY_SENTINEL

        except pycurl.error as e:
            try_count = try_count + 1
            logger.warning(f"pycurl error fetching {url} (attempt {try_count}/{max_try_count}): {str(e)}")
            resp = {"url": url, "status": HTTP_SERVICE_UNAVAILABLE, "seen_time": seen_time}

        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error for {url}: {str(e)}")
            resp = {"url": url, "status": HTTP_SERVICE_UNAVAILABLE, "seen_time": seen_time}
            try_count = MAX_RETRY_SENTINEL

        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            try_count = try_count + 1
            resp = {"url": url, "status": HTTP_SERVICE_UNAVAILABLE, "seen_time": seen_time}

    if try_count >= max_try_count and resp:
        logger.error(f"Failed to fetch {url} after {max_try_count} attempts")

    return resp
