# 简易 Deep Research 程序实作计划（2025Q4）

## DeerFlow 风格最小目标
- **任务**：复刻 DeerFlow 的核心“协调→规划→执行→汇报”闭环，产出含引用的研究总结。
- **范围**：仅使用托管 LLM 与搜索/抓取 API，不落地播客、PPT 等扩展功能。
- **验收**：
  - LangGraph 状态机含 `coordinator → planner → human_feedback → researcher → reporter`。
  - Planner 输出结构化 `Plan`，Researcher 迭代检索并记录 JSON 笔记，Reporter 生成含引用 Markdown。
  - 人在环审阅计划与报告，Trace 记录可在 LangSmith 中查看。

## 核心工作流（最小环）
- **Coordinator**：接收用户问题，初始化状态（主题、locale、历史消息、配置）。
- **Planner**：根据模板生成 `Plan`（步骤、StepType、预期成果）；若上下文不足，转人工审阅。
- **Human Feedback**：使用 LangGraph `interrupt`，允许 `[EDIT_PLAN]` 或 `[ACCEPTED]`。
- **Researcher**：按步骤循环执行“搜索→抓取→阅读→做笔记”；支持 `StepType` 判别补充任务。
- **Reporter**：汇总笔记、生成结构化 Markdown，插入引用编号与来源列表。

## 技术栈与目录约定
- **语言/运行时**：Python 3.11；依赖管理 `uv`；可选 Node + pnpm 扩展 Web UI（阶段外扩）。
- **核心库**：LangChain、LangGraph、langchain-openai/anthropic 等官方客户端、`httpx`、`tenacity`、`pydantic`。
- **工具层**：
  - `src/tools/search.py`：封装 Tavily、Brave Search；统一日志与速率控制。
  - `src/tools/crawler.py`：`httpx` + `readability-lxml` 或 `trafilatura`。
  - `src/tools/retriever.py`：预留私有资料接入（可阶段性空实现）。
- **配置**：`.env`（API Key、搜索选项）、`conf.yaml`（模型、步骤阈值、搜索数量）；通过 `Configuration` 注入节点。

## 里程碑（6 周滚动）
- **M0 – Project Skeleton**（Week 1）：完成目录、配置、最小 API 封装与 CLI 启动。
- **M1 – Planner Loop**（Week 2）：实现 LangGraph 基础节点，Planner 能生成可解析的 `Plan`，支持人工批注。
- **M2 – Research Loop**（Week 4）：Researcher 完成多轮搜索/抓取/笔记，Reporter 生成初版报告（含引用）。
- **M3 – Observability**（Week 5）：接入 LangSmith Trace、记录成本与时长、输出失败样本；补充基础评测集。
- **M4 – Final Demo** (Week 6)：CLI/可选 Web UI 演示完整流程，整理文档与学习笔记。

## 阶段任务

### 阶段 0：准备与需求细化（Week 0–1）
- 明确场景（如技术调研）与输出模版（标题、摘要、关键发现、引用、后续问题）。
- 建立仓库骨架：`src/graph/`、`src/config/`、`src/tools/`、`src/report/`、`scripts/`。
- 编写 `.env.example`、`conf.yaml.example`，封装 `call_llm()`、`search_web()`、`fetch_article()`，加入超时/重试/成本统计。
- 起草 `Plan`/`Step` 数据模型（`pydantic`）与状态类型。

### 阶段 1：Planner + 人在环（Week 1–2）
- 设计 Planner 提示与模板，支持 JSON Mode 输出。
- 搭建 LangGraph：`coordinator → planner → human_feedback → reporter`，确认 `interrupt` 行为可控。
- 实现 `Plan` 校验与存储（JSONL 或内存），记录 Planner 响应与人工反馈。
- 交付物：`uv run main.py` 输入问题 → 输出已审阅的计划文本（不做执行）。

### 阶段 2：Researcher 执行闭环（Week 2–4）
- 添加 `researcher` 节点 + 条件边，实现按 `StepType` 派发检索或处理任务。
- 搜索：集成 Tavily（默认），支持 Brave/SerpAPI 开关；记录查询、tokens、成本。
- 抓取：基于 `fetch_article()` 解析正文；对摘要调用 LLM 输出标准笔记（JSON 字段：`source`, `claim`, `evidence`, `confidence`, `todo`）。
- 完善状态：保存 `current_plan.steps[i].execution_res` 与 `notes` 集合。
- 交付物：CLI 演示多轮检索 → 输出笔记列表。

### 阶段 3：Reporter + 自检（Week 4–5）
- Reporter 节点整合笔记，生成 Markdown 报告（摘要、要点、引用列表）。
- 实现引用映射：`[n]` 对应 `note.source`，若缺来源则标记 TODO。
- 增加 `critic` 简版（可选）：调用 LLM 检查引用一致性、输出补充建议。
- 接入 LangSmith Trace，生成每次 run 的链接；记录成本统计与失败样本。
- 交付物：完整 CLI Demo（问题→计划→执行→报告）。

### 阶段 4：评测与交付（Week 5–6）
- 构建评测集（≥10 个问题）：预期要点 + 可靠来源链接。
- 评测指标：事实匹配率、引用覆盖率、平均搜索轮次/响应时间/成本。
- 撰写 `docs/RETRO.md`（遇到的坑、调参记录、后续改进）。
- Optional：开发极简 Web 面板或导出 JSON API。

## 模块实现细则
- `src/graph/builder.py`：参考 DeerFlow，拆出 `_build_base_graph()` 和 `build_graph()`；允许 MemorySaver 注入。
- `src/config/configuration.py`：封装运行配置，提供 `from_env()` / `from_runnable_config()`。
- `src/agents/planner.py`、`src/agents/researcher.py`：复用 LangChain Runnable，支持 streaming 与日志。
- `src/prompts/`：存放 Planner/Researcher/Reporter 模板，使用模板引擎拼接背景信息。
- `src/report/markdown.py`：负责 Markdown 渲染与引用格式化。

## 观测与评测
- LangSmith：记录 Plan、搜索请求、抓取和 Reporter 输出；用 Dataset 封 10 条问题跑回归。
- 指标板：每 run 输出 `token`, `cost`, `duration`, `search_count`，写入 CSV。
- 质量守护：记录笔记中的 `confidence`，当低于阈值时自动触发补充搜索或提示人工复核。

## 学习资源（对照 DeerFlow）
- `learning/DeerFlow-Tech-Stack.md`（已整理的技术栈参考）。
- LangGraph Cookbook：Planner + Researcher 状态机示例。
- Tavily/Brave API 文档；`trafilatura`/`readability-lxml` 抓取指南。
- LangSmith Docs：Tracing、Dataset、Eval Pipeline。
- DeerFlow 仓库 `src/graph/`、`src/tools/`、`docs/configuration_guide.md` 用作代码风格与配置参考。

## 风险与缓解
- **API 成本**：设置调用预算与速率限制，优先使用低上下文模型；缓存搜索结果。
- **幻觉与引用缺失**：笔记必须携带来源；Reporter 若发现引用缺失则标记 TODO 并提示补充。
- **抓取失败**：准备多搜索源、允许手动传入 URL/文本；对 4xx/5xx 做指数退避。
- **流程复杂度**：保持节点极简，先实现单循环；扩展 coder/critic 前写好单测和 Trace 验证。

## 收尾与沉淀
- 输出 Demo：录屏或 GIF + README（流程图、命令、示例输出、LangSmith 链接）。
- 整理复盘：架构图 + 模块职责 + 成本与性能数据。
- 将总结同步到 `learning/` 与 `work-summary-doc/`，为后续简历/作品集提供素材。
