# Monthly Evidence Default Open Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every monthly Top 5 scoring and verification disclosure open on initial page load while retaining native collapse behavior.

**Architecture:** Keep the existing native `<details>` disclosure and add its boolean `open` attribute in the monthly report component. Protect the behavior with the existing source-level layout contract test; no client script or persisted state is needed.

**Tech Stack:** Astro, HTML `<details>`, Vitest

---

### Task 1: Default-open monthly evidence disclosure

**Files:**
- Modify: `src/components/layout-contract.test.ts`
- Modify: `src/components/MonthlyReportView.astro`

- [x] **Step 1: Write the failing contract assertion**

Change the existing monthly disclosure assertion to:

```ts
expect(view).toContain('<details class="monthly-evidence" open>');
```

- [x] **Step 2: Run the focused test and verify RED**

Run: `npm test -- src/components/layout-contract.test.ts`

Expected: the monthly section-navigation test fails because the component lacks the `open` attribute.

- [x] **Step 3: Add the minimal template behavior**

Change the disclosure opening tag to:

```astro
<details class="monthly-evidence" open>
```

- [x] **Step 4: Verify GREEN and project health**

Run:

```bash
npm test -- src/components/layout-contract.test.ts
npm run check
npm run build
git diff --check
```

Expected: all commands exit successfully; generated monthly pages render the disclosure with the HTML `open` attribute.

- [x] **Step 5: Review the scoped diff**

Run: `git diff -- src/components/layout-contract.test.ts src/components/MonthlyReportView.astro docs/superpowers/specs/2026-08-01-monthly-evidence-default-open-design.md docs/superpowers/plans/2026-08-01-monthly-evidence-default-open.md`

Expected: only the contract assertion, component attribute, design note, and implementation plan appear.
