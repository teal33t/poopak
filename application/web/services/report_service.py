"""
Report service for handling document reporting business logic.

This service coordinates report operations including validation,
submission, and document retrieval for reporting.
"""

import datetime
import logging
from typing import Dict, Optional

from application.repositories.document_repository import DocumentRepository
from application.utils.exceptions import (
    DatabaseConnectionError,
    DocumentNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service for document reporting operations.
    
    Handles business logic for reporting documents, including validation
    and coordination with the document repository.
    """

    def __init__(self, document_repository: DocumentRepository):
        """
        Initialize the report service.
        
        Args:
            document_repository: Repository for document data access
        """
        self.document_repository = document_repository

    def validate_document_id(self, document_id: str) -> bool:
        """
        Validate document ID format.
        
        Args:
            document_id: Document ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not document_id or len(document_id) != 24:
            return False
        return True

    def get_document_for_report(self, document_id: str) -> Dict:
        """
        Retrieve a document for reporting.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Document dictionary
            
        Raises:
            ValidationError: If document ID format is invalid
            DocumentNotFoundError: If document is not found
            DatabaseConnectionError: If database connection fails
        """
        # Validate document ID format
        if not self.validate_document_id(document_id):
            logger.warning(f"Invalid document ID format for report: {document_id}")
            raise ValidationError("Invalid document ID format")

        try:
            document = self.document_repository.find_by_id(document_id)
            
            if not document:
                logger.warning(f"Document not found for report: {document_id}")
                raise DocumentNotFoundError(f"Document {document_id} not found")
            
            return document
            
        except DocumentNotFoundError:
            raise
        except DatabaseConnectionError as e:
            logger.error(
                f"Database error retrieving document for report {document_id}: {str(e)}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving document for report {document_id}: {str(e)}"
            )
            raise DatabaseConnectionError(
                f"Failed to retrieve document: {str(e)}"
            )

    def submit_report(self, document_id: str, report_body: str) -> bool:
        """
        Submit a report for a document.
        
        Args:
            document_id: ID of the document being reported
            report_body: Report description text
            
        Returns:
            True if report was submitted successfully
            
        Raises:
            ValidationError: If document ID format is invalid
            DocumentNotFoundError: If document is not found
            DatabaseConnectionError: If database connection fails
        """
        # Validate document ID format
        if not self.validate_document_id(document_id):
            logger.warning(f"Invalid document ID format for report: {document_id}")
            raise ValidationError("Invalid document ID format")

        try:
            report_data = {
                "report_body": report_body,
                "report_date": datetime.datetime.utcnow(),
            }
            
            self.document_repository.add_report(document_id, report_data)
            logger.info(f"Document {document_id} reported successfully")
            
            return True
            
        except DocumentNotFoundError as e:
            logger.warning(f"Document not found when saving report: {document_id}")
            raise
        except DatabaseConnectionError as e:
            logger.error(
                f"Database error saving report for document {document_id}: {str(e)}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error saving report for document {document_id}: {str(e)}"
            )
            raise DatabaseConnectionError(f"Failed to submit report: {str(e)}")
