# Stage 1 Roadmap — Planner + Human Review

> 对齐 `Deep-Research-Project-Plan.md:42-46`，明确阶段性交付：`coordinator → planner → human_review → reporter` 基础链路，交付 CLI 计划审阅流程。

## Core Deliverables
- 实现 LangGraph 构建函数：`build_graph(AppConfig)` 返回含 `coordinator/planner/human_review/reporter` 节点的 `StateGraph`。
- 开发 `src/agents/planner.py`：
  - 使用 `scripts/validate_planner.py` 的强化提示结构。
  - 输出 `Plan`，并持久化至内存/JSONL，便于后续审阅记录。
- 构建人在环节点：
  - CLI 交互遵循 `docs/human-review-cli.md`。
  - 支持 `ACCEPT_PLAN`、`REQUEST_CHANGES`、`ABORT` 指令，更新 `GraphState`。
- CLI 演示：`uv run scripts/run_cli.py --question "..."` 输出经人工审阅确认的计划文本（暂不执行 Researcher）。

## Implementation Tasks
1. **Agents & Prompts**
   - 新增 `src/prompts/planner_system.txt` 与 `src/prompts/planner_user.jinja`，复用校验通过的 schema 提示。
   - 编写 `PlannerAgent` 类，封装 OpenRouter 调用与 `Plan` 解析；复用 `ResearchNote`、`Plan` 模型。
   - 引入最小日志记录与失败重试策略。
2. **State Graph**
   - 在 `src/graph/builder.py` 中实现 `_build_planner_graph()`，包含：
     - `coordinator`：加载配置、构造初始 `GraphState`。
     - `planner`：调用 `PlannerAgent`，将结果写入 `state.plan` 并标记 review。
     - `human_review`：调用 CLI/自动审阅 hook；根据反馈调整 `state.plan` 或重走 planner。
     - `reporter`：暂以占位返回文本（Stage 1 仅输出计划结构）。
   - 为 LangGraph 节点编写接口 `src/graph/nodes/planner.py` 等，便于后续扩展。
3. **Storage & Logging**
   - 计划运行结果写入 `output/plans/plans.jsonl`（包含输入、Plan、审阅意见）。
   - 预留 `GraphState.metadata['review_log']` 用于审阅追踪。
4. **Testing & Validation**
   - 单元测试：
     - planner 节点生成计划并通过 `Plan.model_validate`。
     - human review 节点对三种指令的状态更新。
   - 集成测试：mock planner 输出 + human feedback，确保 CLI 流程返回最终计划文本。

## Open Questions
- 是否需要在 Stage 1 接入 LangSmith logging？（计划中建议，若时间允许可提前布局）。
- Planner 重试策略：是否采用固定 2 次重试 + fallback 模板？
- human review CLI 如何在自动测试中替代人工输入（建议提供 `--auto-accept` 选项）。

## Next Checkpoint
- 草拟 nodes/agents 结构后，与 Stage 2 的 Researcher 插件化需求评估接口兼容性。
- 完成初版 CLI Demo 再进入 Stage 2 的 Researcher 实装。
