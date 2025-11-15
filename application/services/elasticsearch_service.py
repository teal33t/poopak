"""
Elasticsearch service for document indexing and search operations.

This module provides a service layer for interacting with Elasticsearch,
including document indexing, searching, and index management.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """
    Service for managing Elasticsearch operations.

    Handles document indexing, searching, and index management with
    connection error handling and retry logic.
    """

    def __init__(self, hosts: List[str], index_name: str, timeout: int = 30):
        """
        Initialize Elasticsearch service.

        Args:
            hosts: List of Elasticsearch host URLs
            index_name: Name of the Elasticsearch index
            timeout: Connection timeout in seconds (default: 30)
        """
        self.hosts = hosts
        self.index_name = index_name
        self.timeout = timeout
        self.client = None
        self._available = False

        try:
            from elasticsearch import Elasticsearch

            self.client = Elasticsearch(
                hosts=self.hosts,
                timeout=self.timeout,
                max_retries=3,
                retry_on_timeout=True,
            )

            # Test connection
            if self.client.ping():
                self._available = True
                logger.info(f"Elasticsearch connection established: {self.hosts}")
            else:
                logger.warning(f"Elasticsearch ping failed: {self.hosts}")

        except ImportError:
            logger.error("Elasticsearch package not installed. Install with: pip install elasticsearch")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch client: {e}")

    def is_available(self) -> bool:
        """
        Check if Elasticsearch is available and healthy.

        Returns:
            True if Elasticsearch is available, False otherwise
        """
        if not self._available or not self.client:
            return False

        try:
            return self.client.ping()
        except Exception as e:
            logger.warning(f"Elasticsearch health check failed: {e}")
            return False

    def create_index(self) -> bool:
        """
        Create Elasticsearch index with document mapping.

        Creates the index if it doesn't exist with appropriate field mappings
        for document search.

        Returns:
            True if index was created or already exists, False on error
        """
        if not self.is_available():
            logger.warning("Cannot create index: Elasticsearch unavailable")
            return False

        try:
            # Check if index already exists
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"Index '{self.index_name}' already exists")
                return True

            # Define index mapping
            mapping = {
                "mappings": {
                    "properties": {
                        "url": {"type": "keyword"},
                        "netloc": {"type": "keyword"},
                        "title": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                        "body": {"type": "text", "analyzer": "standard"},
                        "status": {"type": "integer"},
                        "is_onion": {"type": "boolean"},
                        "in_scope": {"type": "boolean"},
                        "seen_time": {"type": "date"},
                        "emails": {"type": "keyword"},
                        "capture_id": {"type": "keyword"},
                    }
                }
            }

            # Create index
            self.client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Created Elasticsearch index: {self.index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create index '{self.index_name}': {e}")
            return False

    def _transform_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform MongoDB document to Elasticsearch format.

        Removes unnecessary fields and converts ObjectId to string.

        Args:
            document: MongoDB document dictionary

        Returns:
            Transformed document for Elasticsearch indexing
        """
        # Create a copy to avoid modifying original
        es_doc = {}

        # Fields to index in Elasticsearch
        fields_to_index = [
            "url",
            "netloc",
            "title",
            "body",
            "status",
            "is_onion",
            "in_scope",
            "seen_time",
            "emails",
            "capture_id",
        ]

        for field in fields_to_index:
            if field in document:
                value = document[field]

                # Convert datetime to ISO format string
                if field == "seen_time" and value is not None:
                    if hasattr(value, "isoformat"):
                        es_doc[field] = value.isoformat()
                    else:
                        es_doc[field] = value
                else:
                    es_doc[field] = value

        return es_doc

    def _retry_operation(self, operation, *args, max_retries: int = 3, **kwargs) -> bool:
        """
        Retry an operation with exponential backoff.

        Args:
            operation: Function to retry
            *args: Positional arguments for operation
            max_retries: Maximum number of retry attempts (default: 3)
            **kwargs: Keyword arguments for operation

        Returns:
            True if operation succeeded, False otherwise
        """
        for attempt in range(max_retries):
            try:
                operation(*args, **kwargs)
                return True
            except Exception as e:
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Operation failed after {max_retries} attempts")

        return False

    def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        Index a single document in Elasticsearch.

        Args:
            doc_id: Document ID (MongoDB ObjectId as string)
            document: Document data dictionary

        Returns:
            True if indexing succeeded, False otherwise
        """
        if not self.is_available():
            logger.warning(f"Cannot index document {doc_id}: Elasticsearch unavailable")
            return False

        try:
            # Transform document for Elasticsearch
            es_doc = self._transform_document(document)

            # Index with retry logic
            def _index():
                self.client.index(index=self.index_name, id=doc_id, body=es_doc)

            success = self._retry_operation(_index)

            if success:
                logger.debug(f"Indexed document: {doc_id}")
            else:
                logger.error(f"Failed to index document: {doc_id}")

            return success

        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            return False

    def update_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        Update an existing document in Elasticsearch.

        Args:
            doc_id: Document ID (MongoDB ObjectId as string)
            document: Updated document data dictionary

        Returns:
            True if update succeeded, False otherwise
        """
        if not self.is_available():
            logger.warning(f"Cannot update document {doc_id}: Elasticsearch unavailable")
            return False

        try:
            # Transform document for Elasticsearch
            es_doc = self._transform_document(document)

            # Update with retry logic
            def _update():
                self.client.update(index=self.index_name, id=doc_id, body={"doc": es_doc, "doc_as_upsert": True})

            success = self._retry_operation(_update)

            if success:
                logger.debug(f"Updated document: {doc_id}")
            else:
                logger.error(f"Failed to update document: {doc_id}")

            return success

        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from Elasticsearch.

        Args:
            doc_id: Document ID (MongoDB ObjectId as string)

        Returns:
            True if deletion succeeded, False otherwise
        """
        if not self.is_available():
            logger.warning(f"Cannot delete document {doc_id}: Elasticsearch unavailable")
            return False

        try:

            def _delete():
                self.client.delete(index=self.index_name, id=doc_id, ignore=[404])

            success = self._retry_operation(_delete)

            if success:
                logger.debug(f"Deleted document: {doc_id}")
            else:
                logger.error(f"Failed to delete document: {doc_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False

    def search(self, query: str, skip: int = 0, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search documents using full-text search.

        Searches across title, body, and url fields with relevance scoring.

        Args:
            query: Search query string
            skip: Number of results to skip (for pagination)
            limit: Maximum number of results to return

        Returns:
            Tuple of (list of matching documents, total count)
        """
        if not self.is_available():
            logger.warning("Cannot search: Elasticsearch unavailable")
            return [], 0

        try:
            # Build multi-field search query
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "body^2", "url"],  # Boost title and body
                        "type": "best_fields",
                        "operator": "or",
                    }
                },
                "from": skip,
                "size": limit,
                "sort": [{"_score": {"order": "desc"}}],
            }

            # Execute search
            response = self.client.search(index=self.index_name, body=search_body)

            # Transform results
            documents = []
            for hit in response["hits"]["hits"]:
                doc = hit["_source"]
                doc["_id"] = hit["_id"]  # Add document ID
                doc["_score"] = hit["_score"]  # Add relevance score
                documents.append(doc)

            total_count = response["hits"]["total"]["value"]

            logger.debug(f"Search query '{query}' returned {len(documents)} results (total: {total_count})")

            return documents, total_count

        except Exception as e:
            logger.error(f"Error executing search query '{query}': {e}")
            return [], 0

    def bulk_index(self, documents: List[Dict[str, Any]], batch_size: int = 1000) -> int:
        """
        Bulk index multiple documents.

        Processes documents in batches for efficient indexing.

        Args:
            documents: List of document dictionaries (must include '_id' field)
            batch_size: Number of documents per batch (default: 1000)

        Returns:
            Number of successfully indexed documents
        """
        if not self.is_available():
            logger.warning("Cannot bulk index: Elasticsearch unavailable")
            return 0

        if not documents:
            logger.info("No documents to index")
            return 0

        try:
            from elasticsearch.helpers import bulk

            total_indexed = 0
            total_docs = len(documents)

            # Process in batches
            for i in range(0, total_docs, batch_size):
                batch = documents[i : i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_docs + batch_size - 1) // batch_size

                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")

                try:
                    # Prepare bulk actions
                    actions = []
                    for doc in batch:
                        # Extract document ID
                        doc_id = doc.get("_id")
                        if isinstance(doc_id, ObjectId):
                            doc_id = str(doc_id)

                        if not doc_id:
                            logger.warning("Document missing '_id' field, skipping")
                            continue

                        # Transform document
                        es_doc = self._transform_document(doc)

                        # Create bulk action
                        action = {"_index": self.index_name, "_id": doc_id, "_source": es_doc}
                        actions.append(action)

                    # Execute bulk operation
                    if actions:
                        success_count, errors = bulk(self.client, actions, raise_on_error=False, stats_only=False)

                        total_indexed += success_count

                        if errors:
                            logger.warning(f"Batch {batch_num} had {len(errors)} errors")
                            for error in errors[:5]:  # Log first 5 errors
                                logger.error(f"Bulk index error: {error}")

                        logger.info(f"Batch {batch_num} completed: {success_count} documents indexed")

                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {e}")
                    # Continue with next batch

            logger.info(f"Bulk indexing completed: {total_indexed}/{total_docs} documents indexed")
            return total_indexed

        except ImportError:
            logger.error("Elasticsearch helpers not available. Install with: pip install elasticsearch")
            return 0
        except Exception as e:
            logger.error(f"Error during bulk indexing: {e}")
            return 0
