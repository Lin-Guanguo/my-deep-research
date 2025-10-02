"""Graph construction helpers for the Deep Research workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Tuple

from langgraph.graph import END, START, StateGraph

from src.agents.planner import PlannerAgent
from src.agents.researcher import (
    ResearchContext,
    ResearcherAgent,
    ResearcherError,
    ResearcherResult,
)
from src.config.configuration import AppConfig

from .state import GraphState
from src.models.plan import Plan, PlanStep, ResearchNote, StepStatus
from src.report.markdown import render_report

# Ordered tuple describing the canonical node pipeline of the research agent.
STANDARD_NODES: Tuple[str, ...] = (
    "coordinator",
    "planner",
    "human_review",
    "researcher",
    "reporter",
)

ReviewHandler = Callable[[GraphState], tuple[str, str]]


def initial_state(topic: str, *, locale: str, metadata: Dict[str, Any] | None = None) -> GraphState:
    """Bootstrap the LangGraph runtime state prior to invoking the coordinator node."""

    return GraphState(topic=topic, locale=locale, metadata=metadata or {})


def build_graph(
    configuration: AppConfig,
    *,
    planner_agent: PlannerAgent | None = None,
    review_handler: ReviewHandler | None = None,
    researcher_agent: ResearcherAgent | None = None,
) -> Any:
    """Construct the LangGraph state machine for coordinator→planner→human_review→reporter."""

    agent = planner_agent or PlannerAgent(configuration)
    researcher = researcher_agent or ResearcherAgent(configuration)
    handler = review_handler or _default_review_handler
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
        current.metadata.pop("last_review_action", None)
        return current.model_dump()

    def _human_review(state: GraphState | Dict[str, Any]) -> Dict[str, Any]:
        current = _ensure_state(state)

        if not configuration.runtime.human_review:
            current.metadata["last_review_action"] = "ACCEPT_PLAN"
            current.pending_human_review = False
            return current.model_dump()

        if not current.pending_human_review:
            current.metadata.setdefault("last_review_action", "ACCEPT_PLAN")
            return current.model_dump()

        action, feedback = handler(current)

        current.metadata.setdefault("review_log", []).append(
            {"action": action, "feedback": feedback}
        )
        current.metadata["last_review_action"] = action
        current.pending_human_review = False
        current.metadata.pop("awaiting_review", None)

        if action == "REQUEST_CHANGES" and feedback:
            context = current.metadata.get("context", "")
            current.metadata["context"] = _merge_context(context, feedback)
        elif action == "ACCEPT_PLAN":
            current.metadata.setdefault("approval_timestamp", _utc_timestamp())

        return current.model_dump()

    def _researcher(state: GraphState | Dict[str, Any]) -> Dict[str, Any]:
        current = _ensure_state(state)

        if current.plan is None:
            current.metadata.setdefault("researcher_status", "missing_plan")
            return current.model_dump()

        step = _select_next_step(current.plan, current.current_step_id)
        if step is None:
            current.metadata.setdefault("researcher_status", "no_pending_steps")
            return current.model_dump()

        current.current_step_id = step.id
        current.plan.mark_step_status(step.id, StepStatus.IN_PROGRESS)

        plan_metadata = current.plan.metadata if current.plan else None
        budget_tokens = getattr(plan_metadata, "budget_tokens", None) if plan_metadata else None
        budget_cost = getattr(plan_metadata, "budget_cost_usd", None) if plan_metadata else None
        context = ResearchContext(
            topic=current.topic,
            locale=current.locale or configuration.runtime.locale,
            step=step,
            max_results=configuration.search.max_queries,
            timeout_seconds=configuration.search.timeout_seconds,
            budget_tokens_remaining=budget_tokens,
            budget_cost_limit=budget_cost,
            degradation_hint=current.metadata.get("researcher_degradation"),
        )

        try:
            result = researcher.run_step(context)
        except ResearcherError as exc:
            current.plan.mark_step_status(step.id, StepStatus.BLOCKED)
            current.metadata.setdefault("researcher_errors", []).append(str(exc))
            current.metadata.setdefault("researcher_status", "blocked")
            return current.model_dump()

        _apply_research_results(current, step, result)
        _update_researcher_metrics(current, step, result)
        current.plan.mark_step_status(step.id, StepStatus.COMPLETED)
        current.metadata.setdefault("researcher_status", "completed_step")
        current.metadata.setdefault("researcher_history", []).append(
            {
                "step_id": step.id,
                "query": result.query,
                "note_count": len(result.notes),
                "duration_seconds": result.duration_seconds,
            }
        )
        current.metadata["researcher_last_query"] = result.query
        current.metadata["last_researcher_step"] = step.id

        return current.model_dump()

    def _reporter(state: GraphState | Dict[str, Any]) -> Dict[str, Any]:
        current = _ensure_state(state)
        current.metadata.setdefault("reporter_placeholder", True)
        summary = _build_reporter_summary(current)
        current.metadata["reporter_summary"] = summary
        if current.plan is not None:
            current.metadata["report_markdown"] = render_report(
                current.plan,
                summary=summary,
                locale=current.locale or configuration.runtime.locale,
            )
        return current.model_dump()

    graph.add_node("coordinator", _coordinator)
    graph.add_node("planner", _planner)
    graph.add_node("human_review", _human_review)
    graph.add_node("researcher", _researcher)
    graph.add_node("reporter", _reporter)

    graph.add_edge(START, "coordinator")
    graph.add_edge("coordinator", "planner")
    graph.add_edge("planner", "human_review")
    graph.add_conditional_edges(
        "human_review",
        _review_transition,
        {
            "accept": "researcher",
            "revise": "planner",
            "abort": END,
        },
    )
    graph.add_edge("researcher", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()


def _ensure_state(state: GraphState | Dict[str, Any]) -> GraphState:
    if isinstance(state, GraphState):
        return state
    return GraphState(**state)


def _default_review_handler(state: GraphState) -> tuple[str, str]:
    return "ACCEPT_PLAN", ""


def _review_transition(state: GraphState | Dict[str, Any]) -> str:
    if isinstance(state, GraphState):
        metadata = state.metadata
    else:
        metadata = state.get("metadata", {})
    action = metadata.get("last_review_action", "ACCEPT_PLAN")
    if action == "REQUEST_CHANGES":
        return "revise"
    if action == "ABORT":
        return "abort"
    return "accept"


def _merge_context(existing: str, feedback: str) -> str:
    existing = (existing or "").strip()
    feedback = feedback.strip()
    if not existing:
        return feedback
    if not feedback:
        return existing
    return f"{existing}\nReviewer feedback: {feedback}"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _select_next_step(plan: Plan, current_step_id: str | None) -> PlanStep | None:
    if current_step_id:
        try:
            current = plan.get_step(current_step_id)
            if current.status != StepStatus.COMPLETED:
                return current
        except KeyError:
            pass

    for candidate in plan.steps:
        if candidate.status != StepStatus.COMPLETED:
            return candidate

    return None


def _apply_research_results(
    state: GraphState, step: PlanStep, result: ResearcherResult
) -> None:
    if state.plan is None:
        return

    notes = result.notes
    references = result.references

    for idx, note in enumerate(notes):
        reference = references[idx] if idx < len(references) else None
        state.plan.append_note(step.id, note, reference=reference)
        state.add_scratchpad_note(note)


def _build_reporter_summary(state: GraphState) -> Dict[str, Any]:
    plan = state.plan
    if plan is None:
        return {
            "total_notes": 0,
            "average_confidence": None,
            "low_confidence": [],
            "researcher_metrics": state.metadata.get("researcher_metrics"),
        }

    note_entries: List[tuple[str, ResearchNote]] = []
    for step in plan.steps:
        for note in step.notes:
            note_entries.append((step.id, note))

    total_notes = len(note_entries)
    confidences = [note.confidence for _, note in note_entries if note.confidence is not None]
    average_confidence = (
        sum(confidences) / len(confidences) if confidences else None
    )

    low_confidence = [
        {
            "step_id": step_id,
            "claim": note.claim,
            "confidence": note.confidence,
        }
        for step_id, note in note_entries
        if note.confidence is not None and note.confidence < 0.6
    ]

    summary = {
        "total_notes": total_notes,
        "average_confidence": average_confidence,
        "low_confidence": low_confidence,
        "researcher_metrics": state.metadata.get("researcher_metrics"),
    }
    return summary


def _update_researcher_metrics(
    state: GraphState, step: PlanStep, result: ResearcherResult
) -> None:
    metrics = state.metadata.get("researcher_metrics") or {
        "total_calls": 0,
        "total_notes": 0,
        "total_results": None,
        "total_duration_seconds": None,
        "calls": [],
    }

    metrics["total_calls"] = metrics.get("total_calls", 0) + 1
    metrics["total_notes"] = metrics.get("total_notes", 0) + len(result.notes)

    duration = result.duration_seconds
    if duration is not None:
        previous = metrics.get("total_duration_seconds") or 0.0
        metrics["total_duration_seconds"] = float(previous) + duration

    result_count = result.total_results
    if result_count:
        previous_results = metrics.get("total_results") or 0
        metrics["total_results"] = int(previous_results) + result_count

    metrics.setdefault("calls", []).append(
        {
            "step_id": step.id,
            "query": result.query,
            "note_count": len(result.notes),
            "duration_seconds": duration,
            "result_count": result_count,
        }
    )

    state.metadata["researcher_metrics"] = metrics
