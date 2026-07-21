"""Tests for the command-line boundary."""

from pathlib import Path

from ai_change_agent.cli import main


def test_cli_initializes_successfully(monkeypatch, tmp_path: Path) -> None:
    """The bootstrap command should be safe to run before agent features exist."""
    monkeypatch.setenv("AI_CHANGE_AGENT_WORKSPACE_ROOT", str(tmp_path))

    assert main([]) == 0
