"""
URL utility functions for the application.

This module provides utility functions for URL processing and extraction,
particularly for onion URLs used in the web crawler.
"""

import re
from typing import List, Pattern
from urllib.parse import urlparse, urlunparse


def extract_onions(text: str) -> List[str]:
    """
    Extract onion URLs from text.

    Searches for onion URLs in the provided text using regex pattern matching.
    Supports URLs with or without protocol (http/https) and with or without www prefix.

    Args:
        text: The text content to search for onion URLs

    Returns:
        A list of onion URLs found in the text. Returns empty list if no URLs found.

    Example:
        >>> extract_onions("Visit http://example.onion for more info")
        ['http://example.onion']
        >>> extract_onions("Check example.onion and test.onion")
        ['example.onion', 'test.onion']
    """
    onion_urls: List[str] = []
    pattern = r"(?:https?://)?(?:www)?(\S*?\.onion)\b"

    for match in re.finditer(pattern, text, re.M | re.IGNORECASE):
        url = str(match.group(0))
        onion_urls.append(url)

    return onion_urls


def build_search_regex(phrase: str) -> Pattern:
    """
    Build a regex pattern for searching text content.

    Creates a case-insensitive regex pattern with word boundaries
    for searching the given phrase in document bodies.

    Args:
        phrase: The search phrase

    Returns:
        Compiled regex pattern for searching

    Example:
        >>> pattern = build_search_regex("test")
        >>> bool(pattern.search(" test "))
        True
    """
    regex = f" {phrase} "
    return re.compile(regex, re.IGNORECASE)


def normalize_url(url: str) -> str:
    """
    Normalize a URL by ensuring it has a scheme.

    If the URL doesn't have a scheme (http/https), adds 'http://' prefix.

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL with scheme

    Example:
        >>> normalize_url("example.onion")
        'http://example.onion'
        >>> normalize_url("http://example.onion")
        'http://example.onion'
    """
    url = url.strip()
    parsed_url = urlparse(url)
    
    if not parsed_url.scheme or parsed_url.scheme == "":
        url = f"http://{url}"
    
    return url


def is_valid_onion_url(url: str) -> bool:
    """
    Validate if a URL is a valid Onion v3 address.

    Checks if the URL contains .onion domain and has exactly 56 characters
    for the hostname portion (excluding .onion suffix). Only Onion v3 addresses
    are supported as v2 addresses were deprecated in October 2021.

    Args:
        url: The URL to validate

    Returns:
        True if valid Onion v3 URL, False otherwise

    Example:
        >>> is_valid_onion_url("http://3g2upl4pq6kufc4m4i2nlhb5hcf32xxxxxxxxxxxxxxxxxxxxxxxx.onion")
        True
        >>> is_valid_onion_url("http://xxxxxxxxxxxxxxxx.onion")
        False
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # Check if it contains .onion
    if ".onion" not in url.lower():
        return False
    
    # Extract the onion address part
    parsed = urlparse(url)
    netloc = parsed.netloc if parsed.netloc else url
    
    # Remove .onion suffix to get the address
    if netloc.lower().endswith(".onion"):
        onion_address = netloc[:-6]  # Remove ".onion"
        # Onion v3 addresses are exactly 56 characters
        # v2 addresses (16 chars) are no longer supported
        return len(onion_address) == 56
    
    return False
