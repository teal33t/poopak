import logging
from typing import List, Optional, Union

import dateutil.parser
from bson import ObjectId
from flask import Response, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from pymongo import DESCENDING
from werkzeug.utils import secure_filename

from application.config import Settings
from application.config.constants import (
    DEFAULT_PAGE_SIZE,
    HTTP_NOT_FOUND,
    HTTP_OK,
    HTTP_SERVER_ERROR,
    JOB_RESULT_TTL,
    JOB_TTL,
)
from application.services.crawler_service import CrawlerService
from application.utils.exceptions import DatabaseConnectionError, DocumentNotFoundError
from application.web.decorators import inject_crawler_service, inject_services, inject_settings
from application.web.helper import extract_onions
from application.web.paginate import create_pagination
from application.web.queues import crawler_q, detector_q
from application.web.scanner import exif_data, text_subjects
from application.web.scanner.exif_data import detect_exif_metadata
from application.web.search.forms import SearchForm
from application.web.stats import onion_stats as oss

from . import dashboardbp
from .forms import MultipleOnion, RangeStats

logger = logging.getLogger(__name__)


@dashboardbp.route("/hs/<document_id>", methods=["GET"])
@inject_crawler_service
def hs_view(document_id: str = "1", crawler_service: CrawlerService = None) -> Union[str, tuple]:
    """
    Display a single document with its child documents.

    Args:
        document_id: Document ID
        crawler_service: Injected CrawlerService instance

    Returns:
        Rendered template with document and children
    """
    search_form = SearchForm()

    try:
        # Get document with children
        result_data = crawler_service.get_document_with_children(document_id)
        document = result_data["document"]
        children = result_data["children"]

        return render_template("dashboard/hs.html", item=document, child_data=children, search_form=search_form)

    except DocumentNotFoundError:
        logger.warning(f"Document not found: {document_id}")
        flash("Document not found", "error")
        return redirect(url_for("dashboard.hs_directory")), HTTP_NOT_FOUND

    except DatabaseConnectionError as e:
        logger.error(f"Database error retrieving document {document_id}: {str(e)}")
        flash("An error occurred while retrieving the document", "error")
        return redirect(url_for("dashboard.hs_directory")), HTTP_SERVER_ERROR

    except Exception as e:
        logger.error(f"Unexpected error in hs_view for document {document_id}: {str(e)}")
        flash("An unexpected error occurred", "error")
        return redirect(url_for("dashboard.hs_directory")), HTTP_SERVER_ERROR


@dashboardbp.route("/hs_directory/", methods=["GET"])
@dashboardbp.route("/hs_directory/<int:page_number>", methods=["GET"])
@inject_services("crawler_service", "settings")
def hs_directory(page_number: int = 1, crawler_service: CrawlerService = None, settings: Settings = None) -> Union[str, tuple]:
    """
    Display directory of out-of-scope documents with pagination.

    Args:
        page_number: Page number for pagination (default: 1)
        crawler_service: Injected CrawlerService instance
        settings: Injected Settings instance

    Returns:
        Rendered template with paginated documents
    """
    search_form = SearchForm()

    try:
        # Get documents by status with pagination
        result_data = crawler_service.get_documents_by_status(
            status=HTTP_OK, in_scope=False, page_number=page_number, page_size=settings.ITEMS_PER_PAGE
        )

        documents = result_data["documents"]
        total_count = result_data["total_count"]

        # Create pagination object
        pagination = create_pagination(page_number, settings.ITEMS_PER_PAGE, total_count)

        return render_template(
            "dashboard/hs_directory.html",
            results=documents,
            pagination=pagination,
            search_form=search_form,
            all_count=total_count,
        )

    except DatabaseConnectionError as e:
        logger.error(f"Database error retrieving directory page {page_number}: {str(e)}")
        flash("An error occurred while retrieving documents", "error")
        return render_template("dashboard/hs_directory.html", search_form=search_form, all_count=0), HTTP_SERVER_ERROR

    except Exception as e:
        logger.error(f"Unexpected error in hs_directory for page {page_number}: {str(e)}")
        flash("An unexpected error occurred", "error")
        return render_template("dashboard/hs_directory.html", search_form=search_form, all_count=0), HTTP_SERVER_ERROR


