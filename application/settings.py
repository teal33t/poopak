"""
Application settings module.

This module is deprecated. Please use application.config.settings instead.
"""

from application.config import settings

# Backward compatibility
redis_url = settings.redis_uri
