# Errors

## [ERR-20260702-001] github_project_scan

**Logged**: 2026-07-02T08:32:31+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
GitHub scanner initially failed under sandbox DNS, then shortlist enrichment exhausted the unauthenticated API quota.

### Error
```
Network error: <urlopen error [Errno 8] nodename nor servname provided, or not known>
GitHub API rate limit reached; reset at 2026-07-02T01:05:59+00:00.
```

### Context
- Three `--no-cache` candidate scans succeeded after network escalation.
- Per-repository `--enrich` exhausted the remaining unauthenticated quota.

### Suggested Fix
Use `GITHUB_TOKEN` for recurring scans, reserve enrichment for the final shortlist, and retain the documented GitHub-page fallback.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/daily/2026-07-02.md
- See Also: automation memory entries for 2026-06-29 through 2026-07-01

### Resolution
- **Resolved**: 2026-07-02T08:32:31+08:00
- **Notes**: Used live GitHub repository, Release, Commit and Issue/PR pages; no cache was presented as live evidence.

---

## [ERR-20260809-001] radar_label_source_assertion

**Logged**: 2026-08-09T19:34:02+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
雷达标签终检把 TypeScript 正则源码误当作未转义的 Markdown 文本匹配。

### Error
终检断言查找字面量 `**介绍：**`，但 `radar.ts` 中保存的是正则源码 `^\*\*介绍：\*\*`，导致产品测试通过时辅助断言误报失败。

### Context
- 命令：W32 四标签格式的 Python 辅助终检。
- 产品文件、解析器测试和 Astro 检查未因该断言失败而受损。

### Suggested Fix
检查正则源码时匹配转义后的字符串，Markdown 内容文件才匹配未转义标签。

### Metadata
- Reproducible: yes
- Related Files: src/lib/radar.ts

### Resolution
- **Resolved**: 2026-08-09T19:34:26+08:00
- **Notes**: 修正辅助断言后重跑，精确标签检查、55 项测试和 Astro 检查全部通过。

---

## [ERR-20260807-001] github_daily_jsonl_separator

**Logged**: 2026-08-07T05:42:00+08:00
**Priority**: high
**Status**: resolved
**Area**: data

### Summary
An inline Python generator emitted the two-character sequence `\\n` instead of a real newline between JSONL records.

### Error
```
json.decoder.JSONDecodeError: Extra data: line 1 column 351 (char 350)
```

### Context
- The candidate ledger and the seven newly appended history records were generated from shell-escaped Python one-liners.
- The first formatting self-check caught the invalid JSONL before completion; no invalid data was reported as final.

### Suggested Fix
Use a dedicated script or a literal `"\\n"` inside Python source, then parse the written JSONL immediately before reporting completion. Avoid double-escaping the separator in shell-embedded Python.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/candidates/2026-08-07.jsonl; data/github-project-digest/history.jsonl

### Resolution
- **Resolved**: 2026-08-07T05:44:00+08:00
- **Notes**: Replaced all 118 literal separators atomically, then re-read 111 candidate records and 182 history records successfully; subsequent format, dedupe, and diff checks passed.

---

## [ERR-20260806-001] luna_codex_exec_argument_build

**Logged**: 2026-08-06T06:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The first isolated Luna test command failed while constructing the `model_reasoning_effort` override in an inline Python f-string.

### Error
```
NameError: name 'reasoning_effort' is not defined
```

### Context
- The nested `codex exec` process had not started, so no test files or external state were changed.
- Shell quoting removed the intended dictionary-key quotes inside the f-string expression.

### Suggested Fix
Build the TOML override with string concatenation instead of a nested f-string expression.

### Metadata
- Reproducible: yes
- Related Files: `/Users/elvis/.codex/automations/github/automation.toml`

### Resolution
- **Resolved**: 2026-08-06T06:00:00+08:00
- **Notes**: Replaced the nested f-string with explicit string concatenation before retrying.

---

## [ERR-20260806-002] nested_codex_state_db_readonly

**Logged**: 2026-08-06T15:51:17+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The isolated Luna test could not initialize Codex because the outer workspace sandbox made the Codex state database read-only.

### Error
```
failed to open state DB at /Users/elvis/.codex/state_5.sqlite: attempt to write a readonly database
Error: failed to initialize in-process app-server client: Operation not permitted
```

### Context
- The nested agent had not started and the isolated test directory was unchanged.
- Codex CLI requires access to its own state under `/Users/elvis/.codex`, outside the workspace-write boundary.

