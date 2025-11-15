"""
Text subject detection module using Spacy NLP service.

This module provides functionality for extracting named entities (subjects)
from document text using the Spacy NLP service. It has been refactored to
use the repository pattern and service layer.

Note: This module is deprecated in favor of DetectionService.
The functionality has been moved to application/services/detection_service.py
"""

import json
import logging
from typing import Any, Dict, List

import requests

from application.config.constants import SPACY_NNP_TAG, SPACY_NNPS_TAG
from application.repositories.document_repository import DocumentRepository
from application.utils.exceptions import DatabaseConnectionError, DetectionError, DocumentNotFoundError

logger = logging.getLogger(__name__)


def _text_subject(id: str, document_repo: DocumentRepository, spacy_url: str) -> bool:
    """
    Extract text subjects for a document.

    Args:
        id: Document ID
        document_repo: Document repository instance
        spacy_url: URL of the Spacy service

    Returns:
        True if successful, False otherwise
    """
    try:
        detector = SpacyDetector(id, document_repo, spacy_url)
        return detector.get_subjects_and_update()
    except Exception as e:
        logger.error(f"Error extracting text subjects for document {id}: {str(e)}")
        return False


class SpacyDetector:
    """
    Detector for extracting named entities (subjects) from document text using Spacy.

    This class has been refactored to use the repository pattern instead of
    direct MongoDB client access.
    """

    def __init__(self, id: str, document_repo: DocumentRepository, spacy_url: str) -> None:
        """
        Initialize the Spacy detector.

        Args:
            id: Document ID to process
            document_repo: Document repository instance
            spacy_url: URL of the Spacy service

        Raises:
            DocumentNotFoundError: If document cannot be retrieved
        """
        try:
            self.document_repo = document_repo
            self.id = id
            self.spacy_url = spacy_url

            result = self.document_repo.find_by_id(id)
            if not result:
                raise DocumentNotFoundError(f"Document {id} not found")

            self.whole_text = result.get("body", "")
            logger.info(f"Initialized SpacyDetector for document {id}")

        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error initializing SpacyDetector for document {id}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to initialize SpacyDetector: {str(e)}")

    def _get_spacy_subj(self) -> Dict[str, Any]:
        """
        Call Spacy service to extract subjects.

        Returns:
            Dictionary with Spacy analysis results

        Raises:
            DetectionError: If Spacy service call fails
        """
        try:
            headers = {"content-type": "application/json"}
            payload = {"text": self.whole_text, "model": "en"}

            logger.debug(f"Calling Spacy service for document {self.id}")
            response = requests.post(self.spacy_url, data=json.dumps(payload), headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result

        except requests.RequestException as e:
            logger.error(f"Spacy service request failed for document {self.id}: {str(e)}")
            raise DetectionError(f"Failed to call Spacy service: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing Spacy response for document {self.id}: {str(e)}")
            raise DetectionError(f"Failed to parse Spacy response: {str(e)}")

    def get_subjects(self) -> Dict[str, List[str]]:
        """
        Extract subjects (proper nouns) from the document text.

        Returns:
            Dictionary with 'subjects' key containing list of extracted subjects
        """
        try:
            resp = self._get_spacy_subj()
            subjects = []

            for item in resp.get("words", []):
                if item.get("tag") in [SPACY_NNP_TAG, SPACY_NNPS_TAG]:
                    subjects.append(item["text"])

            logger.info(f"Extracted {len(subjects)} subjects from document {self.id}")
            return {"subjects": subjects}

        except Exception as e:
            logger.error(f"Error extracting subjects for document {self.id}: {str(e)}")
            raise

    def get_subjects_and_update(self) -> bool:
        """
        Extract subjects and update the document in the database.

        Returns:
            True if successful, False otherwise
        """
        try:
            subject_data = self.get_subjects()
            self.document_repo.update(self.id, subject_data)
            logger.info(f"Updated document {self.id} with extracted subjects")
            return True

        except DatabaseConnectionError as e:
            logger.error(f"Database error updating subjects for document {self.id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating subjects for document {self.id}: {str(e)}")
            return False
