# AGENTS Notes

## Persistent Requirements
- 每次学习结束前更新 `progress.md`，记录当前阶段、已完成事项与下一步计划，方便下次继续。
- 配置统一放在 `config/settings.yaml`，敏感密钥写入根目录 `secret`（KEY=VALUE 格式）且不提交仓库。
- LLM 接口限定使用 OpenRouter，Web 搜索限定 Tavily；后续实现与文档说明保持一致。
- 保持与用户的学习节奏对齐：按照 `Deep-Research-Project-Plan.md` 的阶段顺序逐步推进，并在需要时提供分步指导。
- 如用户提出新的长期指令或偏好（例如工具选择、文档结构），在此文件补充记录。

## Session Context
- 骨架目录与工具接口已搭好，当前集中在阶段 0：选择调研主题、完善配置加载与 Planner 前置模型。
