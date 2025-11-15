"""
Web application configuration module.

This module is deprecated. Please use application.config.settings instead.
"""

from application.config import settings
from application.config.constants import SPACY_TAG_MAP

# Backward compatibility - expose settings as module-level variables
# Note: n_per_page, seed_upload_dir, and get_exif_save_path have been removed.
# Use settings.ITEMS_PER_PAGE, settings.SEED_UPLOAD_DIR, and settings.get_exif_save_path() instead.
redis_uri = settings.redis_uri
mongodb_uri = settings.mongodb_uri
scr_upload_dir = settings.SCREENSHOT_UPLOAD_DIR
spacy_server_url = settings.SPACY_SERVER_URL
EXIF_PATH = settings.EXIF_PATH
localhost = settings.LOCALHOST
tor_pool_url = settings.TOR_POOL_URL
tor_pool_port = settings.TOR_POOL_PORT


# Re-export SPACY_TAG_MAP from constants for backward compatibility
__all__ = ["SPACY_TAG_MAP"]
