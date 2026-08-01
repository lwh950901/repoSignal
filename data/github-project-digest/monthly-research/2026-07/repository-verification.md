# 2026-07 仓库核实

> 月末补跑核实日期：2026-08-01。公开指标来自 GitHub 仓库页约数；release 日期来自官方 Releases。未认证 API 返回 403 后没有补造精确值。

## 验证等级

- L0：仓库、许可证、维护状态、安装入口与官方文档已检查。
- L1：安装并启动最小命令。
- L2：官方最小流程产生预期输出。
- L3：两个或以上仓库完成最小数据连接。
- L4：真实数据完成业务任务。

## Top 5

### ChromeDevTools/chrome-devtools-mcp

- 事实：Apache-2.0；未归档；约 48.3k Stars / 3.3k Forks；v1.5.0（2026-07-03）与 v1.6.0（2026-07-14）均为 7 月正式发布。
- 用途与入口：Node.js MCP server，把 console、network、screenshot、performance trace 与 heap snapshot 暴露给 coding agent；官方提供插件和 `npx` 接入方式。
- 输入/输出：输入 MCP 工具调用与获准的 Chrome 页面，输出浏览器事实、截图、trace 或 heap 数据。
- 认证/存储/外部依赖：需要本机 Chrome/Chrome for Testing；连接现有浏览器或远程调试端口时必须隔离敏感 profile；可关闭 usage statistics、CrUX 与更新检查。
- 运行：npm CLI 仍无输出；改从官方 npm tarball 锁定 v1.6.0，在 Node 24 与隔离无头 Chrome 中完成 JSON-RPC 初始化、`navigate`、`evaluate` 和 `screenshot`。只访问回环地址的合成邮件页面，关闭 usage statistics、CrUX 和 Chrome 后台联网，等级 L2。
- 限制：MCP 客户端可读取或操作页面；性能和 heap 工具会产生较大工件；只验证了合成的本地页面，未验证真实 profile 或非 Chrome Chromium 兼容。
- 来源：[GitHub](https://github.com/ChromeDevTools/chrome-devtools-mcp)、[Releases](https://github.com/ChromeDevTools/chrome-devtools-mcp/releases)。

### heygen-com/hyperframes

- 事实：Apache-2.0；未归档；约 39.0k Stars / 3.7k Forks；v0.7.87 于 2026-07-31 发布。
- 用途与入口：用 HTML/CSS 和可寻址动画定义视频，通过 CLI、Puppeteer 与 FFmpeg 预览和渲染；提供 Studio、player、producer 与 AWS Lambda 包。
- 输入/输出：输入 HTML、CSS、媒体与时间线配置，输出预览或视频文件；云渲染还涉及对象存储和 Lambda。
- 认证/存储/外部依赖：本地依赖浏览器、FFmpeg、字体和媒体资产；完整开发克隆的黄金视频基线约 240 MB，需要 Git LFS。
- 运行：本轮未拉取媒体依赖或渲染样例，等级 L0。
- 限制：0.x 高频发布；浏览器/字体/媒体差异会影响可复现性。README 称在 HeyGen 生产使用，仍按作者来源记录。
- 来源：[GitHub](https://github.com/heygen-com/hyperframes)、[Releases](https://github.com/heygen-com/hyperframes/releases)。

### alibaba/open-code-review

- 事实：Apache-2.0；未归档；约 17.0k Stars / 1.2k Forks；v1.8.3 于 2026-07-31 发布。
- 用途与入口：Go/Node CLI 用确定性文件选择、规则匹配和定位约束 LLM Agent，可扫描 Git diff、提交或完整文件，并接入 CI、VS Code、MCP 和 coding-agent skill。
- 输入/输出：输入 Git diff/文件、规则与模型配置，输出结构化行级审查评论和 session 记录。
- 认证/存储/外部依赖：Git 2.41+；默认模式需要模型 endpoint/API key，delegation mode 可由宿主 agent 执行。
- 运行：本轮未配置模型凭据或运行真实审查，等级 L0。
- 限制：作者公开的大规模内部采用与 benchmark 不能替代独立复现；提示注入、误报和低召回需要实际 PR 基线。
- 来源：[GitHub](https://github.com/alibaba/open-code-review)、[Releases](https://github.com/alibaba/open-code-review/releases)、[官方文档](https://open-codereview.ai/docs)。

### hyperdxio/hyperdx

- 事实：MIT；未归档；约 9.8k Stars / 441 Forks；`@hyperdx/otel-collector@2.32.0` 于 2026-07-27 发布。
- 用途与入口：基于 ClickHouse 与 OpenTelemetry 统一 logs、metrics、traces、errors 和 session replay；支持 Docker Compose、自托管与多语言 SDK。
- 输入/输出：接收 OTLP/SDK telemetry，写入 ClickHouse 并输出查询、告警、回放和 dashboard。
- 认证/存储/外部依赖：需要 ClickHouse、collector、保留策略和权限；开源部署默认收集匿名 usage data，可通过 `USAGE_STATS_ENABLED=false` 关闭。
- 运行：本轮未拉起 ClickHouse/collector，等级 L0。
- 限制：数据量、session replay PII、存储成本和升级恢复均需生产前验证。
- 来源：[GitHub](https://github.com/hyperdxio/hyperdx)、[Releases](https://github.com/hyperdxio/hyperdx/releases)。

### cvat-ai/cvat

- 事实：CVAT Community 为 MIT；未归档；约 16.4k Stars / 3.8k Forks；v2.72.0 于 2026-07-29 发布。
- 用途与入口：图像、视频与 3D 标注平台，提供 Web UI、Python SDK、CLI、REST API、Docker 和 Kubernetes/Helm 路径。
- 输入/输出：输入媒体、任务与标签 schema，输出多种标注格式和质量/协作数据。
- 认证/存储/外部依赖：服务端依赖数据库、队列、对象存储与可选 serverless；`/serverless` 可能引用单独许可证资产，FFmpeg 还有 LGPL/GPL 边界。
- 运行：本轮未部署完整服务，等级 L0。
- 限制：开放 Issue 多、部署面大；升级、备份、多人质检和第三方模型资产需要逐项检查。
- 来源：[GitHub](https://github.com/cvat-ai/cvat)、[Releases](https://github.com/cvat-ai/cvat/releases)、[官方文档](https://docs.cvat.ai/)。

## 其余深度候选

| 仓库 | 许可证 | 7 月证据与接口 | 验证 | 主要限制 | 来源 |
|---|---|---|---|---|---|
| chatwoot/chatwoot | MIT（企业目录另算） | v4.16.2 于 7 月 27 日发布；Web/API/多渠道客服，自托管依赖 Rails、PostgreSQL、Redis 和渠道凭据 | L0 | 运维面和开放 Issue 规模大 | [GitHub](https://github.com/chatwoot/chatwoot)、[Releases](https://github.com/chatwoot/chatwoot/releases) |
| openai/openai-agents-python | MIT | Python 3.10+ SDK，工具、handoff、guardrails、sessions、tracing、voice；v0.18.3 于 7 月 17 日发布，8 月 1 日 v0.19.2 不计月内变化 | L0 | provider 凭据、费用、版本演进 | [GitHub](https://github.com/openai/openai-agents-python)、[Releases](https://github.com/openai/openai-agents-python/releases) |
| alibaba/zvec | Apache-2.0 | v0.6.0 于 7 月 20 日发布；Python/Node/Go/Rust/Dart 进程内向量检索 | L2（7 月 20 日 Node 最小例产生有序 id/score） | 大数据量、并发、恢复与升级未测 | [GitHub](https://github.com/alibaba/zvec)、[Releases](https://github.com/alibaba/zvec/releases) |
| topoteretes/cognee | Apache-2.0 | Agent memory、知识图谱、MCP、自托管；月末仓库与周报显示持续发布/维护 | L0 | 删除语义、召回和多后端复杂度 | [GitHub](https://github.com/topoteretes/cognee) |
| pydantic/pydantic-ai | MIT | 类型化 Agent、eval、MCP、OTel；7 月 release 活跃 | L0 | 本轮未安装，快速升级成本 | [GitHub](https://github.com/pydantic/pydantic-ai)、[文档](https://ai.pydantic.dev/) |
| ModelEngine-Group/nexent | MIT | 零代码 Agent 平台，Docker/Kubernetes/Helm、工具、记忆与控制面；v2.2.1 在 7 月核实 | L0 | 功能面宽、默认开发分支与治理成本 | [GitHub](https://github.com/ModelEngine-Group/nexent) |
| different-ai/openwork | MIT 主体；企业目录另查 | Electron 工作台、远程 MCP 和团队控制面；7 月 Alpha 高频发布 | L0 | keychain、远程权限、企业目录边界 | [GitHub](https://github.com/different-ai/openwork) |
| getagentseal/codeburn | MIT | 本地解析多种 AI coding 工具，输出聚合 JSON；7 月 20 日 npm/CLI/受限 provider 健康检查成功 | L2（既有安全验证） | schema 漂移、身份与隐私治理；本轮临时下载无输出 | [GitHub](https://github.com/getagentseal/codeburn) |
| langchain4j/langchain4j | Apache-2.0 | JVM 模型、RAG、tools/MCP 与主流 Java 框架集成；7 月 release 活跃 | L0 | 本机无 Java；版本与模块面广 | [GitHub](https://github.com/langchain4j/langchain4j)、[文档](https://docs.langchain4j.dev/) |
| bytedance/deer-flow | MIT | 长任务 Agent harness，含 sandbox、memory、tools、skills、subagents；7 月持续有效提交 | L0 | 权限、成本、恢复与 2.0 重写边界 | [GitHub](https://github.com/bytedance/deer-flow) |

## 业务组合补充组件

### duckdb/duckdb

- 事实：MIT；未归档；官方文档支持 `read_json`/`COPY` 导入 JSON。
- 职责：只负责 CodeBurn 聚合 JSON 的单文件分析存储和 SQL 查询，不解析编码工具会话。
- 输入/输出：输入经过 allowlist 和身份剥离的 JSON，输出固定 SQL 汇总表。
- 运行：2026-07-20 Node 包下载实验未完成；2026-08-01 再次以临时 npm 下载尝试 CodeBurn 前置，持续无输出后主动终止，没有关闭 TLS、切换镜像或读取真实会话。等级 L0，组合仍未达到 L3。
- 来源：[GitHub](https://github.com/duckdb/duckdb)、[JSON 导入文档](https://duckdb.org/docs/stable/guides/file_formats/json_import)。

### axllent/mailpit

- 事实：MIT；未归档；7 月 31 日候选账本记录约 10.0k Stars / 317 Forks；v1.30.4、v1.30.5、v1.30.6 均在 7 月发布并包含安全修复。
- 职责：捕获应用发往本地 SMTP 的测试邮件，提供 Web UI、REST API、HTML/link 检查和邮件 HTML 预览，不负责浏览器操作。
- 输入/输出：输入 SMTP 或 Send API 邮件；输出消息元数据、HTML/text、附件、标签和检查结果。
- 运行：官方 v1.30.6 macOS arm64 静态二进制绑定回环地址；Python 标准库发送一封固定内容的合成邮件，REST API 返回正确收件人、主题、标签和摘要，等级 L2。
- 限制：官方截图只能在 Web UI 触发，不能通过 API 自动化；允许内部 HTTP 请求会扩大 SSRF 风险，本轮没有开启；不模拟 Gmail/Outlook 等客户端渲染。
- 来源：[GitHub](https://github.com/axllent/mailpit)、[Releases](https://github.com/axllent/mailpit/releases)、[集成测试](https://mailpit.axllent.org/docs/integration/)、[HTML 截图](https://mailpit.axllent.org/docs/usage/html-screenshots/)。

## 组合验证补记

2026-08-01 使用完全合成的重置密码邮件完成 `应用 SMTP 输出 → Mailpit → /view/latest.html → Chrome DevTools MCP` 连接。Chrome DevTools MCP 通过 MCP 协议读到标题 `Reset password`、固定 `.invalid` 测试身份和回环链接，并在系统临时目录生成截图；两个仓库均先达到 L2，组合达到 L3。未点击真实业务链接、未读取真实邮箱、未使用凭据，结果不等同于跨邮件客户端兼容或真实团队 L4。

## 环境失败边界

GitHub 未认证 API 403、Python TLS 证书链错误、npm CLI 无输出、本机 Docker 未启动、本机无 Java，以及未配置模型/云凭据都是本轮环境或安全边界。可由官方静态包和回环地址安全绕开的部分已单独记录；其余只限制验证等级，不被写成项目不可用。
