"""Entry point for the Deep Research CLI demo."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pydantic import ValidationError

from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearcherAgent
from src.config.configuration import load_config
from src.graph.builder import build_graph, initial_state
from src.models.plan import Plan
from src.models.persistence import (
    PlanRunRecord,
    ResearcherCallLog,
    ResearcherMetrics,
    ReviewAction,
    ReviewLogEntry,
    RunTelemetry,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLANS_DIR = PROJECT_ROOT / "output" / "plans"


def main(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.show_review_help:
        help_path = PROJECT_ROOT / "docs" / "human-review-cli.md"
        sys.stdout.write(help_path.read_text(encoding="utf-8"))
        sys.stdout.write("\n")
        return

    question = args.question or input("Enter research question: ").strip()
    if not question:
        raise SystemExit("Question is required")

    config = load_config()
    locale = args.locale or config.runtime.locale
    context = args.context or ""

    planner_agent = PlannerAgent(config)
    researcher_agent = ResearcherAgent(config)
    attempts = {"count": 0}
    review_log: List[ReviewLogEntry] = []
    current_context = {"value": context}

    def review_handler(state) -> tuple[str, str]:
        attempts["count"] += 1
        if attempts["count"] > args.max_iterations:
            print("[warn] Exceeded max review attempts, aborting.")
            return "ABORT", "Exceeded max iterations"

        plan_obj = state.plan
        if plan_obj is None:
            return "ABORT", "Planner returned no plan"

        _display_plan(plan_obj)
        if args.auto_accept:
            action_enum, feedback = ReviewAction.ACCEPT_PLAN, ""
        else:
            action_enum, feedback = _prompt_review_action()

        review_log.append(
            ReviewLogEntry(
                attempt=attempts["count"],
                action=action_enum,
                feedback=feedback,
            )
        )

        if action_enum is ReviewAction.REQUEST_CHANGES and feedback:
            current_context["value"] = _merge_context(current_context["value"], feedback)
            state.metadata["context"] = current_context["value"]

        return action_enum.value, feedback

    graph = build_graph(
        config,
        planner_agent=planner_agent,
        review_handler=review_handler,  # type: ignore[arg-type]
        researcher_agent=researcher_agent,
    )

    initial = initial_state(
        question,
        locale=locale,
        metadata={"context": current_context["value"]},
    )
    result = graph.invoke(initial.model_dump())
    final_state = Plan.model_validate(result["plan"]) if result.get("plan") else None
    metadata = result.get("metadata", {})
    last_action = metadata.get("last_review_action", "ACCEPT_PLAN")

    if last_action == "ABORT" or final_state is None:
        print("[info] Workflow aborted by reviewer.")
        return

    _emit_summary(final_state, locale)
    if not args.no_store:
        _store_plan(
            question=question,
            locale=locale,
            context=current_context["value"],
            plan=final_state,
            review_log=review_log,
            telemetry=_extract_telemetry(metadata),
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deep Research planner CLI")
    parser.add_argument("--question", "-q", help="Research question to plan")
    parser.add_argument("--locale", help="Locale for prompts (default from config)")
    parser.add_argument("--context", help="Additional context hints for planner")
    parser.add_argument("--auto-accept", action="store_true", help="Skip manual review")
    parser.add_argument("--no-store", action="store_true", help="Do not persist plan output")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum planner retries when requesting changes",
    )
    parser.add_argument(
        "--show-review-help",
        action="store_true",
        help="Print human review workflow instructions and exit.",
    )
    return parser


def _display_plan(plan: Plan) -> None:
    print("\n=== Proposed Plan ===")
    print(f"Topic: {plan.topic}")
    print(f"Goal: {plan.goal}")
    print("Assumptions:")
    for item in plan.assumptions or []:
        print(f"  - {item}")
    print("Risks:")
    for item in plan.risks or []:
        print(f"  - {item}")
    print("Steps:")
    for step in plan.steps:
        print(f"  {step.id} [{step.step_type}] {step.title}")
        print(f"     Expected outcome: {step.expected_outcome}")


def _prompt_review_action() -> Tuple[ReviewAction, str]:
    prompt = "Select action [ACCEPT_PLAN | REQUEST_CHANGES | ABORT]: "
    lookup = {choice.value: choice for choice in ReviewAction}
    action_text = input(prompt).strip().upper()
    while action_text not in lookup:
        print("[warn] Invalid action. Please choose ACCEPT_PLAN, REQUEST_CHANGES, or ABORT.")
        action_text = input(prompt).strip().upper()

    action = lookup[action_text]
    feedback = ""
    if action is ReviewAction.REQUEST_CHANGES:
        print("Enter feedback (finish with empty line):")
        lines = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line.strip())
        feedback = "\n".join(lines)
    return action, feedback


def _emit_summary(plan: Plan, locale: str) -> None:
    print("\n[success] Plan approved.")
    print(f"Locale: {locale}")
    print(f"Steps ({len(plan.steps)}):")
    for step in plan.steps:
        print(f"  - {step.id}: {step.title}")


def _merge_context(existing: str, feedback: str) -> str:
    if not existing:
        return feedback
    return existing + "\nReviewer feedback: " + feedback


def _store_plan(
    *,
    question: str,
    locale: str,
    context: str,
    plan: Plan,
    review_log: List[ReviewLogEntry],
    telemetry: RunTelemetry | None = None,
) -> None:
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    record = PlanRunRecord(
        timestamp=datetime.utcnow(),
        question=question,
        locale=locale,
        context=context,
        plan=plan,
        review_log=review_log,
        telemetry=telemetry,
    )
    path = PLANS_DIR / "plans.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        payload = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)
        handle.write(payload + "\n")


def _extract_telemetry(metadata: Dict[str, Any]) -> RunTelemetry | None:
    metrics_payload = metadata.get("researcher_metrics")
    if not metrics_payload:
        return None

    try:
        researcher_metrics = ResearcherMetrics.model_validate(metrics_payload)
    except ValidationError:
        researcher_metrics = _coerce_metrics(metrics_payload)
    return RunTelemetry(researcher=researcher_metrics)


def _coerce_metrics(payload: Dict[str, Any]) -> ResearcherMetrics:
    calls_payload = payload.get("calls", []) or []
    coerced_calls: List[ResearcherCallLog] = []
    for call in calls_payload:
        if not isinstance(call, dict):
            continue
        step_id = str(call.get("step_id", "")).strip()
        if not step_id:
            continue
        query = str(call.get("query", "")).strip()
        note_count = int(call.get("note_count", 0) or 0)
        duration = call.get("duration_seconds")
        if duration is not None:
            try:
                duration = float(duration)
            except (TypeError, ValueError):
                duration = None
        result_count = call.get("result_count")
        if result_count is not None:
            try:
                result_count = int(result_count)
            except (TypeError, ValueError):
                result_count = None
        coerced_calls.append(
            ResearcherCallLog(
                step_id=step_id,
                query=query,
                note_count=note_count,
                duration_seconds=duration,
                result_count=result_count,
            )
        )

    total_calls = int(payload.get("total_calls", len(coerced_calls)) or 0)
    total_notes = int(payload.get("total_notes", 0) or 0)
    total_duration = payload.get("total_duration_seconds")
    if total_duration is not None:
        try:
            total_duration = float(total_duration)
        except (TypeError, ValueError):
            total_duration = None

    total_results = payload.get("total_results")
    if total_results is not None:
        try:
            total_results = int(total_results)
        except (TypeError, ValueError):
            total_results = None

    return ResearcherMetrics(
        total_calls=total_calls,
        total_notes=total_notes,
        total_duration_seconds=total_duration,
        total_results=total_results,
        calls=coerced_calls,
    )
if __name__ == "__main__":
    main()
