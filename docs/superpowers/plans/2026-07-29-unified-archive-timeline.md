# Unified Archive Timeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the monthly, weekly, and daily left archive menus use one shared daily-style timeline.

**Architecture:** Add a focused `ArchiveTimeline.astro` presentation component that accepts normalized labels, URLs, and current-state flags. Keep report-specific data and mobile selectors in their existing owners, and replace only the divergent desktop list markup.

**Tech Stack:** Astro components, TypeScript props, CSS, Vitest contract tests

---

## File Structure

- Create `src/components/ArchiveTimeline.astro`: render the shared ordered timeline, latest marker, and current-page semantics.
- Modify `src/components/DateRail.astro`: normalize weekly/daily report data and delegate desktop rendering to `ArchiveTimeline`.
- Modify `src/components/MonthlyReportView.astro`: normalize month data and delegate desktop rendering to `ArchiveTimeline`.
- Modify `src/styles/global.css`: remove obsolete weekly-only rules while retaining the daily timeline rules for the shared component.
- Modify `src/components/layout-contract.test.ts`: enforce shared component use and prevent divergent archive markup from returning.

### Task 1: Establish the shared timeline contract

**Files:**
- Test: `src/components/layout-contract.test.ts`

- [ ] **Step 1: Write the failing test**

Add this test inside the existing `navigation layout contract` suite:

```ts
test("uses one daily-style timeline for monthly, weekly, and daily archives", async () => {
  const timeline = await readFile(new URL("./ArchiveTimeline.astro", import.meta.url), "utf8");
  const rail = await readFile(new URL("./DateRail.astro", import.meta.url), "utf8");
  const monthly = await readFile(new URL("./MonthlyReportView.astro", import.meta.url), "utf8");
  const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

  expect(timeline).toContain('<ol class="date-list">');
  expect(timeline).toContain('class="date-dot"');
  expect(timeline).toContain("index === 0");
  expect(timeline).toContain("<small>最新</small>");
  expect(timeline).toContain('aria-current={item.current ? "page" : undefined}');
  expect(rail).toContain('import ArchiveTimeline from "./ArchiveTimeline.astro"');
  expect(rail).toContain("<ArchiveTimeline items={archiveItems} />");
  expect(monthly).toContain('import ArchiveTimeline from "./ArchiveTimeline.astro"');
  expect(monthly).toContain("<ArchiveTimeline items={archiveItems} />");
  expect(rail).not.toContain('class="weekly-links"');
  expect(monthly).not.toContain('class="weekly-links"');
  expect(styles).not.toMatch(/\.weekly-links\s*\{/);
});
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
npm test -- src/components/layout-contract.test.ts
```

Expected: FAIL because `ArchiveTimeline.astro` does not exist and both calling components still contain `weekly-links`.

### Task 2: Implement and adopt the shared timeline

**Files:**
- Create: `src/components/ArchiveTimeline.astro`
- Modify: `src/components/DateRail.astro`
- Modify: `src/components/MonthlyReportView.astro`

- [ ] **Step 1: Create the shared component**

Create `src/components/ArchiveTimeline.astro`:

```astro
---
export interface ArchiveTimelineItem {
  label: string;
  href: string;
  current: boolean;
}

interface Props {
  items: ArchiveTimelineItem[];
}

const { items } = Astro.props;
---

<ol class="date-list">
  {items.map((item, index) => (
    <li class:list={{ active: item.current }}>
      <a href={item.href} aria-current={item.current ? "page" : undefined}>
        <span class="date-dot" aria-hidden="true"></span>
        <span>{item.label}</span>
        {index === 0 && <small>最新</small>}
      </a>
    </li>
  ))}
</ol>
```

- [ ] **Step 2: Normalize weekly and daily items in `DateRail.astro`**

Import the shared component and define:

```ts
import ArchiveTimeline from "./ArchiveTimeline.astro";

const archiveItems = reports.map((report) => ({
  label: weekly ? report.slug : report.date,
  href: href(report.slug),
  current: report.slug === currentSlug,
}));
```

Replace the weekly/daily conditional desktop markup with:

```astro
<ArchiveTimeline items={archiveItems} />
```

Keep the existing mobile `<select>` and `<noscript>` fallback unchanged.

- [ ] **Step 3: Normalize month items in `MonthlyReportView.astro`**

Import the shared component and define:

```ts
import ArchiveTimeline from "./ArchiveTimeline.astro";

const archiveItems = months.map((item) => ({
  label: item.slug,
  href: `/monthly/${item.slug}/`,
  current: item.slug === report.slug,
}));
```

Replace the `weekly-links` block with:

```astro
<ArchiveTimeline items={archiveItems} />
```

- [ ] **Step 4: Run the focused test**

Run:

```bash
npm test -- src/components/layout-contract.test.ts
```

Expected: the new contract may still fail only on obsolete `.weekly-links` CSS, proving component adoption is complete before cleanup.

### Task 3: Remove obsolete weekly-only styling

**Files:**
- Modify: `src/styles/global.css`

- [ ] **Step 1: Remove weekly-only selectors**

Remove `.weekly-links` from the collapsed-rail selector and the mobile hidden selector. Delete these obsolete rules:

```css
.weekly-links { ... }
.weekly-links > span { ... }
.weekly-links a { ... }
.weekly-links a.active { ... }
```

Keep `.date-list`, `.date-dot`, active, and latest-label rules unchanged so every period inherits the established daily appearance.

- [ ] **Step 2: Run the focused test and verify GREEN**

Run:

```bash
npm test -- src/components/layout-contract.test.ts
```

Expected: all layout contract tests pass.

### Task 4: Verify behavior and presentation

**Files:**
- Verify only

- [ ] **Step 1: Run the full automated verification**

Run:

```bash
npm test
npm run check
npm run build
git diff --check
```

Expected: all tests pass, Astro reports zero diagnostics, the static build succeeds, and the diff has no whitespace errors.

- [ ] **Step 2: Inspect all desktop archive types**

Start the site on a temporary port other than 4321 or 4322. Inspect the latest monthly, weekly, and daily routes at a desktop viewport and verify:

- every left list has the same vertical line and circular markers;
- the first item shows “最新”;
- the current item has the yellow filled marker and stronger label;
- there is no horizontal overflow.

- [ ] **Step 3: Inspect responsive behavior and stop the server**

Verify that the desktop timeline remains hidden below `768px`, the existing report selector remains visible, and the page has no horizontal overflow. Stop the temporary server and confirm ports 4321, 4322, and the temporary port have no listeners.
