# LangGraph Builder Contract

> 阶段 0 目标：明确最小可行的节点拓扑、状态形态与人在环中断点，方便 Stage 1 实装。

## Canonical Node Pipeline
1. **coordinator**：解析用户输入、加载配置、初始化 `GraphState`。
2. **planner**：生成 `Plan`，写入 `GraphState.plan`，并根据配置决定是否触发人工审阅。
3. **human_review**：LangGraph `interrupt` 节点，等待 `[ACCEPT_PLAN]` 或 `[REVISE_PLAN]` 指令，更新 `GraphState.pending_human_review`。
4. **researcher**：读取当前步骤，调用搜索/抓取工具，生成 `ResearchNote`，追加到 `PlanStep.notes` 与 `GraphState.scratchpad`。
5. **reporter**：整合 `Plan` 与笔记，生成 Markdown 报告和引用列表。

## GraphState 要点
- `topic` / `locale`：源于 coordinator，保证提示语言一致。
- `plan`：Planner 审阅通过后的结构化计划。
- `current_step_id`：循环执行时的步骤指针，便于中断恢复。
- `scratchpad`：跨步骤聚合的 `ResearchNote` 列表。
- `pending_human_review`：若为 `True`，Graph 应中断并等待外部输入；重入时清零。
- `metadata`：存放执行时间、预算、review 原因等扩展信息。

## Interrupt Workflow
- Planner 完成后，如 `config.runtime.human_review` 为真或 Planner 自行标记风险，则调用 `GraphState.mark_for_review()`。
- LangGraph `interrupt` 输出必须包含：
  ```json
  {
    "plan": {...},
    "actions": ["ACCEPT_PLAN", "REQUEST_CHANGES"],
    "notes": ["Planner flagged open questions about data availability"]
  }
  ```
- 人类反馈后，协调器将指令写回状态：
  - `ACCEPT_PLAN`：`pending_human_review = False`，继续执行。
  - `REQUEST_CHANGES`：回流至 planner 节点，附带人工注释。

## Reporter 依赖
- 需要 `PlanStep.notes` 和 `GraphState.scratchpad` 中的 `ResearchNote`。
- 若发现 `ResearchNote.source` 为空，应返回错误或在报告标记 `TODO`。
- 使用 `confidence` 字段决定是否在“风险与缓解方案”中加入提醒。

## Next Implementation Tasks (Stage 1 Preview)
- 在 `src/graph/builder.py` 中实际构建 `StateGraph`，注册节点函数。
- 实现 planner 节点（接入 OpenRouter）并返回 `Plan`。
- 为 `human_review` 节点提供 CLI/CLI 工具与 LangGraph interrupt 配合。
- 编写针对 `GraphState` 的单元测试，确保中断恢复流程稳定。
