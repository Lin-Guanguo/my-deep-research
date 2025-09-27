"""Entry point for the Deep Research CLI demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from src.agents.planner import PlannerAgent
from src.config.configuration import load_config
from src.graph.builder import build_graph, initial_state
from src.models.plan import Plan

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
    attempts = {"count": 0}
    review_log: List[Dict[str, str]] = []
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
            action, feedback = "ACCEPT_PLAN", ""
        else:
            action, feedback = _prompt_review_action()

        review_log.append(
            {
                "attempt": str(attempts["count"]),
                "action": action,
                "feedback": feedback,
            }
        )

        if action == "REQUEST_CHANGES" and feedback:
            current_context["value"] = _merge_context(current_context["value"], feedback)
            state.metadata["context"] = current_context["value"]

        return action, feedback

    graph = build_graph(
        config,
        planner_agent=planner_agent,
        review_handler=review_handler,  # type: ignore[arg-type]
    )

    initial = initial_state(
        question,
        locale=locale,
        metadata={"context": current_context["value"]},
    )
    result = graph.invoke(initial.model_dump())
    final_state = Plan.model_validate(result["plan"]) if result.get("plan") else None
    last_action = result.get("metadata", {}).get("last_review_action", "ACCEPT_PLAN")

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


def _prompt_review_action() -> Tuple[str, str]:
    prompt = "Select action [ACCEPT_PLAN | REQUEST_CHANGES | ABORT]: "
    action = input(prompt).strip().upper()
    feedback = ""
    if action == "REQUEST_CHANGES":
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
    review_log: List[Dict[str, str]],
) -> None:
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "question": question,
        "locale": locale,
        "context": context,
        "plan": plan.model_dump(),
        "review_log": review_log,
    }
    path = PLANS_DIR / "plans.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
