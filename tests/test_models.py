"""Tests for shared, cross-component domain contracts."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai_change_agent.models import (
    AgentState,
    ChangeReport,
    ChangeRequest,
    ChangeStatus,
    ExecutionPlan,
    PlanStep,
    PlanStepKind,
    ToolCall,
    ToolResult,
    ToolStatus,
)


def test_change_request_is_strict_and_serializable() -> None:
    """Request contracts reject unknown fields and produce JSON-compatible output."""
    request = ChangeRequest(instruction="  Add JWT authentication.  ")

    assert request.instruction == "Add JWT authentication."
    assert request.repository_root == "."
    assert ChangeRequest.model_validate_json(request.model_dump_json()) == request

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ChangeRequest(instruction="Add tests", unexpected=True)  # type: ignore[call-arg]

    with pytest.raises(ValidationError, match="cannot contain '..'"):
        ChangeRequest(instruction="Add tests", repository_root="../another-project")


def test_plan_requires_ordered_known_dependencies() -> None:
    """Plans may only depend on steps that precede them."""
    request_id = uuid4()
    plan = ExecutionPlan(
        request_id=request_id,
        rationale="Authentication needs an implementation and tests.",
        steps=(
            PlanStep(step_id="add-auth", kind=PlanStepKind.EDIT, description="Add authentication."),
            PlanStep(
                step_id="test-auth",
                kind=PlanStepKind.TEST,
                description="Test authentication.",
                depends_on=("add-auth",),
            ),
        ),
    )

    assert plan.steps[1].depends_on == ("add-auth",)
    with pytest.raises(ValidationError, match="earlier unknown step"):
        ExecutionPlan(
            request_id=request_id,
            rationale="Invalid ordering.",
            steps=(
                PlanStep(
                    step_id="test-auth",
                    kind=PlanStepKind.TEST,
                    description="Test first.",
                    depends_on=("add-auth",),
                ),
                PlanStep(step_id="add-auth", kind=PlanStepKind.EDIT, description="Edit later."),
            ),
        )


def test_tool_result_requires_error_code_for_unsuccessful_calls() -> None:
    """Tool failures must retain a stable error category for repair decisions."""
    call = ToolCall(tool_name="read_file")
    result = ToolResult(call_id=call.call_id, status=ToolStatus.SUCCESS, summary="Read file.")

    assert result.error_code is None
    with pytest.raises(ValidationError, match="require an error code"):
        ToolResult(call_id=call.call_id, status=ToolStatus.DENIED, summary="Outside workspace.")


def test_agent_state_rejects_cross_request_data() -> None:
    """A workflow snapshot cannot combine artifacts from different requests."""
    request = ChangeRequest(instruction="Add tests")
    unrelated_plan = ExecutionPlan(
        request_id=uuid4(),
        rationale="Different request.",
        steps=(PlanStep(step_id="one", kind=PlanStepKind.ANALYZE, description="Analyze."),),
    )

    with pytest.raises(ValidationError, match="must belong to the active change request"):
        AgentState(request=request, plan=unrelated_plan)


def test_successful_agent_state_requires_a_report_and_successful_tools() -> None:
    """Terminal state rules prevent incomplete work from being presented as success."""
    request = ChangeRequest(instruction="Add tests")
    with pytest.raises(ValidationError, match="requires a final change report"):
        AgentState(request=request, status=ChangeStatus.SUCCEEDED)

    state = AgentState(
        request=request,
        status=ChangeStatus.SUCCEEDED,
        report=ChangeReport(request_id=request.request_id, summary="Completed."),
    )

    assert state.status is ChangeStatus.SUCCEEDED
