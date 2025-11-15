"""
Crawler service for orchestrating web crawling operations.

This module provides the CrawlerService class that manages crawling operations,
coordinates between repositories and queues, and handles business logic for
the web crawler.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from application.config import Settings
from application.config.constants import (
    DEFAULT_CRAWL_DEPTH,
    DEFAULT_PAGE_SIZE,
    HTTP_OK,
    JOB_RESULT_TTL,
    JOB_TTL,
    MAX_CRAWL_DEPTH,
    QUEUE_HIGH_PRIORITY,
)
from application.infrastructure.queue import QueueFactory, WorkerType
from application.repositories.document_repository import DocumentRepository
from application.utils.exceptions import CrawlerError, DatabaseConnectionError, ValidationError

logger = logging.getLogger(__name__)


class CrawlerService:
    """
    Service for managing web crawling operations.

    Orchestrates crawling logic, coordinates between document repository
    and queue operations, and enforces business rules for crawling.
    """

    def __init__(self, document_repo: DocumentRepository, queue_factory: QueueFactory, settings: Settings = None):
        """
        Initialize the crawler service.

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
        self._crawler_queue = queue_factory.get_queue(WorkerType.CRAWLER, QUEUE_HIGH_PRIORITY)

        logger.info("CrawlerService initialized")

    def crawl_url(
        self,
        url: str,
        depth: int = DEFAULT_CRAWL_DEPTH,
        parent_id: Optional[str] = None,
        is_onion: bool = True,
        in_scope: bool = False,
        use_proxy: bool = True,
        re_crawl: bool = True,
    ) -> str:
        """
        Initiate crawling of a URL.

        This method enqueues a crawl job for the specified URL with the
        given parameters.

        Args:
            url: The URL to crawl
            depth: Crawl depth (0 = no child links, 1+ = follow links)
            parent_id: ID of parent document if this is a child crawl
            is_onion: Whether the URL is an onion address
            in_scope: Whether the URL is in scope for the crawl
            use_proxy: Whether to use proxy for crawling
            re_crawl: Whether to re-crawl if URL already exists

        Returns:
            Job ID of the enqueued crawl task

        Raises:
            ValidationError: If URL or parameters are invalid
            CrawlerError: If enqueueing the crawl job fails
        """
        try:
            # Validate URL
            if not url or not isinstance(url, str):
                raise ValidationError("URL must be a non-empty string")

            # Validate depth
            if depth < 0 or depth > MAX_CRAWL_DEPTH:
                raise ValidationError(f"Depth must be between 0 and {MAX_CRAWL_DEPTH}")

            logger.info(f"Enqueueing crawl for URL: {url}, depth: {depth}, " f"parent: {parent_id}")

            # Import here to avoid circular dependency
            from application.crawler.spider import crawl_with_depth

            # Enqueue the crawl job
            job = self._crawler_queue.enqueue_call(
                func=crawl_with_depth,
                args=(url, parent_id, depth, is_onion, in_scope, use_proxy, re_crawl),
                ttl=JOB_TTL,
                result_ttl=JOB_RESULT_TTL,
            )

            logger.info(f"Crawl job enqueued with ID: {job.id}")
            return job.id

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to enqueue crawl for URL {url}: {str(e)}")
            raise CrawlerError(f"Failed to enqueue crawl: {str(e)}")

    def save_crawl_result(
        self,
        url: str,
        netloc: str,
        status: int,
        seen_time: datetime,
        parent: Optional[str] = None,
        html: Optional[str] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        emails: Optional[List[str]] = None,
        links: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[str]] = None,
        addresses: Optional[Dict[str, List[str]]] = None,
        capture_id: Optional[str] = None,
        is_onion: bool = True,
        in_scope: bool = False,
        re_crawl: bool = True,
    ) -> str:
        """
        Save or update a crawl result in the database.

        If the URL already exists and re_crawl is True, updates the existing
        document. Otherwise, creates a new document.

        Args:
            url: The crawled URL
            netloc: Network location (domain) of the URL
            status: HTTP status code
            seen_time: Timestamp when the URL was crawled
            parent: ID of parent document
            html: Raw HTML content
            title: Page title
            body: Extracted body text
            emails: List of extracted email addresses
            links: List of extracted links
            images: List of extracted image URLs
            addresses: Dictionary of cryptocurrency addresses
            capture_id: Screenshot capture ID
            is_onion: Whether the URL is an onion address
            in_scope: Whether the URL is in scope
            re_crawl: Whether to update if URL already exists

        Returns:
            Document ID (new or existing)

        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            # Prepare document data
            document_data = {
                "url": url,
                "netloc": netloc,
                "status": status,
                "seen_time": seen_time,
                "parent": parent,
                "is_onion": is_onion,
                "in_scope": in_scope,
            }

            # Add optional fields if provided
            if html is not None:
                document_data["html"] = html
            if title is not None:
                document_data["title"] = title
            if body is not None:
                document_data["body"] = body
            if emails is not None:
                document_data["emails"] = emails
            if links is not None:
                document_data["links"] = links
            if images is not None:
                document_data["images"] = images
            if addresses is not None:
                document_data["addresses"] = addresses
            if capture_id is not None:
                document_data["capture_id"] = capture_id

            # Check if URL already exists
            existing_doc = self._document_repo.find_by_url(url)

            if existing_doc:
                if re_crawl:
                    # Update existing document
                    self._document_repo.update_by_url(url, document_data)
                    document_id = str(existing_doc["_id"])
                    logger.info(f"Updated existing document: {document_id}")
                else:
                    # Return existing document ID without updating
                    document_id = str(existing_doc["_id"])
                    logger.info(f"URL already exists, skipping update: {document_id}")
            else:
                # Create new document
                document_id = self._document_repo.create(document_data)
                logger.info(f"Created new document: {document_id}")

            return document_id

        except Exception as e:
            logger.error(f"Failed to save crawl result for URL {url}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to save crawl result: {str(e)}")

    def enqueue_child_crawls(self, links: List[Dict[str, Any]], parent_id: str, depth: int) -> int:
        """
        Enqueue crawl jobs for child links.

        Args:
            links: List of link dictionaries with 'url', 'is_onion', 'in_scope'
            parent_id: ID of the parent document
            depth: Remaining crawl depth

        Returns:
            Number of child crawls enqueued

        Raises:
            CrawlerError: If enqueueing fails
        """
        try:
            if depth <= 0:
                logger.debug("Depth is 0, skipping child crawls")
                return 0

            enqueued_count = 0
            depth_step = 0

            while depth_step < depth:
                for link in links:
                    try:
                        link_url = link.get("url")
                        if not link_url:
                            continue

                        is_onion = link.get("is_onion", True)
                        in_scope = link.get("in_scope", False)

                        # Enqueue child crawl
                        self.crawl_url(
                            url=link_url, depth=depth_step, parent_id=parent_id, is_onion=is_onion, in_scope=in_scope
                        )
                        enqueued_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to enqueue child crawl for {link.get('url')}: {str(e)}")
                        continue

                depth_step += 1

            logger.info(f"Enqueued {enqueued_count} child crawls for parent {parent_id}")
            return enqueued_count

        except Exception as e:
            logger.error(f"Failed to enqueue child crawls: {str(e)}")
            raise CrawlerError(f"Failed to enqueue child crawls: {str(e)}")

    def generate_capture_id(self) -> str:
        """
        Generate a unique capture ID for screenshots.

        Returns:
            Unique capture ID as hex string
        """
        return uuid.uuid4().hex

    def url_exists(self, url: str) -> bool:
        """
        Check if a URL has already been crawled.

        Args:
            url: The URL to check

        Returns:
            True if URL exists in database, False otherwise
        """
        try:
            return self._document_repo.url_exists(url)
        except Exception as e:
            logger.error(f"Error checking if URL exists: {str(e)}")
            return False

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its ID.

        Args:
            document_id: The document ID

        Returns:
            Document dictionary if found, None otherwise
        """
        try:
            return self._document_repo.find_by_id(document_id)
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return None

    def get_document_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its URL.

        Args:
            url: The document URL

        Returns:
            Document dictionary if found, None otherwise
        """
        try:
            return self._document_repo.find_by_url(url)
        except Exception as e:
            logger.error(f"Error retrieving document by URL {url}: {str(e)}")
            return None

    def get_document_with_children(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document with its child documents.

        Args:
            document_id: The document ID

        Returns:
            Dictionary with 'document' and 'children' keys, or None if not found

        Raises:
            DocumentNotFoundError: If document is not found
        """
        from application.utils.exceptions import DocumentNotFoundError

        try:
            document = self._document_repo.find_by_id(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document with ID {document_id} not found")

            children = []
            if document.get("links"):
                for link in document["links"]:
                    link_url = link.get("url")
                    if link_url:
                        child_doc = self._document_repo.find_by_url(link_url)
                        if child_doc:
                            children.append(child_doc)

            return {"document": document, "children": children}

        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving document with children {document_id}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to retrieve document: {str(e)}")

    def get_documents_by_status(
        self, status: int, in_scope: Optional[bool] = None, page_number: int = 1, page_size: int = DEFAULT_PAGE_SIZE
    ) -> Dict[str, Any]:
        """
        Retrieve documents by status with pagination.

        Args:
            status: HTTP status code to filter by
            in_scope: Filter by in_scope flag (None = no filter)
            page_number: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with 'documents', 'total_count', 'page', 'page_size' keys
        """
        try:
            skip = (page_number - 1) * page_size

            # Build filter
            filter_dict = {"status": status}
            if in_scope is not None:
                filter_dict["in_scope"] = in_scope

            # Get documents and count
            documents = self._document_repo.find_by_status(status=status, in_scope=in_scope, skip=skip, limit=page_size)

            total_count = self._document_repo.count(filter_dict)

            return {"documents": documents, "total_count": total_count, "page": page_number, "page_size": page_size}

        except Exception as e:
            logger.error(f"Error retrieving documents by status {status}: {str(e)}")
            raise DatabaseConnectionError(f"Failed to retrieve documents: {str(e)}")

    def get_recent_documents(
        self, status: Optional[int] = None, limit: int = DEFAULT_PAGE_SIZE
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent documents sorted by seen_time.

        Args:
            status: Optional HTTP status code to filter by
            limit: Maximum number of documents to return

        Returns:
            List of document dictionaries
        """
        try:
            if status is not None:
                return self._document_repo.find_by_status(status=status, skip=0, limit=limit)
            else:
                return self._document_repo.find_recent(limit=limit)

        except Exception as e:
            logger.error(f"Error retrieving recent documents: {str(e)}")
            raise DatabaseConnectionError(f"Failed to retrieve recent documents: {str(e)}")

    def enqueue_simple_crawl(self, url: str, timeout: int = JOB_TTL) -> Optional[str]:
        """
        Enqueue a simple crawl job for a URL with default parameters.

        This is a simplified version of crawl_url for basic crawling needs,
        typically used when adding new onion URLs from the web interface.

        Args:
            url: The URL to crawl
            timeout: Job timeout in seconds

        Returns:
            Job ID if successful, None otherwise

        Raises:
            ValidationError: If URL is invalid
            CrawlerError: If enqueueing fails
        """
        try:
            # Validate URL
            if not url or not isinstance(url, str):
                raise ValidationError("URL must be a non-empty string")

            logger.info(f"Enqueueing simple crawl for URL: {url}")

            # Import here to avoid circular dependency
            from application.crawler.spider import crawl_with_depth

            # Enqueue the crawl job with default parameters
            job = self._crawler_queue.enqueue_call(
                func=crawl_with_depth,
                args=(url, None),  # URL and no parent
                ttl=timeout,
                result_ttl=JOB_RESULT_TTL,
            )

            if job and job.id:
                logger.info(f"Simple crawl job enqueued with ID: {job.id}")
                return job.id
            else:
                logger.warning(f"Failed to get job ID for URL: {url}")
                return None

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to enqueue simple crawl for URL {url}: {str(e)}")
            raise CrawlerError(f"Failed to enqueue crawl: {str(e)}")
