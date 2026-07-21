"""Consistent, dependency-free application logging."""

from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    """Configure the process logger with a stable, machine-readable-friendly format.

    This function is deliberately idempotent so tests and command entry points can call it
    safely. Existing handlers are left in place to avoid interfering with host applications.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if root_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root_logger.addHandler(handler)
