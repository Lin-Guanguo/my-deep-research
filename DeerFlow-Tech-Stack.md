# DeerFlow 技术栈概览（参考）

## 核心语言与运行环境
- 后端：Python 3.12，依赖管理使用 `uv`（自动创建虚拟环境），打包基于 `pyproject.toml`。
- 前端：Node.js 22+，包管理 `pnpm`，框架组合（React + Next.js + Tiptap 编辑器）。
- 容器：提供 `Dockerfile`，支持一键构建；FaaS 方案部署到火山引擎。

## 主体框架
- **编排**：LangChain Runnable/LCEL + LangGraph 状态机，节点之间通过 `StateGraph` 与条件边 (`builder.add_conditional_edges`) 协调。
- **LLM 接入**：`litellm` 统一封装（OpenAI、Moonshot、DashScope、Qwen 等），区分 basic/reasoning 模型，支持 JSON Mode 与 streaming。
- **记忆**：LangGraph `MemorySaver` 做会话与计划检查点，可替换为持久化存储。

## 多代理架构
- `coordinator`（入口协调）→ `background_investigator` → `planner` → `human_feedback` → `research_team`（`researcher`/`coder` 子代理循环）→ `reporter`，全部在 `src/graph/` 中实现。
- `Plan` 模式（`prompts/planner_model.py`）描述步骤、类型（RESEARCH/PROCESSING）、执行结果；人类可通过 `[EDIT_PLAN]/[ACCEPTED]` 中断确认。
- 支持扩展代理：`prompt_enhancer`、`podcast`、`ppt`、`prose` 等子图，重用 LangGraph 构建流程。

## 工具与集成
- 搜索：Tavily（默认）、DuckDuckGo、Brave、Arxiv、自建 Searx/SearxNG。
- 抓取：Jina Reader、`readability-lxml` 内容抽取、自建 `crawler` 模块。
- RAG：可选 RAGFlow、VikingDB、Milvus；工具位于 `src/rag/`。
- 编码执行：Python REPL 工具；支持 MCP（Multi-Component Proxy）扩展更多工具。
- TTS/内容生成：Volcengine TTS、Marp PPT 生成、Podcast Audio mixing。

## 配置与运维
- `.env`：搜索/LLM/RAG/音频 API Key 与参数；`conf.yaml` 控制模型类型、搜索结果数、planner 迭代次数、是否启用深度思考。
- 观测：LangSmith 集成（Tracing、Datasets、评测）、结构化日志（`structlog`）。
- CI/CD：GitHub Actions（lint、unittest、容器构建），Makefile 封装 `lint/test/format`。

## UI 与交互
- Web UI：聊天 + 计划编辑 + Notion 风格报告，支持 replay、AI 润色、TTS 播放。
- Console UI：`uv run main.py`，适合快速体验与开发调试。

## 可借鉴点
- LangGraph 状态机拆分角色，便于扩展与调试。
- 统一工具工厂 (`get_web_search_tool`) 与配置注入 (`Configuration.from_runnable_config`) 简化替换。
- 人在环 `interrupt` 与计划结构化 JSON，保证流程可控与可追踪。
