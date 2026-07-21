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

  test("provides an accessible desktop monthly rail toggle", async () => {
    const view = await readFile(new URL("./MonthlyReportView.astro", import.meta.url), "utf8");
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(view).toContain("data-monthly-rail-toggle");
    expect(view).toContain('aria-expanded="true"');
    expect(view).toContain("data-rail-collapsed");
    expect(view).toContain('classList.add("is-enhanced")');
    expect(styles).toMatch(/\.monthly-rail-toggle\s*\{[^}]*display:\s*none/s);
    expect(styles).toMatch(/\.monthly-shell\.is-enhanced \.monthly-rail-toggle\s*\{[^}]*display:\s*grid/s);
    expect(styles).toMatch(/\.monthly-shell\[data-rail-collapsed\]\s*\{[^}]*grid-template-columns:\s*3\.25rem minmax\(0, 1fr\)/s);
  });

  test("keeps the mobile month selector navigable", async () => {
    const view = await readFile(new URL("./MonthlyReportView.astro", import.meta.url), "utf8");
    const styles = await readFile(new URL("../styles/global.css", import.meta.url), "utf8");

    expect(view).toContain('querySelector<HTMLSelectElement>("[data-report-select]")');
    expect(view).toContain('addEventListener("change"');
    expect(view).toContain("window.location.assign(reportSelect.value)");
    expect(styles).toMatch(/@media \(max-width: 768px\)[\s\S]*\.report-select\s*\{[^}]*display:\s*grid/s);
  });
});
