"""Persistence models for storing planner runs and review logs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from .plan import Plan


class ReviewAction(str, Enum):
    """Canonical human-review actions for planner outputs."""

    ACCEPT_PLAN = "ACCEPT_PLAN"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    ABORT = "ABORT"


class ReviewLogEntry(BaseModel):
    """Single reviewer decision captured during planner iteration."""

    attempt: int = Field(..., ge=1, description="1-indexed review attempt counter")
    action: ReviewAction = Field(..., description="Reviewer directive for the planner")
    feedback: str = Field(
        default="",
        description="Optional guidance explaining the decision or requested changes",
    )

    @validator("feedback")
    def _trim_feedback(cls, value: str) -> str:
        return value.strip()


class ResearcherCallLog(BaseModel):
    """Telemetry for a single Researcher execution."""

    step_id: str = Field(..., description="Step identifier associated with the query")
    query: str = Field(..., description="Concrete Tavily query text")
    note_count: int = Field(..., ge=0, description="Number of research notes captured")
    duration_seconds: Optional[float] = Field(
        default=None, ge=0.0, description="Wall-clock duration for the research call"
    )
    result_count: Optional[int] = Field(
        default=None, ge=0, description="Total Tavily results returned for the query"
    )


class ResearcherMetrics(BaseModel):
    """Aggregated Researcher telemetry for a run."""

    total_calls: int = Field(..., ge=0, description="Total number of Researcher invocations")
    total_notes: int = Field(..., ge=0, description="Total notes captured across all steps")
    total_duration_seconds: Optional[float] = Field(
        default=None, ge=0.0, description="Aggregated researcher runtime in seconds"
    )
    total_results: Optional[int] = Field(
        default=None, ge=0, description="Total Tavily results retrieved across calls"
    )
    calls: List[ResearcherCallLog] = Field(
        default_factory=list, description="Per-step researcher execution logs"
    )


class RunTelemetry(BaseModel):
    """Structured telemetry payload persisted alongside plan runs."""

    researcher: Optional[ResearcherMetrics] = Field(
        default=None, description="Researcher execution statistics"
    )


class PlanRunRecord(BaseModel):
    """Schema for persisted planner runs and their review history."""

    timestamp: datetime = Field(..., description="UTC time the record was persisted")
    question: str = Field(..., description="Original research question")
    locale: str = Field(..., description="Locale used for prompts and summaries")
    context: str = Field(
        default="",
        description="Supplementary context supplied to the planner",
    )
    plan: Plan = Field(..., description="Final planner-approved plan structure")
    review_log: List[ReviewLogEntry] = Field(
        default_factory=list,
        description="Chronological reviewer actions captured during the run",
    )
    telemetry: Optional[RunTelemetry] = Field(
        default=None,
        description="Structured runtime telemetry for downstream analysis",
    )

    @validator("question", "locale", "context")
    def _strip_text(cls, value: str) -> str:
        return value.strip()
