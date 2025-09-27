# Research Notes & Citation Validation

> 适用于任意调研主题的通用结构，指导 Researcher 记录笔记、Reporter 执行引用校验。

## Structured Note Schema
- `source` *(string, required)*：引用的原始链接或编号，Reporter 用于生成 `[n]` 标记。
- `claim` *(string, required)*：单条事实陈述，聚焦可验证的信息；避免复合句。
- `evidence` *(string, optional)*：来源中的关键语句或数据摘要，便于人工复查。
- `confidence` *(float 0-1, optional)*：主观置信度分数。低于 `0.6` 时 Reporter 应提醒补充验证或在报告中标注不确定性。
- `todo` *(string, optional)*：待办事项或缺口，例如“需要官方文档印证发布日期”。

示例：
```json
{
  "source": "https://docs.langchain.com/langgraph/overview",
  "claim": "LangGraph 将状态表示为可序列化的数据字典，支持断点恢复",
  "evidence": "LangGraph documentation: 'State is a Python dict-like object that can be saved between runs.'",
  "confidence": 0.8,
  "todo": null
}
```

## Reporter Validation Checklist
1. **引用映射**：为每条笔记分配 `[n]`，并在引用列表中呈现 `source`；若 `source` 缺失，标记为 `TODO` 并列入“后续问题”。
2. **置信度提示**：当 `confidence < 0.6` 时，在正文添加“待复核”脚注或在风险章节列出。
3. **证据摘要**：将 `evidence` 作为引用上下文，可在附录或脚注呈现，便于读者快速验证。
4. **TODO 汇总**：收集所有 `todo` 字段，写入“后续问题与行动项”小节。

## Test Fixtures
- **Positive Case**：包含 3 条以上完整字段的笔记，验证 Reporter 能生成引用、摘要、风险提示。
- **Missing Source Case**：模拟 `source=""` 或缺失，Reporter 应抛出校验错误或添加 `TODO` 标签（用于单元测试）。
- **Low Confidence Case**：置信度低于 0.5，检查风险章节是否出现提醒。

后续实现可在 Reporter 模块中提供 `validate_notes(notes: list[ResearchNote]) -> list[Issue]` 帮助函数，并在单测中覆盖上述场景。