@dashboardbp.route("/hs/detect_exif/<document_id>", methods=["GET", "POST"])
@login_required
def detect_exif_data(document_id: str) -> Response:
    if detect_exif_metadata(document_id):
        flash("EXIF detection started.")
        return redirect(url_for("dashboard.hs_view", document_id=document_id))
    return redirect(url_for("dashboard.hs_view", document_id=document_id))


@dashboardbp.route("/hs/detect_subject/<document_id>", methods=["GET", "POST"])
@login_required
def detect_subjects(document_id: str) -> Response:
    detector_q.enqueue_call(text_subjects._text_subject, args=(document_id,), ttl=JOB_TTL, result_ttl=JOB_RESULT_TTL)
    flash("Detecting started.", "success")
    return redirect(url_for("dashboard.hs_view", document_id=document_id))


@dashboardbp.route("/statistics", methods=["GET", "POST"])
@login_required
def statistics() -> Optional[str]:
    pass


@dashboardbp.route("/settings", methods=["GET", "POST"])
@login_required
def settings() -> Optional[str]:
    pass


def _extract_onions_from_file(file_path: str) -> List[str]:
    """
    Extract onion URLs from a file.

    Args:
        file_path: Path to the file containing URLs

    Returns:
        List of extracted onion URLs

    Raises:
        IOError: If file cannot be read
    """
    try:
        with open(file_path, "r") as file:
            content = file.read()
            onion_urls = extract_onions(content)
            return [url.strip() for url in onion_urls]
    except IOError as e:
        logger.error(f"Error reading seed file {file_path}: {str(e)}")
        raise


def _extract_onions_from_text(text: str) -> List[str]:
    """
    Extract onion URLs from text input.

    Args:
        text: Text containing URLs

    Returns:
        List of extracted onion URLs
    """
    onion_urls = extract_onions(text)
    return [url.strip() for url in onion_urls]


def _enqueue_crawl_jobs(onion_urls: List[str], crawler_service: CrawlerService) -> int:
    """
    Enqueue crawl jobs for a list of URLs.

    Args:
        onion_urls: List of URLs to crawl
        crawler_service: CrawlerService instance

    Returns:
        Number of successfully enqueued jobs
    """
    enqueued_count = 0

    for url in onion_urls:
        try:
            logger.info(f"Enqueueing crawl for URL: {url}")
            crawler_service.crawl_url(url)
            enqueued_count += 1
        except Exception as e:
            logger.error(f"Failed to enqueue crawl for URL {url}: {str(e)}")
            continue

    return enqueued_count


@dashboardbp.route("/upload_seed", methods=["GET", "POST"])
@login_required
@inject_services("crawler_service", "settings")
def upload_seed(crawler_service: CrawlerService = None, settings: Settings = None) -> str:
    """
    Handle seed URL upload via file or text input.

    Allows users to submit onion URLs either by uploading a file
    or pasting URLs directly into a text field.

    Args:
        crawler_service: Injected CrawlerService instance
        settings: Injected Settings instance

    Returns:
        Rendered template with forms
    """
    search_form = SearchForm(request.form)
    multiple_urls_form = MultipleOnion()

    if multiple_urls_form.validate_on_submit():
        try:
            onion_urls_from_file = []
            onion_urls_from_text = []

            # Process file upload
            if multiple_urls_form.seed_file.data:
                try:
                    filename = secure_filename(multiple_urls_form.seed_file.data.filename)
                    file_path = settings.SEED_UPLOAD_DIR + filename
                    multiple_urls_form.seed_file.data.save(file_path)

                    onion_urls_from_file = _extract_onions_from_file(file_path)
                    logger.info(f"Extracted {len(onion_urls_from_file)} URLs from file {filename}")

                except IOError as e:
                    logger.error(f"Error processing uploaded file: {str(e)}")
                    flash("Error processing uploaded file", "error")

            # Process text input
            if multiple_urls_form.urls.data:
                onion_urls_from_text = _extract_onions_from_text(multiple_urls_form.urls.data)
                logger.info(f"Extracted {len(onion_urls_from_text)} URLs from text input")

            # Combine all URLs
            all_onion_urls = onion_urls_from_file + onion_urls_from_text

            if not all_onion_urls:
                flash("No valid onion URLs found", "warning")
            else:
                # Enqueue crawl jobs
                enqueued_count = _enqueue_crawl_jobs(all_onion_urls, crawler_service)

                if enqueued_count > 0:
                    flash(f"{enqueued_count} onion URLs added to crawler queue", "success")
                    logger.info(f"Successfully enqueued {enqueued_count} crawl jobs")
                else:
                    flash("Failed to enqueue any URLs", "error")

        except Exception as e:
            logger.error(f"Unexpected error in upload_seed: {str(e)}")
            flash("An error occurred while processing your request", "error")

    return render_template("dashboard/upload_seed.html", search_form=search_form, multiple_urls_form=multiple_urls_form)


