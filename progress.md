# Deep Research 学习进度

## Current Focus
- 推进阶段 0：明确首个调研场景与报告模版，完善数据模型与 Planner 前置工作。

## 已完成
- 通读 `Deep-Research-Project-Plan.md` 与 `DeerFlow-Tech-Stack.md`，梳理六周学习主线。
- 制定阶段性学习路线与资源清单，用于指导后续实践。
- 初始化 `src/graph|config|tools|report|scripts` 目录，并放置基础占位模块与 CLI 入口。
- 整合配置为单一 `config/settings.yaml`，支持根目录 `secret` 文件覆盖 OpenRouter/Tavily 密钥。
- 实现 OpenRouter LLM 与 Tavily 搜索的最小集成，提供 `scripts/demo_integrations.py`，输出默认保存到 `output/demo_integrations_output.json` 并提供 `.example.json` 参考结果。

## 下一步
- 选定首个调研主题并草拟报告模版示例，确保输出格式清晰。
- 根据本机需求填写 `config/settings.yaml` 与 `secret`，运行 demo 验证配置加载与 API 调用。
- 起草 `Plan`/`Step` 等 pydantic 数据模型，为 Planner 阶段做准备。
