import { readFile } from "node:fs/promises";
import { describe, expect, test } from "vitest";

describe("navigation layout contract", () => {
  test("places the period switcher in the header center column", async () => {
    const layout = await readFile(new URL("../layouts/BaseLayout.astro", import.meta.url), "utf8");
    const switcher = await readFile(new URL("./PeriodSwitcher.astro", import.meta.url), "utf8");
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(layout).toContain('<div class="site-period-navigation">');
    expect(layout.indexOf("site-period-navigation")).toBeLessThan(layout.indexOf("site-actions"));
    expect(switcher).toContain('aria-current={active === period ? "true" : undefined}');
    expect(styles).toMatch(/\.site-header\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\) auto minmax\(0, 1fr\)/s);
    expect(styles).toMatch(/\.site-period-navigation\s*\{[^}]*grid-column:\s*2[^}]*justify-self:\s*center/s);
    expect(styles).toMatch(/\.period-switcher a\[aria-current\]\s*\{/s);
  });

  test("provides one progressively enhanced archive behavior", async () => {
    const layout = await readFile(new URL("../layouts/BaseLayout.astro", import.meta.url), "utf8");
    const view = await readFile(new URL("./MonthlyReportView.astro", import.meta.url), "utf8");
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(view).toContain("data-archive-shell");
    expect(view).toContain("data-archive-rail-toggle");
    expect(view).toContain('aria-expanded="true"');
    expect(view).not.toContain("<script>");
    expect(layout).toContain('querySelector<HTMLElement>("[data-archive-shell]")');
    expect(layout).toContain('classList.add("is-enhanced")');
    expect(layout).toContain('shell?.toggleAttribute("data-rail-collapsed")');
    expect(styles).toMatch(/\.archive-rail-toggle\s*\{[^}]*display:\s*none/s);
    expect(styles).toMatch(/\.archive-shell\.is-enhanced \.archive-rail-toggle\s*\{[^}]*display:\s*grid/s);
    expect(styles).toMatch(/\.archive-shell\[data-rail-collapsed\]\s*\{[^}]*grid-template-columns:\s*3\.25rem minmax\(0, 1fr\)/s);
  });

  test("keeps mobile report selectors navigable", async () => {
    const layout = await readFile(new URL("../layouts/BaseLayout.astro", import.meta.url), "utf8");
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(layout).toContain('querySelector<HTMLSelectElement>("[data-report-select]")');
    expect(layout).toContain('addEventListener("change"');
    expect(layout).toContain("window.location.assign(select.value)");
    expect(styles).toMatch(/@media \(max-width: 768px\)[\s\S]*\.report-select\s*\{[^}]*display:\s*grid/s);
  });

  test("keeps weekly and daily archives separate and collapsible", async () => {
    const rail = await readFile(new URL("./DateRail.astro", import.meta.url), "utf8");
    const reportView = await readFile(new URL("./ReportView.astro", import.meta.url), "utf8");
    const weeklyPage = await readFile(new URL("../pages/weekly/[week].astro", import.meta.url), "utf8");
    const dailyPage = await readFile(new URL("../pages/daily/[date].astro", import.meta.url), "utf8");
    const homePage = await readFile(new URL("../pages/index.astro", import.meta.url), "utf8");

    expect(rail).toContain('period: "weekly" | "daily"');
    expect(rail).toContain("data-archive-rail-toggle");
    expect(rail).toContain("<noscript>");
    expect(rail).not.toContain("<script>");
    expect(reportView).toContain("reports={reports}");
    expect(weeklyPage).toContain("reports={weeklyReports}");
    expect(weeklyPage).not.toContain("dailyReports={dailyReports}");
    expect(dailyPage).toContain("reports={dailyReports}");
    expect(dailyPage).not.toContain("weeklyReports={weeklyReports}");
    expect(homePage).toContain('reports={report.type === "daily" ? dailyReports : weeklyReports}');
  });

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

  test("separates numeric scores from the weekly selection state", async () => {
    const entry = await readFile(new URL("./ProjectEntry.astro", import.meta.url), "utf8");
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(entry).toContain('aria-label="周选项目"');
    expect(entry).toContain('<span class="project-selection">周选</span>');
    expect(entry).not.toContain('project.score ?? "W"');
    expect(entry).not.toContain('"EEKLY"');
    expect(styles).toMatch(/\.project-selection\s*\{/s);
  });

  test("keeps the search action recognizable at mobile widths", async () => {
    const layout = await readFile(new URL("../layouts/BaseLayout.astro", import.meta.url), "utf8");
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(layout).toContain('class="search-trigger__icon"');
    expect(layout).toContain('aria-hidden="true"');
    expect(layout).toContain('<span class="search-trigger__label">搜索</span>');
    expect(styles).toMatch(/\.search-trigger__icon\s*\{/s);
    expect(styles).toMatch(/@media \(max-width: 768px\)[\s\S]*\.search-trigger\s*\{[^}]*min-width:\s*2\.75rem[^}]*min-height:\s*2\.75rem/s);
    expect(styles).toMatch(/@media \(max-width: 768px\)[\s\S]*\.search-trigger__label,\s*\.search-trigger kbd\s*\{[^}]*display:\s*none/s);
  });

  test("adds monthly section navigation and native evidence disclosure", async () => {
    const view = await readFile(new URL("./MonthlyReportView.astro", import.meta.url), "utf8");
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(view).toContain('class="monthly-section-nav"');
    expect(view).toContain('href="#monthly-top5"');
    expect(view).toContain('href="#monthly-opportunities"');
    expect(view).toContain('href="#monthly-methodology"');
    expect(view).toContain("至少一个核心仓库需跑通单仓库核心流程（L2）");
    expect(view).toContain("两个以上仓库用真实格式数据完成连接（L3）");
    expect(view).toMatch(/<h2 id="monthly-opportunities">真实业务与项目机会<\/h2>\s*<p class="monthly-section__intro">/s);
    expect(styles).toMatch(/\.monthly-section__heading--stacked\s*\{[^}]*grid-template-columns:\s*1fr/s);
    expect(view).toContain('aria-labelledby="monthly-discovery-title"');
    expect(view).toContain('<h3 id="monthly-discovery-title">发现流程</h3>');
    expect(view).toContain("01｜仓库盘点");
    expect(view).toContain("02｜需求核实");
    expect(view).toContain("03｜组合设计");
    expect(view).toContain("04｜验证发布");
    expect(styles).toMatch(/\.monthly-discovery__steps\s*\{[^}]*grid-template-columns:\s*repeat\(4,/s);
    expect(styles).toMatch(/@media \(max-width: 768px\)[\s\S]*\.monthly-discovery__steps\s*\{[^}]*grid-template-columns:\s*1fr/s);
    expect(view).toContain('<details class="monthly-evidence" open>');
    expect(view).toContain("<summary>查看评分与核实证据</summary>");
    expect(view).toContain('id="monthly-methodology"');
    expect(styles).toMatch(/\.monthly-section-nav\s*\{/s);
    expect(styles).toMatch(/\.monthly-evidence\s*>\s*summary\s*\{/s);
  });

  test("uses a strictly increasing spacing scale for component and section rhythm", async () => {
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(styles).toMatch(/--space-5:\s*1\.25rem/);
    expect(styles).toMatch(/--space-6:\s*1\.5rem/);
    expect(styles).toMatch(/--space-7:\s*2rem/);
    expect(styles).toMatch(/--space-8:\s*3rem/);
  });

  test("gives desktop report headings and summaries a wider reading measure", async () => {
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(styles).toMatch(/\.report-hero h1\s*\{[^}]*max-width:\s*32ch[^}]*text-wrap:\s*pretty/s);
    expect(styles).toMatch(/\.project-positioning\s*\{[^}]*max-width:\s*min\(62rem,\s*100%\)/s);
    expect(styles).toMatch(/\.project-introduction\s*\{[^}]*max-width:\s*min\(62rem,\s*100%\)/s);
  });
});
