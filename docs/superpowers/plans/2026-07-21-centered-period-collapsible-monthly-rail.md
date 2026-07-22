# Centered Period Navigation and Collapsible Monthly Rail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the 月/周/日 switcher centered on the viewport content area and let desktop readers collapse the monthly archive into a discoverable narrow rail.

**Architecture:** Convert the shared header from flex to a symmetric three-column grid so the center navigation is independent of the brand and search widths. Add one progressively enhanced button to the monthly rail; a `data-rail-collapsed` state on the existing shell drives CSS grid contraction and accessible button text, while mobile keeps the existing month selector.

**Tech Stack:** Astro 7, TypeScript, CSS, Vitest

---

### Task 1: Lock the layout contract with a failing test

**Files:**
- Create: `src/components/layout-contract.test.ts`

- [x] **Step 1: Write the failing test**

```ts
import { readFile } from "node:fs/promises";
import { describe, expect, test } from "vitest";

describe("navigation layout contract", () => {
  test("places the period switcher in the header center column", async () => {
    const layout = await readFile(new URL("../layouts/BaseLayout.astro", import.meta.url), "utf8");
    expect(layout).toContain('<div class="site-period-navigation">');
    expect(layout.indexOf("site-period-navigation")).toBeLessThan(layout.indexOf("site-actions"));
  });

  test("provides an accessible progressively enhanced desktop monthly rail toggle", async () => {
    const view = await readFile(new URL("./MonthlyReportView.astro", import.meta.url), "utf8");
    expect(view).toContain("data-monthly-rail-toggle");
    expect(view).toContain('aria-expanded="true"');
    expect(view).toContain("data-rail-collapsed");
  });

  test("keeps the mobile month selector navigable", async () => {
    const view = await readFile(new URL("./MonthlyReportView.astro", import.meta.url), "utf8");
    expect(view).toContain("window.location.assign(reportSelect.value)");
  });
});
```

- [x] **Step 2: Run the focused test and verify RED**

Run: `npm test -- src/components/layout-contract.test.ts`

Expected: FAIL because the center wrapper and monthly rail toggle do not exist yet.

### Task 2: Implement the centered header and narrow rail

**Files:**
- Modify: `src/layouts/BaseLayout.astro`
- Modify: `src/components/MonthlyReportView.astro`
- Modify: `src/styles/global.css`

- [x] **Step 1: Move the period switcher into the header center column**

```astro
<div class="site-period-navigation">
  <PeriodSwitcher active={activePeriod} links={periodLinks} />
</div>
<nav class="site-actions" aria-label="主要导航">
  <button class="search-trigger" type="button" data-search-open aria-label="打开项目搜索">…</button>
</nav>
```

- [x] **Step 2: Add the monthly rail toggle and minimal state script**

```astro
<button class="monthly-rail-toggle" type="button" data-monthly-rail-toggle aria-expanded="true">
  <span class="monthly-rail-toggle__icon" aria-hidden="true">←</span>
  <span class="monthly-rail-toggle__label">收起归档</span>
</button>

<script>
  const shell = document.querySelector<HTMLElement>(".monthly-shell");
  const toggle = shell?.querySelector<HTMLButtonElement>("[data-monthly-rail-toggle]");
  const reportSelect = shell?.querySelector<HTMLSelectElement>("[data-report-select]");
  shell?.classList.add("is-enhanced");
  toggle?.addEventListener("click", () => {
    const collapsed = shell?.toggleAttribute("data-rail-collapsed") ?? false;
    toggle.setAttribute("aria-expanded", String(!collapsed));
  });
  reportSelect?.addEventListener("change", () => window.location.assign(reportSelect.value));
</script>
```

- [x] **Step 3: Add symmetric header columns and desktop rail transition**

```css
.site-header { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); }
.site-period-navigation { grid-column: 2; justify-self: center; }
.site-actions { grid-column: 3; justify-self: end; }
.monthly-rail-toggle { display: none; }
.monthly-shell.is-enhanced .monthly-rail-toggle { display: grid; }
.monthly-shell { transition: grid-template-columns .2s ease; }
.monthly-shell[data-rail-collapsed] { grid-template-columns: 3.25rem minmax(0, 1fr); }
```

- [x] **Step 4: Run the focused test and verify GREEN**

Run: `npm test -- src/components/layout-contract.test.ts`

Expected: PASS.

### Task 3: Verify responsive behavior and specifications

**Files:**
- Modify: `openspec/changes/redesign-monthly-business-research/specs/ranked-monthly-reports/spec.md`
- Modify: `openspec/changes/redesign-monthly-business-research/design.md`
- Modify: `openspec/changes/redesign-monthly-business-research/tasks.md`

- [x] **Step 1: Run automated verification**

Run: `npm test && npm run check && npm run build && openspec validate redesign-monthly-business-research --strict`

Expected: all commands exit 0.

- [x] **Step 2: Inspect desktop and mobile output**

Run the site and confirm at desktop width that the switcher is geometrically centered and the rail contracts to a narrow visible control. At 360px confirm the toggle is hidden and the existing month selector remains visible.

- [x] **Step 3: Mark OpenSpec increment tasks complete**

Change tasks 8.1–8.4 from `- [ ]` to `- [x]` after their matching verification succeeds.
