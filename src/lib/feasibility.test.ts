import { describe, expect, it } from "vitest";
import { loadFeasibilityReports, parseFeasibilityReport } from "./feasibility";

const reportMarkdown = `# GitHub 项目组合可行性方案｜2026-08-26

> 由定时任务自动生成，属于可行性研究草稿，不是公开结论。
> 今日锚点：daily/2026-08-26.md。
> 验证路径（固定）：每个组件按来源报告复核（固定版本、隔离环境、自有数据复测）。

## 可行性方案

### 1. 安全 Agent 平台（组合 5 个项目，今日锚点 2 个）

**方案评分**：**83/100（中）**（组件可靠度 32/35 · 组件供给 14/15 · 风险敞口 9/15 · 今日锚点 10/15 · 来源多样性 8/10 · 许可证 5/5 · 完整度 5/5）

**业务定位**：把扫描、修复和验证串成证据链。

**目标客户**：企业安全团队。

**市场机会**：Agent 安全供给开始成熟。

**可行性依据**：关键组件已经齐全。

**组合方案**：

| 角色 | 项目 |
|---|---|
| 扫描 | [guard](https://github.com/example/guard) |

**MVP 范围（做什么，不含代码）**：先跑通授权靶场。

**主要风险（来源报告）**：

- 扫描存在误报。

### 2. 本地 AI 工作台（组合 3 个项目，今日锚点 1 个）

**业务定位**：本地优先的个人 AI 工作台。

**目标客户**：知识工作者。

**市场机会**：隐私需求持续增长。

**组合方案**：使用本地组件。

## 单点项目机会（供参考）

- \`example/tool\` → 可做独立服务。

## 行动建议

1. 先验证核心组件。
`;

describe("parseFeasibilityReport", () => {
  it("parses report metadata, multiple plans, summaries, and preserved bodies", () => {
    const report = parseFeasibilityReport(reportMarkdown, "2026-08-26.md");

    expect(report.slug).toBe("2026-08-26");
    expect(report.date).toBe("2026-08-26");
    expect(report.title).toBe("GitHub 项目组合可行性方案｜2026-08-26");
    expect(report.noticeHtml).toContain("可行性研究草稿");
    expect(report.noticeHtml).toContain("验证路径");
    expect(report.plans).toHaveLength(2);
    expect(report.plans[0]).toMatchObject({
      id: "plan-1",
      title: "安全 Agent 平台（组合 5 个项目，今日锚点 2 个）",
      positioning: "把扫描、修复和验证串成证据链。",
      audience: "企业安全团队。",
      marketOpportunity: "Agent 安全供给开始成熟。",
      score: 83,
      grade: "中",
    });
    expect(report.plans[0].scoreParts).toEqual([
      { name: "组件可靠度", points: 32, max: 35 },
      { name: "组件供给", points: 14, max: 15 },
      { name: "风险敞口", points: 9, max: 15 },
      { name: "今日锚点", points: 10, max: 15 },
      { name: "来源多样性", points: 8, max: 10 },
      { name: "许可证", points: 5, max: 5 },
      { name: "完整度", points: 5, max: 5 },
    ]);
    expect(report.plans[0].bodyHtml).not.toContain("方案评分");
    expect(report.plans[0].bodyHtml).toContain("<table>");
    expect(report.plans[0].bodyHtml).toContain("主要风险");
    expect(report.plans[0].bodyHtml).toContain("先跑通授权靶场");
    // 无评分行的历史方案：score 为 null、分项为空，body 保留原样
    expect(report.plans[1].score).toBeNull();
    expect(report.plans[1].grade).toBeNull();
    expect(report.plans[1].scoreParts).toEqual([]);
    expect(report.plans[1].id).toBe("plan-2");
    expect(report.opportunitiesHtml).toContain("example/tool");
    expect(report.actionsHtml).toContain("先验证核心组件");
  });
});

describe("loadFeasibilityReports", () => {
  it("loads only ISO-dated markdown files and sorts them newest first", () => {
    const reports = loadFeasibilityReports({
      "/feasibility/KUN-TASK.md": "# supporting instructions",
      "/feasibility/2026-08-24.md": reportMarkdown.replaceAll("2026-08-26", "2026-08-24"),
      "/feasibility/runs.log": "ignored",
      "/feasibility/2026-08-26.md": reportMarkdown,
      "/feasibility/2026-8-25.md": reportMarkdown,
    });

    expect(reports.map((report) => report.slug)).toEqual(["2026-08-26", "2026-08-24"]);
  });
});
