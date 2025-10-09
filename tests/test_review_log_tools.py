"""Regression tests for review log validation and replay tooling."""

from __future__ import annotations

from pathlib import Path

from scripts.replay_review_log import replay_log
from scripts.validate_review_log import run_validation


SAMPLE_LOG = Path("samples/plan_run_record.jsonl")


def test_run_validation_on_sample(tmp_path) -> None:
    result = run_validation(SAMPLE_LOG, output_dir=tmp_path)
    summary = result["results"]

    assert summary["missing_file"] is False
    assert summary["total"] == 1
    assert summary["valid"] == 1
    assert summary["invalid"] == []
    assert result["output_path"].exists()


def test_replay_log_on_sample(tmp_path) -> None:
    result = replay_log(SAMPLE_LOG, output_dir=tmp_path, index=0)
    summary = result["summary"]
    record = summary["selected_record"]

    assert summary["missing_file"] is False
    assert summary["records_available"] == 1
    assert summary["selected_index"] == 0
    assert record is not None
    assert record["question"].startswith("LangGraph")
    metrics = record.get("researcher_metrics", {})
    assert metrics.get("total_calls") == 2
    assert metrics.get("total_results") == 5
    assert metrics.get("degradation_modes") == ["budget"]
    assert result["output_path"].exists()
