"""Plan and Step data models used by the Planner and downstream nodes."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class StepType(str, Enum):
    """Supported step categories in the research workflow."""

    RESEARCH = "RESEARCH"
    PROCESS = "PROCESS"
    SYNTHESIZE = "SYNTHESIZE"
    REVIEW = "REVIEW"


class StepStatus(str, Enum):
    """Execution status for each plan step."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class PlanStep(BaseModel):
    """Single actionable step produced by the Planner."""

    id: str = Field(..., description="Stable identifier, e.g., step-1")
    title: str = Field(..., description="Short summary of the step objective")
    step_type: StepType = Field(..., description="Indicates how the Researcher should handle the step")
    expected_outcome: str = Field(..., description="What success looks like for this step")
    status: StepStatus = Field(default=StepStatus.PENDING, description="Runtime execution status")
    notes: List[str] = Field(default_factory=list, description="Accumulated research notes or highlights")
    references: List[str] = Field(default_factory=list, description="Captured citation URLs or IDs")
    execution_result: Optional[str] = Field(
        default=None, description="Summary of what happened during execution"
    )


class PlanMetadata(BaseModel):
    """Optional metadata attached to a plan for observability and context."""

    locale: Optional[str] = Field(default=None, description="Locale hint for downstream prompts")
    reviewer: Optional[str] = Field(default=None, description="Name of the human reviewer if applicable")
    budget_tokens: Optional[int] = Field(default=None, description="Token budget allocated for the run")
    budget_cost_usd: Optional[float] = Field(default=None, description="Cost budget in USD")


class Plan(BaseModel):
    """Structured plan containing ordered steps and high-level objectives."""

    topic: str = Field(..., description="Research topic or question")
    goal: str = Field(..., description="Overall objective articulated by the Planner")
    steps: List[PlanStep] = Field(..., description="Ordered list of actionable steps")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made while planning")
    risks: List[str] = Field(default_factory=list, description="Known risks or uncertainties")
    metadata: PlanMetadata = Field(default_factory=PlanMetadata, description="Auxiliary plan metadata")

    def get_step(self, step_id: str) -> PlanStep:
        """Retrieve a step by id, raising `KeyError` when missing."""

        for step in self.steps:
            if step.id == step_id:
                return step
        raise KeyError(f"Step {step_id} not found")

    def mark_step_status(self, step_id: str, status: StepStatus) -> None:
        """Update the status of a step in-place."""

        step = self.get_step(step_id)
        step.status = status

    def append_note(self, step_id: str, note: str, reference: Optional[str] = None) -> None:
        """Attach a note (and optional reference) to a step."""

        step = self.get_step(step_id)
        step.notes.append(note)
        if reference:
            step.references.append(reference)
