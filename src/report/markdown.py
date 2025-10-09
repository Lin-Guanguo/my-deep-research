"""Markdown report assembly utilities."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from src.models.plan import Plan, PlanStep, ResearchNote


def render_report(
    plan: Plan,
    *,
    summary: Mapping[str, Any] | None = None,
    locale: str | None = None,
) -> str:
    """Render a lightweight Markdown report from the plan and telemetry summary."""

    lines: list[str] = []
    title_locale = f" ({locale})" if locale else ""
    lines.append(f"# Research Report: {plan.topic}{title_locale}")
    lines.append("")
    lines.append(f"**Goal:** {plan.goal}")

    telemetry = (summary or {}).get("researcher_metrics") if summary else None
    low_confidence = (summary or {}).get("low_confidence", []) if summary else []

    lines.extend(_render_telemetry_section(telemetry))
    lines.extend(_render_plan_section(plan.steps))

    if low_confidence:
        lines.append("## Low Confidence Notes")
        for item in low_confidence:
            confidence = item.get("confidence")
            formatted = (
                f"- Step `{item.get('step_id')}`: {item.get('claim')} (confidence: {confidence:.2f})"
                if isinstance(confidence, (int, float))
                else f"- Step `{item.get('step_id')}`: {item.get('claim')}"
            )
            lines.append(formatted)

    citations = _collect_citations(plan.steps)
    if citations:
        lines.append("")
        lines.append("## Citations")
        lines.append("| # | Source |")
        lines.append("| --- | --- |")
        for index, source in citations:
            lines.append(f"| {index} | {source} |")

    return "\n".join(lines).rstrip() + "\n"


def _render_telemetry_section(telemetry: Mapping[str, Any] | None) -> list[str]:
    lines: list[str] = []
    lines.append("")
    lines.append("## Researcher Telemetry")
    if not telemetry:
        lines.append("- No researcher telemetry available.")
        return lines

    total_calls = telemetry.get("total_calls")
    total_notes = telemetry.get("total_notes")
    total_duration = telemetry.get("total_duration_seconds")
    total_results = telemetry.get("total_results")

    if total_calls is not None:
        lines.append(f"- Total calls: {total_calls}")
    if total_notes is not None:
        lines.append(f"- Notes captured: {total_notes}")
    if total_results is not None:
        lines.append(f"- Tavily results reviewed: {total_results}")
    if isinstance(total_duration, (int, float)):
        lines.append(f"- Total duration: {total_duration:.2f}s")

    call_entries = telemetry.get("calls") or []
    if call_entries:
        lines.append("")
        lines.append("### Per-call Details")
        for call in call_entries:
            step_id = call.get("step_id", "unknown-step")
            query = call.get("query", "")
            note_count = call.get("note_count")
            duration = call.get("duration_seconds")
            result_count = call.get("result_count")
            detail = f"- `{step_id}` → {note_count} notes"
            if isinstance(result_count, int):
                detail += f", {result_count} results"
            if isinstance(duration, (int, float)):
                detail += f", {duration:.2f}s"
            if query:
                detail += f"\n  \\_ Query: {query}"
            lines.append(detail)

    return lines


def _render_plan_section(steps: Sequence[PlanStep]) -> list[str]:
    lines: list[str] = []
    lines.append("")
    lines.append("## Findings by Step")
    if not steps:
        lines.append("No plan steps available.")
        return lines

    for index, step in enumerate(steps, start=1):
        lines.append("")
        lines.append(f"### Step {index}: {step.title}")
        lines.append(f"_Expected outcome:_ {step.expected_outcome}")
        if not step.notes:
            lines.append("- No notes captured.")
            continue
        for note in step.notes:
            lines.extend(_render_note(note))
    return lines


def _render_note(note: ResearchNote) -> list[str]:
    parts = [f"- **Claim:** {note.claim}"]
    if note.evidence:
        parts.append(f"  - Evidence: {note.evidence}")
    if note.source:
        parts.append(f"  - Source: {note.source}")
    if note.confidence is not None:
        parts.append(f"  - Confidence: {note.confidence:.2f}")
    if note.todo:
        parts.append(f"  - Follow-up: {note.todo}")
    return parts


def _collect_citations(steps: Sequence[PlanStep]) -> list[tuple[int, str]]:
    seen: dict[str, int] = {}
    ordered: list[tuple[int, str]] = []
    counter = 1
    for step in steps:
        for note in step.notes:
            source = note.source.strip() if note.source else ""
            if not source or source in seen:
                continue
            seen[source] = counter
            ordered.append((counter, source))
            counter += 1
    return ordered
