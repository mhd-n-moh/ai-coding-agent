"""Safe, deterministic discovery of files available within a local repository."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ai_change_agent.models import (
    RepositoryFile,
    RepositoryMap,
    SkippedEntry,
    SkipReason,
)

DEFAULT_IGNORED_DIRECTORY_NAMES = frozenset(
    {
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
    }
)


@dataclass(frozen=True, slots=True)
class DiscoveryOptions:
    """Limits and ignore rules governing a repository scan.

    Attributes:
        max_file_bytes: Largest file that may be represented in the project map.
        binary_sample_bytes: Prefix size inspected to distinguish text from binary files.
        ignored_directory_names: Extra directory names to omit at any depth.
        ignored_relative_paths: Exact repository-relative paths to omit.
    """

    max_file_bytes: int = 1_048_576
    binary_sample_bytes: int = 8_192
    ignored_directory_names: frozenset[str] = frozenset()
    ignored_relative_paths: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Reject unsafe limits and normalize configured paths before scanning starts."""
        if self.max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be greater than zero.")
        if self.binary_sample_bytes <= 0:
            raise ValueError("binary_sample_bytes must be greater than zero.")
        if any(
            Path(path).is_absolute() or ".." in Path(path).parts
            for path in self.ignored_relative_paths
        ):
            raise ValueError(
                "ignored_relative_paths must be repository-relative and cannot contain '..'."
            )


class RepositoryScanner:
    """Build a metadata-only map without reading outside the supplied repository root."""

    def __init__(self, options: DiscoveryOptions | None = None) -> None:
        """Create a scanner with explicit, reusable discovery options."""
        self._options = options or DiscoveryOptions()

    def scan(self, repository_root: Path) -> RepositoryMap:
        """Discover eligible files and explain every intentionally skipped entry.

        Directory traversal is deterministic and never follows symbolic links. Files are sampled
        only after their size passes the configured limit, preventing accidental large reads.
        """
        root = repository_root.expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"Repository root does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Repository root is not a directory: {root}")

        directories: list[str] = ["."]
        files: list[RepositoryFile] = []
        skipped_entries: list[SkippedEntry] = []
        configured_names = DEFAULT_IGNORED_DIRECTORY_NAMES | self._options.ignored_directory_names

        for current_directory, directory_names, file_names in os.walk(
            root, topdown=True, followlinks=False
        ):
            current_path = Path(current_directory)
            eligible_directories: list[str] = []
            for directory_name in sorted(directory_names):
                path = current_path / directory_name
                relative_path = path.relative_to(root).as_posix()
                reason = self._skip_directory_reason(path, relative_path, configured_names)
                if reason is None:
                    eligible_directories.append(directory_name)
                    directories.append(relative_path)
                else:
                    skipped_entries.append(SkippedEntry(path=relative_path, reason=reason))
            directory_names[:] = eligible_directories

            for file_name in sorted(file_names):
                path = current_path / file_name
                relative_path = path.relative_to(root).as_posix()
                reason = self._skip_file_reason(path, relative_path)
                if reason is not None:
                    skipped_entries.append(SkippedEntry(path=relative_path, reason=reason))
                    continue

                size_bytes = path.stat().st_size
                files.append(
                    RepositoryFile(
                        path=relative_path,
                        size_bytes=size_bytes,
                        extension=path.suffix.lower(),
                    )
                )

        return RepositoryMap(
            root=str(root),
            directories=tuple(sorted(directories)),
            files=tuple(sorted(files, key=lambda file: file.path)),
            skipped_entries=tuple(sorted(skipped_entries, key=lambda entry: entry.path)),
        )

    def _skip_directory_reason(
        self, path: Path, relative_path: str, configured_names: frozenset[str]
    ) -> SkipReason | None:
        """Classify a directory that must not be descended into, if any."""
        if path.is_symlink():
            return SkipReason.SYMBOLIC_LINK
        if path.name.startswith("."):
            return SkipReason.HIDDEN
        if path.name in configured_names or relative_path in self._options.ignored_relative_paths:
            return SkipReason.CONFIGURED_IGNORE
        return None

    def _skip_file_reason(self, path: Path, relative_path: str) -> SkipReason | None:
        """Classify a file that must not appear in the project map, if any."""
        if path.is_symlink():
            return SkipReason.SYMBOLIC_LINK
        if path.name.startswith("."):
            return SkipReason.HIDDEN
        if relative_path in self._options.ignored_relative_paths:
            return SkipReason.CONFIGURED_IGNORE
        if path.stat().st_size > self._options.max_file_bytes:
            return SkipReason.TOO_LARGE
        if self._is_binary(path):
            return SkipReason.BINARY
        return None

    def _is_binary(self, path: Path) -> bool:
        """Use a bounded sample to identify binary data without loading full files."""
        with path.open("rb") as file_handle:
            sample = file_handle.read(self._options.binary_sample_bytes)
        if b"\x00" in sample:
            return True
        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            return True
        return False
