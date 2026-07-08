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
