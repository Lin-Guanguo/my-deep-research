# Day 1 Log — Deep Research Tooling Bootstrapping

## 今日主题
- 梳理与实现 Deep Research 学习/开发的核心骨架，确保后续能在 LangGraph 上完成“协调→规划→执行→汇报”闭环。
- 建立通用的配置、模板、数据模型与演示脚本，验证 OpenRouter + Tavily 的最小链路，为 Phase 1 规划做好准备。

## 关键成果
- **指导原则与学习计划**：
  - 新增 `AGENTS.md` 记录长期协作约束、提交/输出规范。[`75d3d9a`]
  - 阅读整理 `Deep-Research-Project-Plan.md`、`DeerFlow-Tech-Stack.md`，在 `progress.md` 建立阶段目标；编写初步学习计划文档。[`75d3d9a`, `312f70c`]
- **项目骨架与配置体系**：
  - 创建 `src/`、`scripts/` 目录及占位模块，统一配置加载，提供 `config/settings.yaml` + 根目录 `secret` 方案，并将 `.env/conf` 简化。[`ca494f1`, `d369ab9`, `a4070a6`]
  - `.gitignore` 约定忽略 `secret`、运行产物，并保留 `.example` 示例供参考。
- **API Demo 与输出规范**：
  - 实现 OpenRouter 与 Tavily 的最小封装（`src/tools/llm.py`, `src/tools/search.py`），提供 `scripts/demo_integrations.py` 调试脚本；所有 demo 输出落在 `output/<script>_output.json`，同时维护 `.example.json` 入库。[`2711b1b`, `981c730`, `099d6a5`]
- **模板与数据模型**：
  - 设计通用的调研报告模板 `docs/research-report-template.md` 支撑任意主题。[`3c64fe9`]
  - 使用 Pydantic 定义 `Plan`/`PlanStep` 等模型并撰写 `src/models/README.md`，规范 Planner→Researcher→Reporter 状态共享。[`48372c3`]
- **Planner 准备**：
  - 收集 LangGraph 深度调研资料，整理 Planner 提示词与 JSON 输出示例 (`docs/planner-design.md`)，为 Phase 1 实验定下 schema；填充真实密钥跑通 demo 并刷新参考输出。[`099d6a5`]

## 遇到的问题与解决
- **配置文件分散/冗余** → 合并为单一 YAML + `secret`，通过 Pydantic loader 合并敏感信息。[`ca494f1`, `d369ab9`]
- **输出命名混乱** → 统一脚本输出命名规则及 `.example` 保留策略，避免混淆。[`981c730`]
- **密钥缺失验证困难** → demo 支持空密钥时给出 401 提示，填入真实值后验证成功并生成示例 JSON。[`2711b1b`, `099d6a5`]

## 后续重点
1. 扩充 Planner 输入/输出示例数据集，准备 LangGraph Planner 节点实现与评测。
2. 设计 Researcher 笔记结构与 Reporter 引用校验用例，为 Phase 2/3 的实现做准备。
3. 完善配置与输出规范，确保团队协作和自动化流程一致。

## Commits Covered
`75d3d9acdf8afcdf6d7734bb7b410715ca299196` … `099d6a532e5d4c54f9eb4aa87d97fd0a9208393c`
