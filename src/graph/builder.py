"""Graph construction helpers for the Deep Research workflow."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from src.config.configuration import AppConfig

from .state import GraphState

# Ordered tuple describing the canonical node pipeline of the research agent.
STANDARD_NODES: Tuple[str, ...] = (
    "coordinator",
    "planner",
    "human_review",
    "researcher",
    "reporter",
)


def initial_state(topic: str, *, locale: str, metadata: Dict[str, Any] | None = None) -> GraphState:
    """Bootstrap the LangGraph runtime state prior to invoking the coordinator node."""

    return GraphState(topic=topic, locale=locale, metadata=metadata or {})


def build_graph(configuration: AppConfig) -> Any:
    """Construct the LangGraph state machine for coordinator→planner→researcher→reporter.

    Expected behaviours (to be implemented in Stage 1):
    - Populate a `GraphState` via `initial_state` and inject runtime configuration.
    - Route planner output to `GraphState.plan`, then interrupt for human approval when
      `pending_human_review` is toggled.
    - Iterate researcher execution per `PlanStep.step_type`, appending structured notes
      with `GraphState.add_scratchpad_note`.
    - Hand the accumulated notes and plan to the reporter node for Markdown synthesis.
    """

    raise NotImplementedError("Graph construction not implemented yet")
