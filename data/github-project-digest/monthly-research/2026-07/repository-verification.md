# 2026-07 仓库核实与运行记录

> 核实日期：2026-07-20。Stars/Forks 是核实时页面快照，会变化。除明确写为运行结果的内容外，能力描述来自官方仓库或官方文档，属于 L0。

## 运行环境与安全边界

- 临时目录位于 `/tmp`，没有改动项目依赖或用户配置。
- 不禁用 TLS 校验，不写入凭据，不输出提示词、代码或原始会话。
- Python 包安装同时尝试配置镜像和官方 PyPI，均因本机证书链 `CERTIFICATE_VERIFY_FAILED`/TLS EOF 失败。这是环境阻塞，不是项目安装失败。
- Docker daemon 因本机 socket 权限不可用；没有提升权限绕过。

## 深度候选

### alibaba/zvec

- 事实：Apache-2.0；未归档；核实时约 15.2k Stars / 956 Forks；v0.6.0 于 2026-07-20 发布。
- 用途与入口：进程内向量数据库，支持向量、全文和混合检索；官方提供 Python、Node.js、Go、Rust、Dart 入口。
- 接口与数据：SDK 接收集合 schema、记录和查询向量，返回匹配 id 与 score；数据可本地持久化，不需要远程认证。
- 运行：通过 npm 安装 `@zvec/zvec`，按官方 Node 最小示例写入两条记录并查询，得到有序 id/score 结果。等级 L2。
- 限制：未做大数据量、并发、崩溃恢复或商用工作负载验证。
- 来源：[GitHub](https://github.com/alibaba/zvec)。

### pydantic/pydantic-ai

- 事实：MIT；未归档；约 18.7k Stars / 2.4k Forks；v2.12.0 于 2026-07-17 发布。
- 用途与入口：Python Agent 框架，官方文档覆盖结构化输出、工具、评测和 OpenTelemetry/Logfire 可观测性。
- 接口与数据：Python API 接收模型、依赖、提示与工具，输出类型化结果；模型认证和外部存储随 provider/集成变化。
- 运行：PyPI 安装被本机 TLS 证书链阻断，未通过 L1；保守记录为 L0。
- 限制：未核实真实 provider 调用；接口仍快速演进。
- 来源：[GitHub](https://github.com/pydantic/pydantic-ai)、[官方文档](https://ai.pydantic.dev/)。

### getagentseal/codeburn

- 事实：MIT；未归档；约 8.8k Stars / 687 Forks；Desktop 0.9.17 于 2026-07-17 发布。
- 用途与入口：从本地 AI 编程工具会话统计 token、成本、模型与项目；CLI 支持 `report/status/export --format json`，并提供 MCP 与预览版团队同步。
- 接口与数据：读取本地支持工具的会话文件；JSON 可供下游处理。官方说明 sync 发送 token、成本、模型、项目，不发送提示词或代码；团队 sync 需要 OIDC，协议仍可能变化。
- 运行：npm 安装和 `--help` 成功；`doctor --provider codex --json` 发现 202 个会话并仅抽样解析 8 个，8 个成功、0 个失败。输出只保留数量与状态，没有保存会话正文。等级 L2（核心解析健康检查）。
- 限制：没有运行团队 sync；跨用户权限、项目名治理和协议稳定性仍未验证。
- 来源：[GitHub](https://github.com/getagentseal/codeburn)。

### langchain4j/langchain4j

- 事实：Apache-2.0；未归档；约 12.6k Stars / 2.4k Forks；1.18.0 / beta28 于 2026-07-17 发布。
- 用途与入口：Java/ JVM 的模型、RAG、工具调用、Agent 与集成抽象；通过 Maven/Gradle 模块接入。
- 接口与数据：Java API 接收消息、工具与检索数据，输出模型响应或类型化服务结果；认证与存储取决于所选 provider。
- 运行：本机没有 Java，未进行 Maven 最小示例，等级 L0。
- 限制：集成面广，模块选择、版本兼容与生产约束需由采用团队验证。
- 来源：[GitHub](https://github.com/langchain4j/langchain4j)、[官方文档](https://docs.langchain4j.dev/)。

### bytedance/deer-flow

- 事实：MIT；未归档；约 77.4k Stars / 10.5k Forks；2.0.0 于 2026-06-25 发布，仓库在 2026-07-20 仍有更新。官方说明 2.0 是 ground-up rewrite。
- 用途与入口：面向研究、编码和内容生成的可扩展 Agent harness；依赖模型与沙箱/工具配置。
- 接口与数据：接收任务，经规划、工具和子代理处理后输出报告或工件；认证和外部服务依赖配置。
- 运行：未在本轮拉起完整服务，等级 L0。
- 限制：2.0 重写后的兼容性、长链路成本、失败恢复和权限边界未实测。
- 来源：[GitHub](https://github.com/bytedance/deer-flow)。

### egonex-ai/understand-anything

- 事实：MIT；未归档；约 75.3k Stars / 6.3k Forks；v2.9.0 于 2026-07-10 发布。
- 用途与入口：把代码库分析为可交互知识图谱；官方安装说明覆盖 Codex 等多种编码代理。
- 输入/输出：输入本地代码库，输出知识图谱及交互查看入口。
- 运行：本轮没有对真实代码库执行，等级 L0。
- 限制：大型、多语言或生成代码仓库的图谱质量未验证。
- 来源：[GitHub](https://github.com/egonex-ai/understand-anything)。

### earendil-works/pi

- 事实：MIT；未归档；约 73k Stars / 9k Forks；v0.80.10 于 2026-07-16 发布，累计约 247 个 release。
- 用途与入口：高度可扩展的终端编码 Agent/工具包；通过包管理器安装后由 CLI 工作。
- 输入/输出：读取用户任务与获准的工作区/工具上下文，输出修改和终端结果；模型认证由 provider 配置承担。
- 运行：本轮未安装，等级 L0。
- 限制：扩展自由度高，团队安全策略、评测与共享工作流仍需自行建立。
- 来源：[GitHub](https://github.com/earendil-works/pi)。

### microsoft/skillopt

- 事实：MIT；未归档；约 13.2k Stars / 1.2k Forks；v0.2.0 于 2026-07-02 发布。
- 用途与入口：用评测反馈优化 Agent skill，官方输出为约 300–2000 tokens 的 `best_skill.md`。
- 输入/输出：输入初始 skill、任务/评测配置，输出优化后的 Markdown skill；模型调用需要相应认证。
- 运行：本轮未运行，等级 L0。README 中基准提升只记录为作者声明，不作为独立采用证据。
- 限制：对真实业务任务的迁移性与优化成本未验证。
- 来源：[GitHub](https://github.com/microsoft/skillopt)。

### mempalace/mempalace

- 事实：MIT；未归档；约 57.5k Stars / 7.4k Forks；v3.6.0 于 2026-07-17 发布；默认分支为 `develop`。
- 用途与入口：为 Agent 提供可持久化记忆能力。
- 运行：本轮未安装，等级 L0。
- 限制：记忆正确性、删除/隔离语义、默认分支与稳定发布关系需要进一步运行核实。
- 来源：[GitHub](https://github.com/mempalace/mempalace)。

### nexu-io/open-design

- 事实：Apache-2.0；未归档；约 79.8k Stars / 9.2k Forks；官方 README 指向 0.13.0。
- 用途与入口：local-first 桌面应用、CLI 与 MCP server，把编码 Agent 用作设计引擎；官方列出 `od mcp install <agent>` 接入方式，并支持 HTML/PDF/PPTX/MP4 等工件输出。
- 运行：本轮未安装桌面应用或 MCP，等级 L0。
- 限制：能力面和依赖面很大，BYOK、桌面守护进程、外部模型及媒体导出的安全/稳定边界未实测。
- 来源：[GitHub](https://github.com/nexu-io/open-design)。

### strukto-ai/mirage

- 事实：Apache-2.0；未归档；约 3.3k Stars / 242 Forks；Mirage 0.0.3 于 2026-06-30 发布，共 3 个 release。
- 用途与入口：为 Agent 把 S3、Google Drive、Slack、Gmail、Redis 等数据源挂载为统一虚拟文件系统；TypeScript/Python 包和 Workspace API 是主要入口。
- 输入/输出：后端连接器凭据与路径映射进入 Workspace，Agent 通过文件/命令语义读写；认证和数据驻留取决于各后端。
- 运行：本轮未配置外部数据源，等级 L0。
- 限制：采用证据和维护历史较短；跨 SaaS 凭据、写权限和路径语义需要逐连接器审计。
- 来源：[GitHub](https://github.com/strukto-ai/mirage)。

### VoltAgent/voltagent

- 事实：MIT；未归档；约 10.1k Stars / 1.1k Forks；`@voltagent/core@2.9.0` 于 2026-07-08 发布。
- 用途与入口：TypeScript Agent 框架与运行工具，通过 npm 包接入。
- 运行：本轮未安装，等级 L0。
- 限制：与通用 Agent 框架的功能重叠和生产差异未用真实任务验证。
- 来源：[GitHub](https://github.com/VoltAgent/voltagent)。

### agents-flex/agents-flex

- 事实：Apache-2.0；未归档；约 1k Stars / 135 Forks；v2.2.2 于 2026-07-16 发布，共 27 个 release。
- 用途与入口：Java 8+ 的模块化 AI 应用框架，Maven 依赖覆盖模型、RAG、MCP、Skills、Text2SQL 和子代理。
- 输入/输出：Java API 以 provider、prompt、tool/retrieval 配置为输入，返回同步或流式结果；认证/存储由模块决定。
- 运行：本机无 Java，未运行 Maven quickstart，等级 L0。
- 限制：独立采用证据较弱，且功能面与更成熟 JVM 框架重叠。
- 来源：[GitHub](https://github.com/agents-flex/agents-flex)。

### dietrichgebert/ponytail

- 事实：MIT；未归档；约 86k Stars / 4.7k Forks；v4.8.4 于 2026-06-29 发布，共 14 个 release。
- 用途与入口：以极简/YAGNI 原则约束开发代理的 skill/插件，可安装到多种编码代理；不是完整运行时。
- 输入/输出：输入任务上下文和 skill 指令，影响代理实现决策；输出仍由宿主代理产生。README 的代码量/成本/速度数字属于作者基准。
- 运行：本轮未做独立 A/B 验证，等级 L0。
- 限制：价值范围窄于产品或框架，公开效果数字不能当作独立采用证据。
- 来源：[GitHub](https://github.com/dietrichgebert/ponytail)。

### aprilnea/openlogi

- 2026-07-20 访问官方 GitHub 页面时持续返回内部错误；没有在不确定状态下补写许可证、发布和安装事实。
- 结论：未通过可访问性门槛，不参与 Top 5 冻结。

## 补充组件：duckdb/duckdb

- 事实：MIT；未归档；约 39.6k Stars / 3.4k Forks；v1.5.4 于 2026-06-17 发布，共 62 个 release。
- 用途与入口：进程内分析数据库，提供 CLI 和多语言客户端；官方 `read_json`/`COPY` 可把 JSON 导入表。
- 组合角色：仅用于 CodeBurn 聚合 JSON 的单文件存储与 SQL 查询，不负责解析编码工具会话。
- 运行：两次尝试下载官方 Node 包。沙箱内首次因 `registry.npmjs.org` DNS `ENOTFOUND` 失败；获准联网后重试超过两分钟仍无响应，主动终止以避免无界等待。没有禁用 TLS 或改 registry。等级 L0。
- 结论：接口在文档层面匹配，但 CodeBurn → DuckDB 的 L3 本轮没有跑通，不能写“已验证可行”。
- 来源：[GitHub](https://github.com/duckdb/duckdb)、[JSON 导入文档](https://duckdb.org/docs/stable/guides/file_formats/json_import)。

## 运行失败不等于产品失败

Python TLS、本机无 Java 和 Docker socket 权限是本轮环境限制。公开月报必须把这些项目写为“未运行/仅 L0”，不能写成“安装失败”或“不可用”。
