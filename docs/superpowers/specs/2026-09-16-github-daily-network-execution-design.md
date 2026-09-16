# GitHub 日报最小网络执行权限设计

## 问题

2026-09-16 的日报自动化正常触发，但 `daily_digest_runner.py discover` 在默认 `workspace-write` 沙箱内运行。六个 GitHub Search 子进程均因 DNS 解析失败而返回空结果，检查点停在 `discovery_failed`，日报没有生成。

这是 2026-09-15 运行时预算改造引入的执行环境差异：此前联网主要由 Codex 的托管网页工具完成；改造后联网集中到本地 Python runner，而默认 shell 沙箱没有外网权限。

## 目标

- 保留单次 05:00 调度、90 分钟预算、检查点、紧凑短名单和质量合同。
- 只允许 `python3 scripts/daily_digest_runner.py` 在需要 GitHub 的命令上请求升级执行，不开放全局 shell 网络。
- 默认沙箱失败不得先消耗一次发现机会；自动化必须直接使用已预授权的升级执行。
- 升级执行被拒绝或仍失败时保留检查点并停止，不循环重试。
- 用真实 GitHub 六路发现验证网络、TLS 降级和候选账本写入，而不只依赖伪造扫描器。
- 从 2026-09-16 的失败检查点恢复并生成当天日报。

## 方案

### 最小权限边界

为命令前缀 `python3 scripts/daily_digest_runner.py` 保存升级执行许可。自动化提示词明确要求：仅 `discover` 联网步骤调用终端工具时设置 `sandbox_permissions=require_escalated`；`start`、`inspect`、`audit`、`shortlist` 和 `finalize` 继续在默认沙箱运行。

不设置全局 `danger-full-access`，不修改项目整体 sandbox，不新增 launchd 预抓取任务。

### 失败处理

`discover` 仍保持现有的一次 TLS `--insecure` 降级。升级执行失败时，runner 写入紧凑错误和 `discovery_failed` 检查点；自动化不得改回默认沙箱重试，也不得自行 `resume`。

### 契约固化

自动化契约测试要求提示词同时包含：

- `sandbox_permissions=require_escalated`；
- 权限仅用于 `daily_digest_runner.py discover`；
- 禁止先在默认沙箱运行；
- 升级失败后停止且不得循环重试。

仓库提示词、安装中的自动化 prompt 和紧凑 memory 必须同步。

## 验证

1. 契约测试先因缺少升级执行要求失败，再修改提示词使其通过。
2. 在临时数据目录以升级执行运行真实六路 GitHub 发现，要求 `successfulLanes=6`、候选数大于零、无错误。
3. 运行全部 Python 与前端测试、`git diff --check`。
4. 人工 `resume 2026-09-16` 后按同一权限运行发现、短名单、核验、草稿和 `finalize`。
5. 最终检查 `daily/2026-09-16.md` 存在且非空，检查点为 `complete`，候选、history 和 trial-status 一致。

