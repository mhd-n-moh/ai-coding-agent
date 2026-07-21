# AI Change Agent

AI Change Agent is a learning-oriented, tool-driven coding agent. Given a local Python
repository and a change request, it will eventually plan, make, validate, test, and explain
the smallest practical set of changes.

## Current status

Milestone 2.1 is complete: the agent can safely discover a local repository and produce a
deterministic metadata-only project map. Project understanding, agent workflow, and repository
mutation tools are intentionally introduced in later milestones.

## Development

This project uses Python 3.12 and [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

## Configuration

The application reads these optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `AI_CHANGE_AGENT_LOG_LEVEL` | `INFO` | Logging threshold (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `AI_CHANGE_AGENT_WORKSPACE_ROOT` | current working directory | Root directory available to future repository tools |
| `AI_CHANGE_AGENT_MAX_FILE_BYTES` | `1048576` | Maximum file size future tools may read |

## Project layout

```text
src/ai_change_agent/  Application package
src/ai_change_agent/models/  Strict request, plan, tool, report, and workflow-state contracts
src/ai_change_agent/repository/  Read-only discovery with safety limits and ignore rules
tests/                Automated tests
```

## Quality baseline

All changes should include relevant tests, pass linting and static type checking, and preserve
the documented workspace-safety boundary.
