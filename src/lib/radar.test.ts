import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { loadRadarReports, parseRadarReport } from "./radar";

const validArticle = `# 开源雷达周刊

![仓库雷达｜每周开源项目精选](/covers/repository-radar-weekly-subtitle.png)

本周从公开仓库中选出十个值得继续观察的项目。

## 本周推荐

[示例项目](https://github.com/example/project) 适合小范围试用。
`;

describe("parseRadarReport", () => {
  it("extracts metadata and removes the duplicated title and cover from the body", () => {
    const report = parseRadarReport(validArticle, "2026-W31.md");

    expect(report).toMatchObject({
      slug: "2026-W31",
      date: "2026-W31",
      title: "开源雷达周刊",
      description: "本周从公开仓库中选出十个值得继续观察的项目。",
      cover: "/covers/repository-radar-weekly-subtitle.png",
      coverAlt: "仓库雷达｜每周开源项目精选",
    });
    expect(report.markdown).not.toContain("# 开源雷达周刊");
    expect(report.markdown).not.toContain("![仓库雷达");
    expect(report.html).toContain("<h2>本周推荐</h2>");
  });

  it.each([
    ["week-31.md", "ISO 周"],
    ["2026-W31.md", "一级标题", validArticle.replace("# 开源雷达周刊\n", "")],
    ["2026-W31.md", "封面", validArticle.replace(/!\[[^\]]+\]\([^)]+\)\n/u, "")],
    ["2026-W31.md", "SITE_BASE_URL", `${validArticle}\n{{SITE_BASE_URL}}/weekly/`],
    ["2026-W31.md", "utm_", `${validArticle}\nhttps://example.com/?utm_source=test`],
  ])("rejects invalid public content in %s with a clear %s error", (filename, expected, article = validArticle) => {
    expect(() => parseRadarReport(article, filename)).toThrow(new RegExp(`${filename}.*${expected}`, "u"));
  });

  it("rejects project copy inserted between audience and risk notes", () => {
    const invalidOrder = `${validArticle}
### 1. 示例项目

[示例项目](https://github.com/example/project) 是一个示例工具。

**适合：** 需要示例工具的开发者。

这段推荐依据不应出现在适合与注意之间。

**注意：** 试用前应确认边界。
`;

    expect(() => parseRadarReport(invalidOrder, "2026-W31.md")).toThrow(
      /2026-W31\.md.*“适合”后必须直接接“注意”/u,
    );
  });

  it("requires four labeled project blocks from W32 onward", () => {
    const unlabeledProject = `${validArticle}
### 1. 示例项目

[示例项目](https://github.com/example/project) 是一个示例工具。

它有明确的试用价值。

**适合：** 需要示例工具的开发者。

**注意：** 试用前应确认边界。
`;

    expect(() => parseRadarReport(unlabeledProject, "2026-W32.md")).toThrow(
      /2026-W32\.md.*介绍.*推荐依据.*适合.*注意/u,
    );
  });

  it("rejects 补充介绍 as a substitute for the 介绍 label", () => {
    const supplementaryIntroduction = `${validArticle}
### 1. 示例项目

**补充介绍：** [示例项目](https://github.com/example/project) 是一个示例工具。

**推荐依据：** 它有明确的试用价值。

**适合：** 需要示例工具的开发者。

**注意：** 试用前应确认边界。
`;

    expect(() => parseRadarReport(supplementaryIntroduction, "2026-W32.md")).toThrow(
      /2026-W32\.md.*“介绍、推荐依据、适合、注意”/u,
    );
  });
});

describe("radar discovery", () => {
  it("loads only frozen radar articles newest first", async () => {
    const source = await readFile(new URL("./radar.ts", import.meta.url), "utf8");
    const reports = loadRadarReports();

    expect(source).toContain("data/github-project-digest/radar/*.md");
    expect(source).not.toContain("distribution-drafts");
    expect(reports.length).toBeGreaterThan(0);
    expect(reports.map((report) => report.slug)).toEqual(
      [...reports.map((report) => report.slug)].sort().reverse(),
    );
    for (const report of reports) {
      const projectLinks = new Set(report.markdown.match(/https:\/\/github\.com\/[^)\s]+/gu) ?? []);
      expect(projectLinks.size, `${report.slug} project links`).toBe(10);
      expect(report.coverAlt, `${report.slug} cover alt`).toContain("开源雷达周刊");
      expect(report.markdown.match(/^###\s+\d+\./gmu)?.length, `${report.slug} project headings`).toBe(10);
      expect(report.markdown.match(/^\*\*适合：\*\*/gmu)?.length, `${report.slug} audience notes`).toBe(10);
      expect(report.markdown.match(/^\*\*注意：\*\*/gmu)?.length, `${report.slug} risk notes`).toBe(10);
      if (report.slug >= "2026-W32") {
        expect(report.markdown.match(/^\*\*介绍：\*\*/gmu)?.length, `${report.slug} introductions`).toBe(10);
        expect(report.markdown.match(/^\*\*推荐依据：\*\*/gmu)?.length, `${report.slug} recommendation reasons`).toBe(10);
      }
    }
  });
});
