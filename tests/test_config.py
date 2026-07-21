"""Tests for application configuration."""

from pathlib import Path

import pytest

from ai_change_agent.config import Settings


def test_settings_use_safe_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Defaults should resolve the current working directory and use conservative limits."""
    monkeypatch.chdir(tmp_path)
    for name in ("WORKSPACE_ROOT", "LOG_LEVEL", "MAX_FILE_BYTES"):
        monkeypatch.delenv(f"AI_CHANGE_AGENT_{name}", raising=False)

    settings = Settings.from_environment()

    assert settings.workspace_root == tmp_path.resolve()
    assert settings.log_level == "INFO"
    assert settings.max_file_bytes == 1_048_576


def test_settings_read_environment_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Explicit values should be normalised and preserved."""
    monkeypatch.setenv("AI_CHANGE_AGENT_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("AI_CHANGE_AGENT_LOG_LEVEL", "debug")
    monkeypatch.setenv("AI_CHANGE_AGENT_MAX_FILE_BYTES", "42")

    settings = Settings.from_environment()

    assert settings.workspace_root == tmp_path.resolve()
    assert settings.log_level == "DEBUG"
    assert settings.max_file_bytes == 42


@pytest.mark.parametrize(
    ("variable", "value", "message"),
    [
        ("AI_CHANGE_AGENT_LOG_LEVEL", "verbose", "Invalid log level"),
        ("AI_CHANGE_AGENT_MAX_FILE_BYTES", "nope", "must be an integer"),
        ("AI_CHANGE_AGENT_MAX_FILE_BYTES", "0", "greater than zero"),
    ],
)
def test_settings_reject_invalid_values(
    monkeypatch: pytest.MonkeyPatch, variable: str, value: str, message: str
) -> None:
    """Invalid configuration must fail at startup with an actionable error."""
    monkeypatch.setenv(variable, value)

    with pytest.raises(ValueError, match=message):
        Settings.from_environment()
