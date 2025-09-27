# Plan 数据模型说明

`src/models/plan.py` 定义了 Deep Research 工作流中 Planner→Researcher→Reporter 共享的核心数据结构，使用 [Pydantic](https://docs.pydantic.dev/latest/) 进行类型校验与序列化，便于 LangGraph 节点间传递状态。

## 核心枚举
- `StepType`
  - `RESEARCH`：执行搜索/资料收集类任务。
  - `PROCESS`：摘要、清洗或结构化已获取的信息。
  - `SYNTHESIZE`：整合多条笔记得出结论或推荐。
  - `REVIEW`：触发人工或自动复核。
- `StepStatus`
  - `PENDING` → `IN_PROGRESS` → `COMPLETED` 为默认执行流；`BLOCKED` 用于等待外部输入。

## ResearchNote
Researcher 在执行阶段产生的结构化笔记，字段说明：
- `source`：可追溯的引用（URL、文献编号等），不能为空。
- `claim`：围绕单一事实或洞察的陈述。
- `evidence`：可选的关键语句、数据或上下文摘要。
- `confidence`：0~1 之间的置信度分数，便于 Reporter/Reviewer 判断是否需要补充验证。
- `todo`：若该笔记仍有待办事项或疑问，可在此描述。

## PlanStep
计划中的单个步骤，包含：
- `id`：稳定的标识符（如 `step-1`），用于状态回写。
- `title`/`expected_outcome`：对步骤目的与完成标准的简述。
- `step_type`：由 Planner 判定的执行类型，指导 Researcher 行为。
- `status`：运行时状态，初始为 `PENDING`，由执行方更新。
- `notes`：`ResearchNote` 列表，执行过程中积累的结构化研究笔记。
- `references`：与笔记对应的来源链接或引用编号。
- `execution_result`：对该步骤执行情况的总结，可供 Reporter 复用。

## PlanMetadata
记录计划的辅助信息：
- `locale`：提示链使用的语言偏好。
- `reviewer`：若有人在环参与，记录其姓名。
- `budget_tokens`/`budget_cost_usd`：运行预算，用于对接追踪与报表。

## Plan
完整的调研计划，字段说明：
- `topic`/`goal`：调研问题与整体目标。
- `steps`：有序的 `PlanStep` 列表，是执行闭环的主线。
- `assumptions`：Planner 制定计划时的前提假设。
- `risks`：已知风险或不确定性，便于 Researcher/Reporter 注意。
- `metadata`：嵌套的 `PlanMetadata`。

常用方法：
- `get_step(step_id)`：按 ID 获取步骤，不存在时抛出 `KeyError`。
- `mark_step_status(step_id, status)`：更新步骤状态，实现运行时追踪。
- `append_note(step_id, note, reference=None)`：追加笔记及可选引用，留痕执行过程。

这些模型可直接转换为 JSON，用作 Planner 输出 schema、LangGraph 状态对象或持久化格式，统一了多节点协作时的数据接口。
