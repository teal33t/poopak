import datetime
import logging
from typing import Union

from flask import Response, flash, redirect, render_template, request, url_for

from application.config import Settings
from application.config.constants import (
    CRAWL_TIMEOUT,
    HTTP_OK,
    HTTP_SERVER_ERROR,
    HTTP_SERVICE_UNAVAILABLE,
)
from application.services.crawler_service import CrawlerService
from application.utils.exceptions import DatabaseConnectionError
from application.web.captchar import SessionCaptcha
from application.web.decorators import inject_captcha, inject_crawler_service, inject_services
from application.web.services.report_service import ReportService
from application.web.services.search_service import SearchService

from ..paginate import create_pagination
from . import searchbp
from .forms import AddOnionForm, ReportOnionForm, SearchForm

logger = logging.getLogger(__name__)


@searchbp.route("/", methods=["GET", "POST"])
@inject_services("search_service")
def index(search_service: SearchService = None) -> Union[str, Response]:
    """
    Display the main search index page with statistics.

    Args:
        search_service: Injected SearchService instance

    Returns:
        Rendered index template with search form and statistics
    """
    search_form = SearchForm(request.form)
    if search_form.validate_on_submit():
        return redirect(url_for(".search", phrase=search_form.phrase.data.lower()))

    try:
        stats = search_service.get_index_statistics()

        return render_template(
            "index.html",
            form=search_form,
            checked_onions=stats["checked_onions"],
            alive_onions=stats["alive_onions"],
            offline_onions=stats["offline_onions"],
            last_crawled=stats["last_crawled"],
        )

    except DatabaseConnectionError as e:
        logger.error(f"Database connection error on index page: {str(e)}")
        flash("Error retrieving statistics", "error")
        return render_template("index.html", form=search_form)

    except Exception as e:
        logger.error(f"Unexpected error on index page: {str(e)}")
        return render_template("index.html", form=search_form)


@searchbp.route("/search/<phrase>/", methods=["GET"])
@searchbp.route("/search/<phrase>/<int:page_number>", methods=["GET"])
@inject_services("search_service", "settings")
def search(phrase: str, page_number: int = 1, search_service: SearchService = None, settings: Settings = None) -> str:
    """
    Search for documents containing the specified phrase.

    Args:
        phrase: Search phrase
        page_number: Page number for pagination
        search_service: Injected SearchService instance
        settings: Injected Settings instance

    Returns:
        Rendered search results template
    """
    search_form = SearchForm()

    try:
        # Determine search method for debugging
        search_method = "Elasticsearch" if (
            search_service.elasticsearch_service is not None and 
            search_service._elasticsearch_enabled
        ) else "MongoDB"
        
        # Get documents and count using service
        documents, all_count = search_service.search_documents(
            phrase, page_number, settings.ITEMS_PER_PAGE
        )
        pagination = create_pagination(page_number, settings.ITEMS_PER_PAGE, all_count)

        return render_template(
            "result.html",
            results=documents,
            pagination=pagination,
            phrase=phrase,
            search_form=search_form,
            all_count=all_count,
            search_method=search_method,
        )

    except DatabaseConnectionError as e:
        logger.error(f"Database error during search for '{phrase}': {str(e)}")
        flash("Error performing search", "error")
        return render_template("result.html", phrase=phrase, all_count=0, search_form=search_form)

    except Exception as e:
        logger.error(f"Unexpected error during search for '{phrase}': {str(e)}")
        flash("An unexpected error occurred", "error")
        return render_template("result.html", phrase=phrase, all_count=0, search_form=search_form)


