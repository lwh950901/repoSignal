# Period-Specific Collapsible Archives Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make weekly and daily report pages show only their own archive lists and share the existing desktop narrow-rail collapse behavior.

**Architecture:** Keep the already-independent weekly and daily routes plus their shared report renderer. Pass one period-specific report array into `DateRail`, and move the tiny archive/select behavior into the shared base layout so month, week and day use one script and one set of CSS selectors.

**Tech Stack:** Astro 7, TypeScript, CSS, Vitest

---

### Task 1: Add the failing archive contract

**Files:**
- Modify: `src/components/layout-contract.test.ts`

- [x] **Step 1: Add one focused test**

```ts
test("keeps weekly and daily archives separate and collapsible", async () => {
  const rail = await readFile(new URL("./DateRail.astro", import.meta.url), "utf8");
  const reportView = await readFile(new URL("./ReportView.astro", import.meta.url), "utf8");
  const weeklyPage = await readFile(new URL("../pages/weekly/[week].astro", import.meta.url), "utf8");
  const dailyPage = await readFile(new URL("../pages/daily/[date].astro", import.meta.url), "utf8");

  expect(rail).toContain('period: "weekly" | "daily"');
  expect(rail).toContain("data-archive-rail-toggle");
  expect(reportView).toContain("reports={reports}");
  expect(weeklyPage).toContain("reports={weeklyReports}");
  expect(weeklyPage).not.toContain("dailyReports={dailyReports}");
  expect(dailyPage).toContain("reports={dailyReports}");
  expect(dailyPage).not.toContain("weeklyReports={weeklyReports}");
});
```

- [x] **Step 2: Verify RED**

Run: `npm test -- src/components/layout-contract.test.ts`

Expected: FAIL because `DateRail` still combines daily and weekly reports and has no rail toggle.

### Task 2: Reuse one archive rail behavior

**Files:**
- Modify: `src/components/DateRail.astro`
- Modify: `src/components/ReportView.astro`
- Modify: `src/components/MonthlyReportView.astro`
- Modify: `src/layouts/BaseLayout.astro`
- Modify: `src/pages/weekly/[week].astro`
- Modify: `src/pages/daily/[date].astro`
- Modify: `src/pages/index.astro`
- Modify: `src/styles/global.css`

- [x] **Step 1: Make `DateRail` period-specific**

```astro
interface Props {
  reports: DigestReport[];
  period: "weekly" | "daily";
  currentSlug: string;
}

const { reports, period, currentSlug } = Astro.props;
const weekly = period === "weekly";
const href = (slug: string) => `/${period}/${slug}/`;
---
<aside class="date-rail archive-rail" aria-label={weekly ? "周报归档" : "日报归档"}>
  <div class="archive-rail__header">
    <div class="date-rail__heading"><span>{weekly ? "WEEKLY" : "DAILY"}</span><span>{reports.length} 期</span></div>
    <button class="archive-rail-toggle" type="button" data-archive-rail-toggle data-archive-label={weekly ? "周报" : "日报"} aria-expanded="true" aria-label={`收起${weekly ? "周报" : "日报"}归档`}><span data-archive-rail-icon aria-hidden="true">←</span></button>
  </div>
  <label class="report-select"><span>选择报告</span><select data-report-select>{reports.map((report) => <option value={href(report.slug)} selected={report.slug === currentSlug}>{weekly ? `${report.slug} 周精选` : report.date}</option>)}</select></label>
  {weekly ? <div class="weekly-links">{reports.map((report) => <a href={href(report.slug)}>{report.slug}</a>)}</div> : <ol class="date-list">{reports.map((report) => <li><a href={href(report.slug)}>{report.date}</a></li>)}</ol>}
</aside>
```

- [x] **Step 2: Pass only the active period's reports**

```astro
<!-- ReportView.astro -->
<DateRail reports={reports} period={report.type} currentSlug={report.slug} />

<!-- weekly/[week].astro -->
<ReportView report={report} reports={weeklyReports} />

<!-- daily/[date].astro -->
<ReportView report={report} reports={dailyReports} />
```

- [x] **Step 3: Share the existing enhancement script from `BaseLayout`**

