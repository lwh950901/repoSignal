# GitHub Daily Runtime Budget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Keep the existing report-quality contract while reducing model context, isolating unrelated downstream work, and enforcing 30-minute progress audits with a 90-minute hard ceiling.

**Architecture:** Extend the existing atomic checkpoint with runtime metadata and deterministic audit actions. Add one local runner that batches the six discovery lanes and emits a compact, quality-preserving shortlist; keep final evidence judgment and writing with the configured model.

**Tech Stack:** Python 3 standard library, `unittest`, JSON/JSONL checkpoints, existing GitHub scanner and candidate ledger, Codex cron automation.

---

### Task 1: Runtime checkpoint and audit actions

**Files:**
- Modify: `scripts/test_daily_digest_checkpoint.py`
- Modify: `scripts/daily_digest_checkpoint.py`

- [x] **Step 1: Write failing tests** for idempotent `start_run`, explicit manual `resume_run`, progress updates, 15-minute stalls, and the 30/60/75/85/90-minute action boundaries using injected UTC datetimes.
- [x] **Step 2: Run tests to verify RED** with `python3 -m unittest scripts.test_daily_digest_checkpoint -v`; expected failures are missing `start_run`, `record_progress`, and `audit_run` APIs.
- [x] **Step 3: Implement minimal runtime APIs** that atomically preserve `startedAt`, update `lastProgressAt`, cap errors at five, and return deterministic `action`, `stalled`, and elapsed-minute fields.
- [x] **Step 4: Add CLI commands** `start`, `resume`, `progress`, and `audit`, with `--now` available for deterministic tests and diagnostics; only manual `resume` may reset an expired budget.
- [x] **Step 5: Run checkpoint tests** and expect all cases to pass.

### Task 2: Compact quality-preserving shortlist

**Files:**
- Create: `scripts/test_daily_digest_runner.py`
- Create: `scripts/daily_digest_runner.py`
- Modify: `scripts/candidate_ledger.py`

- [x] **Step 1: Write failing shortlist tests** proving archived/unclear-license/90-day duplicates are excluded, each of the four slots keeps at most three candidates, pending user candidates remain visible, and the rendered JSON stays compact.
- [x] **Step 2: Run tests to verify RED** with `python3 -m unittest scripts.test_daily_digest_runner -v`; expected failure is the missing runner module.
- [x] **Step 3: Implement shortlist generation** using the existing lane labels, recent history, explicit rejection counts, deterministic activity/community ordering, and no automatic final selection.
- [x] **Step 4: Extend candidate records** to retain compact `description`, `language`, `topics`, and creation/update metadata when present, without changing existing required fields.
- [x] **Step 5: Run runner and candidate-ledger tests** and expect all cases to pass.

### Task 3: Batched discovery entry point

**Files:**
- Modify: `scripts/test_daily_digest_runner.py`
- Modify: `scripts/daily_digest_runner.py`

- [x] **Step 1: Write failing tests** using a temporary fake scanner to prove six lanes run, lane provenance is retained, one TLS retry is allowed, non-TLS failures are not retried, partial successful results are written, and an existing candidate ledger is never overwritten.
- [x] **Step 2: Run tests to verify RED** for the missing `discover` behavior.
- [x] **Step 3: Implement `discover`** with `ThreadPoolExecutor`, per-process timeouts bounded by the checkpoint deadline, atomic candidate-ledger output, compact error summaries, and progress updates.
- [x] **Step 4: Run runner tests** and expect all cases to pass.

### Task 4: Prompt and automation contract

**Files:**
- Modify: `scripts/test_daily_automation_contract.py`
- Modify: `docs/automation-prompts/github-daily.md`

- [x] **Step 1: Update contract tests first** to require the runner, 30/60/85/90-minute gates, 15-minute stall handling, no source/full-ledger reads, no automatic retry, the original quality contract, and unchanged model/schedule expectations.
- [x] **Step 2: Run contract tests to verify RED** because the current prompt still has the old 35/40-minute protocol.
- [x] **Step 3: Replace the prompt** with the compact checkpoint/runner protocol while preserving all quality invariants.
- [x] **Step 4: Run contract tests** and expect all cases to pass.

### Task 5: Downstream responsibility isolation

**Files:**
- Modify: `scripts/test_daily_automation_contract.py`
- Modify: `docs/automation-prompts/github-daily.md`
- Modify: `scripts/com.reposignal.opportunity-analysis.plist` only if the existing `/bin/bash` invocation is not already covered.

- [x] **Step 1: Add a failing contract assertion** that the daily automation never triggers, waits for, checks, or reports feasibility.
- [x] **Step 2: Confirm the launchd path already invokes `/bin/bash`**; avoid unrelated permission changes when the existing invocation is correct.
- [x] **Step 3: End the daily automation at report finalize/verification** and make the contract pass.

### Task 6: Full verification and automation update

**Files:**
- Update external automation: `github`
- Compact external memory: `/Users/elvis/.codex/automations/github/memory.md`

- [x] **Step 1: Run targeted suites**: `python3 -m unittest scripts.test_daily_digest_checkpoint scripts.test_daily_digest_runner scripts.test_daily_automation_contract scripts.test_opportunity_analysis -v`.
- [x] **Step 2: Run repository checks**: `python3 scripts/candidate_ledger.py --check`, `python3 scripts/daily_digest_checkpoint.py inspect 2026-09-15 --data-root data/github-project-digest`, and `git diff --check`.
- [x] **Step 3: Compact automation memory** to durable rules, the latest successful run, and unresolved issues; archive removed historical text under `docs/automation-memory/github-daily/archive/`.
- [x] **Step 4: Update automation `github`** from `docs/automation-prompts/github-daily.md`, preserving ACTIVE status, the existing RRULE, `gpt-5.6-terra`, and `high` reasoning.
- [x] **Step 5: Read back the automation** and verify prompt parity, one 05:00 schedule, no automatic retry, and unchanged model settings.
