"""
Dependency injection decorators for Flask views.

This module provides decorators that inject services and dependencies
into view functions, eliminating the need for direct instantiation
within views.
"""

import functools
import logging
from typing import Any, Callable, Optional

from flask import current_app

from application.config import Settings
from application.repositories.document_repository import DocumentRepository
from application.repositories.user_repository import UserRepository
from application.services.authentication_service import AuthenticationService
from application.services.crawler_service import CrawlerService
from application.services.detection_service import DetectionService
from application.services.worker_service import WorkerService
from application.web.services.report_service import ReportService
from application.web.services.search_service import SearchService

logger = logging.getLogger(__name__)


def inject_services(*service_names: str) -> Callable:
    """
    Decorator to inject services into view functions.

    This decorator retrieves services from the Flask application context
    and passes them as keyword arguments to the decorated view function.

    Args:
        *service_names: Names of services to inject (e.g., 'crawler_service', 'document_repository')

    Returns:
        Decorated function with injected services

    Example:
        @inject_services('crawler_service', 'document_repository')
        def my_view(crawler_service: CrawlerService, document_repository: DocumentRepository):
            # Use injected services
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Inject requested services from app context
            for service_name in service_names:
                if service_name not in kwargs:
                    service = getattr(current_app, service_name, None)
                    if service is None:
                        logger.error(f"Service '{service_name}' not found in application context")
                        raise RuntimeError(f"Service '{service_name}' not available")
                    kwargs[service_name] = service

            return func(*args, **kwargs)

        return wrapper

    return decorator


def inject_crawler_service(func: Callable) -> Callable:
    """
    Decorator to inject CrawlerService into view functions.

    Args:
        func: View function to decorate

    Returns:
        Decorated function with crawler_service injected

    Example:
        @inject_crawler_service
        def my_view(crawler_service: CrawlerService):
            # Use crawler_service
            pass
    """
    return inject_services("crawler_service")(func)


def inject_search_service(func: Callable) -> Callable:
    """
    Decorator to inject SearchService into view functions.

    Args:
        func: View function to decorate

    Returns:
        Decorated function with search_service injected

    Example:
        @inject_search_service
        def my_view(search_service: SearchService):
            # Use search_service
            pass
    """
    return inject_services("search_service")(func)


def inject_report_service(func: Callable) -> Callable:
    """
    Decorator to inject ReportService into view functions.

    Args:
        func: View function to decorate

    Returns:
        Decorated function with report_service injected

    Example:
        @inject_report_service
        def my_view(report_service: ReportService):
            # Use report_service
            pass
    """
    return inject_services("report_service")(func)


def inject_detection_service(func: Callable) -> Callable:
    """
    Decorator to inject DetectionService into view functions.

    Args:
        func: View function to decorate

    Returns:
        Decorated function with detection_service injected

    Example:
        @inject_detection_service
        def my_view(detection_service: DetectionService):
            # Use detection_service
            pass
    """
    return inject_services("detection_service")(func)


def inject_authentication_service(func: Callable) -> Callable:
    """
    Decorator to inject AuthenticationService into view functions.

    Args:
        func: View function to decorate

    Returns:
        Decorated function with authentication_service injected

    Example:
        @inject_authentication_service
        def my_view(authentication_service: AuthenticationService):
            # Use authentication_service
            pass
    """
    return inject_services("authentication_service")(func)


def inject_document_repository(func: Callable) -> Callable:
    """
    Decorator to inject DocumentRepository into view functions.

    Args:
        func: View function to decorate

    Returns:
        Decorated function with document_repository injected

    Example:
        @inject_document_repository
        def my_view(document_repository: DocumentRepository):
            # Use document_repository
            pass
    """
    return inject_services("document_repository")(func)


def inject_user_repository(func: Callable) -> Callable:
    """
    Decorator to inject UserRepository into view functions.

    Args:
        func: View function to decorate

    Returns:
        Decorated function with user_repository injected

    Example:
        @inject_user_repository
        def my_view(user_repository: UserRepository):
            # Use user_repository
            pass
    """
    return inject_services("user_repository")(func)


def inject_settings(func: Callable) -> Callable:
    """
    Decorator to inject Settings into view functions.

    Args:
        func: View function to decorate

    Returns:
        Decorated function with settings injected

    Example:
        @inject_settings
        def my_view(settings: Settings):
            # Use settings
            pass
    """
    return inject_services("settings")(func)


def inject_captcha(func: Callable) -> Callable:
    """
    Decorator to inject captcha instance into view functions.

    Args:
        func: View function to decorate

    Returns:
        Decorated function with captcha injected

    Example:
        @inject_captcha
        def my_view(captcha):
            # Use captcha
            pass
    """
    return inject_services("captcha")(func)
