# GitHub 日报自动化韧性实施计划

> 设计依据：`docs/superpowers/specs/2026-09-14-github-daily-automation-resilience-design.md`

## 目标

在不改变日报质量规则和 05:30 单次调度的前提下，新增可恢复的本地检查点，将自动化提示词改为受限执行协议，并明确禁止自动补跑。

## 任务 1：以测试定义检查点契约

**文件：**

- 新增：`scripts/test_daily_digest_checkpoint.py`
- 新增：`scripts/test_daily_automation_contract.py`

先覆盖 `inspect` 的四阶段判断、紧凑输出、`finalize` 的格式/候选/去重校验、成功同步、幂等性及损坏输入保护；再用契约测试锁定提示词长度、搜索/页面/时间上限、主产物优先、单一 05:30 调度和禁止自动补跑。

## 任务 2：实现本地检查点

**文件：**

- 新增：`scripts/daily_digest_checkpoint.py`

实现零第三方依赖 CLI：读取候选和近 90 天 history，紧凑输出恢复阶段；在内存中完成所有校验与目标内容构造后，通过同目录临时文件和 `os.replace` 更新日报、候选、history、trial-status 与日期检查点。重复 `finalize` 不增加 history 行。

## 任务 3：缩短并约束自动化提示词

**文件：**

- 新增：`docs/automation-prompts/github-daily.md`

保留评分、四类顺序、十字段、爆发阈值、事实来源、去重与 feasibility 要求；机械一致性由检查点脚本负责。明确搜索最多 6×12、只 enrich 4–5 项、每项最多 2 个降级页面、输出 4,000 tokens、35/40 分钟截止、失败不循环重试、不自动补跑。

## 任务 4：更新并验证 Codex 自动化

通过 Codex 自动化接口更新 `github`，保持 ACTIVE、`gpt-5.6-luna/high` 和原 RRULE。回读配置，确认只有 05:30 一个时段、提示词与仓库契约一致且长度显著下降。

## 任务 5：验收当日日报和恢复状态

运行新增单元测试、相关现有测试、`git diff --check` 和当日 `inspect`；确认 2026-09-14 返回 `complete`，日报四项、history 无同日重复、feasibility 未被覆盖，并汇总所有有意修改。
