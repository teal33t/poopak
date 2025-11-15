"""
Search service for handling search-related business logic.

This service coordinates search operations, statistics retrieval,
and directory listings for the web interface.
"""

import logging
from typing import Dict, List, Optional, Tuple

from application.config.constants import HTTP_OK, HTTP_SERVICE_UNAVAILABLE
from application.repositories.document_repository import DocumentRepository
from application.utils.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class SearchService:
    """
    Service for search and directory operations.
    
    Handles business logic for searching documents, retrieving statistics,
    and managing directory listings.
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        elasticsearch_service: Optional["ElasticsearchService"] = None,
    ):
        """
        Initialize the search service.
        
        Args:
            document_repository: Repository for document data access
            elasticsearch_service: Optional Elasticsearch service for enhanced search
        """
        self.document_repository = document_repository
        self.elasticsearch_service = elasticsearch_service
        
        # Check if Elasticsearch is enabled and available
        self._elasticsearch_enabled = False
        if self.elasticsearch_service is not None:
            self._elasticsearch_enabled = self.elasticsearch_service.is_available()
            if self._elasticsearch_enabled:
                logger.info("Elasticsearch is enabled and available for search operations")
            else:
                logger.warning("Elasticsearch service provided but not available, will use MongoDB fallback")

    def get_index_statistics(self) -> Dict[str, any]:
        """
        Get statistics for the index page.
        
        Returns:
            Dictionary containing statistics:
                - checked_onions: Total number of crawled documents
                - alive_onions: Number of documents with HTTP 200 status
                - offline_onions: Number of documents with HTTP 503 status
                - last_crawled: Timestamp of last crawl
                
        Raises:
            DatabaseConnectionError: If database connection fails
        """
        try:
            alive_onions = self.document_repository.count({"status": HTTP_OK})
            offline_checked_onions = self.document_repository.count(
                {"status": HTTP_SERVICE_UNAVAILABLE}
            )
            checked_onions = self.document_repository.count()
            last_crawled_time = self.document_repository.get_last_crawled_time()

            return {
                "checked_onions": checked_onions,
                "alive_onions": alive_onions,
                "offline_onions": offline_checked_onions,
                "last_crawled": last_crawled_time,
            }
        except DatabaseConnectionError as e:
            logger.error(f"Database error retrieving index statistics: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving index statistics: {str(e)}")
            raise DatabaseConnectionError(f"Failed to retrieve statistics: {str(e)}")

    def search_documents(
        self, phrase: str, page_number: int, items_per_page: int
    ) -> Tuple[List[Dict], int]:
        """
        Search for documents containing the specified phrase.
        
        Uses Elasticsearch for fast full-text search when available,
        falls back to MongoDB regex search if Elasticsearch is unavailable.
        
        Args:
            phrase: Search phrase
            page_number: Page number for pagination (1-indexed)
            items_per_page: Number of items per page
            
        Returns:
            Tuple of (documents list, total count)
            
        Raises:
            DatabaseConnectionError: If database connection fails
        """
        # Calculate skip for pagination
        skip = (page_number - 1) * items_per_page
        
        # Try Elasticsearch first if available
        if self._elasticsearch_enabled and self.elasticsearch_service is not None:
            try:
                logger.info(f"Using Elasticsearch for search query: '{phrase}'")
                
                # Search using Elasticsearch
                es_documents, total_count = self.elasticsearch_service.search(
                    query=phrase, skip=skip, limit=items_per_page
                )
                
                # Transform Elasticsearch results to match MongoDB format
                documents = self._transform_elasticsearch_results(es_documents)
                
                logger.info(
                    f"Elasticsearch search for '{phrase}' returned {total_count} results "
                    f"(page {page_number}, {len(documents)} documents)"
                )
                
                return documents, total_count
                
            except Exception as e:
                logger.warning(
                    f"Elasticsearch search failed for '{phrase}': {e}. "
                    f"Falling back to MongoDB search"
                )
                # Fall through to MongoDB fallback
        
        # Fallback to MongoDB regex search
        try:
            logger.info(f"Using MongoDB regex search for query: '{phrase}'")
            
            # Get total count
            all_count = self.document_repository.count_by_text_search(phrase)
            
            # Get documents
            documents = self.document_repository.find_by_text_search(
                phrase=phrase, skip=skip, limit=items_per_page
            )

            logger.info(
                f"MongoDB search for '{phrase}' returned {all_count} results "
                f"(page {page_number}, {len(documents)} documents)"
            )
            
            return documents, all_count
            
        except DatabaseConnectionError as e:
            logger.error(f"Database error during search for '{phrase}': {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search for '{phrase}': {str(e)}")
            raise DatabaseConnectionError(f"Search failed: {str(e)}")
    
    def _transform_elasticsearch_results(self, es_documents: List[Dict]) -> List[Dict]:
        """
        Transform Elasticsearch results to match MongoDB document format.
        
        Ensures compatibility with existing view layer expectations.
        
        Args:
            es_documents: List of documents from Elasticsearch
            
        Returns:
            List of documents in MongoDB format
        """
        transformed = []
        
        for es_doc in es_documents:
            # Create document dict matching MongoDB format
            doc = {}
            
            # Copy all fields from Elasticsearch document
            for key, value in es_doc.items():
                if key not in ["_score"]:  # Exclude internal ES fields we don't need
                    doc[key] = value
            
            # Ensure _id is present (Elasticsearch returns it as string)
            if "_id" in es_doc:
                doc["_id"] = es_doc["_id"]
            
            transformed.append(doc)
        
        return transformed

    def get_directory_documents(
        self, page_number: int, items_per_page: int, status_filter: Optional[int] = HTTP_OK
    ) -> Tuple[List[Dict], int]:
        """
        Get documents for directory listing.
        
        Args:
            page_number: Page number for pagination (1-indexed)
            items_per_page: Number of items per page
            status_filter: HTTP status code to filter by (None for all)
            
        Returns:
            Tuple of (documents list, total count)
            
        Raises:
            DatabaseConnectionError: If database connection fails
        """
        try:
            # Calculate skip for pagination
            skip = (page_number - 1) * items_per_page
            
            if status_filter is not None:
                # Filter by status
                all_count = self.document_repository.count({"status": status_filter})
                documents = self.document_repository.find_by_status(
                    status=status_filter, skip=skip, limit=items_per_page
                )
            else:
                # Get all documents
                all_count = self.document_repository.count()
                documents = self.document_repository.find_all(
                    filter=None, skip=skip, limit=items_per_page
                )

            logger.info(
                f"Directory page {page_number} loaded with {all_count} total documents"
            )
            
            return documents, all_count
            
        except DatabaseConnectionError as e:
            logger.error(
                f"Database error loading directory page {page_number}: {str(e)}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error loading directory page {page_number}: {str(e)}"
            )
            raise DatabaseConnectionError(f"Failed to load directory: {str(e)}")

    def export_alive_urls(self, batch_size: int = 100) -> List[str]:
        """
        Export all alive onion URLs in batches.
        
        Args:
            batch_size: Number of documents to fetch per batch
            
        Yields:
            URL strings for alive documents
            
        Raises:
            DatabaseConnectionError: If database connection fails
        """
        try:
            skip = 0
            count = 0
            urls = []
            
            while True:
                documents = self.document_repository.find_by_status(
                    status=HTTP_OK, skip=skip, limit=batch_size
                )
                
                if not documents:
                    break
                
                for document in documents:
                    urls.append(document["url"])
                    count += 1
                
                skip += batch_size
            
            logger.info(f"Exported {count} URLs")
            return urls
            
        except DatabaseConnectionError as e:
            logger.error(f"Database error during export: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during export: {str(e)}")
            raise DatabaseConnectionError(f"Export failed: {str(e)}")
    
    def reindex_all_documents(self, batch_size: int = 1000) -> int:
        """
        Reindex all documents from MongoDB to Elasticsearch.
        
        Fetches all documents from MongoDB in batches and indexes them
        in Elasticsearch using bulk operations for efficiency.
        
        Args:
            batch_size: Number of documents to process per batch (default: 1000)
            
        Returns:
            Total count of successfully indexed documents
            
        Raises:
            DatabaseConnectionError: If database connection fails
            RuntimeError: If Elasticsearch is not available
        """
        if not self._elasticsearch_enabled or self.elasticsearch_service is None:
            error_msg = "Cannot reindex: Elasticsearch is not available"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            logger.info("Starting bulk reindex operation")
            
            # Get total document count
            total_documents = self.document_repository.count()
            logger.info(f"Total documents to reindex: {total_documents}")
            
            if total_documents == 0:
                logger.info("No documents to reindex")
                return 0
            
            # Process documents in batches
            skip = 0
            total_indexed = 0
            batch_num = 0
            
            while skip < total_documents:
                batch_num += 1
                
                logger.info(
                    f"Fetching batch {batch_num} (documents {skip + 1} to "
                    f"{min(skip + batch_size, total_documents)} of {total_documents})"
                )
                
                # Fetch batch from MongoDB
                documents = self.document_repository.find_all(
                    filter=None, skip=skip, limit=batch_size
                )
                
                if not documents:
                    logger.info("No more documents to fetch")
                    break
                
                logger.info(f"Fetched {len(documents)} documents in batch {batch_num}")
                
                # Bulk index to Elasticsearch
                indexed_count = self.elasticsearch_service.bulk_index(
                    documents=documents, batch_size=batch_size
                )
                
                total_indexed += indexed_count
                
                logger.info(
                    f"Batch {batch_num} completed: {indexed_count}/{len(documents)} "
                    f"documents indexed successfully"
                )
                
                # Move to next batch
                skip += batch_size
            
            logger.info(
                f"Bulk reindex completed: {total_indexed}/{total_documents} "
                f"documents indexed successfully"
            )
            
            return total_indexed
            
        except DatabaseConnectionError as e:
            logger.error(f"Database error during reindex: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during reindex: {str(e)}")
            raise DatabaseConnectionError(f"Reindex failed: {str(e)}")
