"""Public domain contracts shared by the agent, tools, and workflow.

The models in this package are intentionally independent of LangGraph and filesystem code. This
keeps data exchanged between components explicit, validated, and easy to test in isolation.
"""

from ai_change_agent.models.enums import (
    ChangeStatus,
    FileOperation,
    PlanStepKind,
    SkipReason,
    TestStatus,
    ToolStatus,
    ValidationStatus,
)
from ai_change_agent.models.repository import RepositoryFile, RepositoryMap, SkippedEntry
from ai_change_agent.models.schemas import (
    ChangedFile,
    ChangeReport,
    ChangeRequest,
    ExecutionPlan,
    PlanStep,
    TestResult,
    ToolCall,
    ToolResult,
    ValidationResult,
)
from ai_change_agent.models.state import AgentState

__all__ = [
    "AgentState",
    "ChangeReport",
    "ChangeRequest",
    "ChangeStatus",
    "ChangedFile",
    "ExecutionPlan",
    "FileOperation",
    "PlanStep",
    "PlanStepKind",
    "RepositoryFile",
    "RepositoryMap",
    "SkipReason",
    "SkippedEntry",
    "TestResult",
    "TestStatus",
    "ToolCall",
    "ToolResult",
    "ToolStatus",
    "ValidationResult",
    "ValidationStatus",
]
