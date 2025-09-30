"""Replay planner review logs and summarize a selected run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import ValidationError

from src.models.persistence import PlanRunRecord

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_PATH = PROJECT_ROOT / "output" / "plans" / "plans.jsonl"
OUTPUT_FILENAME = "replay_review_log_output.json"


def replay_log(
    log_path: Path,
    *,
    output_dir: Path,
    index: int | None = None,
) -> Dict[str, Any]:
    """Load planner run records and emit a concise summary for inspection."""

    records: List[PlanRunRecord] = []
    summary: Dict[str, Any] = {
        "log_path": str(log_path),
        "records_available": 0,
        "selected_index": None,
        "missing_file": False,
        "validation_errors": [],
    }

    if not log_path.exists():
        summary["missing_file"] = True
    else:
        with log_path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                payload = raw_line.strip()
                if not payload:
                    continue
                try:
                    records.append(PlanRunRecord.model_validate_json(payload))
                except (ValidationError, ValueError) as exc:
                    summary["validation_errors"].append(
                        {
                            "line": line_number,
                            "error": str(exc).splitlines()[0],
                        }
                    )

    summary["records_available"] = len(records)

    selected_record: PlanRunRecord | None = None
    if records:
        idx = _normalize_index(index, len(records))
        summary["selected_index"] = idx
        selected_record = records[idx]

    detail: Dict[str, Any] | None = None
    if selected_record:
        detail = {
            "question": selected_record.question,
            "locale": selected_record.locale,
            "context": selected_record.context,
            "plan_goal": selected_record.plan.goal,
            "step_count": len(selected_record.plan.steps),
            "steps": [
                {
                    "id": step.id,
                    "title": step.title,
                    "step_type": step.step_type.value if hasattr(step.step_type, "value") else step.step_type,
                    "expected_outcome": step.expected_outcome,
                }
                for step in selected_record.plan.steps
            ],
            "review_actions": [
                {
                    "attempt": entry.attempt,
                    "action": entry.action.value,
                    "feedback": entry.feedback,
                }
                for entry in selected_record.review_log
            ],
        }
        if selected_record.telemetry and selected_record.telemetry.researcher:
            metrics = selected_record.telemetry.researcher
            detail["researcher_metrics"] = {
                "total_calls": metrics.total_calls,
                "total_notes": metrics.total_notes,
                "total_duration_seconds": metrics.total_duration_seconds,
                "calls": [
                    {
                        "step_id": call.step_id,
                        "query": call.query,
                        "note_count": call.note_count,
                        "duration_seconds": call.duration_seconds,
                    }
                    for call in metrics.calls
                ],
            }

    summary["selected_record"] = detail

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_FILENAME
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"summary": summary, "output_path": output_path}


def _normalize_index(index: int | None, size: int) -> int:
    if not size:
        raise ValueError("Cannot normalize index when size is zero")
    if index is None:
        return size - 1
    if index < 0:
        idx = size + index
    else:
        idx = index
    if idx < 0:
        idx = 0
    if idx >= size:
        idx = size - 1
    return idx


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log-path",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Path to planner review log JSONL file (default: output/plans/plans.jsonl)",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help="0-based index of the record to replay (defaults to the latest entry)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output",
        help="Directory to store the replay summary JSON.",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = replay_log(args.log_path, output_dir=args.output_dir, index=args.index)
    summary = result["summary"]
    if summary["missing_file"]:
        print(f"Log file not found at {summary['log_path']}.")
    else:
        print(
            f"Loaded {summary['records_available']} records from {summary['log_path']}.")
        if summary["selected_record"]:
            idx = summary["selected_index"]
            question = summary["selected_record"]["question"]
            print(f"Replay index {idx}: {question}")
        if summary["validation_errors"]:
            print(
                f"Encountered {len(summary['validation_errors'])} validation errors; "
                f"see {result['output_path']} for details."
            )
    print(f"Summary saved to {result['output_path']}")


if __name__ == "__main__":
    main()
