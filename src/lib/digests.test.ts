import { describe, expect, it } from "vitest";
import {
  loadDailyReports,
  loadWeeklyReports,
  parseDailyReport,
  selectDefaultReport,
} from "./digests";

const sample = `# GitHub 优质项目每日发现｜2026-07-01

> 今日重点：让 AI 编程代理获得更稳定的上下文。其他位置保留跨领域发现。

## 今日结论

三个项目都值得进一步观察。

## 主推荐

### 1. 爆发型：safishamsi/graphify — 82/100

- 仓库：[safishamsi/graphify](https://github.com/safishamsi/graphify)
- 一句话定位：把代码结构提取成可查询知识图谱。
- 主要技术栈：Python、tree-sitter、MCP。
- 风险：热度的长期留存尚需观察。
- 推荐理由：解决了大型代码库的真实痛点。

### 2. 实用型：google-labs-code/design.md — 88/100

- 仓库：[google-labs-code/design.md](https://github.com/google-labs-code/design.md)
- 一句话定位：为编码代理提供视觉身份规范。
- 主要技术栈：TypeScript、YAML、Markdown。

### 3. 潜力型：h4ckf0r0day/obscura — 84/100

- 仓库：[h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura)
- 一句话定位：面向 Agent 的 Rust 无头浏览器。
- 主要技术栈：Rust、V8、CDP。
`;

describe("parseDailyReport", () => {
  it("extracts report metadata and ordered projects", () => {
    const report = parseDailyReport(sample, "2026-07-01.md");

    expect(report.date).toBe("2026-07-01");
    expect(report.theme).toBe("让 AI 编程代理获得更稳定的上下文。");
    expect(report.projects.map((project) => project.kind)).toEqual([
      "爆发型",
      "实用型",
      "潜力型",
    ]);
    expect(report.projects[0].repository).toBe("safishamsi/graphify");
    expect(report.projects[0].score).toBe(82);
    expect(report.projects[0].technologies).toContain("Python");
  });

  it("keeps a readable report when no projects can be parsed", () => {
    const report = parseDailyReport("# 只有标题", "2026-07-02.md");

    expect(report.date).toBe("2026-07-02");
    expect(report.projects).toEqual([]);
    expect(report.markdown).toBe("# 只有标题");
  });
});

describe("digest discovery", () => {
  it("loads real reports newest first with route-safe slugs", () => {
    const daily = loadDailyReports();
    const weekly = loadWeeklyReports();

    expect(daily.length).toBeGreaterThan(0);
    expect(weekly.length).toBeGreaterThan(0);
    expect(daily[0].slug).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(weekly[0].slug).toMatch(/^\d{4}-W\d{2}$/);
    expect(daily.map((report) => report.slug)).toEqual(
      [...daily.map((report) => report.slug)].sort().reverse(),
    );
    for (const report of daily) {
      expect(report.projects, `${report.slug} projects`).toHaveLength(3);
      for (const project of report.projects) {
        expect(project.url, `${report.slug} ${project.repository} url`).toMatch(/^https:\/\/github\.com\//);
        expect(project.score, `${report.slug} ${project.repository} score`).toBeGreaterThan(0);
        expect(project.positioning, `${report.slug} ${project.repository} positioning`).not.toBe("");
        expect(project.technologies, `${report.slug} ${project.repository} technologies`).not.toEqual([]);
        expect(project.risk, `${report.slug} ${project.repository} risk`).not.toBe("");
        expect(project.recommendation, `${report.slug} ${project.repository} recommendation`).not.toBe("");
      }
    }
    for (const report of weekly) {
      expect(report.projects.length, `${report.slug} projects`).toBeGreaterThan(0);
      for (const project of report.projects) {
        expect(project.url, `${report.slug} ${project.repository} url`).toMatch(/^https:\/\/github\.com\//);
        expect(project.positioning, `${report.slug} ${project.repository} positioning`).not.toBe("");
        expect(project.technologies, `${report.slug} ${project.repository} technologies`).not.toEqual([]);
        expect(project.risk, `${report.slug} ${project.repository} risk`).not.toBe("");
        expect(project.recommendation, `${report.slug} ${project.repository} recommendation`).not.toBe("");
      }
    }
  });

  it("prefers the latest weekly selection for the homepage", () => {
    const daily = [parseDailyReport(sample, "2026-07-01.md")];
    const weekly = [{ ...daily[0], type: "weekly" as const, slug: "2026-W27", date: "2026-W27" }];

    expect(selectDefaultReport(daily, weekly)?.slug).toBe("2026-W27");
    expect(selectDefaultReport(daily, [])?.slug).toBe("2026-07-01");
  });
});