### Suggested Fix
Run the official Codex CLI with a scoped outer escalation while retaining `workspace-write` for the nested agent and an isolated working directory.

### Metadata
- Reproducible: yes
- Related Files: `/Users/elvis/.codex/state_5.sqlite`

### Resolution
- **Resolved**: 2026-08-06T15:51:17+08:00
- **Notes**: Retried the official Codex CLI with scoped outer authorization; the nested run remains confined to the temporary project copy.

---
## [ERR-20260708-001] apply_patch_context

**Logged**: 2026-07-08T08:45:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
The first policy update patch matched only part of a longer design-spec line and failed verification.

### Error
```
apply_patch verification failed: Failed to find expected lines
```

### Context
- Attempted to replace the Awesome/tutorial policy using an incomplete expected line.
- No files were partially modified.

### Suggested Fix
Read the exact line with `rg -n` and patch the complete source line.

### Metadata
- Reproducible: yes
- Related Files: docs/superpowers/specs/2026-06-29-github-project-digest-design.md

### Resolution
- **Resolved**: 2026-07-08T08:45:00+08:00
- **Notes**: Reapplied the update using the exact full line and verified the resulting policy and JSONL feedback.

---

## [ERR-20260707-001] github_project_scan

**Logged**: 2026-07-07T00:00:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
GitHub scanner hit sandbox DNS restrictions, then the approved anonymous GitHub API fallback hit the shared-IP rate limit.

### Error
```
Network error: <urlopen error [Errno 8] nodename nor servname provided, or not known>
API rate limit exceeded
```

### Context
- Researching reusable text-to-image and image-to-image web repositories.
- The fallback requested public repository metadata without authentication.

### Suggested Fix
Use authenticated GitHub API access when available; otherwise verify a small shortlist through live repository, commit, and license pages.

### Metadata
- Reproducible: yes
- Related Files: none
- See Also: ERR-20260704-001

### Resolution
- **Resolved**: 2026-07-07T00:00:00+08:00
- **Notes**: Continued with live GitHub web pages and clearly marked any metadata that could not be verified.

---
## [ERR-20260707-001] github_project_scan_tls_and_rate_limit

**Logged**: 2026-07-07T08:36:02+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
The live scanner first hit the sandbox DNS boundary, then a local Python CA verification failure; shortlist enrichment later exhausted the unauthenticated GitHub API quota.

### Error
```
Network error: [Errno 8] nodename nor servname provided, or not known
SSL: CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate
GitHub API rate limit reached; reset at 2026-07-07T01:23:50+00:00
```

### Context
- Three required `--no-cache` candidate searches were attempted.
- Per the skill, `--insecure` was used exactly once to verify connectivity and obtain the live layered pool.
- Exact-repository `--enrich` requests returned no usable data after quota exhaustion.

### Suggested Fix
Repair the local Python CA store and provide a valid `GITHUB_TOKEN` for future automation runs.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/daily/2026-07-07.md
- See Also: ERR-20260704-001, ERR-20260704-002

### Resolution
- **Resolved**: 2026-07-07T08:36:02+08:00
- **Notes**: Used live GitHub repository pages, raw README files and Commit/Release Atom feeds; no stale cache was represented as live data.

---

## [ERR-20260706-001] jq_tree_evidence_filter

**Logged**: 2026-07-06T08:35:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
Local GitHub tree evidence filtering failed because a jq regular expression was over-escaped through the shell.

### Error
```
jq: error: Invalid escape at line 1, column 4 (while parsing '"\\."')
```

### Context
- GitHub tree JSON downloads completed successfully; only the local display filter failed.
- The command embedded a complex regex in nested shell and jq quoting.

### Suggested Fix
Use simple `startswith`/`contains` predicates or a plain path list instead of a doubly escaped jq regex.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/daily/2026-07-06.md

### Resolution
- **Resolved**: 2026-07-06T08:35:00+08:00
- **Notes**: Replaced the regex with simple substring predicates; downloaded source data remained valid.

---

## [ERR-20260704-002] weekly_github_verification

**Logged**: 2026-07-04T12:32:23+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
Weekly shortlist enrichment could not use the configured GitHub CLI identity because its token was invalid, then the unauthenticated scanner quota was exhausted.

### Error
```
The token in default is invalid.
GitHub API rate limit reached; reset at 2026-07-04T04:52:17+00:00.
```

