"""
Pagination utilities for the web application.

This module provides pagination classes and helper functions for
paginating query results in views.
"""

from math import ceil
from typing import Iterator, Optional, Tuple


class Pagination:
    """
    Pagination helper for displaying paginated results.
    
    Provides properties and methods for calculating page numbers,
    navigation links, and iterating through page ranges.
    """

    def __init__(self, page: int, per_page: int, total_count: int) -> None:
        """
        Initialize pagination.
        
        Args:
            page: Current page number (1-indexed)
            per_page: Number of items per page
            total_count: Total number of items
        """
        self.page = max(1, page)  # Ensure page is at least 1
        self.per_page = max(1, per_page)  # Ensure per_page is at least 1
        self.total_count = max(0, total_count)  # Ensure total_count is non-negative

    @property
    def pages(self) -> int:
        """
        Get total number of pages.
        
        Returns:
            Total number of pages
        """
        if self.per_page == 0:
            return 0
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self) -> bool:
        """
        Check if there is a previous page.
        
        Returns:
            True if there is a previous page, False otherwise
        """
        return self.page > 1

    @property
    def has_next(self) -> bool:
        """
        Check if there is a next page.
        
        Returns:
            True if there is a next page, False otherwise
        """
        return self.page < self.pages

    @property
    def prev_page(self) -> Optional[int]:
        """
        Get previous page number.
        
        Returns:
            Previous page number or None if on first page
        """
        return self.page - 1 if self.has_prev else None

    @property
    def next_page(self) -> Optional[int]:
        """
        Get next page number.
        
        Returns:
            Next page number or None if on last page
        """
        return self.page + 1 if self.has_next else None

    @property
    def start_index(self) -> int:
        """
        Get the starting index for the current page (0-indexed).
        
        Returns:
            Starting index for items on current page
        """
        return (self.page - 1) * self.per_page

    @property
    def end_index(self) -> int:
        """
        Get the ending index for the current page (0-indexed, exclusive).
        
        Returns:
            Ending index for items on current page
        """
        return min(self.start_index + self.per_page, self.total_count)

    @property
    def showing_range(self) -> Tuple[int, int]:
        """
        Get the range of items being shown (1-indexed for display).
        
        Returns:
            Tuple of (start, end) item numbers being displayed
        """
        if self.total_count == 0:
            return (0, 0)
        start = self.start_index + 1
        end = self.end_index
        return (start, end)

    def iter_pages(
        self,
        left_edge: int = 2,
        left_current: int = 2,
        right_current: int = 5,
        right_edge: int = 2,
    ) -> Iterator[Optional[int]]:
        """
        Iterate through page numbers with ellipsis for gaps.
        
        Yields page numbers and None for gaps (to be displayed as ellipsis).
        
        Args:
            left_edge: Number of pages to show at the left edge
            left_current: Number of pages to show left of current page
            right_current: Number of pages to show right of current page
            right_edge: Number of pages to show at the right edge
            
        Yields:
            Page numbers (int) or None for gaps
            
        Example:
            For page 10 of 20: [1, 2, None, 8, 9, 10, 11, 12, 13, 14, None, 19, 20]
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (
                    num > self.page - left_current - 1
                    and num < self.page + right_current
                )
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def is_valid_page(self, page: int) -> bool:
        """
        Check if a page number is valid.
        
        Args:
            page: Page number to check
            
        Returns:
            True if page number is valid, False otherwise
        """
        return 1 <= page <= self.pages


def calculate_skip_limit(
    page: int, per_page: int
) -> Tuple[int, int]:
    """
    Calculate skip and limit values for database queries.
    
    Helper function to convert page number and items per page
    into skip and limit values for database queries.
    
    Args:
        page: Page number (1-indexed)
        per_page: Number of items per page
        
    Returns:
        Tuple of (skip, limit) for database query
        
    Example:
        >>> calculate_skip_limit(1, 20)
        (0, 20)
        >>> calculate_skip_limit(3, 20)
        (40, 20)
    """
    page = max(1, page)
    per_page = max(1, per_page)
    skip = (page - 1) * per_page
    return (skip, per_page)


def create_pagination(
    page: int, per_page: int, total_count: int
) -> Pagination:
    """
    Create a Pagination instance with validation.
    
    Factory function that creates a Pagination instance with
    validated parameters.
    
    Args:
        page: Current page number (1-indexed)
        per_page: Number of items per page
        total_count: Total number of items
        
    Returns:
        Pagination instance
    """
    return Pagination(
        page=max(1, page),
        per_page=max(1, per_page),
        total_count=max(0, total_count),
    )
