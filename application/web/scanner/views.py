"""
Scanner views for EXIF and subject detection operations.

This module provides views for initiating and managing detection operations
on crawled documents.
"""

import logging
from typing import Optional

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from application.repositories.document_repository import DocumentRepository
from application.services.detection_service import DetectionService
from application.utils.exceptions import DatabaseConnectionError, DetectionError, DocumentNotFoundError
from application.web.decorators import inject_services

from . import scannerbp

logger = logging.getLogger(__name__)


@scannerbp.route("/scanner", methods=["GET", "POST"])
@login_required
@inject_services("detection_service", "document_repository")
def scanner_overview(detection_service: DetectionService = None, document_repository: DocumentRepository = None) -> str:
    """
    Scanner overview page for detection operations.

    Handles both GET requests to display the scanner interface and POST requests
    to initiate detection operations on documents.

    Args:
        detection_service: Injected DetectionService instance
        document_repository: Injected DocumentRepository instance

    Returns:
        Rendered template or redirect response
    """
    try:
        if request.method == "POST":
            # Get document ID from form
            document_id = request.form.get("document_id", "").strip()

            if not document_id:
                flash("Please provide a document ID", "error")
                return redirect(url_for("scanner.scanner_overview"))

            # Verify document exists
            try:
                document = document_repository.find_by_id(document_id)
                if not document:
                    flash(f"Document {document_id} not found", "error")
                    return redirect(url_for("scanner.scanner_overview"))

            except DocumentNotFoundError:
                flash(f"Document {document_id} not found", "error")
                return redirect(url_for("scanner.scanner_overview"))

            # Get detection type from form
            detection_type = request.form.get("detection_type", "")

            if detection_type == "exif":
                # Enqueue EXIF detection for document images
                try:
                    image_urls = document.get("images", [])
                    if not image_urls:
                        flash("Document has no images for EXIF detection", "warning")
                        return redirect(url_for("scanner.scanner_overview"))

                    count = detection_service.enqueue_exif_detection(document_id, image_urls)
                    flash(f"Enqueued {count} EXIF detection jobs for document {document_id}", "success")
                    logger.info(f"User initiated EXIF detection for document {document_id}")

                except DetectionError as e:
                    flash(f"Failed to enqueue EXIF detection: {str(e)}", "error")
                    logger.error(f"EXIF detection failed for document {document_id}: {str(e)}")

            elif detection_type == "subjects":
                # Enqueue subject detection
                try:
                    job_id = detection_service.enqueue_subject_detection(document_id)
                    flash(f"Subject detection job enqueued (Job ID: {job_id})", "success")
                    logger.info(f"User initiated subject detection for document {document_id}")

                except DetectionError as e:
                    flash(f"Failed to enqueue subject detection: {str(e)}", "error")
                    logger.error(f"Subject detection failed for document {document_id}: {str(e)}")

            else:
                flash("Invalid detection type", "error")

            return redirect(url_for("scanner.scanner_overview"))

        # GET request - display scanner interface
        # Get recent documents for display
        try:
            recent_documents = document_repository.find_recent(limit=10)
            return render_template("scanner/overview.html", documents=recent_documents)

        except DatabaseConnectionError as e:
            logger.error(f"Database error retrieving recent documents: {str(e)}")
            flash("Error loading documents", "error")
            return render_template("scanner/overview.html", documents=[])

    except Exception as e:
        logger.error(f"Unexpected error in scanner_overview: {str(e)}")
        flash("An unexpected error occurred", "error")
        return redirect(url_for("dashboard.dashboard"))
