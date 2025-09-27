# Human Review CLI Workflow

> 阶段 0 产出：定义在命令行中配合 LangGraph `interrupt` 的人在环交互规范。

## Interaction Principles
- CLI 负责展示 Planner 产出的 `Plan` 与上下文提示，并收集审阅指令。
- 支持的指令：
  - `ACCEPT_PLAN`：计划可继续执行。
  - `REQUEST_CHANGES`：返回 Planner 节点，需附带人工反馈文本。
  - `ABORT`：终止本次研究流程，记录原因。
- 每次指令都记录到 `GraphState.metadata.review_log`，供后续追踪。

## Prompt Flow
1. Planner 完成后触发 `GraphState.mark_for_review()`。
2. CLI 读取 `GraphState.plan`，按以下结构打印：
   - 主题与目标
   - 假设与风险
   - 步骤列表（`id`、`title`、`expected_outcome`）
3. CLI 提示用户输入指令：
   ```
   ? Action [ACCEPT_PLAN | REQUEST_CHANGES | ABORT]:
   ```
4. 若选择 `REQUEST_CHANGES`，CLI 继续收集
   ```
   Enter feedback (end with empty line):
   ```
   并将多行文本合并。
5. CLI 将结果写回：
   ```json
   {
     "action": "REQUEST_CHANGES",
     "feedback": "step-2 需要覆盖 LangSmith 集成"
   }
   ```
6. LangGraph 节点读取回写结果，更新状态：
   - `GraphState.pending_human_review = False`
   - `GraphState.metadata['review_feedback'] = {...}`

## Planned CLI Implementation (Stage 1)
- 在 `scripts/run_cli.py` 中实现 `prompt_human_review(plan: Plan) -> Dict`。
- 使用 `argparse` 支持 `--auto-accept`（跳过人工审阅，用于自动化测试）。
- 将指令写入标准输出，LangGraph 通过管道/队列读取。

## Follow-up Checks
- 添加单元测试模拟用户输入，验证三种指令路径。
- 将该流程整合到 Stage 1 完整 CLI 演示中。
