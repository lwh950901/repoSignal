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
