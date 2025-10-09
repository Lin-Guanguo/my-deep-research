# Deep Research 学习进度

## Current Focus
- 进入阶段 1：实现 Planner + 人在环链路（LangGraph 图、节点实现与 CLI 审阅流程）。

## 已完成
- 将 LangGraph `human_review` 节点与 CLI 审阅指令联动，实现自动回流与再规划。
- 实现 `src/agents/planner.py` 与提示模板，封装 OpenRouter 计划生成逻辑并编写单测。
- 构建 LangGraph 管线（`build_graph`）串联 coordinator→planner→human_review→reporter，支持依赖注入与测试。
- 扩展 `scripts/run_cli.py`，完成 Planner→人在环审阅→计划存档流程并提供 `--auto-accept` 选项与 CLI 测试。
- 撰写 `docs/stage1-roadmap.md` 对齐阶段 1 交付物与实现任务。
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
- 新增 `scripts/validate_planner.py`，落地 LLM 调用 + `Plan` 验证闭环，并提供示例输出。
- 实现 Reporter 端笔记校验原型（`src/report/validation.py` + 单测），覆盖引用与置信度提示。
- 补充人在环 CLI 流程文档与入口提示（`docs/human-review-cli.md`、`scripts/run_cli.py --show-review-help`）。
- 修复 Planner CLI 持久化缺失依赖问题，统一审阅指令枚举并补充 `_store_plan` 单测，保证日志可写。
- 设计 Planner 运行记录 schema，新增 `PlanRunRecord` 模型、校验与回放脚本，并提供样例 JSON 输出。
- 梳理 Planner 审阅日志持久化与工具脚本的实现，确认 CLI 测试覆盖与示例输出结构。
- 将审阅日志校验脚本纳入 pytest 回归测试，保持示例 JSONL 与工具脚本长期有效。
- 新增 Researcher 节点接口大纲，为 Stage 2 定义输入输出与开放问题。
- 实现最小 Researcher 节点原型，串联 Tavily 查询→ResearchNote→scratchpad，完成 LangGraph Stage 1 端到端闭环。
- 扩展 ResearcherAgent 支持多结果聚合与置信度估计，并将耗时/笔记统计写入计划遥测。
- 引入 ResearchContext 抽象、Reporter 摘要与研究遥测整合，完成 Stage 1 全链路观测，并刷新文档/示例。
- 实现 Markdown Reporter 最小渲染，输出步骤笔记与遥测摘要。

## 主题与目标
- 当前示例练习：LangGraph 深度调研代理最佳实践（可替换为其他问题）。
- 长期目标：构建可复用的 Deep Research 工具链，支持多种调研场景的闭环执行。

## 下一步
- 优先完成可复现 demo：使用 `uv run scripts/run_cli.py -q "..." --auto-accept` 生成计划并保存 `output/plans/plans.jsonl`。
- 梳理一次人工审阅流程示范（可去掉 `--auto-accept`），记录关键步骤供演示使用。
- 汇总 demo 依赖与运行要点，更新到相关文档或 README 草稿便于复现。

## 待办（后续阶段）
- 将 ResearchContext 扩展字段接入工具降级/预算策略，驱动 Researcher 调用决策。
- 迭代 Reporter Markdown（引用编号、风险表格）并对接 validation 结果。
- 规划 Planner/Researcher LLM 调用成本记录方案，补全 PlanRunRecord 遥测字段。
