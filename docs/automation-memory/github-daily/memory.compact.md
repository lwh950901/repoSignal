# GitHub 优质项目每日发现记忆

## 使用边界

- 本文件只保存长期运行连续性、最近一次结果和未解决异常；不保存每日候选全文。
- 日报合同以 `docs/automation-prompts/github-daily.md` 为准；90 天去重以 `data/github-project-digest/history.jsonl` 为准；用户偏好以 `feedback.jsonl` 为准；当日状态以 candidate、daily、daily-runs 和 trial-status 为准。
- 历史快照位于 `docs/automation-memory/github-daily/archive/`。普通运行禁止读取归档；仅审计、权威状态冲突、确认历史用户决定或用户明确要求回溯时按需读取。
- 记忆和归档都不是 GitHub 实时事实来源。Stars、Forks、许可证、归档状态、活动、Release、Issue/PR 必须在本轮核验。

## 长期规则

- 自动化按 Asia/Shanghai 周一至周六 05:00 单次运行；无自动补跑。模型保持 `gpt-5.6-terra`，推理档位 `high`。
- 每轮显式使用 `find-github-projects` skill。先 `daily_digest_checkpoint.py start/inspect/audit`，仅在 `needs_discovery` 时运行一次 `daily_digest_runner.py discover`，随后用 `shortlist` 的紧凑结果筛选；最终只深核 4–5 项并通过 `finalize` 落盘。
- 每 30 分钟至少审计一次：30 分钟停发现，60 分钟开始报告，85 分钟立即 finalize，90 分钟停止。连续 15 分钟无有效进展时取消当前扩展，使用本轮已有事实。过期检查点只能由人工显式调用 `daily_digest_checkpoint.py resume` 开启新预算；自动化不得自行重置。
- 质量合同不因时间预算降低：五维权重、四类顺序、爆发型 5,000 Stars 与量化加速证据、实用/潜力/学习型门槛、十字段、许可证和 90 天去重均保持不变。
- 本机 Python 访问 GitHub 偶发 TLS 证书链错误；仅允许一次 `--insecure` 降级。匿名 GitHub API 可能限流；限流后停止 API 扩展，使用同轮 Search/Trending 和最多两页 GitHub 证据，未核实事实必须标注或排除。
- 日报自动化的职责止于日报 finalize 和验证，不执行、等待、检查或汇报独立的下游任务。

## 最近一次完成运行：2026-09-15

- 运行结果：`complete`；候选 61 条，正式推荐 4 项，history 新增 4 条后共 365 条。
- 主推荐：`alibaba/open-code-review`（爆发型，94，用户候选且为重复例外）、`questdb/questdb`（实用型，90）、`earthtojake/text-to-cad`（潜力型，88）、`PaddlePaddle/PaddleOCR`（学习型，90）。
- 降级：6 路 Search 中新兴通道超时未重试；首次 TLS 失败后仅一次 insecure 重试；API 限流后改用同轮 Trending、仓库和 Release 页面。
- 对账：日报、候选、history、trial-status、daily-runs 均已同步；candidate 自检和 `git diff --check` 通过。

## 未解决或需观察

- `GH_TOKEN`/`GITHUB_TOKEN`、系统认证及匿名 API 配额会变化，不得沿用旧结论。若限流，不等待重置、不循环重试。
- 2026-09-15 总墙钟时间异常长；新的 runner、紧凑短名单和分段门禁需在下一次计划运行中用 `daily-runs` 的时间字段验证：常规目标不超过 60 分钟，硬上限 90 分钟，并记录 candidate/verified 数量和最多 5 条错误。
- 用户候选 `alibaba/open-code-review` 与 `miounet11/life-kline` 仍由 `feedback.jsonl` 提供上下文；每轮按实时事实和 90 天去重重新判断，不从本记忆继承入选结论。
