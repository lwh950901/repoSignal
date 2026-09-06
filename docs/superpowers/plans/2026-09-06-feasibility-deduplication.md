# Feasibility Deduplication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give feasibility plans stable family/variant identities, reduce repeated component selection, and prevent a weekly radar from republishing a plan family used in the previous four ISO weeks.

**Architecture:** Keep daily project discovery and scoring in `scripts/opportunity_analysis.py`, adding pure identity/history/selection helpers around the existing templates. Add a focused weekly selector that reads Monday–Saturday feasibility Markdown plus the previous four radar articles and returns at most three eligible source plans. Existing Markdown remains readable through title-and-link fallback parsing; newly generated daily plans expose their identity for auditability.

**Tech Stack:** Python 3 standard library, `unittest`, Markdown reports, existing Astro/Vitest validation.

---

### Task 1: Stable plan family and variant identity

**Files:**
- Modify: `scripts/opportunity_analysis.py`
- Create: `scripts/test_opportunity_analysis.py`

- [x] **Step 1: Write failing identity tests**

Add tests which assert that two plans with the same fixed template and different component sets share a `plan_family`, while their `variant` values differ and are independent of component order. Add a parser compatibility test proving that older Markdown without an explicit identity line derives the same family and variant from its heading and GitHub links.

- [x] **Step 2: Run the identity tests and verify RED**

Run: `python3 -m unittest scripts.test_opportunity_analysis -v`

Expected: FAIL because `plan_family`, `plan_variant`, and `parse_plan_identities` do not exist.

- [x] **Step 3: Implement identity helpers**

Add stable `family` slugs to fixed templates. Implement:

```python
def plan_family(name):
    normalized = normalize_plan_name(name)
    return TEMPLATE_FAMILIES.get(normalized, "custom-" + stable_digest(normalized))

def plan_variant(repositories):
    normalized = sorted({normalize_repo(repo) for repo in repositories if normalize_repo(repo)})
    return stable_digest("\n".join(normalized))
```

Attach both keys to every generated combo and render one `**方案身份**` line. Parse older reports by falling back to the normalized heading and repository links.

- [x] **Step 4: Run the identity tests and verify GREEN**

Run: `python3 -m unittest scripts.test_opportunity_analysis -v`

Expected: PASS.

### Task 2: Component reuse penalty and variable output count

**Files:**
- Modify: `scripts/opportunity_analysis.py`
- Modify: `scripts/test_opportunity_analysis.py`

- [x] **Step 1: Write failing selection tests**

Add tests proving that a lower-reuse project beats an otherwise equivalent frequently reused project, and that portfolio selection may return one or two plans when later candidates fall below the novelty threshold. Add a regression test proving there is no fallback that republishes a blocked family.

- [x] **Step 2: Run the selection tests and verify RED**

Run: `python3 -m unittest scripts.test_opportunity_analysis -v`

Expected: FAIL because reuse-aware selection and variable-count portfolio selection do not exist.

- [x] **Step 3: Implement reuse-aware selection**

Load component occurrence counts from the previous seven feasibility dates. Rank slot candidates using their existing tag/today score minus a deterministic per-occurrence penalty. Generate all eligible template combos, then greedily select at most three with additional penalties for repositories already used by a selected plan. Reject candidates whose adjusted score drops below the existing medium threshold of 70.

Remove the blocked-plan fallback in `main`; an empty combination list is valid and is rendered by the existing no-combo branch.

- [x] **Step 4: Run the selection tests and verify GREEN**

Run: `python3 -m unittest scripts.test_opportunity_analysis -v`

Expected: PASS.

### Task 3: Four-week hard deduplication for weekly radar selection

**Files:**
- Create: `scripts/weekly_feasibility_selector.py`
- Create: `scripts/test_weekly_feasibility_selector.py`
- Modify: `package.json`

- [x] **Step 1: Write failing weekly-selection tests**

Build a temporary data root containing six current-week feasibility files and four earlier radar files. Assert that a family found in any earlier radar is excluded even when its variant changed, two remaining families are returned without padding, and source date, score, family, variant, and repositories are preserved.

- [x] **Step 2: Run the weekly tests and verify RED**

Run: `python3 -m unittest scripts.test_weekly_feasibility_selector -v`

Expected: FAIL because the selector module does not exist.

- [x] **Step 3: Implement the selector CLI**

Create a standard-library CLI:

```text
python3 scripts/weekly_feasibility_selector.py 2026-W36 --data-root data/github-project-digest
```

It must compute the ISO Monday–Saturday range, read every existing non-empty feasibility input while reporting missing dates without blocking the radar's main article, parse all candidates, deduplicate by family while retaining the best variant, exclude families from the previous four radar issues, apply component-overlap penalties among selected plans, and emit JSON with `candidateCount`, `deduplicatedCount`, `blockedFamilies`, and `selected` (0–3 entries). It must never fill vacancies with blocked or low-novelty plans.

Add `check:weekly-feasibility` to `package.json` for the current ISO week via an explicit week argument supplied by the automation.

- [x] **Step 4: Run the weekly tests and verify GREEN**

Run: `python3 -m unittest scripts.test_weekly_feasibility_selector -v`

Expected: PASS.

### Task 4: Wire the radar automation and verify end to end

**Files:**
- Modify: Codex automation `automation` prompt through the automation API
- Verify: `scripts/opportunity_analysis.py`
- Verify: `scripts/weekly_feasibility_selector.py`
- Verify: `src/lib/radar.test.ts`

- [x] **Step 1: Update the automation prompt**

Require the weekly radar task to run the selector for the current ISO week, use only its `selected` feasibility entries, accept 0–3 entries without failure, and report blocked families and component-overlap decisions. Preserve all existing requirements for six daily reports, weekly input, Luna review, and final file equality.

- [x] **Step 2: Run focused Python tests**

Run: `python3 -m unittest scripts.test_opportunity_analysis scripts.test_weekly_feasibility_selector -v`

Expected: PASS.

- [x] **Step 3: Run the actual W36 selector audit**

Run: `python3 scripts/weekly_feasibility_selector.py 2026-W36 --data-root data/github-project-digest`

Expected: JSON selecting at most three plans, with any family present in W32–W35 radar excluded.

- [x] **Step 4: Run existing radar regression tests**

Run: `npx vitest run src/lib/radar.test.ts`

Expected: PASS.

- [x] **Step 5: Check formatting and worktree scope**

Run: `git diff --check`

Expected: no output and exit code 0. Confirm no daily, weekly, or radar article was rewritten by the implementation.
