import { readFile } from "node:fs/promises";
import { describe, expect, test } from "vitest";

describe("navigation layout contract", () => {
  test("places the period switcher in the header center column", async () => {
    const layout = await readFile(new URL("../layouts/BaseLayout.astro", import.meta.url), "utf8");
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(layout).toContain('<div class="site-period-navigation">');
    expect(layout.indexOf("site-period-navigation")).toBeLessThan(layout.indexOf("site-actions"));
    expect(styles).toMatch(/\.site-header\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\) auto minmax\(0, 1fr\)/s);
    expect(styles).toMatch(/\.site-period-navigation\s*\{[^}]*grid-column:\s*2[^}]*justify-self:\s*center/s);
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
});
