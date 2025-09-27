"""Shared LangGraph state definitions for the Deep Research workflow."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.models.plan import Plan, ResearchNote


class GraphState(BaseModel):
    """Normalized state object exchanged between LangGraph nodes."""

    topic: str = Field(..., description="User request or research question")
    locale: str = Field("zh-CN", description="Locale preference for prompts and outputs")
    plan: Optional[Plan] = Field(default=None, description="Planner-approved research plan")
    current_step_id: Optional[str] = Field(
        default=None, description="Identifier of the step currently being executed"
    )
    scratchpad: List[ResearchNote] = Field(
        default_factory=list,
        description="Cross-step insights aggregated for reporter synthesis",
    )
    pending_human_review: bool = Field(
        default=False, description="Flag indicating the graph is awaiting human feedback"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional contextual payload shared across nodes"
    )

    def add_scratchpad_note(self, note: ResearchNote | dict) -> None:
        """Append a note to the cross-step scratchpad."""

        if isinstance(note, dict):
            research_note = ResearchNote(**note)
        else:
            research_note = note
        self.scratchpad.append(research_note)

    def mark_for_review(self, reason: str | None = None) -> None:
        """Toggle human-review flag and capture optional reason in metadata."""

        self.pending_human_review = True
        if reason:
            self.metadata.setdefault("review_reasons", []).append(reason)
