"""Explicit state passed between future LangGraph workflow nodes."""

from __future__ import annotations

from pydantic import Field, model_validator

from ai_change_agent.models.enums import ChangeStatus, ToolStatus
from ai_change_agent.models.repository import RepositoryMap
from ai_change_agent.models.schemas import (
    ChangedFile,
    ChangeReport,
    ChangeRequest,
    ContractModel,
    ExecutionPlan,
    TestResult,
    ToolCall,
    ToolResult,
    ValidationResult,
)


class AgentState(ContractModel):
    """Complete, immutable snapshot of one change-agent run.

    Nodes create updated snapshots rather than mutating shared memory. This supports dependable
    graph checkpointing, replay, observability, and test isolation.
    """

    request: ChangeRequest
    status: ChangeStatus = ChangeStatus.PENDING
    repository_map: RepositoryMap | None = None
    plan: ExecutionPlan | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()
    modified_files: tuple[ChangedFile, ...] = ()
    validations: tuple[ValidationResult, ...] = ()
    test_result: TestResult | None = None
    report: ChangeReport | None = None
    errors: tuple[str, ...] = ()
    revision: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_consistency(self) -> AgentState:
        """Enforce cross-field invariants before a graph node receives state."""
        if self.plan is not None and self.plan.request_id != self.request.request_id:
            raise ValueError("Execution plan must belong to the active change request.")
        if self.report is not None and self.report.request_id != self.request.request_id:
            raise ValueError("Change report must belong to the active change request.")
        call_ids = {call.call_id for call in self.tool_calls}
        if any(result.call_id not in call_ids for result in self.tool_results):
            raise ValueError("Every tool result must match a recorded tool call.")
        if self.status is ChangeStatus.SUCCEEDED:
            if self.report is None:
                raise ValueError("A successful agent run requires a final change report.")
            if any(result.status is not ToolStatus.SUCCESS for result in self.tool_results):
                raise ValueError("A successful agent run cannot contain failed tool results.")
        return self
