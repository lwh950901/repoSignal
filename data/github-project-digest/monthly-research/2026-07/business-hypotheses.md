# 2026-07 业务假设漏斗

> 内部发现材料，不进入公开页面。月末补跑复核日期：2026-08-01。

| 假设 | 触发仓库/能力 | 初步问题 | 证据初筛 | 处理 |
|---|---|---|---|---|
| 跨工具 AI 编程用量与成本台账 | getagentseal/codeburn 的多工具本地解析和 JSON 导出 | 企业同时使用多种编码工具时，厂商仪表盘无法形成统一口径 | GitHub 与 Google 均提供组织级指标/导出，CodeBurn 覆盖多种本地工具 | **深入研究** |
| 进程内混合检索组件包 | alibaba/zvec 的本地向量/全文/混合检索 | 中小应用不想运维独立向量服务 | 技术能力明确，但“愿意购买组件包”的独立证据不足 | 不发布；仅作为技术采用题 |
| Agent 回归测试服务 | pydantic-ai 的 eval 与类型化输出 | Agent 升级时需要稳定回归 | 商业/开源竞品已多，尚未找到由本月仓库产生的窄缺口 | 继续观察 |
| JVM 企业 Agent 迁移套件 | langchain4j 的 JVM 集成面 | 传统 Java 团队接入 Agent 的组织成本较高 | 需求范围太宽，主要是咨询/实施而非清晰产品 | 不发布 |
| 研究型 Agent 交付审计 | deer-flow 的长链路研究工作流 | 研究输出需可追踪来源、成本和人工确认 | 现有框架已有部分能力；本轮缺少独立采购或重复建设证据 | 继续观察 |
| 遗留代码知识图谱尽调 | Understand Anything 的代码知识图谱 | 接手旧系统时理解成本高 | 问题真实，但代码搜索/图谱竞品密集，差异缺口未核实 | 不发布 |
| Agent skill 自动优化流水线 | SkillOpt 的 `best_skill.md` 输出 | 团队维护 skill 时缺少系统化评测与迭代 | 目前主要依赖作者基准，跨真实任务需求证据不足 | 不发布 |
| 个人 Agent 长期记忆治理 | MemPalace 的持久化记忆 | 记忆错误、删除与隔离需要治理 | 风险明确，但首要用户、付费方和可组合接口未核实 | 继续观察 |
| Agent 浏览器回归证据包 | Chrome DevTools MCP 的 console/network/trace/screenshot | coding agent 交付页面时需要浏览器事实 | 需求真实但 Playwright、浏览器 MCP 与现有 CI 重叠，未找到足够窄的新产品缺口 | 不发布 |
| Agent-native 视频渲染管线 | HyperFrames 的 HTML/CSS 到视频 | 内容团队需要可复现自动渲染 | 商业视频生成和开源 Remotion 已覆盖大部分需求；缺少独立采购缺口 | 继续观察 |
| AI 代码审查门禁 | OpenCodeReview 的确定性管线 + Agent | 团队希望降低审查噪声并稳定定位 | 商业与开源竞品密集，作者 benchmark 尚未独立复现 | 不发布 |
| 线上 Agent 故障转回归用例 | HyperDX trace + Pydantic AI eval | 将真实失败沉淀为可重放测试 | LangSmith、Braintrust、Langfuse 已正式提供 production trace → dataset → eval 闭环 | 不发布；定义与成熟产品重叠 |
| CVAT 本地数据质检桥 | CVAT + zvec + 图像 embedding | 在标注流程中发现近重复和标签冲突 | FiftyOne 已提供近重复、mistakenness 与 CVAT 双向集成，Encord 也有同类商业能力 | 不发布；缺口已被直接覆盖 |
| 本地事务邮件验收证据包 | Mailpit SMTP/API + Chrome DevTools MCP 页面事实与截图 | coding agent 完成注册、邀请和重置流程时，需要在不投递真实邮件的前提下核对邮件和落地页 | Mailtrap MCP、Litmus 证明需求；Supabase 使用 Mailpit 的现实流程仍要求打开浏览器；MailSandbox 只覆盖邮件读取分析。合成链路已达到 L3 | **深入研究并发布为新开源项目实验** |

## 漏斗结论

月末补跑共复核十四个假设。新增的 Agent 故障回归和 CVAT 质检方向分别被成熟产品的直接能力淘汰；“本地事务邮件验收证据包”因商业需求信号、现实人工流程、开源替代边界、职责分离和合成 L3 同时成立，作为第二个新开源项目实验发布。原有跨工具用量台账仍因 L3 未完成降级为“部分可行”。两项都未完成真实团队 L4，不推断收入、价格或市场规模。
