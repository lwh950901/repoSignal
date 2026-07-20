# 2026-07 Top 5 评分底稿

> 核实日期：2026-07-20。评分是按统一量表做出的可解释编辑判断，不是绝对客观排名。

## 候选池审计

- 数据截止：2026-07-19（只使用截止日前已进入本地候选账本的事实）。
- 确定性合格候选数：120，不是旧示例月报写的 94。
- 复现命令：`python3 scripts/generate_monthly_digest.py 2026-07 --output <临时文件>`。
- 生成器自检：通过。
- 已检查误收项：`0xkaz/llm-governance-dashboard`、`docs/superpowers`、`cli/tui`、`.github/workflows` 均未进入候选。
- 深度候选只按月内可核实信号选取，选取时未预设最终名次。

## 深度候选与评分

| 仓库 | 月 /20 | 价值 /25 | 工程 /20 | 差异 /15 | 维护 /10 | 采用 /10 | 总分 | 验证 | 主要反对理由 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| alibaba/zvec | 20 | 23 | 19 | 14 | 9 | 8 | **93** | L2 | 仍是较新的嵌入式向量数据库；生产边界需用大数据量继续验证。 |
| pydantic/pydantic-ai | 18 | 24 | 20 | 13 | 9 | 8 | **92** | L0 | 本机 Python TLS 阻断安装；快速演进会增加升级成本。 |
| getagentseal/codeburn | 19 | 23 | 18 | 15 | 9 | 7 | **91** | L2 | 团队同步协议仍标为 preview，跨组织治理能力尚未成熟。 |
| langchain4j/langchain4j | 18 | 23 | 20 | 12 | 9 | 9 | **91** | L0 | JVM 生态集成面很宽，团队仍需自己约束最小采用面；本机无 Java。 |
| bytedance/deer-flow | 17 | 23 | 19 | 14 | 8 | 9 | **90** | L0 | 2.0 为大规模重写，长链路运行成本和失败恢复需要真实任务验证。 |
| egonex-ai/understand-anything | 18 | 22 | 18 | 14 | 8 | 9 | 89 | L0 | 知识图谱质量高度依赖仓库结构与分析范围，本轮未运行真实仓库。 |
| earendil-works/pi | 18 | 22 | 18 | 13 | 9 | 9 | 89 | L0 | 高度可定制也意味着团队规范、权限与评测主要由使用者承担。 |
| microsoft/skillopt | 18 | 21 | 18 | 14 | 8 | 7 | 86 | L0 | 官方基准结果仍属于作者声明，能否迁移到真实任务尚未验证。 |
| mempalace/mempalace | 18 | 21 | 17 | 13 | 8 | 8 | 85 | L0 | 默认分支与发布方式增加判断成本，长期记忆的正确性和删除边界需实测。 |
| nexu-io/open-design | 18 | 20 | 17 | 13 | 8 | 8 | 84 | L0 | 采用热度很高，但桌面、MCP、BYOK 与导出链路均未运行复核。 |
| VoltAgent/voltagent | 17 | 21 | 18 | 12 | 9 | 7 | 84 | L0 | 与多种 Agent 框架的能力重叠较多，差异价值需在生产任务中证明。 |
| strukto-ai/mirage | 18 | 20 | 16 | 14 | 7 | 6 | 81 | L0 | 项目较新、采用证据有限，本轮未完成最小运行。 |
| agents-flex/agents-flex | 16 | 19 | 16 | 11 | 7 | 5 | 74 | L0 | 采用和独立生产证据较弱，无法仅凭广泛功能面进入 Top 5。 |
| dietrichgebert/ponytail | 18 | 17 | 14 | 14 | 7 | 8 | 78 | L0 | 极简约束有鲜明定位，但作者基准未独立复现，且不是完整运行时。 |
| aprilnea/openlogi | 12 | 17 | 12 | 12 | 6 | 5 | 64 | 未完成 | 2026-07-20 官方仓库页面无法稳定访问，未通过可访问性门槛。 |

## 校准与冻结

- 首轮试评分后检查了成熟项目、明星数和大公司背景是否自动占优；六维权重保持设计值，**未调整**。Stars/Forks 只进入 10 分的采用证据，不参与其他维度。
- `codeburn` 与 `langchain4j` 同为 91 分。前者月内发布和差异化更强且完成 L2，因此排在前；没有为覆盖技术方向而人工调榜。
- 冻结 Top 5：`alibaba/zvec`、`pydantic/pydantic-ai`、`getagentseal/codeburn`、`langchain4j/langchain4j`、`bytedance/deer-flow`。
- `Understand-Anything` 是最接近入榜者；其用途真实，但本轮缺少运行验证，且总分低 1 分。

## 主要事实来源

- 各仓库 canonical GitHub 页面：[zvec](https://github.com/alibaba/zvec)、[Pydantic AI](https://github.com/pydantic/pydantic-ai)、[CodeBurn](https://github.com/getagentseal/codeburn)、[LangChain4j](https://github.com/langchain4j/langchain4j)、[DeerFlow](https://github.com/bytedance/deer-flow)、[Understand Anything](https://github.com/egonex-ai/understand-anything)、[pi](https://github.com/earendil-works/pi)、[SkillOpt](https://github.com/microsoft/skillopt)、[MemPalace](https://github.com/mempalace/mempalace)、[Open Design](https://github.com/nexu-io/open-design)、[VoltAgent](https://github.com/VoltAgent/voltagent)、[Mirage](https://github.com/strukto-ai/mirage)、[agents-flex](https://github.com/agents-flex/agents-flex)、[ponytail](https://github.com/dietrichgebert/ponytail)。
- 精确指标、release、许可证与验证边界见同目录 `repository-verification.md`；公开月报只采用已完成复核的字段。
