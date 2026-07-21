"""Application configuration and validation.

Settings are read once at the process boundary. Keeping configuration separate from environment
lookups makes application code deterministic and straightforward to test.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_ENV_PREFIX = "AI_CHANGE_AGENT_"
_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated configuration used by the application.

    Attributes:
        workspace_root: Absolute path that future filesystem tools must remain within.
        log_level: Standard-library logging level name.
        max_file_bytes: Upper read-size limit for future repository tools.
    """

    workspace_root: Path
    log_level: str = "INFO"
    max_file_bytes: int = 1_048_576

    @classmethod
    def from_environment(cls) -> Settings:
        """Create settings from environment variables, rejecting unsafe values early."""
        root_value = os.environ.get(f"{_ENV_PREFIX}WORKSPACE_ROOT", os.getcwd())
        workspace_root = Path(root_value).expanduser().resolve()
        log_level = os.environ.get(f"{_ENV_PREFIX}LOG_LEVEL", "INFO").upper()
        max_file_bytes_value = os.environ.get(f"{_ENV_PREFIX}MAX_FILE_BYTES", "1048576")

        if log_level not in _VALID_LOG_LEVELS:
            options = ", ".join(sorted(_VALID_LOG_LEVELS))
            raise ValueError(f"Invalid log level {log_level!r}; expected one of: {options}.")
        try:
            max_file_bytes = int(max_file_bytes_value)
        except ValueError as error:
            raise ValueError("AI_CHANGE_AGENT_MAX_FILE_BYTES must be an integer.") from error
        if max_file_bytes <= 0:
            raise ValueError("AI_CHANGE_AGENT_MAX_FILE_BYTES must be greater than zero.")

        return cls(
            workspace_root=workspace_root,
            log_level=log_level,
            max_file_bytes=max_file_bytes,
        )
