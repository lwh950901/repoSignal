# GitHub 日报自动化限流与检查点设计

## 背景

2026-09-08 至 2026-09-14 的多次日报自动任务在完成前遇到 Codex 后端 403 或响应流中断。日志显示失败任务的单轮输入上下文增长到约 186K–193K tokens，主要来自重复读取长文档、完整输出候选与状态文件、批量打开 GitHub 长页面，以及网络失败后的重复调用。调度本身正常触发，故障发生在任务执行阶段。

## 目标

- 保持周一至周六 05:30（Asia/Shanghai）单次调度，不增加自动补跑。
- 在不削弱日报固定格式、事实核验、四类推荐、90 天去重和风险边界的前提下缩短自动化提示词。
- 将常规运行控制在 40 分钟内，并把单轮模型上下文目标控制在 60K tokens 以下。
- 用本地、按日期存储的检查点支持人工补跑；已经完成的阶段不得重复执行。
- 日报是主产物；每日 feasibility 是附加产物，其失败或文件重叠不得抹去已完成日报。

## 非目标

- 不新增第二个定时任务或自动补跑时段。
- 不改变日报公开格式、评分权重、爆发型量化门槛或四类推荐顺序。
- 不修复外部 GitHub API、GitHub CLI 凭据、Codex 后端 403 或网络断流本身；本设计降低暴露时间并提供恢复能力。
- 不改造周报、周刊或月报自动化。

## 方案

### 1. 按日期检查点

新增 `scripts/daily_digest_checkpoint.py`，使用 `data/github-project-digest/daily-runs/YYYY-MM-DD.json` 保存单日状态。文件采用临时文件加原子替换写入，阶段为：

- `needs_discovery`：没有有效候选文件。
- `candidates_ready`：候选文件存在、非空、JSONL 合法且仓库唯一。
- `report_ready`：日报草稿已通过结构校验，尚未完成最终同步。
- `complete`：日报、候选状态、history 和运行状态全部一致。

`inspect` 命令只输出紧凑 JSON，包括阶段、候选数量、用户指定候选、90 天重复集合和缺失产物，不输出完整 history、candidate、feedback 或 trial-status。

`finalize` 命令接收日报草稿和 4–5 项选择 JSON，执行以下事务式步骤：

1. 校验日报日期、4–5 个正式推荐、前四类顺序和每项十个固定字段。
2. 校验选择均来自当日候选，许可证明确、已核验、未命中 90 天去重；重复例外必须显式记录理由。
3. 原子写入最终日报。
4. 更新候选记录的 `status`、`verified`、`reason` 和 `sources`。
5. 向 history 幂等追加记录，同一天同一仓库不得重复。
6. 写入按日期检查点，并更新现有 `trial-status.json` 的当日摘要。

任一步骤在最终替换前失败时不得留下半成品；再次执行相同选择必须幂等。

### 2. 提示词缩短与限流

自动化提示词保留以下不可省略内容：技能调用、事实来源、评分权重、四类推荐硬约束、爆发型门槛、固定十字段、90 天去重、附加 feasibility 和最终报告要求。详细机械校验交给检查点脚本，避免在提示词中重复实现说明。

执行限制：

- 开始只运行 `checkpoint inspect`，根据阶段决定继续位置。
- `candidates_ready` 时禁止重新运行宽搜索。
- 需要发现时最多 6 条 GitHub Search，每条最多 12 个结果；原始 JSON 写入临时文件，对话只显示计数和错误摘要。
- 只对最终 4–5 项串行 enrichment；不得对全候选 enrichment。
- GitHub API 限流后停止 API 扩展，每项最多打开 2 个 GitHub 页面作为降级证据。
- 不使用批量 `response_length=long`，不完整打印 memory、history、candidate、feedback、trial-status、源码或长网页。
- 单次命令输出上限 4,000 tokens；超出时先在本地聚合再返回摘要。
- 研究达到 35 分钟时停止扩展，使用已核验事实完成草稿；整体 40 分钟时不得继续搜索。
- 首次 TLS 失败只允许一次 `--insecure` 重试；API、DNS 或网页失败不得形成循环重试。

### 3. 主产物优先

日报经 `finalize` 完成后才运行 feasibility。若当日 feasibility 已存在、存在重叠修改、输出 0 个方案或脚本失败，只记录附加步骤状态，不回滚日报、候选或 history。

### 4. 调度与模型

保留现有 RRULE：`FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA;BYHOUR=5;BYMINUTE=30;BYSECOND=0`。不增加自动补跑。模型保持 `gpt-5.6-luna`、`high`，先通过输入与工具限流解决上下文问题，避免同时改变模型变量。

## 错误处理与恢复

- 发现阶段断流：候选尚未生成，下次人工补跑从 `needs_discovery` 开始。
- 候选生成后断流：检查点返回 `candidates_ready`，人工补跑直接筛选，不重复宽搜索。
- 草稿校验失败：保留草稿路径和错误摘要，最终日报不落盘。
- finalize 中断：幂等逻辑依据最终文件、history 和候选状态重新对账，不重复追加。
- 日报完成后断流：检查点返回 `complete`，人工补跑只报告已完成。
- feasibility 失败：日报保持 `complete`，检查点记录附加步骤失败或阻塞。

## 测试

新增 `scripts/test_daily_digest_checkpoint.py`，至少覆盖：

- 无候选时返回 `needs_discovery`。
- 候选合法时返回 `candidates_ready`，且输出不包含完整候选或 history。
- finalize 拒绝字段缺失、类型顺序错误、候选外仓库和未授权 90 天重复。
- finalize 成功时同时生成日报、更新候选、追加 history 和检查点。
- 相同输入执行两次不重复追加 history。
- 中间文件或 JSONL 损坏时不覆盖最终日报。
- feasibility 已存在或失败不改变日报完成状态。

新增自动化提示词契约测试，验证调度仍只有 05:30，提示词包含检查点、搜索与网页上限、35/40 分钟截止、主产物优先和禁止自动补跑语义。

## 验收标准

- 2026-09-14 补跑日报及对应 history、candidate、trial-status 通过既有格式与去重检查。
- 检查点测试和自动化契约测试全部通过。
- 自动化配置仍为 ACTIVE，RRULE 未增加第二时段。
- 新提示词显著短于旧提示词，并保留所有产品与事实完整性要求。
- 用当日现有产物运行 `inspect` 返回 `complete`；重复 finalize 不改变 history 行数。
