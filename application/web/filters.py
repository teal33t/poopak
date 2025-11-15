"""
Jinja2 template filters for the web application.

This module provides custom filters for use in Jinja2 templates.
"""

from datetime import datetime
from typing import Optional

from pytz import timezone


def datetimeformat(value: Optional[datetime], format: str = "%d-%m-%Y - %H:%M:%S") -> Optional[str]:
    """
    Format a datetime value as a string.

    Args:
        value: Datetime value to format
        format: Format string (default: "%d-%m-%Y - %H:%M:%S")

    Returns:
        Formatted datetime string or None if value is None
    """
    if value:
        value = value.replace(tzinfo=timezone("UTC"))
        return value.strftime(format)
    return None


def limitbody(value: Optional[str], size: int = 700) -> Optional[str]:
    """
    Limit body text to a specified size.

    Args:
        value: Text to limit
        size: Maximum size (default: 700)

    Returns:
        Truncated text with "..." appended or None if value is None
    """
    if value:
        body = value.strip()
        return f"{body[:size]}..."
    return None
