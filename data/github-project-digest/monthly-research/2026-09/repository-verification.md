# 2026-09 仓库与组合验证

> 冻结时间：2026-10-01（Asia/Shanghai）。L0 表示官方资料核对；L2 条目为上游发布、测试或官方最小流程的可复核证据，本机未复跑。没有 L3/L4。

| 仓库 | 许可证 | 职责/接口事实 | 月度等级 | 证据和限制 |
|---|---|---|---|---|
| siyuan-note/siyuan | AGPL-3.0 | 本地工作空间、块 ID、导出/API | L2（上游流程） | 官方仓库与 9 月版本；本机未启动，写权限和同步恢复未测 |
| deeplethe/utopia | Apache-2.0 | 离线知识模型、事实/出处 | L0 | README 定位；未验证时态事实格式 |
| sibyl-labs/sibyl-memory | MIT | SQLite/FTS5 记忆 | L0 | README 定位；激活/凭据边界未跑 |
| langchain-ai/langchain | MIT | Retriever `invoke` 与测试流程 | L2（上游流程） | 官方代码与集成测试；本机未安装/运行 |
| topoteretes/cognee | Apache-2.0 | 知识摄取与检索 | L0 | 官方资料；数据隔离和元数据格式未测 |
| lyellr88/marm-memory | Apache-2.0 | 长期记忆检索 | L0 | 官方资料；迁移未测 |
| tencentcloud/cubesandbox | Apache-2.0 | 隔离动作执行 | L0 | Linux/KVM 前置；本机无法启动 |
| coze-dev/coze-loop | Apache-2.0 | trace/评测 | L0 | 官方自托管资料；多依赖、数据留存未测 |
| tastyeffectco/sandboxd | MIT | Docker 隔离执行 | L0 | Docker socket 无权限 |
| promptfoo/promptfoo | MIT | eval JSON/JUnit 输出 | L2（上游流程） | 官方 CLI 输出格式与测试指引；npm registry 无法解析，本机未跑 |
| openai/codex-security | Apache-2.0 | 安全扫描 | L0 | 权限/成本前置未测 |
| omnigent-ai/omnigent | Apache-2.0 | Agent 编排与策略 | L0 | alpha，版本和策略边界未测 |
| diegosouzapw/omniroute | MIT | 多模型路由与用量 | L0 | 凭据/成本/数据地域需试验 |

Top 5 五仓库仅达到 L0；它们的星标与 Fork 取 9 月候选快照，Release、许可证和当月维护再对照官方仓库/发布页。未把 Stars 总数当作月增长。L2 是上游证据等级而非本机通过；本月实际组合验证等级低于 L3。下一步只能在具备隔离环境后用合成数据复测。