@searchbp.route("/report/<string:document_id>", methods=["GET", "POST"])
@inject_services("report_service", "captcha")
def report(document_id: str, report_service: ReportService = None, captcha: SessionCaptcha = None) -> Union[str, Response]:
    """
    Report a document for inappropriate content.

    Args:
        document_id: ID of the document to report
        report_service: Injected ReportService instance
        captcha: Injected SessionCaptcha instance

    Returns:
        Rendered report form or redirect
    """
    from application.utils.exceptions import DocumentNotFoundError, ValidationError
    
    report_form = ReportOnionForm()
    search_form = SearchForm()
    document = None

    try:
        document = report_service.get_document_for_report(document_id)
        report_form.url = document["url"]
        report_form.id = document_id

    except ValidationError as e:
        logger.warning(f"Validation error for report: {str(e)}")
        flash("Invalid document ID", "error")
        return redirect(url_for("search.index"))
    except DocumentNotFoundError:
        flash("Document not found", "error")
        return redirect(url_for("search.index"))
    except DatabaseConnectionError as e:
        logger.error(f"Database error retrieving document for report {document_id}: {str(e)}")
        flash("Error retrieving document", "error")
        return redirect(url_for("search.index"))
    except Exception as e:
        logger.error(f"Unexpected error retrieving document for report {document_id}: {str(e)}")
        flash("Invalid document ID", "error")
        return redirect(url_for("search.index"))

    if report_form.validate_on_submit():
        # Validate captcha with improved error messages
        is_valid, error_message = captcha.validate()
        
        if not is_valid:
            if error_message:
                flash(error_message, "danger")
        else:
            try:
                report_service.submit_report(document_id, report_form.body.data)
                flash("Reported! You are helping the community.", "success")
                return redirect(url_for("search.index"))

            except (DocumentNotFoundError, ValidationError) as e:
                logger.warning(f"Error submitting report: {str(e)}")
                flash("Document not found", "error")
                return redirect(url_for("search.index"))
            except DatabaseConnectionError as e:
                logger.error(f"Database error saving report for document {document_id}: {str(e)}")
                flash("Error submitting report", "error")
            except Exception as e:
                logger.error(f"Unexpected error saving report for document {document_id}: {str(e)}")
                flash("Error submitting report", "error")

    if document and document.get("url"):
        return render_template("report.html", search_form=search_form, report_form=report_form)
    else:
        flash("Invalid document", "error")
        return redirect(url_for("search.index"))


@searchbp.route("/new/", methods=["GET", "POST"])
@inject_services("crawler_service", "captcha")
def add_onion(crawler_service: CrawlerService = None, captcha: SessionCaptcha = None) -> Union[str, Response]:
    """
    Add a new onion URL to the crawler queue.

    Args:
        crawler_service: Injected CrawlerService instance
        captcha: Injected SessionCaptcha instance

    Returns:
        Rendered form or redirect after submission
    """
    from application.utils.url_utils import normalize_url, is_valid_onion_url
    from application.utils.exceptions import ValidationError, CrawlerError
    
    add_form = AddOnionForm()
    search_form = SearchForm()

    if add_form.validate_on_submit():
        # Validate captcha with improved error messages
        is_valid, error_message = captcha.validate()
        
        if not is_valid:
            if error_message:
                flash(error_message, "danger")
            return redirect(url_for("search.add_onion"))
        
        url = add_form.url.data.strip()

        try:
            # Normalize URL (ensure it has a scheme)
            url = normalize_url(url)
            
            # Validate onion URL
            if not is_valid_onion_url(url):
                flash(
                    "Address is not valid, onion must be at least 16 chars, "
                    "ie. http://xxxxxxxxxxxxxxxx.onion or xxxxxxxxxxxxxxxx.onion",
                    "danger",
                )
                return redirect(url_for("search.add_onion"))

            # Enqueue crawl job using service
            job_id = crawler_service.enqueue_simple_crawl(url, timeout=CRAWL_TIMEOUT)

            if job_id:
                logger.info(f"New onion URL added to crawler queue: {url} (Job ID: {job_id})")
                flash("New onion added to crawler queue.", "success")
            else:
                logger.warning(f"Failed to get job ID for URL: {url}")
                flash("Failed to add onion to queue", "error")

            return redirect(url_for("search.index"))

        except ValidationError as e:
            logger.warning(f"Validation error for URL {url}: {str(e)}")
            flash("Invalid URL format", "error")
            return redirect(url_for("search.add_onion"))
        except CrawlerError as e:
            logger.error(f"Crawler error enqueueing URL {url}: {str(e)}")
            flash("Error adding onion to crawler queue", "error")
            return redirect(url_for("search.add_onion"))
        except Exception as e:
            logger.error(f"Unexpected error enqueueing crawl for URL {url}: {str(e)}")
            flash("Error adding onion to crawler queue", "error")
            return redirect(url_for("search.add_onion"))

    elif "url" in add_form.errors:
        flash(
            "Address is not valid, onion must be at least 16 chars, "
            "ie. http://xxxxxxxxxxxxxxxx.onion or xxxxxxxxxxxxxxxx.onion",
            "danger",
        )
        return redirect(url_for("search.add_onion"))

    return render_template("new.html", add_form=add_form, search_form=search_form)


