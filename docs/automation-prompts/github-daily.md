# GitHub 优质项目每日发现：90 分钟受限协议

工作区：`/Users/elvis/Desktop/repo-signal`；时区：Asia/Shanghai。模型保持 `gpt-5.6-terra`、推理档位 `high`。调度契约：RRULE：`FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA;BYHOUR=5;BYMINUTE=0;BYSECOND=0`。每天仅 05:00 运行一次，禁止自动补跑；失败后等人工从检查点续跑。

## 启动、恢复与时间门禁

1. 完整读取并遵守 `find-github-projects` skill。不得读取源码；不得读取完整 memory、history、candidate、feedback 或 trial-status，也不得把长网页或原始 JSON 打进上下文。
2. 立即运行：
   - `python3 scripts/daily_digest_checkpoint.py start YYYY-MM-DD --data-root data/github-project-digest`
   - `python3 scripts/daily_digest_checkpoint.py inspect YYYY-MM-DD --data-root data/github-project-digest`
   - `python3 scripts/daily_digest_checkpoint.py audit YYYY-MM-DD --data-root data/github-project-digest`
3. `complete` 直接报告；`report_ready` 只修复 finalize 同步；`candidates_ready` 禁止宽搜索；仅 `needs_discovery` 执行发现。用户候选以 inspect/shortlist 输出为准，优先核验但不保证入选。
4. 开始各阶段前后调用 `daily_digest_checkpoint.py audit`，且每 30 分钟至少检查一次。连续 15 分钟无有效进展即取消当前扩展，改用本轮已有事实。
5. 按 audit 动作执行：30 分钟停止发现；60 分钟停止研究并开始报告；85 分钟停止一切扩展并立即 finalize；90 分钟硬停止，只保留检查点并报告人工运行 `python3 scripts/daily_digest_checkpoint.py resume YYYY-MM-DD --data-root data/github-project-digest` 后续跑；自动化不得自行调用 resume。

## 有界发现与核验

- 仅在 `needs_discovery` 运行一次 `python3 scripts/daily_digest_runner.py discover YYYY-MM-DD --data-root data/github-project-digest`。仅该 `daily_digest_runner.py discover` 命令调用终端工具时必须设置 `sandbox_permissions=require_escalated`，使用已预授权的最小网络权限；不得先在默认沙箱试跑，也不得把权限扩大到其他命令。升级执行被拒绝或失败时记录检查点并立即停止，不得降回默认沙箱或循环重试。runner 并发执行最多 6 条 GitHub Search、每条最多 12 个结果，覆盖增长、成熟实用、新兴潜力、学习/RAG、开发工具、跨界主题；同日账本存在时不得覆盖。
- 运行 `python3 scripts/daily_digest_runner.py shortlist YYYY-MM-DD --data-root data/github-project-digest --output <临时JSON>`，只读取该短名单。它负责归档、许可证不明和普通 90 天重复的硬过滤，并为四类各保留最多 3 项；不能直接当成最终排名。
- 只对最终 4–5 项做 enrichment，并尽量一次批量完成。每项最多 2 个 GitHub 页面；事实优先级为 GitHub API/仓库元数据、README、Release、Commit、Issue/PR、GitHub Trending。无法核实就标注或排除，不得以旧缓存冒充实时数据。
- TLS/证书失败仅允许 runner 自动进行一次 `--insecure` 降级；API、DNS、页面、工具失败不得循环重试。GitHub API 限流后停止 API 扩展，改用已取得的仓库事实和最多两页证据。
- 联网只用短/中摘要；单次命令输出最多 4,000 tokens，超出先本地聚合。禁止长响应，禁止调试式反复打开页面或打印完整文件。

## 不变的质量合同

统一评分：社区信号 25%、维护状态 25%、项目质量 20%、用户适合度 20%、风险 10%。Stars 只是信号，不单独排名。正式推荐 4–5 项，前四项严格为爆发型、实用型、潜力型、学习型；第 5 项可复用类型。内容型项目最多一个主位置。主推荐原则上不低于 80 分，70–79 分只能进额外发现或明确说明例外。

90 天内 history 已出现的仓库默认不得再推荐；仅显著增长、重大版本或用户明确要求可破例，选择 JSON 必须含 `repeat_exception: true` 和具体 `repeat_reason`。用户候选无论入选与否都须在候选账本保留结论。

爆发型必须当前至少 5,000 Stars 且有可核验加速证据：

- 36–60 小时窗口：起始不足 1,000 时 +200 且 +30%；1,000–9,999 时 +500 且 +20%；至少 10,000 时 +1,000 且 +10%。
- 7 天窗口：起始不足 1,000 时 +500 且 +50%；1,000–9,999 时 +1,500 且 +30%；至少 10,000 时 +3,000 且 +20%。
- 新建不超过 48 小时或 7 天且达到 5,000 Stars，可结合实时事实、质量和风险判断；日期明确的 Trending、重大 Release 或显著讨论也可举证。无合格项就报告“爆发型位置阻塞”，不得凑位。

实用型必须有安装/启动、可运行示例、最近 90 天有效活动，并在测试、CI、稳定 Release、完整文档、复用示例、Issue/PR 维护中至少满足 3 项。潜力型最近 60 天有活动，说明差异化、二次开发路径和至少 2 条质量证据。学习型最近 180 天有活动或解释例外，说明可拆解对象、复现入口、实现新鲜度和不宜照搬的风险。正式推荐排除归档、纯镜像、明显玩具及许可证不明且构成使用风险的项目。

## 报告与提交

日报写入 `data/github-project-digest/daily/YYYY-MM-DD.md`，固定结构为标题、今日重点、今日结论、主推荐、今天最值得亲自试用，可有 0–2 个额外发现。每项按固定顺序包含十个字段：仓库、一句话定位、类型与适合用途、核心亮点与场景、主要技术栈、实时指标、近期有意义活动、质量证据、风险、推荐理由。

先在临时路径写草稿和 4–5 项选择 JSON；选择至少含 `repo`、`slot`、`score`、`reason`、`activity`、`sources`、`verified: true`、`repeat_exception`。仅通过下列命令落盘：

`python3 scripts/daily_digest_checkpoint.py finalize YYYY-MM-DD --data-root data/github-project-digest --draft <草稿> --selections <选择JSON>`

finalize 失败只修报错项，不重新发现。日报自动化的职责在 finalize 和验证完成后结束，不触发、等待、检查或汇报任何下游任务。

最终仅汇报日报路径、主推荐、额外发现数、检查点阶段、降级路径和验证结果。不自动补跑、不创建第二时段、不自行调度重试。
