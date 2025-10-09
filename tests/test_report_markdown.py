"""Tests for Markdown report rendering utilities."""

from __future__ import annotations

from src.models.plan import Plan
from src.report.markdown import render_report


def _build_sample_plan() -> Plan:
    return Plan(
        topic="LangGraph Deep Research",
        goal="Summarize best practices",
        steps=[
            {
                "id": "step-1",
                "title": "Collect references",
                "step_type": "RESEARCH",
                "expected_outcome": "List official docs",
                "notes": [
                    {
                        "source": "https://example.com/doc",
                        "claim": "LangGraph enables declarative graphs",
                        "evidence": "LangGraph docs section 1",
                        "confidence": 0.8,
                    }
                ],
            },
            {
                "id": "step-2",
                "title": "Synthesize findings",
                "step_type": "SYNTHESIZE",
                "expected_outcome": "Produce guidance",
                "notes": [],
            },
        ],
        assumptions=[],
        risks=[],
    )


def test_render_report_includes_sections() -> None:
    plan = _build_sample_plan()
    summary = {
        "total_notes": 1,
        "average_confidence": 0.8,
        "low_confidence": [],
        "researcher_metrics": {
            "total_calls": 1,
            "total_notes": 1,
            "total_duration_seconds": 0.6,
            "total_results": 3,
            "calls": [
                {
                    "step_id": "step-1",
                    "query": "LangGraph | Collect references",
                    "note_count": 1,
                    "duration_seconds": 0.6,
                    "result_count": 3,
                }
            ],
        },
    }

    markdown = render_report(plan, summary=summary, locale="en-US")

    assert "# Research Report: LangGraph Deep Research (en-US)" in markdown
    assert "## Researcher Telemetry" in markdown
    assert "Total calls: 1" in markdown
    assert "## Findings by Step" in markdown
    assert "### Step 1: Collect references" in markdown
    assert "LangGraph enables declarative graphs" in markdown
    assert "No notes captured" in markdown
    assert "## Citations" in markdown
    assert "https://example.com/doc" in markdown


def test_render_report_low_confidence_section() -> None:
    plan = _build_sample_plan()
    plan.steps[0].notes[0].confidence = 0.5

    summary = {
        "total_notes": 1,
        "average_confidence": 0.5,
        "low_confidence": [
            {"step_id": "step-1", "claim": "LangGraph enables declarative graphs", "confidence": 0.5}
        ],
        "researcher_metrics": None,
    }

    markdown = render_report(plan, summary=summary)
    assert "## Low Confidence Notes" in markdown
    assert "confidence: 0.50" in markdown