```astro
<script>
  const shell = document.querySelector<HTMLElement>("[data-archive-shell]");
  const toggle = shell?.querySelector<HTMLButtonElement>("[data-archive-rail-toggle]");
  const icon = toggle?.querySelector<HTMLElement>("[data-archive-rail-icon]");
  const select = shell?.querySelector<HTMLSelectElement>("[data-report-select]");
  shell?.classList.add("is-enhanced");
  toggle?.addEventListener("click", () => {
    const collapsed = shell.toggleAttribute("data-rail-collapsed");
    const label = toggle.dataset.archiveLabel ?? "报告";
    toggle.setAttribute("aria-expanded", String(!collapsed));
    toggle.setAttribute("aria-label", `${collapsed ? "展开" : "收起"}${label}归档`);
    if (icon) icon.textContent = collapsed ? "→" : "←";
  });
  select?.addEventListener("change", () => window.location.assign(select.value));
</script>
```

Both `ReportView` and `MonthlyReportView` add `data-archive-shell`; the old component-local scripts are deleted.

- [x] **Step 4: Generalize the existing CSS selectors**

```css
.archive-shell { transition: grid-template-columns .2s ease; }
.archive-shell[data-rail-collapsed] { grid-template-columns: 3.25rem minmax(0, 1fr); }
.archive-rail-toggle { display: none; }
.archive-shell.is-enhanced .archive-rail-toggle { display: grid; }
.archive-shell[data-rail-collapsed] .archive-rail__header { justify-content: center; }
.archive-shell[data-rail-collapsed] .archive-rail__header p,
.archive-shell[data-rail-collapsed] .archive-rail__header .date-rail__heading,
.archive-shell[data-rail-collapsed] .weekly-links,
.archive-shell[data-rail-collapsed] .date-list,
.archive-shell[data-rail-collapsed] .archive-links { display: none; }
```

At `max-width: 768px`, hide `.archive-rail__header`; the existing `.report-select` rule remains unchanged.

- [x] **Step 5: Verify GREEN**

Run: `npm test -- src/components/layout-contract.test.ts`

Expected: PASS.

### Task 3: Verify and commit

**Files:**
- Modify: `openspec/changes/redesign-monthly-business-research/specs/ranked-monthly-reports/spec.md`
- Modify: `openspec/changes/redesign-monthly-business-research/design.md`
- Modify: `openspec/changes/redesign-monthly-business-research/tasks.md`

- [x] **Step 1: Record the period-specific archive requirement and tasks**

Add an OpenSpec requirement that weekly pages expose only weekly archive links, daily pages expose only daily archive links, and both desktop rails collapse with the same accessible state as monthly.

```markdown
### Requirement: Report archives are period-specific and collapsible
周报页面 MUST 只展示周报归档，日报页面 MUST 只展示日报归档。桌面归档 MUST 可收起为保留展开按钮的窄栏；移动端 MUST 保留只含当前周期报告的选择器。

#### Scenario: Reader opens a weekly or daily report
- **WHEN** 读者打开周报或日报详情页
- **THEN** 归档链接与选择器只包含当前周期，且桌面折叠按钮通过 `aria-expanded` 暴露状态
```

- [x] **Step 2: Run full verification**

Run: `npm test && npm run check && npm run build && openspec validate redesign-monthly-business-research --strict && git diff --check`

Expected: 0 failures, 0 Astro diagnostics, successful static build, valid OpenSpec and clean diff check.

- [x] **Step 3: Inspect representative pages**

Check `/weekly/2026-W29/` and `/daily/2026-07-18/` at desktop and 360px. Confirm list isolation, collapse/expand, select navigation, no horizontal overflow and no console warnings.

- [x] **Step 4: Commit**

```bash
git add src/components/DateRail.astro src/components/ReportView.astro src/components/MonthlyReportView.astro src/layouts/BaseLayout.astro src/pages/weekly/'[week].astro' src/pages/daily/'[date].astro' src/pages/index.astro src/styles/global.css src/components/layout-contract.test.ts openspec/changes/redesign-monthly-business-research docs/superpowers/plans/2026-07-21-period-specific-collapsible-archives.md
git commit -m "feat: separate weekly and daily archives"
```
