# Telemetry Roadmap (Stage 2)

## Current Coverage
- Researcher metrics persisted per run：调用次数、笔记数量、耗时、搜索结果数量、降级模式。
- Reporter 摘要输出：总笔记数、平均置信度、低置信度提示、Markdown 报告。
- CLI / 回放工具读取并展示上述信息，例子已同步更新。

## Planned Enhancements
1. **LLM 成本记录**
   - Planner：捕获 OpenRouter 调用的 token、费用、模型版本，写入 `telemetry.planner`。
   - Researcher：如后续接入 LLM 总结，也记录 token/cost，便于预算审计。
   - Reporter：输出生成时记录渲染耗时 / 生成 token。
2. **工具降级策略**
   - 扫描 `ResearchContext` 的预算字段，自动写入使用的降级模式，并区分预算不足、速率限制等原因。
   - 在 `PlanRunRecord` 中落入 `telemetry.researcher.degradation_modes`，同时在 Reporter 提示中提醒。
3. **阶段性对接 LangSmith / OpenTelemetry**
   - 允许可选地上传执行 trace，统一分析 Planner→Researcher→Reporter 链路性能。

## Next Steps
- 在 Stage 2 完结前补充 Planner LLM 成本统计方案（字段设计 + 采集位置）。
- Stage 3 开始时，与 Reporter 渲染结合，生成最终 Markdown & PDF 报告，同时输出遥测摘要。
