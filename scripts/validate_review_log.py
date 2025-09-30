"""Validate persisted planner review logs against the canonical schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import ValidationError

from src.models.persistence import PlanRunRecord

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_PATH = PROJECT_ROOT / "output" / "plans" / "plans.jsonl"
OUTPUT_FILENAME = "validate_review_log_output.json"


def run_validation(log_path: Path, *, output_dir: Path) -> Dict[str, Any]:
    """Validate each JSONL entry and emit a summary report."""

    results: Dict[str, Any] = {
        "log_path": str(log_path),
        "total": 0,
        "valid": 0,
        "invalid": [],
        "missing_file": False,
    }

    if not log_path.exists():
        results["missing_file"] = True
    else:
        with log_path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                payload = raw_line.strip()
                if not payload:
                    continue
                results["total"] += 1
                try:
                    PlanRunRecord.model_validate_json(payload)
                except (ValidationError, ValueError) as exc:  # ValueError for JSON decode
                    results["invalid"].append(
                        {
                            "line": line_number,
                            "error": _truncate_error_message(str(exc)),
                        }
                    )
                else:
                    results["valid"] += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_FILENAME
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"results": results, "output_path": output_path}


def _truncate_error_message(message: str, *, limit: int = 240) -> str:
    stripped = message.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3] + "..."


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log-path",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Path to planner review log JSONL file (default: output/plans/plans.jsonl)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output",
        help="Directory to store the validation summary JSON.",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = run_validation(args.log_path, output_dir=args.output_dir)
    summary = result["results"]
    print(
        f"Validated {summary['valid']} / {summary['total']} records "
        f"in {summary['log_path']}."
    )
    if summary["invalid"]:
        print(f"Found {len(summary['invalid'])} invalid entries; see {result['output_path']} for details.")
    elif summary["missing_file"]:
        print(f"Log file not found at {summary['log_path']}. Summary saved to {result['output_path']}.")
    else:
        print(f"Summary saved to {result['output_path']}")


if __name__ == "__main__":
    main()

