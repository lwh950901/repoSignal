## 1. Candidate ledger utility

- [x] 1.1 Add one Python standard-library utility that reads scanner JSON arrays, normalizes and deduplicates repositories, preserves lanes and sources, and atomically writes deterministic date-keyed JSONL.
- [x] 1.2 Add a runnable self-check covering case-insensitive deduplication, required fields, deterministic output, and malformed-input protection.

## 2. Digest integration

- [x] 2.1 Document the candidate record contract and daily ledger step in the existing digest design baseline.
- [x] 2.2 Record today's published extra discoveries in `history.jsonl` with `role: extra`, and require future primary and extra history rows to include a role.
- [x] 2.3 Update the daily run-status contract to report candidate counts by lane, final disposition counts, and scanner fallback state.

## 3. Verification

- [x] 3.1 Run the utility self-check, validate generated JSONL and history JSONL, and validate the OpenSpec change against the completed implementation.

## 4. P1 Review Fixes

- [x] 4.1 Normalize duplicate scanner observations through the same field extraction used for new records, so later `stargazers_count`, `forks_count`, structured license, and `pushed_at` values replace stale facts; extend the self-check with this regression case.
- [x] 4.2 Accept real discovery lane and source metadata through the CLI instead of emitting `lane-N` and `scanner` placeholders; verify merged output preserves every supplied lane and source.
- [x] 4.3 Reconcile all published extra discoveries across the daily report, `history.jsonl`, and `trial-status.json`, including `HKUDS/DeepTutor`, and verify the counts and roles agree.
