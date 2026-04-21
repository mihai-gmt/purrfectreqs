"""
Centralised logging configuration for PurrfectReqs.

Configure logging once here at application startup.
All other modules use: logger = logging.getLogger(__name__)

Never use print() statements. Never configure logging in individual modules.
"""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """
    Set up structured logging for the application.

    Uses human-readable formatting in development.
    Uses JSON formatting in production for machine parsing by Loki.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    if settings.is_development:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(messages)s"
        datfmt = "%Y-%m-%d %H:%M:%S"
    else:
        fmt = '{"time": "%(asctime)s", "level": "(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        datfmt = "%Y-%m-%dT%H:%M:%S"

    logging.basicConfig(level=log_level, format=fmt, datefmt=datfmt, stream=sys.stdout)

    # Suppress noisy third-party loggers

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
