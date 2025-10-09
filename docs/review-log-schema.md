# Planner Review Log Schema

> 定义 `output/plans/plans.jsonl` 中单条运行记录的字段结构，用于审阅回放与自动校验。

## Record Structure

每行保存一个 JSON 对象，对应一次 Planner 运行。字段如下：

- `timestamp` (`string`): ISO8601 UTC 时间戳，记录写入时间。
- `question` (`string`): 原始调研问题。
- `locale` (`string`): 本次执行使用的语言/区域设定。
- `context` (`string`): 传递给 Planner 的额外提示或审阅反馈合并文本。
- `plan` (`Plan`): 通过 `src/models/plan.py` 定义的结构化计划，包含 `steps`、`assumptions`、`risks` 等字段。
- `review_log` (`ReviewLogEntry[]`): 按时间顺序记录人在环决策。
- `telemetry` (`RunTelemetry`): 可选的运行遥测信息，目前包含 Researcher 调用次数、耗时、笔记数量、搜索返回数量等统计。

### ReviewLogEntry

```json
{
  "attempt": 1,                  // 第几次审阅（从 1 开始）
  "action": "REQUEST_CHANGES",  // 取值：ACCEPT_PLAN | REQUEST_CHANGES | ABORT
  "feedback": "Clarify LangGraph concurrency story"
}
```

## Validation & Replay Tooling

- `scripts/validate_review_log.py`：逐行校验 JSONL 是否符合 `PlanRunRecord` schema，并输出统计到 `output/validate_review_log_output.json`。
- `scripts/replay_review_log.py`：读取 JSONL 并生成指定索引的计划与审阅摘要，输出到 `output/replay_review_log_output.json`。
- `tests/test_review_log_tools.py`：在 pytest 测试中调用上述脚本，确保示例日志始终符合 schema 并可回放。

提供了对应的 `.example.json` 参考输出，便于比对格式和字段。

## 示例记录

```json
{
  "timestamp": "2024-08-12T10:15:42.310000Z",
  "question": "LangGraph 深度调研代理的最佳实践有哪些？",
  "locale": "zh-CN",
  "context": "Reviewer feedback: 强调成本评估",
  "plan": {
    "topic": "LangGraph 深度调研代理最佳实践",
    "goal": "总结构建 Planner→Researcher→Reporter 闭环的推荐做法",
    "assumptions": ["OpenRouter 与 Tavily 凭证可用"],
    "risks": ["LangGraph 新版本 API 变动可能导致示例过时"],
    "steps": [
      {"id": "step-1", "title": "梳理官方文档", "step_type": "RESEARCH", "expected_outcome": "列出核心节点与状态模式"}
    ],
    "metadata": {
      "locale": "zh-CN",
      "budget_tokens": 8000,
      "budget_cost_usd": 2.5,
      "reviewer": null
    }
  },
  "review_log": [
    {"attempt": 1, "action": "REQUEST_CHANGES", "feedback": "请补充成本估算"},
    {"attempt": 2, "action": "ACCEPT_PLAN", "feedback": ""}
  ],
  "telemetry": {
    "researcher": {
      "total_calls": 2,
      "total_notes": 3,
      "total_duration_seconds": 1.25,
      "total_results": 5,
      "degradation_modes": ["budget"],
      "calls": [
        {"step_id": "step-1", "query": "LangGraph 深度调研代理最佳实践 | 梳理官方文档 | zh-CN", "note_count": 2, "duration_seconds": 0.72, "result_count": 3, "applied_max_results": 3, "applied_max_notes": 2, "degradation_mode": null},
        {"step_id": "step-2", "query": "LangGraph 深度调研代理最佳实践 | 整理社区范例 | zh-CN", "note_count": 1, "duration_seconds": 0.53, "result_count": 2, "applied_max_results": 2, "applied_max_notes": 1, "degradation_mode": "budget"}
      ]
    }
  }
}
```

> JSONL 文件中每条记录独立，占用一行，便于追加与后续回放。
