"""
EXIF metadata detection module.

This module provides functionality for detecting EXIF metadata in images
from crawled documents. It has been refactored to use the repository pattern
and service layer.

Note: This module is deprecated in favor of DetectionService.
The functionality has been moved to application/services/detection_service.py
"""

import logging
import uuid
from os.path import splitext
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import exifread
import pycurl
from flask import current_app
from homura import download

from application.repositories.document_repository import DocumentRepository
from application.utils.exceptions import DatabaseConnectionError, DocumentNotFoundError

logger = logging.getLogger(__name__)


def set_exif_data(id: str, tags: Dict[str, Any], document_repo: DocumentRepository) -> Optional[bool]:
    """
    Set EXIF data for a document.

    Args:
        id: Document ID
        tags: EXIF tags to set
        document_repo: Document repository instance

    Returns:
        True if successful, None otherwise
    """
    try:
        document_repo.update(id, tags)
        logger.info(f"Set EXIF data for document {id}")
        return True
    except DatabaseConnectionError as e:
        logger.error(f"Database error setting EXIF data for document {id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error setting EXIF data for document {id}: {str(e)}")
        return None


def download_and_detect(
    id: str, url: str, filename: str, document_repo: DocumentRepository, tor_proxy_url: str, tor_proxy_port: int
) -> Optional[bool]:
    """
    Download an image and detect EXIF metadata.

    Args:
        id: Document ID
        url: Image URL to download
        filename: Path to save the downloaded file
        document_repo: Document repository instance
        tor_proxy_url: TOR proxy URL
        tor_proxy_port: TOR proxy port

    Returns:
        True if successful, None otherwise
    """
    try:
        opt = {
            pycurl.PROXY: tor_proxy_url,
            pycurl.PROXYPORT: tor_proxy_port,
            pycurl.PROXYTYPE: pycurl.PROXYTYPE_SOCKS5_HOSTNAME,
        }
        download(url, path=filename, pass_through_opts=opt)

        with open(filename, "rb") as f:
            tags = exifread.process_file(f)
            set_exif_data(id, {"exif": list(tags.keys())}, document_repo)

        logger.info(f"Downloaded and detected EXIF for {url}")
        return True

    except IOError as e:
        logger.error(f"File I/O error downloading {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading and detecting EXIF for {url}: {str(e)}")
        return None


def detect_exif_metadata(id: str, document_repo: DocumentRepository) -> bool:
    """
    Detect EXIF metadata for images in a document.

    This function is deprecated. Use DetectionService.enqueue_exif_detection instead.

    Args:
        id: Document ID
        document_repo: Document repository instance

    Returns:
        True if detection was initiated successfully
    """
    try:
        logger.info(f"EXIF metadata detection initiated for document {id}")

        # Verify document exists
        document = document_repo.find_by_id(id)
        if not document:
            logger.warning(f"Document {id} not found for EXIF detection")
            return False

        # Note: The actual detection logic should use DetectionService
        # This is kept for backward compatibility but should be migrated
        logger.warning("detect_exif_metadata is deprecated. Use DetectionService instead.")

        return True

    except DocumentNotFoundError:
        logger.warning(f"Document {id} not found for EXIF detection")
        return False
    except Exception as e:
        logger.error(f"Error initiating EXIF detection for document {id}: {str(e)}")
        return False
