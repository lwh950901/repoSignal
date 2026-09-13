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

## [ERR-20260813-001] daily_report_patch_generation

**Logged**: 2026-08-13T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
The first generated daily-report patch failed because Markdown inline-code backticks were interpreted as JavaScript template-literal delimiters.

### Error
`SyntaxError: Unexpected identifier 'find'`

### Context
- Operation: generate and apply `data/github-project-digest/daily/2026-08-13.md`
- Root cause: the report body was embedded in a JavaScript template literal without escaping its backticks.

### Suggested Fix
Use plain Chinese quotation marks in generated Markdown or escape all backticks before composing a tool patch.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/daily/2026-08-13.md

### Resolution
- **Resolved**: 2026-08-13T00:00:00+08:00
- **Notes**: Regenerated the report body without inline-code backticks before applying the patch.

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

## [ERR-20260811-001] daily_report_node_validation

**Logged**: 2026-08-11T14:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
An inline Node validation command double-escaped regex literals through the JavaScript tool string, producing an invalid-regexp-flags error.

### Error
`SyntaxError: Invalid regular expression flags`

### Context
- Command: ad hoc Node format validation for `data/github-project-digest/daily/2026-08-11.md`
- Root cause: regex escaping was interpreted once by the tool string and again by Node.

### Suggested Fix
Use line-prefix checks and string parsing for shell-embedded validation, or put complex regex validation in a checked-in script.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/daily/2026-08-11.md

### Resolution
- **Resolved**: 2026-08-11T14:20:00+08:00
- **Notes**: Replaced the regex-only command with a line-oriented Node validation. The first replacement still used a faulty heading-boundary lookup; direct per-heading slices confirmed the report fields before the final check.

---

## [ERR-20260818-001] temporary_trial_status_script

**Logged**: 2026-08-18T06:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: automation

### Summary
The temporary trial-status updater was referenced after its patch creation did not persist.

### Error
```text
python3: can't open file '/Users/elvis/Desktop/repo-signal/scripts/.tmp_update_trial_status_2026-08-18.py': [Errno 2] No such file or directory
```

### Context
- Operation: update `data/github-project-digest/trial-status.json` after the daily discovery run.
- Root cause: the transient helper file was not present when the command ran; the failed command did not modify the target JSON.

### Suggested Fix
After applying a transient helper patch, verify the file exists before execution; prefer a single direct patch or a checked-in reusable updater for automation state.

### Metadata
- Reproducible: unknown
- Related Files: data/github-project-digest/trial-status.json

### Resolution
- **Resolved**: 2026-08-18T06:25:00+08:00
- **Notes**: Trial status was updated via a direct JSON patch workflow and will be read back with `jq`.

---
## [ERR-20260826-001] shortlist_repo_metadata_shell_loop

**Logged**: 2026-08-26T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: automation

### Summary
The zsh metadata loop used the read-only variable name `status` and aborted before processing the shortlist.

### Error
```text
zsh:16: read-only variable: status
```

### Context
- Operation: fetch live GitHub repository metadata for shortlisted daily-discovery candidates.
- Root cause: `status` is reserved/read-only in zsh; the command had already created only the temporary detail directory and did not modify project data.

### Suggested Fix
Use task-specific variable names such as `repo_summary` in zsh loops and avoid common shell option names.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/candidates/2026-08-26.jsonl

### Resolution
- **Resolved**: 2026-08-26T00:00:00+08:00
- **Notes**: The rerun uses a non-reserved variable name.

---
## [ERR-20260827-001] portable_heading_statistics

**Logged**: 2026-08-27T20:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
A diagnostic heading-statistics pipeline used a BSD `sed` expression with an invalid delimiter form, then used `rg -h` expecting filename suppression even though ripgrep treats it as help.

### Error
```text
sed: bad flag in substitute command: '#'
rg -h printed ripgrep help instead of matched lines
```

### Context
- Operation: count repeated feasibility-plan headings across dated Markdown reports.
- Root cause: mixed assumptions from different command-line implementations.
- No source report or automation state was modified by either failed pipeline.

