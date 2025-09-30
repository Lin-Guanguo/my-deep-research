"""Persistence models for storing planner runs and review logs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

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

    @validator("question", "locale", "context")
    def _strip_text(cls, value: str) -> str:
        return value.strip()

