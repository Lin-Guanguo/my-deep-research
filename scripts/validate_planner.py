"""Run planner prompts against OpenRouter and validate JSON output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.configuration import load_config
from src.models.plan import Plan
from src.tools.llm import LLMError, call_llm

OUTPUT_FILENAME = "validate_planner_output.json"
SYSTEM_PROMPT = """You are the Planner agent inside a systematic deep-research workflow. Produce a plan JSON payload that conforms exactly to the schema below.

Output requirements:
- Return raw JSON only (no markdown, commentary, or code fences).
- Use double quotes for all keys/strings.
- Preserve the property order shown in the schema.

Schema:
{
  "topic": string,
  "goal": string,
  "assumptions": [string, ...],
  "risks": [string, ...],
  "steps": [
    {
      "id": "step-1" | "step-2" | ...,
      "title": string,
      "step_type": "RESEARCH" | "PROCESS" | "SYNTHESIZE" | "REVIEW",
      "expected_outcome": string
    }
  ],
  "metadata": {
    "locale": string,
    "budget_tokens": integer,
    "budget_cost_usd": float,
    "reviewer": string | null
  }
}

Constraints:
- Provide 3 to 6 steps; IDs must increment sequentially starting at "step-1".
- `topic` and `goal` must restate the user's request in the specified locale.
- `metadata.locale` must equal the user's locale input.
- Choose reasonable budgets (tokens,cost) for the task difficulty.
- Use null for reviewer when no reviewer is known.
- Do not add any extra fields."""

USER_PROMPT_TEMPLATE = """User Question: {topic}\nLocale: {locale}\nContext Hints: {context}"""


def extract_json_block(text: str) -> str:
    """Return the JSON segment from model output, handling fenced code blocks."""

    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop the first fence line and optional language tag
        if lines:
            lines = lines[1:]
        # Remove trailing fence if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def load_questions(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Planner questions file must contain a list")
    return payload


def run_validation(questions_path: Path, *, output_dir: Path) -> Dict[str, Any]:
    config = load_config()
    api_cfg = config.api

    if not api_cfg.openrouter_key:
        raise SystemExit(
            "Missing OpenRouter key. Copy secret.example to secret and fill OPENROUTER_KEY."
        )

    questions = load_questions(questions_path)

    results: Dict[str, Any] = {
        "total": len(questions),
        "success": 0,
        "failures": [],
        "plans": [],
    }

    for entry in questions:
        topic = entry.get("topic", "").strip()
        locale = entry.get("locale", config.runtime.locale)
        context = entry.get("context", "").strip() or "(none)"
        prompt = USER_PROMPT_TEMPLATE.format(topic=topic, locale=locale, context=context)

        try:
            llm_response = call_llm(
                prompt,
                model=config.models.planner,
                openrouter_key=api_cfg.openrouter_key,
                temperature=config.models.temperature,
                timeout=45.0,
                extra={"topic": topic, "locale": locale},
                system_prompt=SYSTEM_PROMPT,
            )
        except LLMError as exc:
            results["failures"].append(
                {
                    "topic": topic,
                    "locale": locale,
                    "reason": f"LLM request failed: {exc}",
                }
            )
            continue

        try:
            json_payload = extract_json_block(llm_response)
            plan = Plan.model_validate_json(json_payload)
        except Exception as exc:  # noqa: BLE001 - capture parsing/validation errors
            results["failures"].append(
                {
                    "topic": topic,
                    "locale": locale,
                    "reason": f"Validation error: {exc}",
                    "raw_response": llm_response,
                }
            )
            continue

        results["success"] += 1
        results["plans"].append(
            {
                "topic": topic,
                "locale": locale,
                "plan": plan.model_dump(),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = (output_dir / OUTPUT_FILENAME).resolve()
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"output_path": output_path, "summary": {k: results[k] for k in ("total", "success")}}


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        type=Path,
        default=Path("samples/planner_questions.json"),
        help="Path to JSON file containing planner questions.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output",
        help="Directory to store validation output.",
    )
    args = parser.parse_args(argv)

    result = run_validation(args.questions, output_dir=args.output_dir)
    summary = result["summary"]
    output_path = result["output_path"]
    try:
        relative_path = output_path.relative_to(PROJECT_ROOT)
    except ValueError:
        relative_path = output_path

    print(
        f"Validation complete. {summary['success']} / {summary['total']} plans parsed successfully.\n"
        f"Saved details to {relative_path}"
    )


if __name__ == "__main__":
    main()
