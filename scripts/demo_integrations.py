"""Quick check script for OpenRouter and Tavily integrations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src` package is importable when
# running the script directly (python scripts/demo_integrations.py).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.configuration import load_config
from src.tools.llm import LLMError, call_llm
from src.tools.search import SearchError, search_web

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILENAME = "demo_integrations_output.json"


def main() -> None:
    config = load_config()
    api_cfg = config.api

    if not api_cfg.openrouter_key:
        raise SystemExit(
            "Missing OpenRouter key. Copy secret.example to secret and fill OPENROUTER_KEY."
        )
    if not api_cfg.tavily_key:
        raise SystemExit(
            "Missing Tavily key. Copy secret.example to secret and fill TAVILY_API_KEY."
        )

    prompt = "用一句话总结 LangGraph 的核心特点。"

    print("Calling OpenRouter...")
    try:
        llm_response = call_llm(
            prompt,
            model=config.models.planner,
            openrouter_key=api_cfg.openrouter_key,
            temperature=config.models.temperature,
            timeout=30.0,
        )
    except LLMError as exc:
        raise SystemExit(f"OpenRouter call failed: {exc}")

    print("OpenRouter response:\n", llm_response)

    print("\nCalling Tavily...")
    try:
        search_results = search_web(
            "LangGraph planner researcher loop",
            tavily_key=api_cfg.tavily_key,
            max_results=min(3, config.search.max_queries),
            timeout=config.search.timeout_seconds,
        )
    except SearchError as exc:
        raise SystemExit(f"Tavily search failed: {exc}")

    print("Tavily top results:")
    for idx, result in enumerate(search_results, start=1):
        print(f"  {idx}. {result['title']} -> {result['url']}")
        if result.get("snippet"):
            print("     ", result["snippet"])  # brief context

    output_path = OUTPUT_DIR / OUTPUT_FILENAME
    output_payload = {
        "prompt": prompt,
        "llm_response": llm_response,
        "search_results": search_results,
    }
    output_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved raw output to {output_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
