# GitHub 日报最小网络执行权限 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 让日报 runner 在定时任务中以最小权限可靠访问 GitHub，并补齐 2026-09-16 日报。

**Architecture:** 保留现有检查点和批量 runner，只把 `discover` 的终端调用提升到已预授权的网络执行；其余命令继续留在默认沙箱。通过提示词契约测试和真实 GitHub 临时目录冒烟同时验证静态配置与运行环境。

**Tech Stack:** Python `unittest`、Codex Scheduled Tasks、GitHub Search runner、Markdown 自动化提示词。

---

### Task 1: 固化最小网络权限契约

**Files:**
- Modify: `scripts/test_daily_automation_contract.py`
- Modify: `docs/automation-prompts/github-daily.md`

- [x] **Step 1: 写失败测试**，要求提示词包含 `sandbox_permissions=require_escalated`、权限仅限 `discover`、禁止默认沙箱预跑和失败后停止。
- [x] **Step 2: 运行 `python3 -m unittest scripts.test_daily_automation_contract -v`**，确认新测试因提示词缺少网络权限要求而失败。
- [x] **Step 3: 最小修改提示词**，只为 `daily_digest_runner.py discover` 增加升级执行说明。
- [x] **Step 4: 重跑定向测试**，确认通过且提示词仍满足长度、模型、调度和质量合同。

### Task 2: 同步已安装自动化

**Files:**
- Modify: `docs/automation-memory/github-daily/memory.compact.md`
- External config: `/Users/elvis/.codex/automations/github/automation.toml`
- External memory: `/Users/elvis/.codex/automations/github/memory.md`

- [x] **Step 1: 更新紧凑 memory**，记录 runner 的最小升级执行边界和 2026-09-16 故障。
- [x] **Step 2: 通过自动化更新接口同步 prompt**，保留原 ID、RRULE、模型、推理档位和 ACTIVE 状态。
- [x] **Step 3: 同步安装中的 memory 并回读**，确认仓库 prompt/memory 与安装版本逐字一致。

### Task 3: 运行真实网络冒烟

**Files:**
- No repository changes.

- [x] **Step 1: 以 `sandbox_permissions=require_escalated` 在临时数据根运行六路 `discover`**。
- [x] **Step 2: 确认输出为 `status=complete`、`successfulLanes=6`、`candidateCount>0`、`errors=[]`。
- [x] **Step 3: 验证未给全局 sandbox 或其他命令扩大权限**。

### Task 4: 补跑 2026-09-16 日报

**Files:**
- Create: `data/github-project-digest/candidates/2026-09-16.jsonl`
- Create: `data/github-project-digest/daily/2026-09-16.md`
- Modify: `data/github-project-digest/daily-runs/2026-09-16.json`
- Modify: `data/github-project-digest/history.jsonl`
- Modify: `data/github-project-digest/trial-status.json`

- [x] **Step 1: 人工执行检查点 `resume`**，开启新的 90 分钟预算。
- [x] **Step 2: 以升级执行运行真实 `discover`**，生成不可覆盖的候选账本。
- [x] **Step 3: 生成紧凑短名单，只核验最终 4–5 项并写草稿与 selections JSON**。
- [x] **Step 4: 通过 `finalize` 原子落盘并运行检查点 `inspect`/`audit`**。

### Task 5: 完整验证

**Files:**
- All changed files above.

- [x] **Step 1: 运行 `python3 -m unittest scripts.test_daily_digest_runner scripts.test_daily_digest_checkpoint scripts.test_daily_automation_contract -v`**。
- [x] **Step 2: 运行 `npm test -- --run`**。
- [x] **Step 3: 运行 `git diff --check` 和日报结构/日期/检查点对账**。
- [x] **Step 4: 回读自动化，确认仍为周一至周六 05:00、`gpt-5.6-terra/high`、ACTIVE，且只有 discover 使用升级网络权限。

