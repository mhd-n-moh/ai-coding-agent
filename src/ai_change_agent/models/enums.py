"""Finite status values used throughout the agent's execution lifecycle."""

from enum import StrEnum


class ChangeStatus(StrEnum):
    """Lifecycle state of a requested repository change."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


class FileOperation(StrEnum):
    """Supported types of repository file mutation."""

    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class PlanStepKind(StrEnum):
    """High-level intent of an execution-plan step."""

    ANALYZE = "analyze"
    EDIT = "edit"
    VALIDATE = "validate"
    TEST = "test"


class ToolStatus(StrEnum):
    """Outcome of one tool invocation."""

    SUCCESS = "success"
    ERROR = "error"
    DENIED = "denied"


class ValidationStatus(StrEnum):
    """Outcome of a non-test validation operation."""

    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"


class TestStatus(StrEnum):
    """Normalized outcome of test-suite execution."""

    PASS = "pass"
    FAIL = "fail"
    NO_TESTS_FOUND = "no_tests_found"
    EXECUTION_ERROR = "execution_error"
