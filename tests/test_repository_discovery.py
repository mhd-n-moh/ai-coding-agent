"""Tests for safe, deterministic repository discovery."""

from pathlib import Path

import pytest

from ai_change_agent.models import SkipReason
from ai_change_agent.repository import DiscoveryOptions, RepositoryScanner


def _write_file(root: Path, relative_path: str, content: str | bytes) -> Path:
    """Create a fixture file, including parents, without coupling tests to scan internals."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def test_scanner_builds_sorted_map_and_skips_unsafe_entries(tmp_path: Path) -> None:
    """Discovery includes readable text only and explains every standard exclusion."""
    _write_file(tmp_path, "src/zebra.py", "print('zebra')\n")
    _write_file(tmp_path, "src/alpha.py", "a\n")
    _write_file(tmp_path, ".env", "SECRET=value\n")
    _write_file(tmp_path, ".venv/ignored.py", "pass\n")
    _write_file(tmp_path, "assets/image.bin", b"header\x00payload")
    _write_file(tmp_path, "logs/large.log", "x" * 20)

    project_map = RepositoryScanner(DiscoveryOptions(max_file_bytes=10)).scan(tmp_path)

    assert project_map.directories == (".", "assets", "logs", "src")
    assert [file.path for file in project_map.files] == ["src/alpha.py"]
    assert [(entry.path, entry.reason) for entry in project_map.skipped_entries] == [
        (".env", SkipReason.HIDDEN),
        (".venv", SkipReason.HIDDEN),
        ("assets/image.bin", SkipReason.TOO_LARGE),
        ("logs/large.log", SkipReason.TOO_LARGE),
        ("src/zebra.py", SkipReason.TOO_LARGE),
    ]


def test_scanner_handles_binary_and_configured_ignores(tmp_path: Path) -> None:
    """Configured ignores and binary files are excluded independently of file size."""
    _write_file(tmp_path, "main.py", "print('ok')\n")
    _write_file(tmp_path, "vendor/generated.py", "generated\n")
    _write_file(tmp_path, "image.dat", b"valid-size\x00binary")

    scanner = RepositoryScanner(
        DiscoveryOptions(
            ignored_directory_names=frozenset({"vendor"}),
            ignored_relative_paths=frozenset({"main.py"}),
        )
    )
    project_map = scanner.scan(tmp_path)

    assert project_map.files == ()
    assert [(entry.path, entry.reason) for entry in project_map.skipped_entries] == [
        ("image.dat", SkipReason.BINARY),
        ("main.py", SkipReason.CONFIGURED_IGNORE),
        ("vendor", SkipReason.CONFIGURED_IGNORE),
    ]


def test_scanner_rejects_invalid_roots_and_options(tmp_path: Path) -> None:
    """The scanner fails before traversal when the root or safety configuration is invalid."""
    with pytest.raises(FileNotFoundError, match="does not exist"):
        RepositoryScanner().scan(tmp_path / "missing")
    with pytest.raises(NotADirectoryError, match="not a directory"):
        RepositoryScanner().scan(_write_file(tmp_path, "file.txt", "text"))
    with pytest.raises(ValueError, match="cannot contain '..'"):
        DiscoveryOptions(ignored_relative_paths=frozenset({"../outside"}))


def test_scanner_does_not_follow_symbolic_links(tmp_path: Path) -> None:
    """A symlink is reported but never dereferenced, keeping reads within the repository."""
    target = _write_file(tmp_path, "target.py", "print('target')\n")
    link = tmp_path / "linked.py"
    try:
        link.symlink_to(target)
    except OSError as error:
        pytest.skip(f"Symbolic links are unavailable: {error}")

    project_map = RepositoryScanner().scan(tmp_path)

    assert [file.path for file in project_map.files] == ["target.py"]
    assert [(entry.path, entry.reason) for entry in project_map.skipped_entries] == [
        ("linked.py", SkipReason.SYMBOLIC_LINK),
    ]
