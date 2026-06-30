# Errors

## [ERR-20260629-001] github_project_scan

**Logged**: 2026-06-29T12:34:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
Unauthenticated GitHub Search API exhausted its rate limit during the initial daily digest candidate scan.

### Error
```
GitHub API rate limit reached; reset at 2026-06-29T04:35:29+00:00.
```

### Context
- Four enriched, cache-disabled search scans were started concurrently.
- No candidate data was returned by those scans.
- Final repositories were verified after the reset with cache disabled.

### Suggested Fix
Use `GITHUB_TOKEN` when available and avoid parallel enriched searches against the unauthenticated limit; use GitHub pages as the fallback and reserve API calls for shortlisted repositories.

### Metadata
- Reproducible: yes
- Related Files: data/github-project-digest/trial-status.json

### Resolution
- **Resolved**: 2026-06-29T12:35:40+08:00
- **Notes**: Reran three shortlisted repository checks after reset and received live API data.

---

## [ERR-20260629-002] github_digest_history_readback

**Logged**: 2026-06-29T12:39:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
Concurrent automation appended three history rows between the initial read and this run's append.

### Error
```
Expected 3 history rows after append; read back 6 valid rows.
```

### Context
- The history file was empty at the initial read.
- Three unrelated same-date rows appeared before this run appended its three recommendations.
- The two sets had no repository overlap.

### Suggested Fix
Treat JSONL history as append-only shared state: re-read immediately before append, deduplicate by normalized repository and date window, preserve unrelated concurrent rows, and validate only the rows owned by the current run.

### Metadata
- Reproducible: unknown
- Related Files: data/github-project-digest/history.jsonl, data/github-project-digest/trial-status.json

### Resolution
- **Resolved**: 2026-06-29T12:39:00+08:00
- **Notes**: Preserved all six rows, confirmed no repository overlap, and updated trial status to record the concurrency anomaly.

---