### Suggested Fix
Use `rg --no-filename` and perform prefix removal/counting with a small portable `awk` program.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/feasibility/*.md

### Resolution
- **Resolved**: 2026-08-27T20:00:00+08:00
- **Notes**: Replaced the pipeline with `rg --no-filename ... | awk ... | sort | uniq -c`.

---
## [ERR-20260902-001] automation_memory_patch_context

**Logged**: 2026-09-02T06:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
An automation-memory append patch used stale surrounding text and failed verification before changing any file.

### Error
```text
apply_patch verification failed: Failed to find expected lines in /Users/elvis/.codex/automations/github/memory.md
```

### Context
- Operation: append the 2026-09-02 GitHub digest run to the automation memory file.
- Root cause: the patch context was copied from an earlier truncated memory view rather than the exact current tail.
- No target digest file was modified by the failed patch.

### Suggested Fix
Read the exact file tail immediately before patching and use a minimal append context.

### Metadata
- Reproducible: yes
- Related Files: /Users/elvis/.codex/automations/github/memory.md

### Resolution
- **Resolved**: 2026-09-02T06:00:00+08:00
- **Notes**: Re-read the memory tail; the correct append is pending in the next operation.

---

## [ERR-20260906-001] daily-feasibility-overlap-analysis

**Logged**: 2026-09-06T06:14:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
The read-only overlap-analysis script had an unclosed template interpolation.

### Error
```text
Unexpected token `ident`. Expected `}`
```

### Context
- Operation: compare daily feasibility-plan titles and component sets for 2026-W35 and 2026-W36.
- Cause: `p.title` in a JavaScript template literal lacked its closing brace.
- No repository content was read or changed by the failed script beyond attempting to parse local files.

### Suggested Fix
Use a corrected template literal and validate the script before relying on its counts.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/feasibility/*.md

### Resolution
- **Resolved**: 2026-09-06T06:14:00+08:00
- **Notes**: Corrected the interpolation before rerunning the analysis.

---

## [ERR-20260906-002] daily-feasibility-overlap-analysis

**Logged**: 2026-09-06T06:15:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
The corrected script completed but matched zero plans because the shell-embedded regular expression was over-escaped.

### Error
```text
planCounts: W35=0, W36=0
```

### Context
- Operation: parse local feasibility Markdown headings in a Node one-liner.
- Cause: regex escaping crossed JavaScript-string, shell and regex layers incorrectly.
- The empty result was rejected before any reporting or file change.

### Suggested Fix
For shell-embedded one-off analysis, parse Markdown lines with string operations instead of layered regular-expression escaping.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/feasibility/*.md

### Resolution
- **Resolved**: 2026-09-06T06:15:00+08:00
- **Notes**: Replaced the regex parser with explicit heading and URL string parsing.

---

## [ERR-20260907-001] daily-github-digest-format-check

**Logged**: 2026-09-07T05:42:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The first fixed-format self-check rejected a valid report because its heading regex omitted the space after the numbered slot marker.

### Error
```text
AssertionError: []
```

### Context
- Operation: validate the generated 2026-09-07 GitHub digest headings and required fields.
- Cause: the check expected `### 1.爆发型` while the required report format is `### 1. 爆发型`.
- No generated digest file was changed by the failed check.

### Suggested Fix
Keep the checker regex aligned with the literal fixed format, including the space after the numeric period; rerun the complete validation before proceeding.

### Metadata
- Reproducible: yes
- Related Files: /Users/elvis/Desktop/repo-signal/data/github-project-digest/daily/2026-09-07.md

### Resolution
- **Resolved**: 2026-09-07T05:42:30+08:00
- **Notes**: Corrected the validation expression and reran the checks.

---

## [ERR-20260907-002] apply_patch

**Logged**: 2026-09-07T15:50:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
One generated patch declared two update operations for the same radar file, so `apply_patch` rejected the entire patch.

### Error
```text
apply_patch verification failed: invalid patch: multiple operations target data/github-project-digest/radar/2026-W36.md
```

### Context
- Operation: mechanically reduce three five-column feasibility tables in both W36 radar artifacts to three columns and normalize the final newline.
- Cause: table hunks and the trailing-newline hunk were emitted as separate `Update File` operations for the same path.
- The failed patch was atomic and did not alter either W36 file.

### Suggested Fix
Emit one `Update File` operation per path and place all hunks for that path inside it.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/radar/2026-W36.md, data/github-project-digest/distribution-drafts/2026-W36-wechat.md

### Resolution
- **Resolved**: 2026-09-07T15:51:00+08:00
- **Notes**: Regenerated the patch with one operation per file; it applied successfully.

---

## [ERR-20260907-003] apply_patch

**Logged**: 2026-09-07T16:03:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
`apply_patch` rejected a reverse Git diff because its hunk headers contained line-number ranges.

### Error
```text
apply_patch verification failed: Failed to find context '-25,13 +25,13 @@'
```

### Context
- Operation: restore an unintended feasibility-file edit using a reverse Git diff while still applying the change through `apply_patch`.
- Cause: standard Git hunk headers such as `@@ -25,13 +25,13 @@` are not accepted by this patch wrapper.
- The failed patch did not change the file.

### Suggested Fix
Normalize numbered Git hunk headers to plain `@@` before passing the reverse diff to `apply_patch`.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/feasibility/2026-09-07.md

### Resolution
- **Resolved**: 2026-09-07T16:04:00+08:00
- **Notes**: Removed line-number ranges from the hunk headers; the reverse patch restored the content, then the missing trailing blank line was restored separately to make the file byte-identical to HEAD.

---

## [ERR-20260907-004] qlmanage-svg-preview

**Logged**: 2026-09-07T17:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
Quick Look could not render the generated SVG inside the managed filesystem sandbox.

### Error
```text
sandbox initialization failed: invalid data type of path filter; expected pattern, got boolean
```

### Context
- Operation: render `public/brand/reposignal-logo.svg` to a temporary PNG for visual inspection.
- A follow-up attempt with the built-in image viewer also reported `invalid or unsupported image data` because it does not accept SVG input.
- An in-app browser attempt was blocked because its URL policy does not allow local `file://` URLs.
- The SVG source and generated project assets were not modified by the failed preview command.

### Suggested Fix
Use an in-app browser for visual SVG previews; use the image viewer only for supported raster formats.

### Metadata
- Reproducible: yes
- Related Files: public/brand/reposignal-logo.svg

### Resolution
- **Resolved**: 2026-09-07T17:20:30+08:00
- **Notes**: Re-ran Quick Look with the required filesystem approval, produced a temporary PNG successfully, and visually inspected the rendered logo. The SVG remains the canonical asset.

---

## [ERR-20260907-005] apply_patch

**Logged**: 2026-09-07T17:32:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
An SVG replacement patch repeated the known unsupported delete-and-add operation for one path.

### Error
```text
apply_patch verification failed: invalid patch: multiple operations target /Users/elvis/Desktop/repo-signal/public/brand/reposignal-logo.svg
```

### Context
- Operation: replace the text-bearing RepoSignal SVG with a mark-only SVG.
- The failed patch was atomic and left the existing SVG unchanged.

### Suggested Fix
Use a single `Update File` operation when replacing all content at an existing path.

### Metadata
- Reproducible: yes
- Related Files: public/brand/reposignal-logo.svg
- See Also: ERR-20260907-002

### Resolution
- **Resolved**: 2026-09-07T17:32:30+08:00
- **Notes**: Reissued the replacement as one `Update File` operation; it applied successfully.

---

## [ERR-20260907-006] svg-no-text-check

**Logged**: 2026-09-07T17:34:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The first no-visible-text SVG check incorrectly matched accessible metadata.

### Error
```text
2:  <title id="title">RepoSignal 开源雷达图形标</title>
```

### Context
- Operation: verify that the final Logo has no visible text.
- Cause: the check searched for brand words in the entire XML instead of checking only for rendered `<text>` elements.

### Suggested Fix
Check for SVG `<text>` elements while allowing accessible `<title>` and `<desc>` metadata.

### Metadata
- Reproducible: yes
- Related Files: public/brand/reposignal-logo.svg

### Resolution
- **Resolved**: 2026-09-07T17:34:30+08:00
- **Notes**: Narrowed the verification to rendered `<text>` elements and reran the complete asset checks.

---

## [ERR-20260910-001] exec-command-workdir-typo

**Logged**: 2026-09-10T21:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
An exact GitHub scan failed before launch because the workspace path was mistyped.

### Error
```text
Failed to create unified exec process: No such file or directory (os error 2)
```

### Context
- Operation: run `github_project_scan.py` for the `teamai-cli` shortlist candidate.
- The command used `/Users/elvis1/Desktop/repo-signal` instead of `/Users/elvis/Desktop/repo-signal`.
- No process started and no files were changed.

### Suggested Fix
Reuse the environment-provided workspace path exactly and validate `workdir` before launching external scans.

### Metadata
- Reproducible: yes
- Related Files: none

### Resolution
- **Resolved**: 2026-09-10T21:20:30+08:00
- **Notes**: Corrected the working directory for subsequent commands.

---

## [ERR-20260910-002] candidate-ledger-manual-entry

**Logged**: 2026-09-10T21:30:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: docs

### Summary
Manual candidate-ledger authoring introduced one invalid JSON object and several misspelled fields or URLs.

### Error
```text
jq: parse error: ':' not as part of an object at line 4, column 205
```

### Context
- Operation: add backfill ledgers for 2026-09-08 through 2026-09-10.
- Root cause: several records were typed manually without validating each JSONL line before moving on.

### Suggested Fix
Run `jq -c .` and a schema-key check immediately after every JSONL patch; prefer the existing candidate-ledger utility when importing larger scan results.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/candidates/2026-09-09.jsonl, data/github-project-digest/candidates/2026-09-10.jsonl

### Resolution
- **Resolved**: 2026-09-10T21:31:00+08:00
- **Notes**: Corrected the malformed license field, fork key, repository URLs, and textual typos; queued full JSONL and schema verification.

---

## [ERR-20260910-003] verification-shell-quoting

**Logged**: 2026-09-10T21:36:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The first combined verification command did not start because an `rg` pattern contained an unmatched shell quote.

### Error
```text
zsh:4: unmatched '
```

### Context
- A stray quoted fragment was appended after the typo-detection regex.
- No validation result was produced and no files were changed.

### Suggested Fix
Keep the regex in one balanced single-quoted argument and list paths separately.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest

### Resolution
- **Resolved**: 2026-09-10T21:36:30+08:00
- **Notes**: Reissued the verification command with balanced quoting.

---

## [ERR-20260910-004] verification-jq-expression

**Logged**: 2026-09-10T21:42:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The final history summary check used an unbalanced jq object expression.

### Error
```text
jq: error: syntax error, unexpected INVALID_CHARACTER
```

### Context
- One closing parenthesis was missing in the `dates` value expression.
- Earlier checks in the same shell ran, but the command exited before diff and status checks.

### Suggested Fix
Split dense jq summaries into smaller expressions and validate them independently.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/history.jsonl

### Resolution
- **Resolved**: 2026-09-10T21:42:30+08:00
- **Notes**: Replaced the dense expression with a simpler valid jq summary and reran the full verification.

---

## [ERR-20260911-001] shell-quote-check

**Logged**: 2026-09-11T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: automation

### Summary
The first read-only history deduplication loop used an unmatched shell quote.

### Error
```text
zsh:1: unmatched '
```

### Context
- The loop embedded a quoted repository variable inside a single-quoted `rg` expression.
- No files were changed; the check was rerun with a simpler argument form.

### Suggested Fix
Prefer `rg -F -- "$repo"` or pass structured values through a small script instead of nested shell quoting.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/history.jsonl

### Resolution
- **Resolved**: 2026-09-11T00:01:00+08:00
- **Notes**: Reissued the check using fixed-string matching and explicit arguments.

---

## [ERR-20260911-002] session-json-extractor

**Logged**: 2026-09-11T14:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
An ad-hoc Node.js command for extracting prior automation evidence omitted a closing brace.

### Error
```text
SyntaxError: Unexpected end of input
```

### Context
- The command only read a local Codex session JSONL file.
- No project artifact was changed.

### Suggested Fix
Use a smaller parser with a single output path and validate its brace structure before execution.

### Metadata
- Reproducible: yes
- Related Files: /Users/elvis/.codex/sessions/2026/09/11/rollout-2026-09-11T05-32-02-01a08d3c-1fb1-7263-b694-378b7ca82f0a.jsonl

### Resolution
- **Resolved**: 2026-09-11T14:10:00+08:00
- **Notes**: Switched to a simpler parser that extracts only the required repository fields.

---

## [ERR-20260911-003] session-output-shape

**Logged**: 2026-09-11T14:12:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
An ad-hoc session parser assumed a tool-output block was iterable when its payload used a different shape.

### Error
```text
TypeError: x.payload.output is not iterable
```

### Context
- The failed command was read-only and did not alter project files.

### Suggested Fix
Inspect one event's payload shape before iterating, or use live GitHub evidence when it is already required.

### Metadata
- Reproducible: yes
- Related Files: /Users/elvis/.codex/sessions/2026/09/11/rollout-2026-09-11T05-32-02-01a08d3c-1fb1-7263-b694-378b7ca82f0a.jsonl

### Resolution
- **Resolved**: 2026-09-11T14:12:00+08:00
- **Notes**: Avoided the session-output path and continued with a narrow live Trending query.

---

## [ERR-20260911-004] web-batch-syntax

**Logged**: 2026-09-11T14:14:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A combined GitHub page click and text-find request was rejected by the web tool parser.

### Error
```text
SyntaxError: Unexpected string
```

### Context
- The request was read-only and no project artifact changed.

### Suggested Fix
Use a single direct raw-file request for the required license evidence instead of mixing independent web operations.

### Metadata
- Reproducible: unknown
- Related Files: data/github-project-digest/daily/2026-09-11.md

### Resolution
- **Resolved**: 2026-09-11T14:14:00+08:00
- **Notes**: Switched to direct raw GitHub license retrieval.
## [ERR-20260913-001] radar-ad-hoc-score-check

**Logged**: 2026-09-13T20:18:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
An ad-hoc radar preflight rejected valid market-opportunity prose because it searched globally for the phrase `组件供给` instead of limiting the check to score-detail lines.

### Error
```text
AssertionError
```

### Context
- The W37 draft correctly preserved the selected feasibility reports' market-opportunity text.
- The forbidden output is the component-scoring breakdown after `方案评分`, not ordinary prose containing the same words.

### Suggested Fix
Scope the assertion to `方案评分` lines and reject parentheses or named score components only on those lines.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/distribution-drafts/2026-W37-wechat.md.tmp

### Resolution
- **Resolved**: 2026-09-13T20:18:00+08:00
- **Notes**: Replaced the global substring assertion with a line-scoped score-format assertion.

---
## [ERR-20260913-002] tool-wrapper-syntax

**Logged**: 2026-09-13T20:27:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A finalization command did not start because the JavaScript tool wrapper had a missing closing parenthesis.

### Error
```text
SyntaxError: missing ) after argument list
```

### Context
- The failure occurred before shell execution, so no draft or radar file was moved.

### Suggested Fix
Keep the wrapper minimal and validate the `text(r.output)` call before execution.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/distribution-drafts/2026-W37-wechat.md.tmp

### Resolution
- **Resolved**: 2026-09-13T20:27:00+08:00
- **Notes**: Reissued the unchanged finalization command with a valid wrapper.

---
## [ERR-20260913-003] tool-wrapper-syntax

**Logged**: 2026-09-13T22:15:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A read-only source inspection did not start because stray text was inserted into the JavaScript `text()` wrapper.

### Error
```text
SyntaxError: missing ) after argument list
```

### Context
- The shell command was never executed and no repository artifact changed.

### Suggested Fix
Use the minimal wrapper `text(r.output);` for command output.

### Metadata
- Reproducible: yes
- Related Files: scripts/opportunity_analysis.py, scripts/weekly_feasibility_selector.py

### Resolution
- **Resolved**: 2026-09-13T22:15:00+08:00
- **Notes**: Reissued the same read-only inspection with a valid wrapper.

---
