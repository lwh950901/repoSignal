# 业务调查：跨工具 AI 编程用量与成本台账

> 状态：通过发布门槛，L3 未完成；核实日期 2026-07-20。

## 摘要

- 形态：企业内部工具。
- 首要市场与用户：全球软件团队中，同时试用两种以上 AI 编程工具的平台工程或研发效能负责人。
- 需求状态：有需求信号。两家独立商业厂商都提供组织级采用/用量指标，但“跨厂商统一台账”仍是由这些事实推导出的缺口，未取得付费访谈。
- 本月核心仓库：`getagentseal/codeburn`。
- 补充组件：`duckdb/duckdb`（不要求来自 2026-07 候选）。
- 当前最高验证：CodeBurn L2；组合 L3 已尝试但受依赖下载阻塞。
- 当前组合结论：部分可行。
- 当前业务判断：值得做技术实验，不等于已确认商业市场。

## 真实问题与证据

目标用户需要回答“哪些团队在用、用了什么模型、token/成本如何变化、不同工具的口径如何对齐”。当前事实证据是：

1. GitHub 为企业/组织管理员、billing manager 等角色提供 Copilot usage dashboard、API 和 NDJSON 导出，指标包括活跃用户、采纳、模型、代码生成与 PR 生命周期；团队级指标还需要把用户—团队报告与用户使用报告做 join。这证明组织级采用度量和自定义 BI 是官方支持的实际管理流程。
2. Google Cloud 为 Gemini Code Assist 提供组织级 Cloud Monitoring 指标，包括活跃用户、建议/接受、token 与 API 调用；官方同时说明记录范围受产品 surface 限制。这独立证明另一家厂商也把组织用量监控作为管理能力，并显示厂商数据天然按自己的产品边界分割。

证据没有证明所有企业都会同时采购多种工具，也没有证明它们愿意为统一台账付费，因此只标“有需求信号”，不标“已确认需求”。

## 市场与现有方案

| 方案 | 类型/服务对象 | 能力与部署 | 公开价格 | 采用证据 | 对本假设的限制 |
|---|---|---|---|---|---|
| GitHub Copilot usage metrics | 商业产品；Copilot 企业/组织管理员 | GitHub 托管 dashboard、REST API、NDJSON 导出 | 指标功能单独价格未知 | 官方企业功能和管理员权限模型 | 只覆盖 Copilot 定义的 surfaces；跨工具需另建数据层 |
| Gemini Code Assist monitoring | 商业产品；Google Cloud 管理员 | Cloud Monitoring dashboard、日志与自定义指标 | 指标功能单独价格未知 | 官方组织监控文档和 IAM 角色 | 主要覆盖 Gemini Code Assist，部分指标仅 IDE 交互 |
| OpenLIT | 开源/可自托管；AI 应用工程团队 | Apache-2.0；OTel SDK/Collector/ClickHouse 与 dashboard | 开源部署成本未知 | 官方仓库约 2.5k Stars、273 releases，支持 50+ provider/框架 | 重点是应用运行时 LLM 可观测性，不直接解析本地编码代理会话 |
| 厂商导出 + 表格/自建 BI | 现实流程；研发效能团队 | 定期下载 NDJSON/Cloud Monitoring 数据，join 后做图表 | 人力与基础设施成本未知 | GitHub 官方明确支持 NDJSON 供 custom BI/long-term storage | 口径、身份映射、刷新与权限由团队自行维护 |

尚未找到可信来源证明现有跨工具产品的收入、客户数或市场规模，因此全部记为未知。

## 产品定义

第一版是一个内部“聚合台账”，而不是员工绩效评分系统：

1. 每位自愿加入试点的开发者在本机运行 CodeBurn，仅产生聚合 JSON。
2. 一个明确审计过的适配器删除/哈希项目身份，只保留日期、provider、model、token、估算成本与 session 计数。
3. 适配器把记录导入本地 DuckDB；负责人用固定 SQL 查看团队汇总和数据完整性。
4. 输出只用于工具预算和试点采用判断，不用于个人排名。

非目标：读取或上传提示词/代码；声称 token 数等于开发效率；首版直接接入所有厂商管理员 API；预测 ROI。

## 仓库组合

| 仓库 | 身份 | 职责 | 许可证 | 接口与输入/输出 | 验证 |
|---|---|---|---|---|---|
| `getagentseal/codeburn` | 本月核心 | 解析 Codex、Claude Code、Cursor 等本地会话，计算聚合用量 | MIT | CLI 读取本地会话；`status/report/export --format json` 输出结构化 JSON | L2：npm 安装、CLI 与受限 provider 健康检查成功 |
| `duckdb/duckdb` | 补充组件 | 单文件分析存储与 SQL 聚合 | MIT | `read_json`/`COPY` 导入 JSON，SQL 输出汇总表 | L0；Node L3 实验受网络阻塞 |

