# GitHub 优质项目每日发现：受限执行协议

工作区：`/Users/elvis/Desktop/repo-signal`。时区：Asia/Shanghai。调度契约仅用于校验，RRULE：`FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA;BYHOUR=5;BYMINUTE=30;BYSECOND=0`。每天只有 05:30 这一次计划运行，禁止自动补跑；失败后等待人工触发，人工补跑必须从本地检查点续跑。

## 启动与恢复

1. 完整读取并严格使用 `find-github-projects` skill；不要把 skill、memory、history 或候选全文打印进对话。
2. 立即运行 `python3 scripts/daily_digest_checkpoint.py inspect YYYY-MM-DD --data-root data/github-project-digest`。
3. `complete`：不搜索、不改写，直接报告已经完成。`report_ready`：只修复 finalize 所缺同步。`candidates_ready`：禁止宽搜索，从现有候选筛选。只有 `needs_discovery` 才执行发现。
4. feedback 只处理 inspect 输出的用户候选；用户指定候选优先核验，但不保证入选。

## 强制资源上限

- 发现阶段最多 6 条 GitHub Search，每条最多 12 个结果；覆盖增长、成熟实用、新兴潜力、学习/RAG、开发工具、跨界主题。原始 JSON 写临时文件，对话只保留数量和错误摘要。
- 只对最终 4–5 项串行 enrichment，不对全候选 enrichment。GitHub API 限流后停止 API 扩展，每项最多 2 个 GitHub 页面作为降级证据。
- 联网页面使用短或中等摘要；不得完整输出长网页、源码、memory、history、candidate、feedback 或 trial-status。单次命令输出最多 4,000 tokens，超出先在本地聚合。
- TLS 失败只允许一次 `--insecure` 重试；API、DNS、页面或工具失败不得循环重试。不得以旧缓存冒充本轮实时数据。
- 研究到 35 分钟立即停止扩展，用已核验事实完成草稿；总运行到 40 分钟不得继续搜索，优先 finalize。不要创建或调度任何补跑任务。

## 候选与事实

发现结果通过 `scripts/candidate_ledger.py` 写入 `data/github-project-digest/candidates/YYYY-MM-DD.jsonl`；同日文件已存在时不得重跑宽搜索或覆盖。事实优先级：GitHub API/仓库元数据、README、Release、Commit、Issue/PR、GitHub Trending；无法核实就明确标注或排除。正式推荐排除归档、纯镜像、明显玩具，以及许可证不明并造成使用风险的仓库。

90 天内 history 已出现的仓库默认不得再推荐；只有显著增长、重大版本或用户明确要求时可破例，选择 JSON 必须设置 `repeat_exception: true` 和具体 `repeat_reason`。用户候选无论入选与否都要在候选账本保留结论。

## 评分与四类硬约束

统一评分：社区信号 25%、维护状态 25%、项目质量 20%、用户适合度 20%、风险 10%。Stars 只是信号，不单独排名。正式推荐 4–5 项，前四项严格为爆发型、实用型、潜力型、学习型；第 5 项可复用类型。内容型项目最多占一个主位置。原则上主推荐不低于 80 分，70–79 分只能进入额外发现或明确说明例外。

爆发型必须当前至少 5,000 Stars，并有可核验加速证据，不能只看总量：

- 36–60 小时窗口：起始不足 1,000 时 +200 且 +30%；1,000–9,999 时 +500 且 +20%；至少 10,000 时 +1,000 且 +10%。
- 7 天窗口：起始不足 1,000 时 +500 且 +50%；1,000–9,999 时 +1,500 且 +30%；至少 10,000 时 +3,000 且 +20%。
- 新建不超过 48 小时或 7 天且达到 5,000 Stars，可结合实时事实、质量证据和风险作为加速证据。日期明确的 Trending、重大 Release 或显著讨论也可作为证据。没有合格项目就报告“爆发型位置阻塞”，不得凑位。

实用型必须有安装/启动与可运行示例、最近 90 天有效活动，并在测试、CI、稳定 Release、完整文档、复用示例、Issue/PR 维护中至少满足 3 项。潜力型最近 60 天有活动，指出差异化亮点、二次开发路径和至少 2 条质量证据。学习型最近 180 天有活动或解释例外，明确可拆解对象、复现入口、实现新鲜度和不宜照搬的风险。

## 报告与提交

日报写入 `data/github-project-digest/daily/YYYY-MM-DD.md`。固定结构为标题、今日重点、今日结论、主推荐、今天最值得亲自试用；可有 0–2 个额外发现。每个正式推荐按固定顺序完整包含十个字段：仓库、一句话定位、类型与适合用途、核心亮点与场景、主要技术栈、实时指标、近期有意义活动、质量证据、风险、推荐理由。

先在临时路径写日报草稿和 4–5 项选择 JSON。选择项至少含 `repo`、`slot`、`score`、`reason`、`activity`、`sources`、`verified: true`、`repeat_exception`；破例时再含 `repeat_reason`。然后只通过：

`python3 scripts/daily_digest_checkpoint.py finalize YYYY-MM-DD --data-root data/github-project-digest --draft <草稿> --selections <选择JSON>`

完成格式、候选、许可证、90 天去重、history、trial-status 和检查点同步；不要手工重复追加 history。finalize 失败时只修正报错项，不重新发现。

日报是主产物。只有 finalize 返回 `complete` 后才运行 `scripts/run-opportunity-analysis.sh YYYY-MM-DD` 生成 feasibility；若 feasibility 已存在、存在用户修改、输出为空或执行失败，只记录附加步骤状态，不得覆盖该文件，也不得回滚或改写已完成日报。

最终只汇报：日报路径、4–5 个主推荐、额外发现数量、检查点阶段、feasibility 状态、采用的降级路径和验证结果。再次强调：不自动补跑，不创建第二时段，不因失败自行调度重试。
