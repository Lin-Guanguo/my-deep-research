# Researcher Node Interface Outline

> Stage 1 准备内容：明确 Researcher 节点在 LangGraph 中的输入输出契约，为后续实现留出接口与数据依赖。

## Responsibilities
- 读取 Planner 确认后的 `Plan` 和当前执行步骤，决定需要的检索与调研动作。
- 调用 OpenRouter / Tavily / 其他工具链生成结构化 `ResearchNote`，并将结果附加到 `PlanStep.notes` 与 `GraphState.scratchpad`。
- 根据反馈或失败情况，向上游写入状态（例如补充风险、建议重新规划）。

## Inputs
- `GraphState.plan`: 已通过审阅的计划；必须包含步骤、假设、风险等字段。
- `GraphState.current_step_id`: 当前处理的步骤标识，缺失时回退到首个未完成步骤。
- `GraphState.metadata`: 包含预算、速率限制、review 信息；可选地携带上一节点的上下文。
- 工具凭证：来自 `config/settings.yaml` 与 `secret` 中的 OpenRouter / Tavily 等配置。

## Outputs
- 更新目标步骤的 `PlanStep.status`（`IN_PROGRESS` → `COMPLETE` 等）和 `PlanStep.notes` 列表。
- 将新生成的 `ResearchNote` append 至 `GraphState.scratchpad`，用于 Reporter 汇总。
- 如果发现阻塞问题，将描述写入 `GraphState.metadata['researcher_flags']`，供协调器或 Planner 判定是否中断。

## Error Handling & Retries
- 统一返回结构，标记 `success` / `failure`，并在失败时包含 `reason` 与建议的修复动作。
- 支持调用方根据 `GraphState.retry_count` 或配置决定是否重试、降级或请求人工介入。

## Open Questions
1. 是否需要在 Researcher 内部实现并发子任务，还是交由 Planner 细分步骤？
2. Tavily 结果去重 / 合并策略如何与 Reporter 协调，避免重复引用？
3. `ResearchNote` 中的 `source` 字段是否强制要求 URL？如何记录付费 API 的引用？
4. 需要哪些遥测数据（调用时长、Token 耗费）写入 `PlanRunRecord` 或独立日志？

## Current Prototype
- `ResearcherAgent.run_step` 根据 Plan 步骤构造 Tavily 查询，默认取首条有效结果生成 `ResearchNote`。
- LangGraph `researcher` 节点会更新步骤状态、写入 `scratchpad`，并记录查询元数据供 Reporter/审计复用。

## Next Steps
- 定义 `ResearchContext` 数据类，封装 locale、预算、工具配置，降低函数签名复杂度。
- 扩展 Tavily 结果整合策略（多条笔记、去重及置信度评分），与 Reporter 输出格式对齐。
- 与 Reporter 节点的模板对齐，确认需要的 note 字段（证据、摘要、置信度等）。
