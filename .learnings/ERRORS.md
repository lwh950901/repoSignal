# Errors

## [ERR-20260701-001] git-commit

**Logged**: 2026-07-01T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary

Git could not create `.git/index.lock` under the workspace sandbox.

### Error

```text
fatal: Unable to create '/Users/elvis/Desktop/schedule/.git/index.lock': Operation not permitted
```

### Context

- Operation: stage and commit a newly written design specification.
- Environment: workspace files are writable, but `.git` is read-only without scoped escalation.

### Suggested Fix

Retry the same narrowly scoped Git command with explicit escalated permission.

### Metadata

- Reproducible: yes
- Related Files: docs/superpowers/specs/2026-07-01-github-project-gallery-design.md

### Resolution

- **Resolved**: 2026-07-01T00:00:00+08:00
- **Notes**: Use scoped escalation for Git index writes in this workspace.

---