@searchbp.route("/directory/", methods=["GET"])
@searchbp.route("/directory/<int:page_number>", methods=["GET"])
@inject_services("search_service", "settings")
def directory(page_number: int = 1, search_service: SearchService = None, settings: Settings = None) -> str:
    """
    Display directory of alive onion sites (HTTP 200 status).

    Args:
        page_number: Page number for pagination
        search_service: Injected SearchService instance
        settings: Injected Settings instance

    Returns:
        Rendered directory template
    """
    search_form = SearchForm()

    try:
        documents, all_count = search_service.get_directory_documents(
            page_number, settings.ITEMS_PER_PAGE, status_filter=HTTP_OK
        )
        pagination = create_pagination(page_number, settings.ITEMS_PER_PAGE, all_count)

        return render_template(
            "directory.html", results=documents, pagination=pagination, search_form=search_form, all_count=all_count
        )

    except DatabaseConnectionError as e:
        logger.error(f"Database error loading directory page {page_number}: {str(e)}")
        flash("Error loading directory", "error")
        return render_template("directory.html", search_form=search_form, all_count=0)

    except Exception as e:
        logger.error(f"Unexpected error loading directory page {page_number}: {str(e)}")
        flash("An unexpected error occurred", "error")
        return render_template("directory.html", search_form=search_form, all_count=0)


@searchbp.route("/directory/all", methods=["GET"])
@searchbp.route("/directory/all/<int:page_number>", methods=["GET"])
@inject_services("search_service", "settings")
def directory_all(page_number: int = 1, search_service: SearchService = None, settings: Settings = None) -> str:
    """
    Display directory of all crawled onion sites (all statuses).

    Args:
        page_number: Page number for pagination
        search_service: Injected SearchService instance
        settings: Injected Settings instance

    Returns:
        Rendered directory template
    """
    search_form = SearchForm()

    try:
        documents, all_count = search_service.get_directory_documents(
            page_number, settings.ITEMS_PER_PAGE, status_filter=None
        )
        pagination = create_pagination(page_number, settings.ITEMS_PER_PAGE, all_count)
        is_all = True

        return render_template(
            "directory.html",
            results=documents,
            pagination=pagination,
            search_form=search_form,
            all_count=all_count,
            is_all=is_all,
        )

    except DatabaseConnectionError as e:
        logger.error(f"Database error loading all directory page {page_number}: {str(e)}")
        flash("Error loading directory", "error")
        return render_template("directory.html", search_form=search_form, all_count=0)

    except Exception as e:
        logger.error(f"Unexpected error loading all directory page {page_number}: {str(e)}")
        flash("An unexpected error occurred", "error")
        return render_template("directory.html", search_form=search_form, all_count=0)


@searchbp.route("/faq")
def faq() -> str:
    search_form = SearchForm()
    return render_template("faq.html", search_form=search_form)


