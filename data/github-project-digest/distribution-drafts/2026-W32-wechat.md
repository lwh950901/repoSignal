# 开源雷达周刊

![开源雷达周刊｜每周开源项目精选](/covers/repository-radar-weekly-subtitle.png)

本周的 10 个项目，前四项落在可以马上动手的日常工具上：PDF 解析、容器桌面、自托管笔记和邮件测试；其余项目则围绕代码审查、Agent 评测、隔离执行与安全研究展开。它们解决的问题都很具体，不需要先接受一套宏大的技术叙事。

这份清单也呈现出一个清晰方向：Agent 工程正在从“能调用工具”走向更严格的上下文选择、质量门禁、运行隔离和效果评测。与此同时，成熟的小工具依然最容易带来确定收益，适合先用真实数据和现有流程做一次低成本验证。

## 一、本地工具与日常基础设施

### 1. pdf-inspector：先判断 PDF，再决定是否调用 OCR

[pdf-inspector](https://github.com/firecrawl/pdf-inspector) 是一个纯 Rust 的 PDF 分类、文本抽取和 Markdown 转换库，同时提供 Python、Node.js、WASM 绑定与 CLI。它可以先区分文本型、扫描型、图像型或混合型 PDF，再决定哪些页面需要进入 OCR 流程。

**适合：** 正在搭建 RAG 文档预处理、报告抽取或 OCR 分流链路的开发者。

**为什么推荐：** 项目不仅有多语言入口，还公开了 200 份 PDF 的项目方实验、逐文档结果和基准工具；本周也有依赖升级与嵌套 PDF 拒绝服务风险修复，便于同时观察解析设计和安全响应。

**注意：** 它本身不执行 OCR，扫描件仍要交给外部工具。项目方基准不能替代自有语料验证，复杂字体、多栏、表格、恶意文件和超大文件都应在隔离环境中复测；目前没有正式 Release，生产使用宜固定提交或包版本。

### 2. Podman Desktop：把容器与 Kubernetes 工作流放进桌面端

[Podman Desktop](https://github.com/podman-desktop/podman-desktop) 是跨平台容器桌面应用，可用于安装、配置和管理 Podman、镜像、Pod、卷、注册表及 Kubernetes 上下文，并提供扩展机制。

**适合：** 希望用图形界面管理本地容器环境，或正在评估 Docker Desktop 兼容工作流的开发团队。

**为什么推荐：** 项目已有稳定发布节奏，README、独立文档、路线图、贡献指南和采用者清单齐全；仓库还配置了 Playwright、CodeQL、Codecov 与 OpenSSF Scorecard 等质量和供应链检查。

**注意：** 桌面应用、虚拟机、容器引擎与 Kubernetes 叠加后，网络、卷、权限、代理和证书行为都会受操作系统影响。企业落地前应先验证注册表策略、代理链路和多引擎兼容性。

### 3. Memos：轻量、自托管的快速记录系统

[Memos](https://github.com/usememos/memos) 是 Markdown 原生的自托管笔记应用，可用 Go 二进制或 Docker 部署，支持 SQLite、MySQL、PostgreSQL，并提供 REST 与 gRPC API。

**适合：** 想建立个人知识记录空间，或需要把轻量笔记后端接入小团队工作流的用户。

**为什么推荐：** 它的部署、迁移和集成入口较完整，既能直接作为应用使用，也适合阅读 Go 服务、数据库抽象、API 与前端之间的组织方式。本周报告记录的最新明确版本为 v0.30.0。

**注意：** 公开部署仍需自行配置访问控制、TLS、附件与数据库备份，并实际演练恢复。项目处于 v0.x，升级前要固定镜像版本、阅读迁移说明，不能把默认 Docker 参数当作生产安全配置。

### 4. Mailpit：给开发和 CI 准备的邮件捕获器

[Mailpit](https://github.com/axllent/mailpit) 提供低资源 SMTP 捕获服务、邮件 Web UI 和 REST API，用于检查邮件模板、调试 MIME 与附件，以及编写自动化集成测试。它可以通过 Go 单二进制或多架构 Docker 镜像部署。

**适合：** 需要在本地或 CI 中验证注册、通知、找回密码等邮件流程的开发团队。

**为什么推荐：** 功能边界小而完整，部署和自动化接口明确。v1.30.6 包含安全与协议处理修复，并增加 POP3 登录保护和 CORS 测试，近期多个版本也持续处理安全问题。

**注意：** 默认 Web UI 和 SMTP 监听在 `0.0.0.0`。接受任意认证、启用链接检查或直接暴露公网都会扩大攻击面；共享环境至少应限制监听地址，并配置认证、TLS 和网络访问控制。

## 二、代码质量与 Agent 工程

### 5. code-review-graph：用代码关系图缩小审查上下文

[code-review-graph](https://github.com/tirth8205/code-review-graph) 为代码库构建持久化关系图，再通过 MCP、CLI 和 GitHub Action 返回与变更影响相关的审查上下文。它支持增量更新和 blast-radius 分析，目标是减少 Agent 在大型仓库中盲目读取文件。

**适合：** 维护中大型代码库、正在评估 AI 代码审查，或希望研究结构化代码上下文的团队。

**为什么推荐：** 项目把 Tree-sitter 解析、关系图、影响分析、评测和多种工具接入放在同一条链路中，并提供 tests、CI、SECURITY.md 与可复现评测材料。v2.3.7 还记录了多语言、MCP 并发和安全处理改进。

**注意：** 上下文缩减和 recall 数字来自项目方评测，不是对所有仓库的保证；小变更未必值得建图。接入远程 Embedding 前，还要确认代码数据的驻留与脱敏边界。

### 6. Fallow：把代码健康检查变成可消费的变更门禁

[Fallow](https://github.com/fallow-rs/fallow) 是用 Rust 编写的 TypeScript、JavaScript 代码库健康工具，提供单二进制、npm 包、GitHub Action、MCP，以及 JSON、SARIF 等输出。它的 `audit` 模式可以只阻断新增问题。

**适合：** 想把静态检查接入 CI、PR 门禁或 Agent 工作流的 TypeScript、JavaScript 团队。

**为什么推荐：** 稳定 JSON 合约、退出码和 changed-file gate 让它便于自动化消费；仓库还包含 tests、fuzz、benchmarks、SECURITY.md 和 Docker 示例。本周发布的 v3.14.0 带验证签名。

**注意：** 框架约定、生成代码和缺失入口可能造成误报，type-aware 模式也不能替代 `tsc` 或完整测试。可选的 Fallow Runtime 属于付费能力，评估时要区分开源核心与商业层。

### 7. CozeLoop：把 Prompt、评测、Trace 和监控串起来

[CozeLoop](https://github.com/coze-dev/coze-loop) 是面向 AI Agent 团队的 AgentOps 平台，覆盖 Prompt Playground、评测数据集、评测器、实验、Trace 与监控，可通过 Docker Compose 或 Helm 部署。

**适合：** 已经在开发 Agent，但缺少统一提示词管理、效果评测和运行观测的团队。

**为什么推荐：** 它把 Prompt 开发、实验和观测放进一个完整平台，Wiki 也覆盖架构、启动、二次开发、测试和排障。近期提交处理了评测超时、异步记录可见性与沙箱回收等实际运维问题。

**注意：** MySQL、Redis、ClickHouse 等依赖让部署面明显大于轻量 SDK；公网使用还需检查注册、SSRF、横向越权、模型密钥和数据隔离。最新正式 Release 仍是 2026 年 1 月的 v1.5.1，不能把主分支近期变化直接视为稳定版本。

## 三、隔离、安全与学习路径

### 8. Microsandbox：用 microVM 隔离不可信代码

[Microsandbox](https://github.com/superradcompany/microsandbox) 提供本地优先的 microVM 运行时、CLI、SDK 与 MCP、Skills 接入，可用于隔离 Agent、插件、CI 和自动化任务中的不可信代码，支持 Rust、Python、TypeScript 和 Go 调用。

**适合：** 需要为代码执行增加隔离层，或想拆解 microVM 生命周期与跨语言 SDK 设计的开发者。

**为什么推荐：** Rust 核心、多个 SDK、示例、文档、安全材料和多平台发布资产形成了完整的学习路径；最新明确版本为 v0.6.8。

**注意：** 本地 microVM 不自动等于多租户生产级隔离。网络、镜像、权限、虚拟化能力和镜像供应链都要按自身威胁模型测试；项目仍标注为 beta，0.x API 可能出现破坏性变化。

### 9. ADR：从遥测到检测的 Agent 安全研究样本

[ADR](https://github.com/uber/ADR) 面向 Agent 安全研究与防御工程，包含 Agent 遥测 Sensor、ADR-Bench 安全基准和双层威胁检测器，并提供 Python 代码、评测脚本、合成 fixture、论文及复现实验文档。

**适合：** 正在研究 Agent 攻击检测、遥测协议或内部安全评测的团队。

**为什么推荐：** 项目将 Sensor、Detection 与 benchmark 分层组织，覆盖 300 多个任务、133 个 MCP server 和 17 类攻击技术；README 明确称 ADR 已在 Uber 生产部署，同时给出了可复现实验流程和 Sensor v1.0.0 Release。

**注意：** 这不是可以直接照搬的完整生产防线。开源版不包含 Prevention 和离线 ADR Explorer，benchmark 含合成环境，双 Agent 检测还依赖模型与 API 成本；项目方生产部署说明也不等于对其他组织环境的独立验证。

### 10. learn-claude-code：逐章拆解 Agent harness

[learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 是内容型可执行教程，不是生产 Agent 框架。它用 20 个章节和独立代码讲解 Agent 循环、工具、上下文压缩、子代理、团队、MCP、worktree 与权限机制。

**适合：** 想从最小循环开始理解 Agent harness，或需要一条可逐章实验学习路线的开发者。

**为什么推荐：** `s01` 到 `s20` 的章节结构把叙事、代码、图示和测试分开，并提供中英日文说明及可执行入口，便于对照观察每一步新增的机制与复杂度。

**注意：** 教程实现为了可读性刻意简化，不具备完整的模型路由、密钥管理、并发限流、沙箱、审计和回滚能力；项目也没有正式 Release，API 变化可能让部分章节失效，不能直接复制为生产系统。

## 本周优先试用

如果只安排一次短试用，可以按当前问题选择：文档管线先用 pdf-inspector 跑一组真实 PDF；邮件流程先用 Mailpit 在隔离的本地或 CI 环境捕获一轮邮件；Agent 安全研究则从 ADR 的离线 benchmark 或 microsandbox 的无敏感数据示例开始。先验证最小链路，再决定是否进入团队基础设施。

完整周报记录了这 10 个项目的维护证据、版本口径、许可证、风险与上手建议。

**阅读全文：** [2026-W32 完整周报](/weekly/2026-W32/)

这 10 个项目里，你更想先看哪一个的真实试用记录，或者你正在解决的工程问题更接近哪一类？

---

**关于仓库雷达**

仓库雷达持续整理值得使用、学习和二次开发的开源项目。日报负责发现，周报负责筛选，也会尽量把风险和低成本试法说清楚。
