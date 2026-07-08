## Why

The daily digest records only published recommendations, so missed projects, duplicate search hits, and rejection reasons disappear after each run. A minimal candidate ledger is needed to make search coverage auditable and improve discovery without adding a database or a new pipeline framework.

## What Changes

- Add one append-only JSONL candidate ledger per daily run.
- Normalize candidates from existing GitHub searches around a canonical repository identifier.
- Record each candidate's discovery lane, source, verification state, final disposition, and reason.
- Keep the current Markdown reports, feedback file, history file, scanner, and run-status file rather than introducing parallel stores.
- Add one runnable check for normalization, deduplication, and valid JSONL output.

## Capabilities

### New Capabilities

- `candidate-ledger`: Capture, deduplicate, and audit every repository considered during a daily discovery run.

### Modified Capabilities

None.

## Impact

- `scripts/`: one small standard-library candidate ledger utility.
- `data/github-project-digest/candidates/`: date-keyed JSONL candidate ledgers.
- `docs/superpowers/specs/2026-06-29-github-project-digest-design.md`: daily workflow and candidate record contract.
- No new runtime dependency, database, or external service.
