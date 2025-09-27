"""Graph construction helpers for the Deep Research workflow."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from langgraph.graph import END, START, StateGraph

from src.agents.planner import PlannerAgent

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


def build_graph(configuration: AppConfig, *, planner_agent: PlannerAgent | None = None) -> Any:
    """Construct the LangGraph state machine for coordinator→planner→human_review→reporter."""

    agent = planner_agent or PlannerAgent(configuration)
    graph = StateGraph(GraphState)

    def _coordinator(state: GraphState | Dict[str, Any]) -> Dict[str, Any]:
        current = _ensure_state(state)
        if not current.locale:
            current.locale = configuration.runtime.locale
        current.metadata.setdefault("context", current.metadata.get("context", ""))
        current.metadata.setdefault("review_log", [])
        return current.model_dump()

    def _planner(state: GraphState | Dict[str, Any]) -> Dict[str, Any]:
        current = _ensure_state(state)
        context = current.metadata.get("context")
        plan = agent.generate_plan(
            current.topic,
            locale=current.locale or configuration.runtime.locale,
            context=context,
        )
        current.plan = plan
        current.pending_human_review = configuration.runtime.human_review
        current.metadata.setdefault("planner_model", configuration.models.planner)
        return current.model_dump()

    def _human_review(state: GraphState | Dict[str, Any]) -> Dict[str, Any]:
        current = _ensure_state(state)
        if current.pending_human_review:
            current.metadata.setdefault("awaiting_review", True)
        return current.model_dump()

    def _reporter(state: GraphState | Dict[str, Any]) -> Dict[str, Any]:
        current = _ensure_state(state)
        # Stage 1: reporter simply echoes plan/metadata for CLI consumption.
        current.metadata.setdefault("reporter_placeholder", True)
        return current.model_dump()

    graph.add_node("coordinator", _coordinator)
    graph.add_node("planner", _planner)
    graph.add_node("human_review", _human_review)
    graph.add_node("reporter", _reporter)

    graph.add_edge(START, "coordinator")
    graph.add_edge("coordinator", "planner")
    graph.add_edge("planner", "human_review")
    graph.add_edge("human_review", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()


def _ensure_state(state: GraphState | Dict[str, Any]) -> GraphState:
    if isinstance(state, GraphState):
        return state
    return GraphState(**state)
