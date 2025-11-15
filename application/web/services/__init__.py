"""
Web services layer for view-specific business logic.

This module provides service classes that handle business logic
specific to web views, coordinating between repositories and
providing higher-level operations for controllers.
"""

from .search_service import SearchService
from .report_service import ReportService

__all__ = ["SearchService", "ReportService"]
