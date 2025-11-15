"""
Detection service for EXIF and text subject detection operations.

This module provides the DetectionService class that orchestrates EXIF metadata
detection and text subject extraction, coordinating between repositories and
queue operations.
"""

import json
import logging
import uuid
from os.path import splitext
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from application.config import Settings
from application.config.constants import QUEUE_HIGH_PRIORITY
from application.infrastructure.queue import QueueFactory, WorkerType
from application.repositories.document_repository import DocumentRepository
from application.utils.exceptions import DatabaseConnectionError, DetectionError, DocumentNotFoundError

logger = logging.getLogger(__name__)


class DetectionService:
    """
    Service for managing EXIF and text subject detection operations.

    Orchestrates detection logic, coordinates between document repository
    and queue operations for asynchronous detection tasks.
    """

    def __init__(self, document_repo: DocumentRepository, queue_factory: QueueFactory, settings: Settings = None):
        """
        Initialize the detection service.

        Args:
            document_repo: Repository for document data access
            queue_factory: Factory for creating queue connections
            settings: Application configuration settings
        """
        if settings is None:
            from application.config import settings as default_settings

            settings = default_settings

        self._document_repo = document_repo
        self._queue_factory = queue_factory
        self._settings = settings
        self._detector_queue = queue_factory.get_queue(WorkerType.DETECTOR, QUEUE_HIGH_PRIORITY)

        logger.info("DetectionService initialized")

    def enqueue_exif_detection(self, document_id: str, image_urls: List[str]) -> int:
        """
        Enqueue EXIF detection jobs for image URLs.

        Creates detection jobs for each image URL associated with a document.
        Each job will download the image and extract EXIF metadata.

        Args:
            document_id: ID of the document containing the images
            image_urls: List of image URLs to process

        Returns:
            Number of detection jobs enqueued

        Raises:
            DetectionError: If enqueueing fails
        """
        try:
            if not image_urls:
                logger.debug(f"No images to process for document {document_id}")
                return 0

            enqueued_count = 0

            for image_url in image_urls:
                try:
                    # Extract file extension from URL
                    parsed_url = urlparse(image_url)
                    _, ext = splitext(parsed_url.path)

                    if not ext:
                        logger.warning(f"No file extension for image URL: {image_url}")
                        continue

                    # Generate unique filename for downloaded image
                    obj_uuid = uuid.uuid4().hex
                    save_path = self._settings.get_exif_save_path(obj_uuid, ext)

                    # Enqueue detection job
                    job = self._detector_queue.enqueue_call(
                        func=self._download_and_detect_exif,
                        args=(document_id, image_url, save_path),
                        ttl=86400,  # 24 hours
                        result_ttl=1,
                    )

                    enqueued_count += 1
                    logger.debug(f"Enqueued EXIF detection job {job.id} for {image_url}")

                except Exception as e:
                    logger.warning(f"Failed to enqueue EXIF detection for {image_url}: {str(e)}")
                    continue

            logger.info(f"Enqueued {enqueued_count} EXIF detection jobs for document {document_id}")
            return enqueued_count

        except Exception as e:
            logger.error(f"Failed to enqueue EXIF detection: {str(e)}")
            raise DetectionError(f"Failed to enqueue EXIF detection: {str(e)}")

    def _download_and_detect_exif(self, document_id: str, image_url: str, save_path: str) -> bool:
        """
        Download an image and extract EXIF metadata.

        This is a worker function that downloads an image through the proxy,
        extracts EXIF tags, and updates the document with the results.

        Args:
            document_id: ID of the document to update
            image_url: URL of the image to download
            save_path: Local path to save the downloaded image

        Returns:
            True if successful, False otherwise
        """
        try:
            import exifread
            import pycurl
            from homura import download

            # Download image through proxy
            opt = {
                pycurl.PROXY: self._settings.TOR_POOL_URL,
                pycurl.PROXYPORT: self._settings.TOR_POOL_PORT,
                pycurl.PROXYTYPE: pycurl.PROXYTYPE_SOCKS5_HOSTNAME,
            }

            logger.info(f"Downloading image from {image_url}")
            download(image_url, path=save_path, pass_through_opts=opt)

            # Extract EXIF data
            with open(save_path, "rb") as f:
                tags = exifread.process_file(f)

            # Update document with EXIF tag keys
            exif_data = {"exif": list(tags.keys())}
            self._document_repo.update(document_id, exif_data)

            logger.info(f"Successfully extracted {len(tags)} EXIF tags from {image_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to download and detect EXIF for {image_url}: {str(e)}")
            return False

    def enqueue_subject_detection(self, document_id: str) -> str:
        """
        Enqueue text subject detection job for a document.

        Creates a job to extract named entities (subjects) from the document's
        body text using the Spacy NLP service.

        Args:
            document_id: ID of the document to process

        Returns:
            Job ID of the enqueued detection task

        Raises:
            DetectionError: If enqueueing fails
        """
        try:
            logger.info(f"Enqueueing subject detection for document {document_id}")

            job = self._detector_queue.enqueue_call(
                func=self._detect_and_update_subjects, args=(document_id,), ttl=86400, result_ttl=1  # 24 hours
            )

            logger.info(f"Subject detection job enqueued with ID: {job.id}")
            return job.id

        except Exception as e:
            logger.error(f"Failed to enqueue subject detection: {str(e)}")
            raise DetectionError(f"Failed to enqueue subject detection: {str(e)}")

    def _detect_and_update_subjects(self, document_id: str) -> bool:
        """
        Detect subjects in document text and update the document.

        This is a worker function that retrieves a document, sends its body
        text to the Spacy NLP service for subject extraction, and updates
        the document with the results.

        Args:
            document_id: ID of the document to process

        Returns:
            True if successful, False otherwise

        Raises:
            DocumentNotFoundError: If document doesn't exist
        """
        try:
            # Retrieve document
            document = self._document_repo.find_by_id(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document {document_id} not found")

            body_text = document.get("body", "")
            if not body_text:
                logger.warning(f"Document {document_id} has no body text")
                return False

            # Extract subjects using Spacy service
            subjects = self._extract_subjects_from_text(body_text)

            # Update document with subjects
            self._document_repo.update(document_id, {"subjects": subjects})

            logger.info(f"Successfully extracted {len(subjects)} subjects from document {document_id}")
            return True

        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to detect and update subjects for document {document_id}: {str(e)}")
            return False

    def _extract_subjects_from_text(self, text: str) -> List[str]:
        """
        Extract subjects (proper nouns) from text using Spacy NLP service.

        Args:
            text: Text to analyze

        Returns:
            List of extracted subject strings

        Raises:
            DetectionError: If Spacy service request fails
        """
        try:
            headers = {"content-type": "application/json"}
            payload = {"text": text, "model": "en"}

            logger.debug(f"Sending text to Spacy service: {self._settings.SPACY_SERVER_URL}")
            response = requests.post(
                self._settings.SPACY_SERVER_URL, data=json.dumps(payload), headers=headers, timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # Extract proper nouns (NNP, NNPS tags)
            subjects = []
            for word in result.get("words", []):
                tag = word.get("tag", "")
                if tag in ("NNP", "NNPS"):
                    subjects.append(word.get("text", ""))

            logger.debug(f"Extracted {len(subjects)} subjects from text")
            return subjects

        except requests.RequestException as e:
            logger.error(f"Spacy service request failed: {str(e)}")
            raise DetectionError(f"Failed to extract subjects: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to parse Spacy response: {str(e)}")
            raise DetectionError(f"Failed to extract subjects: {str(e)}")

    def detect_subjects_sync(self, document_id: str) -> List[str]:
        """
        Synchronously detect subjects in a document.

        This method performs subject detection immediately without using
        the queue system.

        Args:
            document_id: ID of the document to process

        Returns:
            List of extracted subjects

        Raises:
            DocumentNotFoundError: If document doesn't exist
            DetectionError: If detection fails
        """
        try:
            # Retrieve document
            document = self._document_repo.find_by_id(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document {document_id} not found")

            body_text = document.get("body", "")
            if not body_text:
                logger.warning(f"Document {document_id} has no body text")
                return []

            # Extract subjects
            subjects = self._extract_subjects_from_text(body_text)

            # Update document
            self._document_repo.update(document_id, {"subjects": subjects})

            return subjects

        except (DocumentNotFoundError, DetectionError):
            raise
        except Exception as e:
            logger.error(f"Failed to detect subjects: {str(e)}")
            raise DetectionError(f"Failed to detect subjects: {str(e)}")
