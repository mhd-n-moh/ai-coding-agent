"""Validated, serializable data contracts for the AI Change Agent.

These schemas are the boundary between the language model, graph nodes, and tools. They reject
unknown fields and invalid input so downstream code does not need to guess at data shape.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from ai_change_agent.models.enums import (
    FileOperation,
    PlanStepKind,
    TestStatus,
    ToolStatus,
    ValidationStatus,
)

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
RepositoryPath = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


def _validate_repository_path(value: str) -> str:
    """Return a safe repository-relative path or reject a workspace escape attempt."""
    path_parts = value.replace("\\", "/").split("/")
    if value.startswith(("/", "\\")) or ".." in path_parts:
        raise ValueError("Path must be relative to the repository and cannot contain '..'.")
    return value


class ContractModel(BaseModel):
    """Base model that makes all cross-component contracts strict and immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ChangeRequest(ContractModel):
    """A user's requested change, scoped to one local workspace."""

    request_id: UUID = Field(default_factory=uuid4)
    instruction: NonEmptyText
    repository_root: RepositoryPath = "."
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("repository_root")
    @classmethod
    def validate_repository_root(cls, value: str) -> str:
        """Keep the request scope within the caller-provided workspace."""
        return _validate_repository_path(value)


class PlanStep(ContractModel):
    """One atomic, observable action within an execution plan."""

    step_id: NonEmptyText
    kind: PlanStepKind
    description: NonEmptyText
    expected_files: tuple[RepositoryPath, ...] = ()
    depends_on: tuple[NonEmptyText, ...] = ()

    @field_validator("expected_files")
    @classmethod
    def validate_expected_files(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Ensure planned file targets are workspace-relative before tools see them."""
        return tuple(_validate_repository_path(value) for value in values)

    @model_validator(mode="after")
    def validate_dependencies(self) -> PlanStep:
        """Reject duplicate or self-referential dependencies before execution begins."""
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError("Plan-step dependencies must be unique.")
        if self.step_id in self.depends_on:
            raise ValueError("A plan step cannot depend on itself.")
        return self


class ExecutionPlan(ContractModel):
    """An ordered, validated plan for satisfying a change request."""

    request_id: UUID
    steps: tuple[PlanStep, ...] = Field(min_length=1)
    rationale: NonEmptyText

    @model_validator(mode="after")
    def validate_step_references(self) -> ExecutionPlan:
        """Ensure every dependency points to an earlier, unique step."""
        step_ids = tuple(step.step_id for step in self.steps)
        if len(set(step_ids)) != len(step_ids):
            raise ValueError("Execution-plan step IDs must be unique.")
        known_steps: set[str] = set()
        for step in self.steps:
            unknown = set(step.depends_on) - known_steps
            if unknown:
                names = ", ".join(sorted(unknown))
                raise ValueError(
                    f"Step {step.step_id!r} depends on an earlier unknown step: {names}."
                )
            known_steps.add(step.step_id)
        return self


class ToolCall(ContractModel):
    """An auditable request to invoke one approved repository tool."""

    call_id: UUID = Field(default_factory=uuid4)
    tool_name: NonEmptyText
    arguments: dict[str, object] = Field(default_factory=dict)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolResult(ContractModel):
    """The normalized output of a tool invocation, including safe failure information."""

    call_id: UUID
    status: ToolStatus
    summary: NonEmptyText
    data: dict[str, object] = Field(default_factory=dict)
    error_code: str | None = None

    @model_validator(mode="after")
    def validate_error_details(self) -> ToolResult:
        """Require a stable error code for failed or denied tool calls."""
        if self.status is ToolStatus.SUCCESS and self.error_code is not None:
            raise ValueError("Successful tool results cannot include an error code.")
        if self.status is not ToolStatus.SUCCESS and self.error_code is None:
            raise ValueError("Failed or denied tool results require an error code.")
        return self


class ChangedFile(ContractModel):
    """A single file affected by a successful execution step."""

    path: RepositoryPath
    operation: FileOperation
    reason: NonEmptyText

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        """Ensure reported changes cannot name a path outside the repository."""
        return _validate_repository_path(value)


class ValidationResult(ContractModel):
    """Outcome of syntax, formatting, or static-analysis validation."""

    name: NonEmptyText
    status: ValidationStatus
    summary: NonEmptyText
    output: str = ""


class TestResult(ContractModel):
    """Normalized outcome from the target project's test command."""

    command: NonEmptyText
    status: TestStatus
    summary: NonEmptyText
    output: str = ""
    exit_code: int | None = None


class ChangeReport(ContractModel):
    """Human-readable handoff describing an agent execution."""

    request_id: UUID
    summary: NonEmptyText
    modified_files: tuple[ChangedFile, ...] = ()
    validations: tuple[ValidationResult, ...] = ()
    test_result: TestResult | None = None
    remaining_issues: tuple[NonEmptyText, ...] = ()
