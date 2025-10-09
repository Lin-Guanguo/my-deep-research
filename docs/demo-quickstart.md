# Quick Demo Guide

> Short checklist for running the Deep Research CLI demo with planner + human review.

## 1. Prerequisites
- Python 3.11+ and the [`uv`](https://docs.astral.sh/uv/) package manager installed locally.
- OpenRouter and Tavily API keys (write them to the repo root `secret` file, see below).

## 2. Install dependencies
```bash
uv sync
```
This creates a `.venv/` folder with the packages declared in `pyproject.toml`. Subsequent `uv run` calls reuse it automatically.

## 3. Configure credentials
1. Copy `secret.example` to `secret` (already gitignored).
2. Fill in the keys:
   ```
   OPENROUTER_KEY=sk-...
   TAVILY_API_KEY=tvly-...
   ```
3. Adjust `config/settings.yaml` only if you need to change locale, review toggles, or model names.

## 4. Connectivity smoke test
Use the bundled script to verify both APIs before running the full workflow:
```bash
uv run scripts/demo_integrations.py
```
Successful runs write `output/demo_integrations_output.json` (kept out of git) and print the raw responses for quick inspection.

## 5. Run the planner + review loop
Plan-only fast path (auto-approve review):
```bash
uv run scripts/run_cli.py -q "<your research question>" --auto-accept
```
Interactive review (recommended for demos):
```bash
uv run scripts/run_cli.py -q "<your research question>"
```
- The CLI prints the structured plan, prompts for `ACCEPT_PLAN`, `REQUEST_CHANGES`, or `ABORT`, and appends review history to `output/plans/plans.jsonl`.
- Use `--show-review-help` to display the review instructions if you need a quick refresher.

## 6. After the run
- Approved runs render a Markdown summary (including telemetry and citations) in the terminal and store the plan + review log at `output/plans/plans.jsonl`.
- Keep staged outputs out of version control unless you add an `.example.json` reference. Real runs stay ignored via `.gitignore`.

This flow works for any research topic—the LangGraph planner emits structured steps, the reviewer node captures human feedback, and the researcher/report stages can be toggled or extended later.
