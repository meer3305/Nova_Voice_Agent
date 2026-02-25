"""Centralized logger setup for Nova."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from nova.config import get_settings


_LOGGER_READY = False


def configure_logger() -> None:
    """Configure console and rotating file logging once."""

    global _LOGGER_READY
    if _LOGGER_READY:
        return

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(logs_dir / "nova.log", maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    root.handlers.clear()
    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    _LOGGER_READY = True


def get_logger(name: str) -> logging.Logger:
    """Get logger with shared configuration."""

    configure_logger()
    return logging.getLogger(name)
