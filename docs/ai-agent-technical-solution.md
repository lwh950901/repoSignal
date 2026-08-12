# 个人 AI 助理技术方案

- 版本：v0.1（草案）
- 日期：2026-08-12
- 状态：待评审

## 1. 背景与目标

构建一个**独立的个人 AI 助理**，与 repo-signal 项目本身无耦合。数据来源：GitHub 优质项目的每日发现与每周发现（`data/github-project-digest/daily/` 与 `weekly/` 中的仓库数据）。这些发现数据仅作为助理的知识集/数据集，**导入**助理自己的存储后使用；运行时不依赖 repo-signal 的任何代码、目录或流程。

目标能力：

1. **日常对话与任务执行**：个人助理基础能力（问答、工具调用、自动化任务）。
2. **基于发现数据的知识问答**：「本周精选了哪些项目？」「pdf-inspector 是做什么的？」
3. **个性化项目推荐**：结合用户偏好，从发现数据中推荐项目。
4. **每日/每周摘要**：从最新一期发现数据生成摘要，推送到助理自己的渠道（CLI/WebUI/消息网关）。

## 2. 选型依据（来自每日/每周发现的项目）

所有选型项目均来自 `data/github-project-digest/daily/` 与 `weekly/` 的实际发现，标注来源与评分。

| 架构层 | 项目 | 发现来源 | 评分 | 决定 |
|---|---|---|---|---|
| 核心框架 | pydantic/pydantic-ai | 07-15 日报、W29 周报 | 92/100 | **主框架**（类型安全、结构化输出、原生 MCP、evals） |
| 核心框架备选 | openai/openai-agents-python | 07-20 日报、W30 周报 | 91/100 | 备选（handoff/guardrails/tracing 成熟） |
| 运行时参考 | HKUDS/nanobot | 07-25 日报、W30 周报 | 90/100 | 参考其 WebUI、多渠道、模型路由设计 |
| 多渠道参考 | NousResearch/hermes-agent | 08-10 日报 | 90/100 | 参考 CLI + 消息网关 + 记忆 + 研究架构 |
| 记忆知识 | topoteretes/cognee | 07-28 日报、W31 周报 | 90/100 | **长期记忆 + 知识图谱 + 向量 + MCP** |
| 记忆备选 | MemPalace/mempalace | 07-18 日报、W29 周报 | 86/100 | 本地优先 RAG 备选 |
| 记忆备选 | aiming-lab/SimpleMem | 07-22 日报 | 86/100 | 压缩记忆备选 |
| 代码库理解 | DeusData/codebase-memory-mcp | 06-29 日报、W27 周报 | 94/100 | 可选工具（代码库知识图谱） |
| 浏览器工具 | ChromeDevTools/chrome-devtools-mcp | 07-25 日报、W30 周报 | 92/100 | 可选工具 |
| 执行沙箱 | opensandbox-group/OpenSandbox | 08-12 日报 | 91/100 | M3 引入（安全代码执行） |
| 评测可观测 | coze-dev/coze-loop | 08-04 日报 | 89/100 | 评测、追踪、监控 |
| 开发方法 | github/spec-kit | 08-10 日报 | 92/100 | 开发流程（spec-driven） |

## 3. 总体架构

```
┌─ 接入层 ─────────────────────────────┐
│ CLI（优先）│ WebUI（参考 nanobot）│ 消息网关（M3 预留）│
└──────────────────┬───────────────────┘
┌─ Agent 核心层（pydantic-ai）──────────┐
│ 主对话 Agent（意图路由 / handoff 编排）│
│  ├─ 记忆工具 Agent   → cognee         │
│  └─ 数据查询 Agent   → 项目知识库      │
└──────┬────────────────────┬──────────┘
       │                    │ 查询工具
┌──────▼───────────┐  ┌─────▼────────────────┐
│ 记忆服务（cognee）│  │ 项目知识库（本地 SQLite）│
│ 长期记忆/图谱/向量│  │ projects 表            │
│ SQLite + 向量索引 │  │ 由发现数据导入，运行期   │
│                  │  │ 不依赖 repo-signal     │
└──────────────────┘  └───────────────────────┘
                ▲
                │ 导入脚本（一次性/定期）
        data/github-project-digest/daily/ + weekly/（仅数据输入）
```

## 4. 核心模块设计

### 4.1 接入层

- M1 以 **CLI**（Typer）为主，交互式对话 + 工具调用日志可视化。
- WebUI 参考 nanobot 的设计：聊天界面 + 工具调用/记忆可视化。
- 消息网关（微信/Telegram）M3 引入，参考 hermes-agent 的网关 + 会话恢复设计。

### 4.2 Agent 核心（pydantic-ai）