两者不重叠：CodeBurn 负责理解不同编码工具的本地数据，DuckDB 负责持久化、跨日期查询和团队聚合。CodeBurn 没有官方“直接写 DuckDB”连接器，因此组合依赖一个小型、必须自研且审计的数据适配器。

## L3 组合实验

- 计划：运行 CodeBurn 的轻量 `status --format json` 生成聚合数据，不显示或保存提示词/代码；用 DuckDB Node 客户端 `read_json` 导入并查询字段。
- 已完成前置：CodeBurn npm 安装、CLI 启动和受限 provider 解析健康检查达到 L2；DuckDB 官方文档确认 JSON 导入接口。
- 阻塞：沙箱内 npm 下载首先因 `registry.npmjs.org` DNS `ENOTFOUND` 失败；获准联网重试后超过两分钟仍没有数据或错误输出，主动终止。没有关闭 TLS 校验、替换不可信镜像或提升本机 Docker socket 权限。
- 结果：没有产生 DuckDB 查询结果，组合不得标为 L3。当前结论维持“部分可行”。
- 继续所需：在能正常取得官方 DuckDB 包的环境重跑；实现 schema allowlist 和身份字段剥离后才允许导入真实聚合数据。

## 组合链路

`本地编码工具会话 → CodeBurn 解析与聚合 → JSON 隐私适配器 → DuckDB 表 → 固定 SQL 汇总 → 研发效能负责人复核`

认证边界：本地采集无需模型 API key；团队上传/身份映射若后续启用，需要企业 SSO/OIDC、最小权限和删除机制。CodeBurn 的 sync 目前是 preview，本轮不把它作为已验证基础设施。

## 必须自行开发

- JSON schema 版本适配、幂等导入和错误隔离。
- 项目/用户身份哈希、同意机制、保留期和删除流程。
- 跨工具 provider/model/currency 口径映射。
- 企业 SSO、团队目录映射、审计日志和权限控制。
- 数据完整性提示；明确禁止从 token/成本直接推导个人绩效。
- 若接入 Copilot/Gemini 管理员 API，还需分别实现授权、分页、限流和字段映射。

## MVP 验证

- 单一目标用户：一支 10–30 人、已同时试用至少两种 AI 编程工具的软件团队的研发效能负责人。
- 输入：连续 14 天、参与者明确同意后的 CodeBurn 聚合 JSON；不含提示词和代码。
- 核心流程：本地导出、隐私转换、DuckDB 导入、按日/provider/model 查询。
- 输出：一份可复现的成本/采用汇总和一份缺失数据报告。
- 成功指标：数据负责人能在不查看个人内容的前提下，对齐至少两种工具的日期、模型和成本口径，并指出原厂 dashboard 无法回答的一项跨工具问题。
- 停止条件：需要上传原始会话才能得到有用结果；参与者不同意隐私边界；两周内无法稳定映射两种工具；维护成本高于直接使用各厂商导出。
- 第一版不做：个人排行榜、生产率评分、自动采购决策、全公司部署、ROI 预测。

## 业务判断

最可能受益者是已有多工具试点的平台工程/研发效能团队。价值不是替代厂商 dashboard，而是统一最小口径和保留可审计的本地数据。最大采用阻力是员工监控观感、会话数据敏感性、成本估算误差和各工具 schema 变化。

在没有用户访谈、真实团队 L4 和付费证据前，结论只能是**值得做技术实验**。若安全的 L3 数据连接成功，可进入 3–5 位管理员访谈；不能直接进入商业开发。

## 证据边界与来源

已证实：两家厂商提供组织用量指标；GitHub 支持 API/NDJSON 与 team join；Gemini 数据进入 Cloud Monitoring 且有 surface 限制；CodeBurn 提供多工具本地解析与 JSON；DuckDB 官方支持 JSON 导入。

推断：同时使用多种工具的团队会需要统一口径；CodeBurn 的本地汇总可比原厂 telemetry 更适合作为隐私受控的输入。

未验证：真实团队愿意采用；跨设备身份映射；CodeBurn schema 长期稳定；管理员 API 接入；效率或 ROI 改善；任何收入或客户数量。

来源（均核实于 2026-07-20）：

- [GitHub Copilot usage metrics](https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/copilot-usage-metrics/copilot-metrics)
- [GitHub Copilot metric fields and NDJSON/API reports](https://docs.github.com/en/enterprise-cloud@latest/copilot/reference/copilot-usage-metrics/copilot-usage-metrics)
- [GitHub team-level metric join](https://docs.github.com/en/enterprise-cloud@latest/copilot/reference/copilot-usage-metrics/team-level-metrics)
- [Gemini Code Assist monitoring](https://docs.cloud.google.com/gemini/docs/codeassist/monitor-gemini-code-assist?hl=en)
- [CodeBurn](https://github.com/getagentseal/codeburn)
- [OpenLIT](https://github.com/openlit/openlit)
- [DuckDB JSON import](https://duckdb.org/docs/stable/guides/file_formats/json_import)
- [DuckDB](https://github.com/duckdb/duckdb)
