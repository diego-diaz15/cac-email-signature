"""Application-wide logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path

from signature_builder.paths import app_data_dir

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: int = logging.INFO) -> Path:
    """Configure stdout and rotating file logging. Returns the log file path."""
    log_dir = app_data_dir()
    log_file = log_dir / "signature-builder.log"

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    root.addHandler(stream)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    logging.getLogger("signature_builder").debug("Logging to %s", log_file)
    return log_file
