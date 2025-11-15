"""
Document domain model.

This module provides the CrawledDocument model for representing
crawled web documents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class CrawledDocument:
    """
    Domain model for a crawled web document.
    
    Represents a document that has been crawled from the web,
    including all extracted metadata and content.
    
    Attributes:
        url: The full URL of the document
        netloc: The network location (domain) of the URL
        status: HTTP status code from the crawl
        html: Raw HTML content of the page
        title: Extracted page title
        body: Extracted body text
        emails: List of email addresses found on the page
        links: List of links found on the page (as dictionaries)
        images: List of image URLs found on the page
        addresses: Dictionary of extracted addresses (e.g., Bitcoin, cryptocurrency)
        parent: ID of the parent document (if crawled from another page)
        seen_time: Timestamp when the document was first crawled
        capture_id: Unique identifier for the screenshot capture
        is_onion: Whether this is an onion (Tor) site
        in_scope: Whether this document is within the crawl scope
    """
    
    url: str
    netloc: str
    status: int
    html: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    emails: List[str] = field(default_factory=list)
    links: List[Dict[str, Any]] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    addresses: Dict[str, Any] = field(default_factory=dict)
    parent: Optional[str] = None
    seen_time: datetime = field(default_factory=datetime.utcnow)
    capture_id: Optional[str] = None
    is_onion: bool = True
    in_scope: bool = False

    def __post_init__(self) -> None:
        """
        Validate and normalize data after initialization.
        
        Ensures that the document has valid data types and
        performs any necessary data normalization.
        """
        # Ensure lists are not None
        if self.emails is None:
            self.emails = []
        if self.links is None:
            self.links = []
        if self.images is None:
            self.images = []
        if self.addresses is None:
            self.addresses = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the document to a dictionary representation.
        
        Useful for serialization to JSON or storage in MongoDB.
        
        Returns:
            Dictionary representation of the document
        """
        return {
            'url': self.url,
            'netloc': self.netloc,
            'status': self.status,
            'html': self.html,
            'title': self.title,
            'body': self.body,
            'emails': self.emails,
            'links': self.links,
            'images': self.images,
            'addresses': self.addresses,
            'parent': self.parent,
            'seen_time': self.seen_time,
            'capture_id': self.capture_id,
            'is_onion': self.is_onion,
            'in_scope': self.in_scope,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrawledDocument':
        """
        Create a CrawledDocument instance from a dictionary.
        
        Useful for deserializing from MongoDB or JSON.
        
        Args:
            data: Dictionary containing document data
            
        Returns:
            CrawledDocument instance
        """
        return cls(
            url=data.get('url', ''),
            netloc=data.get('netloc', ''),
            status=data.get('status', 0),
            html=data.get('html'),
            title=data.get('title'),
            body=data.get('body'),
            emails=data.get('emails', []),
            links=data.get('links', []),
            images=data.get('images', []),
            addresses=data.get('addresses', {}),
            parent=data.get('parent'),
            seen_time=data.get('seen_time', datetime.utcnow()),
            capture_id=data.get('capture_id'),
            is_onion=data.get('is_onion', True),
            in_scope=data.get('in_scope', False),
        )

    def has_content(self) -> bool:
        """
        Check if the document has any content.
        
        Returns:
            True if the document has HTML, title, or body content
        """
        return bool(self.html or self.title or self.body)

    def has_links(self) -> bool:
        """
        Check if the document has any links.
        
        Returns:
            True if the document has links
        """
        return len(self.links) > 0

    def has_images(self) -> bool:
        """
        Check if the document has any images.
        
        Returns:
            True if the document has images
        """
        return len(self.images) > 0

    def __repr__(self) -> str:
        """
        Get string representation of the document.
        
        Returns:
            String representation showing key attributes
        """
        return (
            f"<CrawledDocument(url='{self.url}', "
            f"status={self.status}, "
            f"seen_time='{self.seen_time}')>"
        )
