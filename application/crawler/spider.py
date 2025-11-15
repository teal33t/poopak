#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Web crawler spider module.

This module provides the Spider class for crawling web pages and extracting
information, with support for depth-based crawling and queue-based job processing.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from rq import Queue

from application.config.constants import HTTP_OK, JOB_RESULT_TTL, JOB_TTL, QUEUE_HIGH_PRIORITY

from .curl import query
from .data_storage import DataStorage
from .html_extractors import Extractor
from .screenshot import get_screenshot

logger = logging.getLogger(__name__)


def crawl_with_depth(
    target: str,
    parent: Optional[str],
    depth: int = 0,
    is_onion: bool = True,
    in_scope: bool = False,
    use_proxy: bool = True,
    re_crawl: bool = True,
) -> None:
    """
    Crawl a target URL with specified depth.

    This is a convenience function that creates a Spider instance with
    necessary dependencies and initiates the crawling process.

    Args:
        target: Target URL to crawl
        parent: Parent document ID (None for root URLs)
        depth: Crawl depth (0 for single page, >0 for recursive crawling)
        is_onion: Whether the URL is an onion address
        in_scope: Whether the URL is in scope for the crawl
        use_proxy: Whether to use proxy for the request
        re_crawl: Whether to re-crawl if URL already exists
    """
    logger.info(f"Starting crawl for {target} with depth {depth}")

    # Create dependencies
    from application.config import settings
    from application.infrastructure.queue import QueueFactory, WorkerType

    queue_factory = QueueFactory(settings)
    crawler_queue = queue_factory.get_queue(WorkerType.CRAWLER, QUEUE_HIGH_PRIORITY)
    document_repository = DataStorage()

    # Create and run spider
    spider = Spider(
        base_url=target,
        crawler_queue=crawler_queue,
        document_repository=document_repository,
        depth=depth,
        is_onion=is_onion,
        in_scope=in_scope,
        use_proxy=use_proxy,
        re_crawl=re_crawl,
        parent=parent,
    )
    spider.process_crawl()


