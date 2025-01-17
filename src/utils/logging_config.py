"""
Enhanced logging configuration module with better shutdown handling and log filtering.

This module provides a centralized logging configuration with proper shutdown handling
and filtering of duplicate logs.
"""

import logging
import logging.config
from typing import Optional
from functools import lru_cache
from contextlib import contextmanager


class DuplicateFilter(logging.Filter):
    """
    Filter that eliminates duplicate log messages within a specified time window.
    """
    def __init__(self, timeout=1.0):
        super().__init__()
        self.timeout = timeout
        self.last_log = {}

    def filter(self, record):
        # Create a key from the log message and level
        key = (record.getMessage(), record.levelno)
        current_time = record.created
        # Check if we've seen this message recently
        if key in self.last_log:
            if current_time - self.last_log[key] < self.timeout:
                return False
        self.last_log[key] = current_time
        return True


class LoggerManager:
    """
    Singleton class to manage application-wide logging configuration with shutdown handling.
    """
    _instance: Optional['LoggerManager'] = None
    _logger: Optional[logging.Logger] = None
    _is_shutting_down: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_logger(cls, name: str = None) -> logging.Logger:
        """
        Get or create the configured logger instance.

        Args:
            name (str, optional): Logger name. Defaults to root logger if None.

        Returns:
            logging.Logger: Configured logger instance
        """
        if cls._logger is None:
            cls._logger = cls._configure_logging()
        return logging.getLogger(name) if name else cls._logger

    @staticmethod
    @lru_cache(maxsize=1)
    def _configure_logging() -> logging.Logger:
        """
        Configure and return the logger for the application.
        Uses lru_cache to ensure configuration only happens once.

        Returns:
            logging.Logger: Configured logger instance
        """
        try:
            # Create the duplicate filter
            duplicate_filter = DuplicateFilter(timeout=1.0)

            logging_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "detailed": {
                        "format": (
                            "%(asctime)s - %(name)s - %(levelname)s - "
                            "%(process)d:%(thread)d - %(message)s"
                        )
                    },
                    "simple": {
                        "format": "%(levelname)s: %(message)s"
                    }
                },
                "filters": {
                    "duplicate_filter": {
                        "()": lambda: duplicate_filter
                    }
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "detailed",
                        "level": "INFO",
                        "filters": ["duplicate_filter"]
                    },
                    "file": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "filename": "app.log",
                        "maxBytes": 10 * 1024 * 1024,  # 10 MB
                        "backupCount": 5,
                        "formatter": "detailed",
                        "level": "INFO",
                        "filters": ["duplicate_filter"]
                    }
                },
                "loggers": {
                    "": {  # Root logger
                        "handlers": ["console", "file"],
                        "level": "INFO",
                        "propagate": True
                    },
                    "uvicorn": {
                        "handlers": ["console", "file"],
                        "level": "INFO",
                        "propagate": False
                    },
                    "fastapi": {
                        "handlers": ["console", "file"],
                        "level": "INFO",
                        "propagate": False
                    },
                    "services.service_data": {
                        "handlers": ["console", "file"],
                        "level": "INFO",
                        "propagate": False
                    }
                }
            }

            # Apply the logging configuration
            logging.config.dictConfig(logging_config)
            logger = logging.getLogger(__name__)
            logger.info("Logging system initialized successfully")
            return logger

        except (ValueError, OSError) as exc:
            # Fallback to basic console logging
            logging.basicConfig(
                level=logging.INFO,
                format=(
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(process)d:%(thread)d - %(message)s"
                )
            )
            logger = logging.getLogger(__name__)
            logger.warning(
                "Failed to configure advanced logging, falling back to basic logs: %s",
                str(exc)
            )
            return logger

    @classmethod
    @contextmanager
    def shutdown_context(cls):
        """
        Context manager for handling application shutdown logging.
        Ensures logs are available throughout the shutdown process.
        """
        cls._is_shutting_down = True
        logger = cls.get_logger()
        try:
            yield logger
        finally:
            cls._is_shutting_down = False
            # Ensure all handlers are properly closed
            for handler in logger.handlers:
                handler.close()


# Convenience functions
def get_logger(name: str = None) -> logging.Logger:
    """Get the configured logger instance."""
    return LoggerManager.get_logger(name)


def get_shutdown_context():
    """Get the shutdown context manager."""
    return LoggerManager.shutdown_context()
