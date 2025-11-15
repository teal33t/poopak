.PHONY: help dev-up dev-down dev-logs dev-build dev-restart prod-up prod-down prod-logs prod-build prod-restart clean health backup restore

# Default target
help:
	@echo "Onion Crawler - Docker Management"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev-up          - Start development environment"
	@echo "  make dev-down        - Stop development environment"
	@echo "  make dev-logs        - View development logs"
	@echo "  make dev-build       - Rebuild development images"
	@echo "  make dev-restart     - Restart development environment"
	@echo "  make dev-shell       - Open shell in web-app container"
	@echo ""
	@echo "Production Commands:"
	@echo "  make prod-up         - Start production environment"
	@echo "  make prod-down       - Stop production environment"
	@echo "  make prod-logs       - View production logs"
	@echo "  make prod-build      - Rebuild production images"
	@echo "  make prod-restart    - Restart production environment"
	@echo "  make prod-shell      - Open shell in web-app container"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  make health          - Check service health status"
	@echo "  make backup          - Backup databases"
	@echo "  make restore         - Restore databases from backup"
	@echo "  make reindex         - Reindex Elasticsearch"
	@echo "  make clean           - Remove all containers and volumes"
	@echo "  make stats           - Show container resource usage"
	@echo ""

# Development environment
dev-up:
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Development environment started. Access at http://localhost"
	@echo "MongoDB Admin: http://localhost:3000"

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

dev-build:
	docker-compose -f docker-compose.dev.yml build --no-cache

dev-restart:
	docker-compose -f docker-compose.dev.yml restart

dev-shell:
	docker exec -it onion-web-app-dev bash

# Production environment
prod-up:
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Copy .env.example to .env and configure it."; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Production environment started. Access at http://localhost"

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

prod-build:
	docker-compose -f docker-compose.prod.yml build --no-cache

prod-restart:
	docker-compose -f docker-compose.prod.yml restart

prod-shell:
	docker exec -it onion-web-app-prod bash

# Health checks
health:
	@echo "Checking service health..."
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep onion

# Statistics
stats:
	docker stats --no-stream

# Backup
backup:
	@echo "Creating backup directory..."
	@mkdir -p backups
	@echo "Backing up MongoDB..."
	@docker exec onion-mongodb-prod mongodump --out /tmp/backup
	@docker cp onion-mongodb-prod:/tmp/backup ./backups/mongodb-$(shell date +%Y%m%d-%H%M%S)
	@echo "Backup completed: backups/mongodb-$(shell date +%Y%m%d-%H%M%S)"

# Restore (use: make restore BACKUP=backups/mongodb-20240101-120000)
restore:
	@if [ -z "$(BACKUP)" ]; then \
		echo "Error: Please specify BACKUP path. Example: make restore BACKUP=backups/mongodb-20240101-120000"; \
		exit 1; \
	fi
	@echo "Restoring MongoDB from $(BACKUP)..."
	@docker cp $(BACKUP) onion-mongodb-prod:/tmp/restore
	@docker exec onion-mongodb-prod mongorestore /tmp/restore
	@echo "Restore completed"

# Reindex Elasticsearch
reindex:
	@echo "Reindexing Elasticsearch..."
	@docker exec onion-web-app-prod python manage.py reindex_elasticsearch
	@echo "Reindex completed"

# Clean up
clean:
	@echo "WARNING: This will remove all containers, volumes, and data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f docker-compose.dev.yml down -v; \
		docker-compose -f docker-compose.prod.yml down -v; \
		docker system prune -f; \
		echo "Cleanup completed"; \
	else \
		echo "Cleanup cancelled"; \
	fi

# Install dependencies
install:
	@echo "Installing Docker and Docker Compose..."
	@echo "Please run the appropriate installation script for your OS"
	@echo "Visit: https://docs.docker.com/get-docker/"
