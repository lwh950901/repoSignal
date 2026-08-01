# 2026-07 Top 5 评分底稿

> 核实日期：2026-08-01。评分是按统一量表做出的可解释编辑判断，不是绝对客观排名。

## 候选池审计

- Asia/Shanghai 数据截止：2026-07-31。
- 确定性合格候选数：203；生成器按小写 `owner/repo` 合并候选账本、7 月日报和与 7 月重叠的 ISO 周报。
- 复现命令：`python3 scripts/generate_monthly_digest.py 2026-07 --output <临时文件>`。
- 生成器把重叠周的 2026-08-02 周末日期钳制为 7 月 31 日公开截止；8 月 1 日日报不计入 7 月。
- 硬门槛：仓库可访问、未归档、许可证与用途明确、有安装入口、7 月存在发布或有效变化，且没有直接否决推荐的安全或合规风险。
- 深度候选按多来源重复、7 月发布/有效提交、工程材料和采用证据选择；Stars 不能单独触发深查或排名。

## 深度候选与评分

| 仓库 | 月 /20 | 价值 /25 | 工程 /20 | 差异 /15 | 维护 /10 | 采用 /10 | 总分 | 验证 | 主要反对理由 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| ChromeDevTools/chrome-devtools-mcp | 20 | 25 | 20 | 14 | 9 | 8 | **96** | L0 | 浏览器权限面大，本轮 npm 临时安装无输出，未完成最小握手。 |
| heygen-com/hyperframes | 20 | 23 | 19 | 15 | 8 | 9 | **94** | 0.x 高频发布，浏览器、FFmpeg、字体和媒体资产会放大输出一致性风险。 |
| alibaba/open-code-review | 20 | 23 | 19 | 15 | 8 | 8 | **93** | 公开基准和大规模内部采用主要来自作者，独立检出率尚未复现。 |
| hyperdxio/hyperdx | 18 | 25 | 20 | 12 | 9 | 8 | **92** | ClickHouse、遥测留存和 session replay 带来显著运维与隐私成本。 |
| cvat-ai/cvat | 18 | 24 | 20 | 11 | 9 | 9 | **91** | 系统体量、开放 Issue 和第三方资产许可证需要采用者逐项治理。 |
| chatwoot/chatwoot | 17 | 24 | 19 | 11 | 9 | 9 | 89 | L0 | 自托管需要维护数据库、Redis、邮件和渠道凭据，企业目录许可证另算。 |
| openai/openai-agents-python | 18 | 23 | 20 | 12 | 9 | 7 | 89 | L0 | 快速演进且深度使用通常绑定模型凭据、费用和数据边界。 |
| alibaba/zvec | 17 | 23 | 19 | 14 | 9 | 7 | 89 | L2 | 生产数据规模、并发、恢复和升级边界仍需工作负载验证。 |
| pydantic/pydantic-ai | 17 | 24 | 20 | 12 | 9 | 7 | 89 | L0 | 类型化体验突出，但 7 月下半月信号弱于榜首项目且本轮未运行。 |
| topoteretes/cognee | 18 | 22 | 18 | 14 | 8 | 8 | 88 | L0 | 记忆正确性、删除语义和多后端组合复杂度未在真实任务验证。 |
| langchain4j/langchain4j | 16 | 23 | 20 | 11 | 9 | 9 | 88 | L0 | JVM 集成面很宽，团队仍需自行约束版本、模块与最小采用面。 |
| getagentseal/codeburn | 17 | 22 | 18 | 15 | 8 | 7 | 87 | L2 | 团队同步和隐私治理尚未成熟；本轮临时下载未完成。 |
| bytedance/deer-flow | 16 | 22 | 18 | 13 | 8 | 9 | 86 | L0 | 长链路成本、沙箱权限和失败恢复需要真实任务验证。 |
| ModelEngine-Group/nexent | 18 | 22 | 18 | 12 | 8 | 6 | 84 | L0 | 功能面宽且默认开发分支持续变化，生产治理成本未实测。 |
| different-ai/openwork | 19 | 21 | 17 | 13 | 7 | 7 | 84 | L0 | Alpha 高频迭代，主体 MIT 与企业目录/远程控制面边界需要审查。 |

## 校准与冻结

- 六维权重保持设计值，未调整。Stars/Forks 只辅助采用证据，不进入其他维度。
- 未为技术方向多样性或业务组合用途调榜；分数按总分降序冻结。
- Pydantic AI 与 zvec 在旧截止稿中领先，但月末新增候选具备更强的 7 月发布、工程和采用信号，重新统一评分后未进入前五。
- 冻结 Top 5：`ChromeDevTools/chrome-devtools-mcp`、`heygen-com/hyperframes`、`alibaba/open-code-review`、`hyperdxio/hyperdx`、`cvat-ai/cvat`。
- 核实日期：2026-08-01。指标使用当日 GitHub 公开页面快照，精确 release 日期使用官方 Releases；未认证 API 403 后没有猜测精确 Stars。

## 主要事实来源

- [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp)、[Releases](https://github.com/ChromeDevTools/chrome-devtools-mcp/releases)
- [HyperFrames](https://github.com/heygen-com/hyperframes)、[Releases](https://github.com/heygen-com/hyperframes/releases)
- [OpenCodeReview](https://github.com/alibaba/open-code-review)、[Releases](https://github.com/alibaba/open-code-review/releases)
- [HyperDX](https://github.com/hyperdxio/hyperdx)、[Releases](https://github.com/hyperdxio/hyperdx/releases)
- [CVAT](https://github.com/cvat-ai/cvat)、[Releases](https://github.com/cvat-ai/cvat/releases)
- 其余候选的 canonical GitHub 页面与同目录 `repository-verification.md`。
