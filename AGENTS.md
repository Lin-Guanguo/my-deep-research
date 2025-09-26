# AGENTS Notes

## Persistent Requirements
- 每次学习结束前更新 `progress.md`，记录当前阶段、已完成事项与下一步计划，方便下次继续。
- 配置统一放在 `config/settings.yaml`，敏感密钥写入根目录 `secret`（KEY=VALUE 格式）且不提交仓库。
- LLM 接口限定使用 OpenRouter，Web 搜索限定 Tavily；后续实现与文档说明保持一致。
- 所有 demo 或脚本输出命名为 `<script>_output.json`（如 `demo_integrations_output.json`），并存放在 `output/`；保留对应 `.example.json` 版本入库作为参考，其余运行产物保持忽略。
- Git 提交按阶段性成果进行，不必在每个细微步骤后提交。
- 报告模板与实现需保持通用性，能支持任意调研主题；具体练习主题仅作为示例，不写死在代码或模板中。
- 如用户提出新的长期指令或偏好（例如工具选择、文档结构），在此文件补充记录。

## Session Context
- 正在阶段 0：完善通用报告模板、配置验证与 Planner 数据模型；当前练习主题为 LangGraph 深度调研代理，但工具需兼容其他问题。