def _handle_search_form(search_form) -> Optional[Response]:
    """
    Handle search form submission.

    Args:
        search_form: SearchForm instance

    Returns:
        Redirect response if form is valid, None otherwise
    """
    if search_form.validate_on_submit():
        phrase = search_form.phrase.data.lower()
        logger.info(f"Search form submitted with phrase: {phrase}")
        return redirect(url_for(".search", phrase=phrase))
    return None


def _handle_range_stats_form(range_stats_form, search_form, status_count, last_200, last_all) -> Optional[str]:
    """
    Handle range statistics form submission.

    Args:
        range_stats_form: RangeStats form instance
        search_form: SearchForm instance
        status_count: Status count statistics
        last_200: Recent documents with status 200
        last_all: All recent documents

    Returns:
        Rendered template if form is valid, None otherwise
    """
    if range_stats_form.validate_on_submit():
        if range_stats_form.from_dt.data and range_stats_form.to_dt.data:
            try:
                from_date = dateutil.parser.parse(str(range_stats_form.from_dt.data))
                to_date = dateutil.parser.parse(str(range_stats_form.to_dt.data))

                time_series = oss.get_requests_stats(from_date, to_date)
                logger.info(f"Generated time series stats from {from_date} to {to_date}")

                return render_template(
                    "dashboard/dashboard.html",
                    search_form=search_form,
                    status_count=status_count,
                    range_stats=range_stats_form,
                    time_series=time_series,
                    last_200=last_200,
                    last_all=last_all,
                )
            except Exception as e:
                logger.error(f"Error generating time series stats: {str(e)}")
                flash("Error generating statistics", "error")

    return None


@dashboardbp.route("/", methods=["GET", "POST"])
@login_required
@inject_crawler_service
def dashboard(crawler_service: CrawlerService = None) -> Union[str, Response]:
    """
    Display main dashboard with statistics and recent documents.

    Shows status counts, recent documents, and allows searching
    and filtering by date range.

    Args:
        crawler_service: Injected CrawlerService instance

    Returns:
        Rendered dashboard template
    """
    search_form = SearchForm(request.form)
    range_stats_form = RangeStats()

    try:
        # Get status count statistics
        status_count = oss.get_requests_stats_all()

        # Get recent documents
        last_200 = crawler_service.get_recent_documents(status=HTTP_OK, limit=DEFAULT_PAGE_SIZE)
        last_all = crawler_service.get_recent_documents(limit=DEFAULT_PAGE_SIZE)

        logger.info("Dashboard data retrieved successfully")

    except DatabaseConnectionError as e:
        logger.error(f"Database error retrieving dashboard data: {str(e)}")
        flash("Error retrieving dashboard data", "error")
        last_200 = []
        last_all = []
        status_count = {}

    except Exception as e:
        logger.error(f"Unexpected error retrieving dashboard data: {str(e)}")
        flash("An unexpected error occurred", "error")
        last_200 = []
        last_all = []
        status_count = {}

    # Handle search form submission
    search_redirect = _handle_search_form(search_form)
    if search_redirect:
        return search_redirect

    # Handle range stats form submission
    range_stats_response = _handle_range_stats_form(range_stats_form, search_form, status_count, last_200, last_all)
    if range_stats_response:
        return range_stats_response

    # Render default dashboard
    return render_template(
        "dashboard/dashboard.html",
        search_form=search_form,
        status_count=status_count,
        range_stats=range_stats_form,
        last_200=last_200,
        last_all=last_all,
    )
