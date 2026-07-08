## Context

The digest already has a GitHub scanner, Markdown reports, `history.jsonl`, `feedback.jsonl`, and `trial-status.json`. What it lacks is the middle record: which repositories the searches surfaced before final selection. The solution must remain file-based, inspectable in Git, and usable without new dependencies.

## Goals / Non-Goals

**Goals:**

- Produce one valid JSONL ledger for each daily discovery run.
- Deduplicate repositories found by multiple search lanes while preserving every lane and source.
- Retain enough state to explain whether a candidate was rejected, shortlisted, published as a primary recommendation, or published as an extra discovery.
- Make the smallest useful change around the existing scanner and data layout.

**Non-Goals:**

- Building a crawler, database, dashboard, scheduler, or historical metrics warehouse.
- Replacing the scanner, Markdown reports, `history.jsonl`, feedback, or run status.
- Automating final qualitative scoring or risk judgment.

## Decisions

### One date-keyed JSONL ledger

Write `data/github-project-digest/candidates/YYYY-MM-DD.jsonl`. Each line represents one canonical `owner/repo` and contains the observation date, repository URL, discovery lanes, sources, available GitHub facts, verification state, disposition, and reason.

Alternative considered: separate raw, verified, and rejected files. Rejected because status fields provide the same audit trail without multiplying files.

### Reuse scanner JSON and the Python standard library

Add one small utility under `scripts/` that reads one or more JSON arrays produced by the installed GitHub scanner, normalizes repository names case-insensitively, merges duplicate lanes and sources, and emits deterministic JSONL. Invalid input fails without replacing an existing ledger.

Alternative considered: shell plus `jq`. Rejected because the automation environment already requires Python for the scanner, while a Python utility can provide atomic writes and one portable self-check without another runtime assumption.

### Keep judgment outside the normalizer

New records start with `status: discovered` and `verified: false`. During the existing review workflow, the automation updates shortlisted and published records with `status`, `reason`, and verification evidence. The utility does not score projects or decide recommendation slots.

Alternative considered: encode scoring and selection in the utility. Rejected because those decisions require live evidence and qualitative judgment already handled by the digest workflow.

### Track all displayed projects in history

`history.jsonl` remains the compact cross-run index. Published primary and extra discoveries are recorded with a `role` field, while the larger daily candidate pool stays only in the date-keyed ledger. This prevents duplicate resurfacing without turning history into a raw search dump.

## Risks / Trade-offs

- Candidate files grow over time → one compact JSONL file per run is acceptable; add retention only if repository size becomes measurable pain.
- Later status edits mean the daily file is not a strict event log → prefer one final atomic rewrite at the end of a run; an event-sourced model is unnecessary.
- Scanner fields can be absent after API degradation → preserve missing values as `null` and record verification/fallback details instead of guessing.
- Repository renames can appear as separate identities → use canonical `owner/repo` from live GitHub facts when available; defer rename history until a real collision occurs.

## Migration Plan

Start with the next daily run. Do not backfill old raw candidates because they cannot be reconstructed reliably. Add today's manually reviewed extra discoveries to history with `role: extra`, then let future runs produce ledgers prospectively.

Rollback is deletion of the utility and `candidates/` directory; existing reports and history remain readable.

## Open Questions

None. Retention and rename tracking remain deliberately deferred.
