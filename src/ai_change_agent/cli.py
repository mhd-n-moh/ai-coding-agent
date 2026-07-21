"""Command-line entry point for the AI Change Agent."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from ai_change_agent.config import Settings
from ai_change_agent.logging import configure_logging

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser without performing application work."""
    parser = argparse.ArgumentParser(
        prog="ai-change-agent",
        description="Safely plan and apply focused changes to a local Python repository.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
        help="Show the installed version and exit.",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the command-line application and return a shell-compatible status code."""
    build_parser().parse_args(arguments)
    settings = Settings.from_environment()
    configure_logging(settings.log_level)
    logger.info("AI Change Agent is initialized for workspace: %s", settings.workspace_root)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through package entry point.
    raise SystemExit(main())
