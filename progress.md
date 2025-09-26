# Deep Research 学习进度

## Current Focus
- 推进阶段 0：搭建通用 Deep Research 工作流的基础能力（配置验证、报告模版、Planner 前置工作）。

## 已完成
- 通读 `Deep-Research-Project-Plan.md` 与 `DeerFlow-Tech-Stack.md`，梳理六周学习主线。
- 制定阶段性学习路线与资源清单，用于指导后续实践。
- 初始化 `src/graph|config|tools|report|scripts` 目录，并放置基础占位模块与 CLI 入口。
- 整合配置为单一 `config/settings.yaml`，支持根目录 `secret` 文件覆盖 OpenRouter/Tavily 密钥。
- 实现 OpenRouter LLM 与 Tavily 搜索的最小集成，提供 `scripts/demo_integrations.py`，输出默认保存到 `output/demo_integrations_output.json` 并提供 `.example.json` 参考结果。
- 草拟通用的 `docs/research-report-template.md`，用于所有调研主题的结构化输出。
- 新增 `src/models/plan.py`，使用 Pydantic 定义 `Plan`/`PlanStep` 等模型与辅助方法。

## 主题与目标
- 当前示例练习：针对 LangGraph 深度调研代理探索最佳实践（可替换为其他问题）。
- 长期目标：构建可复用的 Deep Research 工具链，支持多种调研场景的闭环执行。

## 下一步
- 根据本机需求填写 `config/settings.yaml` 与 `secret`，运行 demo 验证配置加载与 API 调用。
- 收集首批练习主题素材，准备阶段 1 的 Planner 提示词实验。
- 规划 Planner 输出 schema 的 JSON 示例，方便后续与 LangGraph 节点对接。
