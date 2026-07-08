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

const bonusSample = `# GitHub 优质项目每日发现｜2026-07-08

> 今日重点：测试。

## 主推荐

### 1. 爆发型：test/repo — 80/100

- 仓库：[test/repo](https://github.com/test/repo)
- 一句话定位：测试项目。
- 主要技术栈：Go。
- 风险：无。
- 推荐理由：测试。

## 额外发现

### 额外发现：asgeirtj/system_prompts_leaks — 74/100

- 仓库：[asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks)
- 一句话定位：持续整理主流 AI 产品系统提示词及工具定义的研究型资料库。
- 主要技术栈：Markdown 内容库；JavaScript、Python 用于仓库流量统计与展示辅助。
- 风险：部分内容无法独立确认完整性与真实性。
- 推荐理由：它对 Agent 指令设计研究和版本比较具有明显发现价值。

## 今天最值得亲自试用

test
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

  it("parses bonus findings from daily report", () => {
    const report = parseDailyReport(bonusSample, "2026-07-08.md");

    expect(report.bonusProjects.length).toBe(1);
    expect(report.bonusProjects[0].repository).toBe("asgeirtj/system_prompts_leaks");
    expect(report.bonusProjects[0].score).toBe(74);
    expect(report.bonusProjects[0].kind).toBe("额外发现");
    expect(report.bonusProjects[0].positioning).toContain("持续整理");
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
