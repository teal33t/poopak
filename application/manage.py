"""
Worker management CLI commands.

This module provides Click commands for starting RQ workers for different
worker types (panel, app, detector, crawler). All worker logic is delegated
to the WorkerService to eliminate code duplication.
"""

from typing import Optional

import click

from application.config import settings
from application.config.constants import QUEUE_HIGH_PRIORITY
from application.infrastructure.queue import WorkerType
from application.services.worker_service import WorkerService

# Initialize worker service with application settings
worker_service = WorkerService(settings)


def _initialize_search_service():
    """
    Initialize SearchService with all required dependencies.
    
    Returns:
        Configured SearchService instance
        
    Raises:
        RuntimeError: If Elasticsearch is not available
    """
    from application.infrastructure.database import DatabaseConnection
    from application.repositories.document_repository import DocumentRepository
    from application.services.elasticsearch_service import ElasticsearchService
    from application.web.services.search_service import SearchService
    
    # Initialize database connection
    db_connection = DatabaseConnection(settings)
    database = db_connection.get_database()
    
    # Initialize Elasticsearch service if enabled
    elasticsearch_service = None
    if settings.ELASTICSEARCH_ENABLED:
        try:
            # Parse hosts from comma-separated string to list
            es_hosts = [host.strip() for host in settings.ELASTICSEARCH_HOSTS.split(',')]
            
            elasticsearch_service = ElasticsearchService(
                hosts=es_hosts,
                index_name=settings.ELASTICSEARCH_INDEX,
                timeout=settings.ELASTICSEARCH_TIMEOUT
            )
            
            if not elasticsearch_service.is_available():
                raise RuntimeError("Elasticsearch service is not available")
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Elasticsearch: {e}")
    else:
        raise RuntimeError("Elasticsearch is disabled in configuration")
    
    # Initialize document repository with Elasticsearch
    document_repository = DocumentRepository(database, elasticsearch_service)
    
    # Initialize and return search service
    return SearchService(document_repository, elasticsearch_service)


@click.group()
def cli() -> None:
    """Management commands for workers and maintenance tasks."""
    pass


@click.group()
def workers() -> None:
    """Worker management commands."""
    pass


@click.command(name="run_panel_worker")
@click.option("--queue", default=QUEUE_HIGH_PRIORITY, help=f"Queue name to process (default: {QUEUE_HIGH_PRIORITY})")
def run_panel_worker(queue: str) -> None:
    """
    Start the panel worker.

    The panel worker processes jobs from the panel queue (Redis DB 0).

    Args:
        queue: Name of the queue to process
    """
    worker_service.start_worker(WorkerType.PANEL, queue)


@click.command(name="run_app_worker")
@click.option("--queue", default=QUEUE_HIGH_PRIORITY, help=f"Queue name to process (default: {QUEUE_HIGH_PRIORITY})")
def run_app_worker(queue: str) -> None:
    """
    Start the app worker.

    The app worker processes jobs from the app queue (Redis DB 1).

    Args:
        queue: Name of the queue to process
    """
    worker_service.start_worker(WorkerType.APP, queue)


@click.command(name="run_detector_worker")
@click.option("--queue", default=QUEUE_HIGH_PRIORITY, help=f"Queue name to process (default: {QUEUE_HIGH_PRIORITY})")
def run_detector_worker(queue: str) -> None:
    """
    Start the detector worker.

    The detector worker processes jobs from the detector queue (Redis DB 2).

    Args:
        queue: Name of the queue to process
    """
    worker_service.start_worker(WorkerType.DETECTOR, queue)


@click.command(name="run_crawler_worker")
@click.option("--queue", default=QUEUE_HIGH_PRIORITY, help=f"Queue name to process (default: {QUEUE_HIGH_PRIORITY})")
def run_crawler_worker(queue: str) -> None:
    """
    Start the crawler worker.

    The crawler worker processes jobs from the crawler queue (Redis DB 3).

    Args:
        queue: Name of the queue to process
    """
    worker_service.start_worker(WorkerType.CRAWLER, queue)


# Register commands with the workers group
workers.add_command(run_panel_worker)
workers.add_command(run_app_worker)
workers.add_command(run_detector_worker)
workers.add_command(run_crawler_worker)


@click.command(name="reindex_elasticsearch")
@click.option("--batch-size", default=1000, help="Number of documents to process per batch (default: 1000)")
def reindex_elasticsearch(batch_size: int) -> None:
    """
    Reindex all documents from MongoDB to Elasticsearch.
    
    This command fetches all documents from MongoDB and indexes them
    in Elasticsearch using bulk operations for efficiency. Progress
    is displayed during the operation.
    
    Args:
        batch_size: Number of documents to process per batch
    """
    import sys
    import time
    
    click.echo("=" * 60)
    click.echo("Elasticsearch Bulk Reindex Operation")
    click.echo("=" * 60)
    click.echo()
    
    try:
        # Initialize search service
        click.echo("Initializing services...")
        search_service = _initialize_search_service()
        click.echo("✓ Services initialized successfully")
        click.echo()
        
        # Start reindex operation
        click.echo(f"Starting reindex with batch size: {batch_size}")
        click.echo()
        
        start_time = time.time()
        
        # Call reindex method
        total_indexed = search_service.reindex_all_documents(batch_size=batch_size)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Display summary statistics
        click.echo()
        click.echo("=" * 60)
        click.echo("Reindex Summary")
        click.echo("=" * 60)
        click.echo(f"Total documents indexed: {total_indexed}")
        click.echo(f"Elapsed time: {elapsed_time:.2f} seconds")
        
        if total_indexed > 0:
            docs_per_second = total_indexed / elapsed_time
            click.echo(f"Average speed: {docs_per_second:.2f} documents/second")
        
        click.echo()
        click.echo("✓ Reindex completed successfully")
        
    except RuntimeError as e:
        click.echo()
        click.echo(f"✗ Error: {str(e)}", err=True)
        click.echo()
        click.echo("Please ensure:")
        click.echo("  1. Elasticsearch is enabled in configuration (ELASTICSEARCH_ENABLED=true)")
        click.echo("  2. Elasticsearch service is running and accessible")
        click.echo("  3. Connection settings are correct (ELASTICSEARCH_HOSTS)")
        sys.exit(1)
        
    except Exception as e:
        click.echo()
        click.echo(f"✗ Unexpected error: {str(e)}", err=True)
        click.echo()
        click.echo("Check the application logs for more details.")
        sys.exit(1)


# Register command groups and commands
cli.add_command(workers)
cli.add_command(reindex_elasticsearch)


if __name__ == "__main__":
    cli()
