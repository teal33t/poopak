"""
Document repository implementation.

This module provides data access methods for document (crawled URL) operations.
"""

import logging
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.database import Database

from application.config.constants import DEFAULT_PAGE_SIZE, HTTP_OK
from application.utils.exceptions import DatabaseConnectionError, DocumentNotFoundError, ValidationError

from .base_repository import BaseRepository

if TYPE_CHECKING:
    from application.services.elasticsearch_service import ElasticsearchService

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository):
    """
    Repository for document data access operations.

    Provides methods for querying, creating, and updating crawled documents
    in the MongoDB database.
    """

    def __init__(self, database: Database, elasticsearch_service: Optional['ElasticsearchService'] = None):
        """
        Initialize the document repository.

        Args:
            database: MongoDB database instance
            elasticsearch_service: Optional Elasticsearch service for automatic indexing
        """
        super().__init__(database, "documents")
        self.elasticsearch_service = elasticsearch_service

    def find_by_id(self, id: Any) -> Optional[Dict[str, Any]]:
        """
        Find a document by its ID.

        Args:
            id: The document ID (ObjectId or string)

        Returns:
            Document dictionary if found, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            if isinstance(id, str):
                id = ObjectId(id)

            document = self.collection.find_one({"_id": id})
            logger.debug(f"Found document with ID {id}: {document is not None}")
            return document
        except Exception as e:
            logger.error(f"Error finding document by ID {id}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to find document: {str(e)}")

    def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Find a document by its URL.

        Args:
            url: The document URL

        Returns:
            Document dictionary if found, None otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            document = self.collection.find_one({"url": url})
            logger.debug(f"Found document with URL {url}: {document is not None}")
            return document
        except Exception as e:
            logger.error(f"Error finding document by URL {url}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to find document: {str(e)}")

    def find_by_status(
        self,
        status: int,
        in_scope: Optional[bool] = None,
        skip: int = 0,
        limit: int = 0,
        sort_by: str = "seen_time",
        sort_order: int = DESCENDING,
    ) -> List[Dict[str, Any]]:
        """
        Find documents by HTTP status code.

        Args:
            status: HTTP status code to filter by
            in_scope: Optional filter by in_scope flag (None = no filter)
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (0 for no limit)
            sort_by: Field to sort by
            sort_order: Sort order (ASCENDING or DESCENDING)

        Returns:
            List of document dictionaries

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            filter_query = {"status": status}
            if in_scope is not None:
                filter_query["in_scope"] = in_scope

            cursor = self.collection.find(filter_query)
            cursor = cursor.sort(sort_by, sort_order)

            if skip > 0:
                cursor = cursor.skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)

            documents = list(cursor)
            logger.debug(f"Found {len(documents)} documents with status {status}")
            return documents
        except Exception as e:
            logger.error(f"Error finding documents by status {status}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to find documents: {str(e)}")

    def find_by_text_search(
        self, phrase: str, skip: int = 0, limit: int = 0, sort_by: str = "seen_time", sort_order: int = DESCENDING
    ) -> List[Dict[str, Any]]:
        """
        Find documents containing a text phrase in the body.

        Args:
            phrase: Text phrase to search for
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (0 for no limit)
            sort_by: Field to sort by
            sort_order: Sort order (ASCENDING or DESCENDING)

        Returns:
            List of document dictionaries

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            regex = f" {phrase} "
            regex_pattern = re.compile(regex, re.IGNORECASE)

            cursor = self.collection.find({"body": regex_pattern})
            cursor = cursor.sort(sort_by, sort_order)

            if skip > 0:
                cursor = cursor.skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)

            documents = list(cursor)
            logger.debug(f"Found {len(documents)} documents matching phrase '{phrase}'")
            return documents
        except Exception as e:
            logger.error(f"Error searching documents for phrase '{phrase}': {str(e)}")
            raise DatabaseConnectionError(f"Failed to search documents: {str(e)}")

    def find_out_of_scope(
        self, skip: int = 0, limit: int = 0, sort_by: str = "seen_time", sort_order: int = DESCENDING
    ) -> List[Dict[str, Any]]:
        """
        Find documents that are out of scope (status 200 but in_scope is False).

        Args:
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (0 for no limit)
            sort_by: Field to sort by
            sort_order: Sort order (ASCENDING or DESCENDING)

        Returns:
            List of document dictionaries

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            filter_query = {"$and": [{"status": HTTP_OK}, {"in_scope": {"$eq": False}}]}
            cursor = self.collection.find(filter_query)
            cursor = cursor.sort(sort_by, sort_order)

            if skip > 0:
                cursor = cursor.skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)

            documents = list(cursor)
            logger.debug(f"Found {len(documents)} out-of-scope documents")
            return documents
        except Exception as e:
            logger.error(f"Error finding out-of-scope documents: {str(e)}")
            raise DatabaseConnectionError(f"Failed to find documents: {str(e)}")

    def find_latest(self, limit: int = DEFAULT_PAGE_SIZE, status: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find the most recently seen documents.

        Args:
            limit: Maximum number of documents to return
            status: Optional HTTP status code filter

        Returns:
            List of document dictionaries sorted by seen_time descending

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            filter_query = {"status": status} if status else {}
            cursor = self.collection.find(filter_query)
            cursor = cursor.sort("seen_time", DESCENDING).limit(limit)

            documents = list(cursor)
            logger.debug(f"Found {len(documents)} latest documents")
            return documents
        except Exception as e:
            logger.error(f"Error finding latest documents: {str(e)}")
            raise DatabaseConnectionError(f"Failed to find documents: {str(e)}")

    def find_all(
        self,
        filter: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 0,
        sort_by: str = "seen_time",
        sort_order: int = DESCENDING,
    ) -> List[Dict[str, Any]]:
        """
        Find all documents matching the filter.

        Args:
            filter: MongoDB query filter (None for all documents)
            skip: Number of documents to skip (for pagination)
            limit: Maximum number of documents to return (0 for no limit)
            sort_by: Field to sort by
            sort_order: Sort order (ASCENDING or DESCENDING)

        Returns:
            List of document dictionaries

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            filter_query = filter if filter else {}
            cursor = self.collection.find(filter_query)
            cursor = cursor.sort(sort_by, sort_order)

            if skip > 0:
                cursor = cursor.skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)

            documents = list(cursor)
            logger.debug(f"Found {len(documents)} documents")
            return documents
        except Exception as e:
            logger.error(f"Error finding documents: {str(e)}")
            raise DatabaseConnectionError(f"Failed to find documents: {str(e)}")

    def create(self, data: Dict[str, Any]) -> str:
        """
        Create a new document.

        Args:
            data: Document data to insert

        Returns:
            ID of the created document as string

        Raises:
            ValidationError: If data validation fails
            DatabaseConnectionError: If database operation fails
        """
        try:
            if not data.get("url"):
                raise ValidationError("Document must have a URL")

            result = self.collection.insert_one(data)
            document_id = str(result.inserted_id)
            logger.info(f"Created document with ID {document_id}")
            
            # Index document in Elasticsearch if service is available
            if self.elasticsearch_service:
                try:
                    # Add _id to document data for indexing
                    doc_with_id = {**data, '_id': result.inserted_id}
                    self.elasticsearch_service.index_document(document_id, doc_with_id)
                except Exception as es_error:
                    logger.error(f"Failed to index document {document_id} in Elasticsearch: {es_error}")
                    # Don't raise - allow create operation to succeed even if indexing fails
            
            return document_id
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            raise DatabaseConnectionError(f"Failed to create document: {str(e)}")

    def update(self, id: Any, data: Dict[str, Any]) -> bool:
        """
        Update an existing document.

        Args:
            id: The document ID to update
            data: Fields to update

        Returns:
            True if document was updated, False otherwise

        Raises:
            DocumentNotFoundError: If document with given ID doesn't exist
            DatabaseConnectionError: If database operation fails
        """
        try:
            if isinstance(id, str):
                id = ObjectId(id)

            result = self.collection.update_one({"_id": id}, {"$set": data}, upsert=False)

            if result.matched_count == 0:
                raise DocumentNotFoundError(f"Document with ID {id} not found")

            logger.info(f"Updated document with ID {id}")
            
            # Update document in Elasticsearch if service is available
            if self.elasticsearch_service and result.modified_count > 0:
                try:
                    # Fetch the updated document to get complete data
                    updated_doc = self.collection.find_one({"_id": id})
                    if updated_doc:
                        self.elasticsearch_service.update_document(str(id), updated_doc)
                except Exception as es_error:
                    logger.error(f"Failed to update document {id} in Elasticsearch: {es_error}")
                    # Don't raise - allow update operation to succeed even if indexing fails
            
            return result.modified_count > 0
        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating document {id}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to update document: {str(e)}")

    def update_by_url(self, url: str, data: Dict[str, Any]) -> bool:
        """
        Update a document by its URL.

        Args:
            url: The document URL
            data: Fields to update

        Returns:
            True if document was updated, False otherwise

        Raises:
            DocumentNotFoundError: If document with given URL doesn't exist
            DatabaseConnectionError: If database operation fails
        """
        try:
            result = self.collection.update_one({"url": url}, {"$set": data}, upsert=False)

            if result.matched_count == 0:
                raise DocumentNotFoundError(f"Document with URL {url} not found")

            logger.info(f"Updated document with URL {url}")
            
            # Update document in Elasticsearch if service is available
            if self.elasticsearch_service and result.modified_count > 0:
                try:
                    # Fetch the updated document to get complete data including ID
                    updated_doc = self.collection.find_one({"url": url})
                    if updated_doc:
                        doc_id = str(updated_doc['_id'])
                        self.elasticsearch_service.update_document(doc_id, updated_doc)
                except Exception as es_error:
                    logger.error(f"Failed to update document with URL {url} in Elasticsearch: {es_error}")
                    # Don't raise - allow update operation to succeed even if indexing fails
            
            return result.modified_count > 0
        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating document by URL {url}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to update document: {str(e)}")

    def add_report(self, id: Any, report_data: Dict[str, Any]) -> bool:
        """
        Add a report to a document's tags array.

        Args:
            id: The document ID
            report_data: Report data to add (should contain 'report_body' and 'report_date')

        Returns:
            True if report was added successfully

        Raises:
            DocumentNotFoundError: If document with given ID doesn't exist
            DatabaseConnectionError: If database operation fails
        """
        try:
            if isinstance(id, str):
                id = ObjectId(id)

            result = self.collection.update_one({"_id": id}, {"$push": {"tags": report_data}})

            if result.matched_count == 0:
                raise DocumentNotFoundError(f"Document with ID {id} not found")

            logger.info(f"Added report to document with ID {id}")
            return result.modified_count > 0
        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error adding report to document {id}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to add report: {str(e)}")

    def delete(self, id: Any) -> bool:
        """
        Delete a document by its ID.

        Args:
            id: The document ID to delete

        Returns:
            True if document was deleted, False otherwise

        Raises:
            DocumentNotFoundError: If document with given ID doesn't exist
            DatabaseConnectionError: If database operation fails
        """
        try:
            if isinstance(id, str):
                id = ObjectId(id)

            result = self.collection.delete_one({"_id": id})

            if result.deleted_count == 0:
                raise DocumentNotFoundError(f"Document with ID {id} not found")

            logger.info(f"Deleted document with ID {id}")
            
            # Delete document from Elasticsearch if service is available
            if self.elasticsearch_service:
                try:
                    self.elasticsearch_service.delete_document(str(id))
                except Exception as es_error:
                    logger.error(f"Failed to delete document {id} from Elasticsearch: {es_error}")
                    # Don't raise - allow delete operation to succeed even if ES deletion fails
            
            return True
        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting document {id}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to delete document: {str(e)}")

    def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching the filter.

        Args:
            filter: MongoDB query filter (None for all documents)

        Returns:
            Number of documents matching the filter

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            filter_query = filter if filter else {}
            count = self.collection.count_documents(filter_query)
            logger.debug(f"Counted {count} documents")
            return count
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}")
            raise DatabaseConnectionError(f"Failed to count documents: {str(e)}")

    def count_by_text_search(self, phrase: str) -> int:
        """
        Count documents containing a text phrase in the body.

        Args:
            phrase: Text phrase to search for

        Returns:
            Number of documents matching the phrase

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            regex = f" {phrase} "
            regex_pattern = re.compile(regex, re.IGNORECASE)
            count = self.collection.count_documents({"body": regex_pattern})
            logger.debug(f"Counted {count} documents matching phrase '{phrase}'")
            return count
        except Exception as e:
            logger.error(f"Error counting documents for phrase '{phrase}': {str(e)}")
            raise DatabaseConnectionError(f"Failed to count documents: {str(e)}")

    def url_exists(self, url: str) -> bool:
        """
        Check if a URL exists in the database.

        Args:
            url: The URL to check

        Returns:
            True if URL exists, False otherwise

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        return self.exists({"url": url})

    def get_last_crawled_time(self) -> Optional[Any]:
        """
        Get the timestamp of the most recently crawled document.

        Returns:
            The seen_time of the most recent document, or None if no documents exist

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            cursor = self.collection.find().sort("seen_time", DESCENDING).limit(1)
            documents = list(cursor)
            
            if documents:
                return documents[0].get("seen_time")
            return None
        except Exception as e:
            logger.error(f"Error getting last crawled time: {str(e)}")
            raise DatabaseConnectionError(f"Failed to get last crawled time: {str(e)}")
