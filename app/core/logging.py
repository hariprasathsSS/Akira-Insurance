"""Structured JSON logging setup for AKIRA INSURANCE."""
from __future__ import annotations

import logging
import sys

try:
    from pythonjsonlogger import jsonlogger  # type: ignore
except ImportError:
    jsonlogger = None

from app.core.config import get_settings


def configure_logging(level: str | None = None) -> None:
    settings = get_settings()
    level_str = level or settings.LOG_LEVEL
    log_level = getattr(logging, level_str.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if jsonlogger is not None:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# Alias setup_logging to configure_logging for consistency
setup_logging = configure_logging


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
