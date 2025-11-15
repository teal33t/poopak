# POOPAK | TOR Hidden Service Crawler

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Open Source Love](https://badges.frapsoft.com/os/v1/open-source-badges/) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![Generic badge](https://img.shields.io/badge/Tor-Hidden%20Services-green.svg)](https://torproject.org/)

An experimental application for crawling, scanning, and gathering data from TOR hidden services.

## Features

- Multi-level in-depth crawling using CURL
- Link extraction and email/BTC/ETH/XMR address detection
- EXIF metadata extraction
- Screenshot capture (using Splash)
- Subject detection (using Spacy)
- Port scanning
- Report generation (CSV/PDF)
- Full-text search with Elasticsearch
- Language detection
- Docker-based deployment with web UI

## Quick Start

### Development
```bash
make dev-up      # Start all services
make dev-logs    # View logs
```
Access at: http://localhost

### Production
```bash
cp .env.example .env    # Configure passwords
make prod-up            # Start all services
make health             # Check status
```

## Architecture

### Core Services
- **nginx**: Web server & reverse proxy
- **web-app**: Flask application
- **mongodb**: Database
- **redis**: Message queue
- **elasticsearch**: Search engine
- **torpool**: Tor proxy pool
- **splash**: Screenshot service
- **spacy**: NLP service
- **workers**: Background processing (crawler, detector, app, panel)

### Key Features
- Separate dev/prod Docker configurations
- Health checks for all services
- Network isolation in production
- Automatic service dependencies
- Hot-reload in development

## Common Commands

```bash
# Development
make dev-up          # Start
make dev-logs        # View logs
make dev-shell       # Open shell
make dev-down        # Stop

# Production
make prod-up         # Start
make prod-logs       # View logs
make health          # Check health
make backup          # Backup databases
make prod-down       # Stop

# Maintenance
make reindex         # Reindex Elasticsearch
make stats           # Resource usage
```

## Configuration

### Environment Variables (Production)

Create `.env` file:
```bash
# Database
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=your-secure-password

# Redis
REDIS_PASSWORD=your-secure-password

# Application
SECRET_KEY=your-random-secret-key
FLASK_ENV=production

# Elasticsearch
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_HOSTS=http://elasticsearch:9200

# Error Tracking (Optional)
ERROR_TRACKING_ENABLED=true
SENTRY_DSN=your-sentry-dsn
```

## Recent Improvements

### Docker & Infrastructure
- ✅ Separate dev/prod configurations
- ✅ Health checks for all services
- ✅ Multi-stage Dockerfile
- ✅ Network isolation (production)
- ✅ Non-root containers
- ✅ Optimized caching

### Application Architecture
- ✅ Dependency injection for web views
- ✅ Repository pattern for data access
- ✅ Service layer for business logic
- ✅ Comprehensive error handling
- ✅ Production error tracking (Sentry)
- ✅ Elasticsearch integration

### Code Quality
- ✅ Type hints throughout
- ✅ Structured logging
- ✅ Custom exception hierarchy
- ✅ Consistent error responses
- ✅ User-friendly error pages

## Requirements

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

## Installation

```bash
# Clone repository
git clone <repository-url>
cd poopak

# Start development environment
make dev-up

# Verify services
make health

# Access application
open http://localhost
```

## Health Monitoring

Check service health:
```bash
make health
```

Or visit: http://localhost:8000/health

Response:
```json
{
  "status": "healthy",
  "service": "onion-crawler",
  "components": {
    "mongodb": "healthy",
    "redis": "healthy",
    "elasticsearch": "healthy"
  }
}
```

## Troubleshooting

### Services won't start
```bash
make dev-logs        # Check logs
make health          # Check health
```

### Port conflicts
```bash
lsof -i :80          # Find what's using port 80
```

### Clean restart
```bash
make dev-down
make dev-up
```

### Database issues
```bash
docker exec onion-mongodb-dev mongosh --eval "db.adminCommand('ping')"
```

## Development

### Project Structure
```
application/
├── config/              # Configuration
├── crawler/             # Crawler components
├── infrastructure/      # Database, queue, logging
├── models/              # Data models
├── repositories/        # Data access layer
├── services/            # Business logic
├── utils/               # Utilities
└── web/                 # Flask application
    ├── auth/            # Authentication
    ├── dashboard/       # Dashboard views
    ├── scanner/         # Scanner views
    ├── search/          # Search views
    └── templates/       # HTML templates
```

### Adding New Features

1. Define requirements in `.kiro/specs/<feature>/requirements.md`
2. Create design in `.kiro/specs/<feature>/design.md`
3. Break down tasks in `.kiro/specs/<feature>/tasks.md`
4. Implement following the task list

### Testing

```bash
# Run tests
docker exec onion-web-app-dev python -m pytest

# Check syntax
python -m py_compile application/**/*.py
```

## Security

### Development
- No passwords required
- All ports exposed
- Debug mode enabled

### Production
- Passwords required (set in `.env`)
- Minimal port exposure (only nginx)
- Network isolation
- Non-root containers
- Structured logging

## Backup & Restore

```bash
# Backup
make backup

# Restore
make restore BACKUP=backups/mongodb-20240101-120000
```

## Performance

### Elasticsearch
```bash
# Reindex documents
make reindex

# Check cluster health
curl http://localhost:9200/_cluster/health
```

### Resource Usage
```bash
make stats
```

## License

This software is made available under the GPL v.3 license. If you run a modified program on a server and let other users communicate with it, your server must also allow them to download the source code.

## Contributing

Looking for open-source developers to work together on PoopakV2. Interested? Contact: yolato@protonmail.com

## Support

1. Check logs: `make dev-logs`
2. Check health: `make health`
3. Verify setup: `./validate-docker-setup.sh`
4. Review documentation in `.kiro/specs/`

---

**Ready to start?** Run `make dev-up` and visit http://localhost
