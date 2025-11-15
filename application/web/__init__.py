"""
Flask application factory and initialization.

This module provides the application factory pattern with dependency injection
for infrastructure components, repositories, and services.
"""

import logging

import flask_login
from flask import Flask, redirect, send_from_directory, url_for
from flask_wtf.csrf import CSRFProtect

from application.config import Settings, settings
from application.config.constants import QUEUE_HIGH_PRIORITY
from application.infrastructure.database import DatabaseConnection
from application.infrastructure.logging_config import configure_logging
from application.infrastructure.queue import QueueFactory
from application.repositories.document_repository import DocumentRepository
from application.repositories.user_repository import UserRepository
from application.services.authentication_service import AuthenticationService
from application.services.crawler_service import CrawlerService
from application.services.detection_service import DetectionService
from application.services.elasticsearch_service import ElasticsearchService
from application.services.worker_service import WorkerService
from application.web.services.report_service import ReportService
from application.web.services.search_service import SearchService

from .captchar import SessionCaptcha
from application.models import User
from .error_tracking import init_error_tracking

logger = logging.getLogger(__name__)


def create_app(config: Settings = None) -> Flask:
    """
    Application factory with dependency injection.

    Creates and configures the Flask application with all necessary
    infrastructure, repositories, and services initialized and injected.

    Args:
        config: Optional configuration settings (uses default if None)

    Returns:
        Configured Flask application instance
    """
    if config is None:
        config = settings

    app = Flask(__name__)

    # Configure Flask application
    app.config["WTF_CSRF_ENABLED"] = config.WTF_CSRF_ENABLED
    app.config["BOOTSTRAP_SERVE_LOCAL"] = True
    app.config["REDIS_URL"] = config.redis_uri
    app.config["QUEUES"] = QUEUE_HIGH_PRIORITY
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["SESSION_TYPE"] = config.SESSION_TYPE
    app.config["CAPTCHA_ENABLE"] = config.CAPTCHA_ENABLE
    app.config["CAPTCHA_LENGTH"] = config.CAPTCHA_LENGTH

    # Configure logging
    configure_logging(app)

    # Initialize error tracking for production
    error_tracker = init_error_tracking(app)
    app.error_tracker = error_tracker

    # Initialize infrastructure layer
    db_connection = DatabaseConnection(config)
    queue_factory = QueueFactory(config)

    # Initialize Elasticsearch service if enabled
    elasticsearch_service = None
    if config.ELASTICSEARCH_ENABLED:
        try:
            # Parse hosts from comma-separated string to list
            es_hosts = [host.strip() for host in config.ELASTICSEARCH_HOSTS.split(',')]
            
            elasticsearch_service = ElasticsearchService(
                hosts=es_hosts,
                index_name=config.ELASTICSEARCH_INDEX,
                timeout=config.ELASTICSEARCH_TIMEOUT
            )
            
            # Create index on startup if it doesn't exist
            if elasticsearch_service.is_available():
                elasticsearch_service.create_index()
                logger.info("Elasticsearch service initialized successfully")
            else:
                logger.warning("Elasticsearch service created but not available")
                elasticsearch_service = None
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch service: {e}")
            elasticsearch_service = None
    else:
        logger.info("Elasticsearch is disabled in configuration")

    # Initialize repositories
    database = db_connection.get_database()
    document_repository = DocumentRepository(database, elasticsearch_service)
    user_repository = UserRepository(database)

    # Initialize services
    authentication_service = AuthenticationService(user_repository)
    crawler_service = CrawlerService(document_repository, queue_factory, config)
    detection_service = DetectionService(document_repository, queue_factory, config)
    worker_service = WorkerService(queue_factory)
    
    # Initialize web services
    search_service = SearchService(document_repository, elasticsearch_service)
    report_service = ReportService(document_repository)

    # Store dependencies in app context for view access
    app.db_connection = db_connection
    app.queue_factory = queue_factory
    app.document_repository = document_repository
    app.user_repository = user_repository
    app.authentication_service = authentication_service
    app.crawler_service = crawler_service
    app.detection_service = detection_service
    app.worker_service = worker_service
    app.search_service = search_service
    app.report_service = report_service
    app.elasticsearch_service = elasticsearch_service
    app.settings = config

    # Initialize Flask-Login
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)
    login_manager.session_protection = "strong"
    login_manager.login_view = "auth.login"
    login_manager.login_message = ""

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load user by ID for Flask-Login.

        Args:
            user_id: The user ID (username)

        Returns:
            User instance if found, None otherwise
        """
        try:
            user_data = user_repository.find_by_id(user_id)
            if not user_data:
                return None
            return User(user_data["_id"])
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {str(e)}")
            return None

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        """Handle unauthorized access attempts."""
        return redirect(url_for("auth.login"))

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Initialize captcha
    captcha = SessionCaptcha(app)
    app.captcha = captcha
    # Store in extensions for decorator access
    if not hasattr(app, "extensions"):
        app.extensions = {}
    app.extensions["captcha"] = captcha

    # Register blueprints
    from .auth import authbp

    app.register_blueprint(authbp, url_prefix="/auth")

    from .search import searchbp

    app.register_blueprint(searchbp)

    from .scanner import scannerbp

    app.register_blueprint(scannerbp, url_prefix="/scanner")

    from .dashboard import dashboardbp

    app.register_blueprint(dashboardbp, url_prefix="/dashboard")

    # Custom routes
    @app.route("/screenshots/<path:filename>")
    def screenshots_path(filename):
        """
        Serve screenshot files.

        Args:
            filename: The screenshot filename (without .png extension)

        Returns:
            Screenshot file response
        """
        _filename = f"{filename}.png"
        return send_from_directory(config.SCREENSHOT_UPLOAD_DIR, _filename)

    @app.route("/health")
    def health_check():
        """
        Health check endpoint for Docker and monitoring systems.

        Returns:
            JSON response with service status
        """
        from flask import jsonify
        
        health_status = {
            "status": "healthy",
            "service": "onion-crawler",
            "components": {}
        }
        
        # Check MongoDB
        try:
            db_connection.client.admin.command('ping')
            health_status["components"]["mongodb"] = "healthy"
        except Exception as e:
            health_status["components"]["mongodb"] = "unhealthy"
            health_status["status"] = "degraded"
            logger.warning(f"MongoDB health check failed: {e}")
        
        # Check Redis
        try:
            queue_factory.get_queue(QUEUE_HIGH_PRIORITY).connection.ping()
            health_status["components"]["redis"] = "healthy"
        except Exception as e:
            health_status["components"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"
            logger.warning(f"Redis health check failed: {e}")
        
        # Check Elasticsearch
        try:
            if elasticsearch_service and elasticsearch_service.is_available():
                health_status["components"]["elasticsearch"] = "healthy"
            else:
                health_status["components"]["elasticsearch"] = "unavailable"
        except Exception as e:
            health_status["components"]["elasticsearch"] = "unhealthy"
            logger.warning(f"Elasticsearch health check failed: {e}")
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code

    # Register error handlers
    from .errors import register_error_handlers as register_app_error_handlers
    register_app_error_handlers(app)

    # Register filters
    register_filters(app)

    logger.info("Flask application initialized successfully")

    return app





def register_filters(app: Flask) -> None:
    """
    Register Jinja2 filters for the application.

    Args:
        app: Flask application instance
    """
    from .filters import datetimeformat, limitbody

    app.jinja_env.filters["datetimeformat"] = datetimeformat
    app.jinja_env.filters["limitbody"] = limitbody


# Create default application instance for backward compatibility
app = create_app()