@searchbp.route("/export_all")
@inject_services("search_service")
def export_csv(search_service: SearchService = None) -> Response:
    """
    Export all alive onion URLs as plain text with streaming.

    Args:
        search_service: Injected SearchService instance

    Returns:
        Plain text response with list of URLs
    """
    from flask import stream_with_context

    def generate_export():
        """
        Generator function for streaming export data.
        
        Yields lines of text for the export file.
        """
        try:
            yield f"# {HTTP_OK} OK status list\n"
            
            # Use service to get all URLs
            urls = search_service.export_alive_urls(batch_size=100)
            
            for url in urls:
                yield f"{url}\n"
            
        except DatabaseConnectionError as e:
            logger.error(f"Database error during export: {str(e)}")
            yield "# Error: Unable to export data\n"
        except Exception as e:
            logger.error(f"Unexpected error during export: {str(e)}")
            yield "# Error: Unable to export data\n"

    try:
        return Response(
            stream_with_context(generate_export()),
            mimetype="text/plain",
            headers={"Content-Disposition": "attachment; filename=onion_export.txt"}
        )
    except Exception as e:
        logger.error(f"Error creating export response: {str(e)}")
        return Response("# Error: Unable to export data\n", mimetype="text/plain", status=HTTP_SERVER_ERROR)


@searchbp.route("/admin/reindex", methods=["POST"])
@inject_services("search_service")
def admin_reindex(search_service: SearchService = None) -> Response:
    """
    Admin endpoint to trigger bulk reindex of all documents to Elasticsearch.
    
    This endpoint should be protected by authentication in production.

    Args:
        search_service: Injected SearchService instance

    Returns:
        JSON response with reindex status and count
    """
    from flask import jsonify
    
    try:
        # Check if Elasticsearch is available
        if search_service.elasticsearch_service is None or not search_service._elasticsearch_enabled:
            logger.warning("Reindex requested but Elasticsearch is not available")
            return jsonify({
                "success": False,
                "error": "Elasticsearch is not available"
            }), HTTP_SERVICE_UNAVAILABLE
        
        logger.info("Starting bulk reindex operation via admin endpoint")
        
        # Trigger reindex
        indexed_count = search_service.reindex_all_documents()
        
        logger.info(f"Bulk reindex completed: {indexed_count} documents indexed")
        
        return jsonify({
            "success": True,
            "indexed_count": indexed_count,
            "message": f"Successfully reindexed {indexed_count} documents"
        }), HTTP_OK
        
    except RuntimeError as e:
        logger.error(f"Runtime error during reindex: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), HTTP_SERVICE_UNAVAILABLE
        
    except DatabaseConnectionError as e:
        logger.error(f"Database error during reindex: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Database connection error"
        }), HTTP_SERVER_ERROR
        
    except Exception as e:
        logger.error(f"Unexpected error during reindex: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred"
        }), HTTP_SERVER_ERROR


@searchbp.route("/health/elasticsearch", methods=["GET"])
@inject_services("search_service")
def elasticsearch_health(search_service: SearchService = None) -> Response:
    """
    Health check endpoint for Elasticsearch status.
    
    Returns the current status of Elasticsearch connection and availability.

    Args:
        search_service: Injected SearchService instance

    Returns:
        JSON response with Elasticsearch health status
    """
    from flask import jsonify
    
    try:
        # Check if Elasticsearch service exists
        if search_service.elasticsearch_service is None:
            return jsonify({
                "status": "disabled",
                "available": False,
                "message": "Elasticsearch service is not configured"
            }), HTTP_OK
        
        # Check if Elasticsearch is available
        is_available = search_service.elasticsearch_service.is_available()
        
        if is_available:
            return jsonify({
                "status": "healthy",
                "available": True,
                "hosts": search_service.elasticsearch_service.hosts,
                "index": search_service.elasticsearch_service.index_name,
                "message": "Elasticsearch is available and healthy"
            }), HTTP_OK
        else:
            return jsonify({
                "status": "unhealthy",
                "available": False,
                "hosts": search_service.elasticsearch_service.hosts,
                "index": search_service.elasticsearch_service.index_name,
                "message": "Elasticsearch is configured but not available"
            }), HTTP_SERVICE_UNAVAILABLE
            
    except Exception as e:
        logger.error(f"Error checking Elasticsearch health: {str(e)}")
        return jsonify({
            "status": "error",
            "available": False,
            "error": str(e),
            "message": "Error checking Elasticsearch health"
        }), HTTP_SERVER_ERROR
