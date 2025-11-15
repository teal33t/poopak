"""
Configuration module for the web crawler application.

This module provides centralized configuration management using environment
variables with sensible defaults.
"""

import os
from typing import Dict


class Settings:
    """
    Centralized configuration settings for the application.

    All configuration values are loaded from environment variables with
    sensible defaults for development.
    """

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB_PANEL: int = int(os.getenv("REDIS_DB_PANEL", "0"))
    REDIS_DB_APP: int = int(os.getenv("REDIS_DB_APP", "1"))
    REDIS_DB_DETECTOR: int = int(os.getenv("REDIS_DB_DETECTOR", "2"))
    REDIS_DB_CRAWLER: int = int(os.getenv("REDIS_DB_CRAWLER", "3"))

    # MongoDB Configuration
    MONGODB_HOST: str = os.getenv("MONGODB_HOST", "mongodb")
    MONGODB_PORT: int = int(os.getenv("MONGODB_PORT", "27017"))
    MONGODB_USERNAME: str = os.getenv("MONGODB_USERNAME", "admin")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD", "123qwe")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "crawler")

    # Flask Application Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sacredteal33tX#")
    WTF_CSRF_ENABLED: bool = os.getenv("WTF_CSRF_ENABLED", "True").lower() == "true"
    SESSION_TYPE: str = os.getenv("SESSION_TYPE", "filesystem")

    # Captcha Configuration
    CAPTCHA_ENABLE: bool = os.getenv("CAPTCHA_ENABLE", "True").lower() == "true"
    CAPTCHA_LENGTH: int = int(os.getenv("CAPTCHA_LENGTH", "4"))

    # File Upload Directories
    SEED_UPLOAD_DIR: str = os.getenv("SEED_UPLOAD_DIR", "/application/files/seeds/")
    SCREENSHOT_UPLOAD_DIR: str = os.getenv("SCREENSHOT_UPLOAD_DIR", "/application/files/screenshots/")
    EXIF_PATH: str = os.getenv("EXIF_PATH", "/application/files/exif/")

    # External Services
    SPACY_SERVER_URL: str = os.getenv("SPACY_SERVER_URL", "http://spacy:8000/dep/")
    TOR_POOL_URL: str = os.getenv("TOR_POOL_URL", "torpool")
    TOR_POOL_PORT: int = int(os.getenv("TOR_POOL_PORT", "5566"))

    # Pagination
    ITEMS_PER_PAGE: int = int(os.getenv("ITEMS_PER_PAGE", "20"))

    # Localhost mode (for development)
    LOCALHOST: bool = os.getenv("LOCALHOST", "False").lower() == "true"

    # Error Tracking Configuration
    ERROR_TRACKING_ENABLED: bool = os.getenv("ERROR_TRACKING_ENABLED", "False").lower() == "true"
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

    # Elasticsearch Configuration
    ELASTICSEARCH_ENABLED: bool = os.getenv("ELASTICSEARCH_ENABLED", "true").lower() == "true"
    ELASTICSEARCH_HOSTS: str = os.getenv("ELASTICSEARCH_HOSTS", "http://elasticsearch:9200")
    ELASTICSEARCH_INDEX: str = os.getenv("ELASTICSEARCH_INDEX", "onion_documents")
    ELASTICSEARCH_TIMEOUT: int = int(os.getenv("ELASTICSEARCH_TIMEOUT", "30"))

    @property
    def mongodb_uri(self) -> str:
        """
        Construct MongoDB connection URI.

        Returns:
            MongoDB connection string
        """
        return (
            f"mongodb://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}"
            f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DATABASE}"
        )

    @property
    def redis_uri(self) -> str:
        """
        Construct Redis connection URI.

        Returns:
            Redis connection string
        """
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def upload_directories(self) -> Dict[str, str]:
        """
        Get all upload directory paths.

        Returns:
            Dictionary of upload directory paths
        """
        return {"seeds": self.SEED_UPLOAD_DIR, "screenshots": self.SCREENSHOT_UPLOAD_DIR, "exif": self.EXIF_PATH}

    def get_exif_save_path(self, filename: str, ext: str) -> str:
        """
        Construct EXIF file save path.

        Args:
            filename: Base filename
            ext: File extension

        Returns:
            Full path for EXIF file
        """
        return f"{self.EXIF_PATH}{filename}{ext}"


# Create a default settings instance
settings = Settings()