### Context
- `gh auth status -h github.com` failed before shortlist enrichment.
- One exact-repository `--enrich --no-cache` retry was attempted after approved network access.
- No API output from the failed scan was used as evidence.

### Suggested Fix
Re-authenticate `gh` before the next weekly run so the scanner can safely reuse `gh auth token`; continue limiting enrichment to the five-item shortlist.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/weekly/2026-W27.md
- See Also: ERR-20260702-001, ERR-20260704-001

### Resolution
- **Resolved**: 2026-07-04T12:32:23+08:00
- **Notes**: Used at most two live GitHub repository/release/commit pages per shortlisted repository and explicitly marked the one Release-label inconsistency.

---

## [ERR-20260704-001] github_project_scan

**Logged**: 2026-07-04T08:31:30+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
GitHub scanner could not resolve GitHub from the restricted sandbox on the first live-search attempt.

### Error
```
Network error: <urlopen error [Errno 8] nodename nor servname provided, or not known>
```

### Context
- Three required `--no-cache` candidate searches failed before returning data.
- This matches the recurring sandbox DNS boundary from prior digest runs.

### Suggested Fix
Rerun the identical scanner commands with approved network access; keep API enrichment limited to the shortlist.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/daily/2026-07-04.md
- See Also: ERR-20260702-001

### Resolution
- **Resolved**: 2026-07-04T08:35:00+08:00
- **Notes**: Reran the scanner with approved network access; after later API exhaustion, used GitHub repository, Release, Commit and Issue/PR pages and did not present stale cache as live evidence.

---
## [ERR-20260706-003] skill_path_lookup

**Logged**: 2026-07-06T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
The first skill read used a workspace-relative path even though the skill registry supplied a home-directory absolute path.

### Error
```
sed: /Users/elvis/Desktop/repo-signal/.agents/skills/using-superpowers/SKILL.md: No such file or directory
```

### Context
- Attempted to read the mandatory conversation skill before researching ScreenCoder alternatives.
- The registry path was `/Users/elvis/.agents/skills/using-superpowers/SKILL.md`.

### Suggested Fix
Always copy the exact absolute locator from the available-skills registry.

### Metadata
- Reproducible: yes
- Related Files: none

### Resolution
- **Resolved**: 2026-07-06T00:00:00+08:00
- **Notes**: Retried with the registry-provided absolute path.

---

## [ERR-20260708-002] zsh_empty_glob

**Logged**: 2026-07-08T09:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
An OpenSpec capability scan used an unmatched zsh glob and failed before checking the empty specs directory.

### Error
```
zsh: no matches found: openspec/specs/*/spec.md
```

### Context
- The repository had no active capability specs.
- No files were modified by the failed read.

### Suggested Fix
Use `find openspec/specs -type f -name spec.md` for optional file sets.

### Metadata
- Reproducible: yes
- Related Files: openspec/specs

### Resolution
- **Resolved**: 2026-07-08T09:05:00+08:00
- **Notes**: Re-ran discovery with `find`, confirmed there were no existing capability specs, and created a single new capability in the proposal.

---

## [ERR-20260708-003] zsh_reserved_history

**Logged**: 2026-07-08T19:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A verification command used zsh's reserved read-only `history` variable and stopped before the final consistency assertions.

### Error
```
zsh: read-only variable: history
```

### Context
- P1 merge and metadata assertions had already passed.
- Product files were not modified by the failed command.

### Suggested Fix
Use descriptive names such as `history_extra_count` in zsh verification scripts.

### Metadata
- Reproducible: yes
- Related Files: none

### Resolution
- **Resolved**: 2026-07-08T19:10:00+08:00
- **Notes**: Renamed the shell variable and reran the remaining consistency checks.

---

## [ERR-20260711-001] weekly_report_awk_validation

**Logged**: 2026-07-11T11:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The weekly-report field-order check double-escaped the numbered-heading regex when passing an awk program through a JavaScript string.

### Error
The check reported every field as unexpected and found zero projects even though the report used valid `## 1. Project` headings.

### Context
- Command: ad hoc awk schema validation for `data/github-project-digest/weekly/2026-W28.md`
- Root cause: `\\.` reached awk as an unintended double escape.

### Suggested Fix
Use `[.]` for literal dots in awk regexes embedded in JavaScript strings.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/weekly/2026-W28.md

### Resolution
- **Resolved**: 2026-07-11T11:00:00+08:00
- **Notes**: Verified that `/^## [1-5][.] /` matches all five weekly project headings before rerunning the full check.

---
