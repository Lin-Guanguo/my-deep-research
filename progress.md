# Deep Research 学习进度

## Current Focus
- 推进阶段 0：完善配置验证、通用模板与 Planner 前置工作，准备进入 LangGraph 实装阶段。

## 已完成
- 通读 `Deep-Research-Project-Plan.md` 与 `DeerFlow-Tech-Stack.md`，梳理六周学习主线。
- 制定阶段性学习路线与资源清单，用于指导后续实践。
- 初始化 `src/graph|config|tools|report|scripts` 目录，并放置基础占位模块与 CLI 入口。
- 整合配置为单一 `config/settings.yaml`，支持根目录 `secret` 文件覆盖 OpenRouter/Tavily 密钥。
- 实现 OpenRouter LLM 与 Tavily 搜索的最小集成，提供 `scripts/demo_integrations.py`，输出默认保存到 `output/demo_integrations_output.json` 并提供 `.example.json` 参考结果。
- 草拟通用的 `docs/research-report-template.md`，用于各类调研主题的结构化输出。
- 新增 `src/models/plan.py` 与 `src/models/README.md`，统一 Planner/Researcher/Reporter 共享的数据模型。
- 填写真实密钥后运行 demo，成功验证 OpenRouter 与 Tavily 的调用链并刷新示例输出。
- 整理 Planner 提示词与 JSON 输出示例，记录于 `docs/planner-design.md`。
- 编写 `tests/test_configuration.py` 验证 settings/secret 合并逻辑，完成配置验证的自检基础。
- 设计 `ResearchNote` 结构并更新模型/文档，沉淀 `docs/research-notes-spec.md` 指南。
- 整理 `samples/planner_plans.jsonl` 与校验单测，确保 Planner 输出示例可解析。
- 明确 LangGraph 状态与节点契约，新增 `src/graph/state.py` 与 `docs/langgraph-contract.md`。

## 主题与目标
- 当前示例练习：LangGraph 深度调研代理最佳实践（可替换为其他问题）。
- 长期目标：构建可复用的 Deep Research 工具链，支持多种调研场景的闭环执行。

## 下一步
- 将 Planner 校验流程接入真实 LLM 生成结果，构建最小评测脚本。
- 实现 Reporter 引用校验与置信度提示逻辑的原型测试。
- 准备 CLI 人审交互方案，定义 `interrupt` 指令格式与回写流程。