- **主对话 Agent**：意图路由，按需 handoff 到子 Agent；输出用 pydantic 模型定义 schema。
- **记忆工具 Agent**：读写 cognee 长期记忆（用户偏好、历史对话要点）。
- **数据查询 Agent**：调用项目知识库的查询工具，返回结构化结果。
- **任务执行 Agent**：执行白名单本地命令，关键操作需用户确认（HITL）。

### 4.3 项目知识库（数据层，核心）

- **独立存储**：本地 SQLite，`projects` 表字段：`repo`、`url`、`一句话定位`、`类型`（爆发型/实用型/潜力型/学习型/周精选）、`评分`、`来源`（daily 日期 / weekly 周次）、`亮点`、`技术栈`、`实时指标`、`风险`、`推荐理由`。
- **导入脚本**（如 `import_digests.py`）：解析 daily/weekly 的 Markdown → 写入 SQLite；按 `date+repo` 幂等去重，可重复执行；发现数据格式变化时只改这一处。
- **查询工具**（Agent 工具函数）：`search_projects(keyword, kind, date_range)`、`get_daily(date)`、`get_weekly(week)`、`latest_digest()`、`recommend(preferences)`。
- 数据只在导入时与发现文件交互，**运行期不读 repo-signal 目录**。

### 4.4 记忆层（cognee）

- 长期记忆：用户偏好、偏好演变（对应用户在问答/推荐中的反馈）。
- 可选：把项目知识库的关键字段索引进图谱，支持语义检索。
- 通过 MCP 暴露查询，Agent 无需直接操作存储。

### 4.5 执行与安全

- M1/M2：本地命令**白名单** + 关键操作人工确认，不引入沙箱。
- M3：引入 OpenSandbox 做不可信代码的安全执行。

### 4.6 评测与可观测（coze-loop）

- 会话日志、工具调用追踪（含 token 成本）。
- 以发现数据为 ground truth，定期评测知识问答准确率。

## 5. 关键流程

### 5.1 知识问答与项目推荐

1. 用户提问 → 主 Agent 意图识别。
2. handoff 数据查询 Agent → 项目知识库查询 → 结构化结果。
3. 记忆 Agent 结合历史偏好，输出个性化回答/推荐。

### 5.2 每日发现摘要（可选能力）

1. 定时触发 → Agent 读取知识库中最新一期数据 → 生成摘要。
2. 结合用户偏好标注感兴趣的项目，推送到助理自己的渠道（WebUI/消息网关）。
3. 与 repo-signal 的发布流程无关，数据只在导入时交互。

## 6. 数据设计

- 本地 SQLite：`conversations`、`messages`、`tool_calls`、`user_prefs`、`projects`；记忆图谱由 cognee 管理。
- 导入幂等：`(date, repo)` 唯一键，支持增量更新（新日报出现后重新导入）。
- 可选导出：`projects` 可导出 JSON，便于其他用途。

## 7. 部署

- 独立项目目录（与 repo-signal 分离），Python 3.11+，uv 管理依赖。
- macOS 本地：launchd 常驻服务 + 定时导入/定时摘要（助理自己的 plist，与 repo-signal 的自动提交无关）。
- 模型：OpenAI 兼容 API（默认 DeepSeek），预留多模型路由（参考 nanobot 的模型路由思路）。

## 8. 里程碑

| 阶段 | 范围 | 周期 |
|---|---|---|
| M1（MVP） | CLI + 主 Agent + cognee 记忆 + 导入脚本 + 项目知识库问答 | 2 周 |
| M2 | WebUI + 偏好推荐 + 每日发现摘要 | 2 周 |
| M3 | 消息网关 + OpenSandbox 沙箱 + coze-loop 评测 | 2 周 |

开发流程按 spec-kit：需求 → 计划 → 任务 → 实现。

## 9. 风险与对策

| 风险 | 对策 |
|---|---|
| 发现数据格式变化 | 解析逻辑集中在导入脚本，用样例测试锁定 |
| 知识库数据陈旧 | 定时/手动重新导入增量 |
| 记忆膨胀/检索噪声 | cognee 图谱压缩、定期归档、检索上限 |
| 模型成本 | 默认 DeepSeek，常用查询缓存 |
| 本地命令执行风险 | 白名单 + HITL 确认，M3 起沙箱隔离 |

## 10. 待确认项（当前默认值）

| 项 | 默认值 | 可调整 |
|---|---|---|
| 模型供应商 | DeepSeek（OpenAI 兼容） | 可换 OpenAI/Anthropic/本地 |
| 消息渠道 | M1 仅 CLI | 渠道选型在 M3 前定 |
| 沙箱 | M1/M2 不引入，白名单命令 | 需要执行不可信代码时提前 |
| 评测深度 | 先日志追踪，后补 evals | 视使用频率 |
| 部署位置 | 本地 macOS（launchd，独立于 repo-signal） | 如需云部署再评估 |
| 知识库更新 | 手动导入优先，后加定时 | 视数据更新频率 |