class Spider:
    """
    Web crawler spider for extracting and processing web page content.

    The Spider class handles fetching web pages, extracting structured data,
    capturing screenshots, and enqueueing child URLs for recursive crawling.
    """

    def __init__(
        self,
        base_url: str,
        crawler_queue: Queue,
        document_repository: DataStorage,
        depth: int = 0,
        is_onion: bool = True,
        in_scope: bool = False,
        use_proxy: bool = True,
        re_crawl: bool = True,
        parent: Optional[str] = None,
    ):
        """
        Initialize the Spider.

        Args:
            base_url: The URL to crawl
            crawler_queue: RQ Queue instance for enqueueing child crawl jobs
            document_repository: DataStorage instance for persisting crawled data
            depth: Crawl depth (0 for single page, >0 for recursive)
            is_onion: Whether the URL is an onion address
            in_scope: Whether the URL is in scope for the crawl
            use_proxy: Whether to use proxy for the request
            re_crawl: Whether to re-crawl if URL already exists
            parent: Parent document ID (None for root URLs)
        """
        self.base_url = base_url
        self.netloc = urlparse(self.base_url).netloc
        self.is_onion = is_onion
        self.in_scope = in_scope
        self.depth = depth
        self.proxy = use_proxy
        self.re_crawl = re_crawl
        self.parent = parent

        # Injected dependencies
        self.crawler_queue = crawler_queue
        self.document_repository = document_repository

        # Fetch the page
        self.response = query(base_url)

        logger.debug(f"Spider initialized for {base_url} " f"(depth={depth}, is_onion={is_onion}, in_scope={in_scope})")

    def _build_base_document_data(self) -> Dict[str, Any]:
        """
        Build base document data from response.

        Returns:
            Dictionary with base document fields
        """
        return {
            "netloc": self.netloc,
            "url": self.base_url,
            "status": self.response["status"],
            "seen_time": self.response["seen_time"],
            "parent": self.parent,
        }

    def _extract_html_content(self, extractor: Extractor) -> Dict[str, Any]:
        """
        Extract structured content from HTML.

        Args:
            extractor: Extractor instance with parsed HTML

        Returns:
            Dictionary with extracted content fields
        """
        return {
            "html": self.response["html"],
            "body": extractor.get_body(),
            "title": extractor.get_title(),
            "emails": extractor.get_emails(),
            "links": extractor.get_links(),
            "images": extractor.get_img_links(),
            "addresses": {
                "btc": extractor.get_bitcoin_addrs(),
                "monero": extractor.get_monero_addrs(),
                "eth": extractor.get_eth_addrs(),
            },
        }

    def _build_full_document_data(self) -> Dict[str, Any]:
        """
        Build full document data including extracted HTML content.

        Returns:
            Dictionary with all document fields
        """
        base_data = self._build_base_document_data()

        # Add crawl metadata
        base_data.update({"is_onion": self.is_onion, "in_scope": self.in_scope})

        # Extract HTML content if available
        if "html" in self.response:
            extractor = Extractor(base_url=self.base_url, html=self.response["html"])
            html_data = self._extract_html_content(extractor)
            base_data.update(html_data)

            # Capture screenshot for successful responses
            if int(self.response["status"]) == HTTP_OK:
                capture_id = self._capture_screenshot()
                if capture_id:
                    base_data["capture_id"] = capture_id

        return base_data

    def _capture_screenshot(self) -> Optional[str]:
        """
        Capture screenshot of the page.

        Returns:
            Capture ID if successful, None otherwise
        """
        try:
            capture_id = uuid.uuid4().hex
            get_screenshot(self.base_url, capture_id)
            logger.info(f"Screenshot captured for {self.base_url}: {capture_id}")
            return capture_id
        except Exception as e:
            logger.error(f"Failed to capture screenshot for {self.base_url}: {str(e)}")
            return None

    def _save_or_update_document(self, document_data: Dict[str, Any]) -> Optional[str]:
        """
        Save new document or update existing one.

        Args:
            document_data: Document data to save or update

        Returns:
            Document ID if saved/updated, None otherwise
        """
        try:
            if self.document_repository.is_url_exist(self.base_url):
                if self.re_crawl:
                    self.document_repository.update_crawled_url(self.base_url, document_data)
                    logger.info(f"Updated existing document: {self.base_url}")
                    # Return existing document ID
                    existing_doc = self.document_repository.get_document_by_url(self.base_url)
                    return str(existing_doc["_id"]) if existing_doc else None
                else:
                    logger.debug(f"Skipping re-crawl of {self.base_url}")
                    return None
            else:
                document_id = self.document_repository.add_crawled_url(document_data)
                logger.info(f"Saved new document: {self.base_url} (ID: {document_id})")
                return document_id
        except Exception as e:
            logger.error(f"Failed to save/update document {self.base_url}: {str(e)}")
            return None

    def _enqueue_child_links(self, links: List[Dict[str, Any]], parent_id: str) -> None:
        """
        Enqueue child links for crawling at the next depth level.

        Args:
            links: List of link dictionaries with 'url', 'is_onion', 'in_scope'
            parent_id: Parent document ID for the child links
        """
        if not links or self.depth <= 0:
            return

        enqueued_count = 0

        for depth_level in range(self.depth):
            for link in links:
                try:
                    self.crawler_queue.enqueue_call(
                        func=crawl_with_depth,
                        args=(link["url"], parent_id, depth_level, link["is_onion"], link["in_scope"]),
                        ttl=JOB_TTL,
                        result_ttl=JOB_RESULT_TTL,
                    )
                    enqueued_count += 1
                except Exception as e:
                    logger.error(f"Failed to enqueue link {link['url']} " f"at depth {depth_level}: {str(e)}")

        logger.info(f"Enqueued {enqueued_count} child crawl jobs " f"for {self.base_url} (depth={self.depth})")

    def process_crawl(self) -> Optional[str]:
        """
        Process the crawl: extract data, save document, and enqueue child links.

        Returns:
            Document ID if successful, None otherwise
        """
        logger.info(f"Processing crawl for {self.base_url}")

        # Check if response has valid status
        if not self.response.get("status"):
            logger.warning(f"No valid status for {self.base_url}")
            document_data = self._build_base_document_data()
            return self._save_or_update_document(document_data)

        # Build full document data
        document_data = self._build_full_document_data()

        # Save or update the document
        parent_id = self._save_or_update_document(document_data)

        # Enqueue child links if depth crawling is enabled
        if parent_id and "links" in document_data and self.depth > 0:
            self._enqueue_child_links(document_data["links"], parent_id)

        logger.info(f"Completed crawl processing for {self.base_url}")
        return parent_id
