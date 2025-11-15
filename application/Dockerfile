# Multi-stage build for optimized image size
FROM python:3.8-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set the working directory
WORKDIR /application

# Development stage
FROM base as development

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir flask

# Copy wait script
COPY docker_wait /wait
RUN chmod +x /wait

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /application/files/exif && \
    chown -R appuser:appuser /application

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["/wait"]

# Production stage
FROM base as production

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir flask gunicorn

# Copy wait script
COPY docker_wait /wait
RUN chmod +x /wait

# Copy application code (excluding dev files)
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /application/files/exif && \
    chown -R appuser:appuser /application

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["/wait"]
