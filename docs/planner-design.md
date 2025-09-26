# Planner Prompt & Schema Notes

本笔记聚焦 Deep Research Planner 节点的提示词设计与结构化输出规范，便于 Phase 1 实验与实现。

## 参考资料
- Building a Deep Research Agent with LangGraph — Sid Bharath（https://www.siddharthbharath.com/build-deep-research-agent-langgraph/）
- LangGraph - GPT Researcher 多代理流程文档（https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph）
- LangGraph 101: Let's Build A Deep Research Agent（https://towardsdatascience.com/langgraph-101-lets-build-a-deep-research-agent/）
- DeerFlow 项目结构与 Planner 模板（参考内部仓库）

## Planner 提示框架（草案）
系统提示示例：
```
You are the Planner agent inside a deep-research workflow. Your goal is to break down the user's question into 3-5 actionable steps.

Rules:
1. Output **valid JSON** matching the provided schema.
2. Each step needs a unique `id` (`step-1`, `step-2`, ...).
3. Use `RESEARCH` when new information is required, `PROCESS` when existing notes must be summarised, `SYNTHESIZE` when consolidating findings, and `REVIEW` for human checks.
4. Provide a short `expected_outcome` describing the success criteria.
5. Document explicit `assumptions` and potential `risks`.
```

用户提示拼接：
```
User Question: {{question}}
Locale: {{locale}}
Context Hints: {{context}}
```

## Plan JSON 输出示例
```json
{
  "topic": "LangGraph Deep Research agent best practices",
  "goal": "Provide an actionable summary of how to build a LangGraph-based research agent similar to DeerFlow.",
  "assumptions": [
    "User can call OpenRouter and Tavily APIs",
    "Scope limited to text-based research"
  ],
  "risks": [
    "Source reliability varies",
    "API rate limits may interrupt execution"
  ],
  "steps": [
    {
      "id": "step-1",
      "title": "Survey official LangGraph documentation",
      "step_type": "RESEARCH",
      "expected_outcome": "List key capabilities relevant to multi-agent research workflows"
    },
    {
      "id": "step-2",
      "title": "Analyse DeerFlow planner and researcher nodes",
      "step_type": "PROCESS",
      "expected_outcome": "Summarise reusable design patterns and configuration hooks"
    },
    {
      "id": "step-3",
      "title": "Synthesize best practices and open questions",
      "step_type": "SYNTHESIZE",
      "expected_outcome": "Draft actionable checklist and identify gaps requiring human review"
    },
    {
      "id": "step-4",
      "title": "Prepare human review checklist",
      "step_type": "REVIEW",
      "expected_outcome": "Ensure plan addresses citation coverage and risk mitigation"
    }
  ],
  "metadata": {
    "locale": "zh-CN",
    "budget_tokens": 8000,
    "budget_cost_usd": 2.5
  }
}
```

> 与 `src/models/plan.py` 一致，若 Planner 无法满足要求，应触发人工中断（LangGraph interrupt）。

## TODO
- 评估 JSON Schema 的自动校验方式（Pydantic vs. LLM JSON mode schema）。
- 针对不同主题准备示例问句与 Planner 输出，用于后续测试集。
