import { describe, expect, it } from "vitest";
import {
  createMonthlySearchIndex,
  loadMonthlyReports,
  loadMonthlyReportsFromFiles,
  parseMonthlyReport,
} from "./monthly";

const monthlySample = `# GitHub 项目月度精选｜2026-07

> 月度主题：AI 编程工具开始走向可组合的工作流。
> 数据截止：2026-07-20
> 候选数量：18

## 本月结论

本月值得优先关注可被团队实际采用的 AI 工具链。

## 三句话读懂这个月

1. AI 编程代理正从单点能力走向协作工作流。
2. 开源项目的可维护性开始比短期热度更重要。
3. 产品团队应先验证真实任务，而不是追逐模型参数。

## Top 5

### 1. Alpha

- 仓库：[Acme/Alpha](https://github.com/Acme/Alpha)
- 主要角色：独立开发者
- 次要角色：技术负责人、AI 产品创业者
- 入选依据：把复杂任务拆成可验证的步骤。
- 最佳使用场景：需要快速验证自动化开发流程的小型项目。
- 主要风险：生态仍在快速变化。
- 证据强度：高

### 2. Beta

- 仓库：[Acme/Beta](https://github.com/Acme/Beta)
- 主要角色：技术负责人
- 入选依据：提供团队可复用的工作流边界。
- 最佳使用场景：需要统一工程规范的产品团队。
- 主要风险：初次配置成本较高。
- 证据强度：中

### 3. Gamma

- 仓库：[Acme/Gamma](https://github.com/Acme/Gamma)
- 主要角色：AI 产品创业者
- 入选依据：缩短原型到用户测试的反馈周期。
- 最佳使用场景：验证 AI 功能价值的早期产品。
- 主要风险：依赖上游模型服务。
- 证据强度：观察

### 4. Delta

- 仓库：[Acme/Delta](https://github.com/Acme/Delta)
- 主要角色：独立开发者
- 入选依据：让本地工具链更容易组合。
- 最佳使用场景：维护多个小型自动化脚本。
- 主要风险：文档覆盖尚不完整。
- 证据强度：中

### 5. Epsilon

- 仓库：[Acme/Epsilon](https://github.com/Acme/Epsilon)
- 主要角色：技术负责人
- 入选依据：让团队能观察关键执行路径。
- 最佳使用场景：评估 AI 工具引入后的工程质量。
- 主要风险：指标解释需要经验。
- 证据强度：高

## 分类推荐

### 独立开发者

#### Swift Start

- 仓库：[Acme/SwiftStart](https://github.com/Acme/SwiftStart)
- 推荐理由：适合在周末完成一个可演示原型。
- 主要风险：功能边界较窄。

### 技术负责人

#### Team Guard

- 仓库：[Acme/TeamGuard](https://github.com/Acme/TeamGuard)
- 推荐理由：帮助团队建立可审计的发布流程。
- 主要风险：需要接入现有 CI。

### AI 产品创业者

#### Product Loop

- 仓库：[Acme/ProductLoop](https://github.com/Acme/ProductLoop)
- 推荐理由：让早期团队快速连接真实用户反馈。
- 主要风险：需要持续投入用户研究。

## 本月观察信号

### 快速上升：可组合代理正在成为默认形态

- 支撑项目：Acme/Alpha、Acme/Beta、Acme/Gamma
- 观察：越来越多项目把执行、记忆和评估拆为独立能力。
- 证据强度：高

### 持续成熟：团队治理工具开始补齐

- 支撑项目：Acme/Beta、Acme/Delta、Acme/Epsilon
- 观察：可观测性与权限能力正进入主流工具链。
- 证据强度：中

## 行动建议

### 独立开发者

- 选择一个重复任务，在一周内验证自动化效果。
- 记录失败路径，避免把演示当成生产能力。

### 技术负责人

- 为试点团队建立成功指标和退出条件。

### AI 产品创业者

- 用真实用户任务检验产品差异，而非仅比较模型能力。
`;

describe("parseMonthlyReport", () => {
  it("parses a complete monthly selection report", () => {
    const report = parseMonthlyReport(monthlySample, "2026-07.md");

    expect(report).toMatchObject({
      type: "monthly",
      slug: "2026-07",
      cutoffDate: "2026-07-20",
      candidateCount: 18,
    });
    expect(report.theses).toHaveLength(3);
    expect(report.topProjects).toHaveLength(5);
    expect(report.topProjects[0]).toMatchObject({
      id: "monthly-project-61636d652f616c706861",
      repository: "Acme/Alpha",
      primaryAudience: "独立开发者",
      secondaryAudiences: ["技术负责人", "AI 产品创业者"],
    });
    expect(report.topProjects[0].html).toContain("入选依据");
    expect(report.recommendations).toHaveLength(3);
    expect(report.signals[0].direction).toBe("快速上升");
    expect(report.actions[2].items[0]).toContain("真实用户任务");
  });

  it("rejects a missing required Top 5 field", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace("- 主要风险：生态仍在快速变化。\n", ""),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*Acme\/Alpha.*主要风险/u);
  });

  it("defaults omitted Top 5 evidence strength to observation", () => {
    const report = parseMonthlyReport(
      monthlySample.replace("- 证据强度：高\n\n### 2. Beta", "\n### 2. Beta"),
      "2026-07.md",
    );

    expect(report.topProjects[0].evidenceStrength).toBe("观察");
  });

  it("requires exactly five Top 5 projects", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace(/^### 5\. Epsilon[\s\S]*?(?=\n## 分类推荐)/mu, ""),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*Top 5.*5/u);
  });

  it("rejects invalid GitHub URLs", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace("https://github.com/Acme/Alpha", "https://gitlab.com/Acme/Alpha"),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*Acme\/Alpha.*GitHub URL/u);
  });

  it("rejects repositories duplicated case-insensitively across selections", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace("Acme/SwiftStart](https://github.com/Acme/SwiftStart)", "acme/alpha](https://github.com/acme/alpha)"),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*duplicate.*acme\/alpha/iu);
  });

  it("uses collision-free IDs for punctuation-distinct repositories", () => {
    const report = parseMonthlyReport(
      monthlySample
        .replaceAll("Acme/Alpha", "Foo/foo.bar")
        .replaceAll("Acme/Beta", "Foo/foo-bar")
        .replaceAll("Acme/Gamma", "Foo/foo_bar"),
      "2026-07.md",
    );
    const projectIds = report.topProjects.slice(0, 3).map((project) => project.id);
    const searchIds = createMonthlySearchIndex([report]).slice(0, 3).map((item) => item.id);

    expect(new Set(projectIds)).toHaveLength(3);
    expect(new Set(searchIds)).toHaveLength(3);
  });

  it("accepts canonical .github repository names in projects and signals", () => {
    const topProjectReport = parseMonthlyReport(
      monthlySample.replaceAll("Acme/Alpha", "github/.github"),
      "2026-07.md",
    );
    const recommendationReport = parseMonthlyReport(
      monthlySample.replaceAll("Acme/SwiftStart", "github/.github"),
      "2026-07.md",
    );

    expect(topProjectReport.topProjects[0].repository).toBe("github/.github");
    expect(topProjectReport.signals[0].supportingRepositories).toContain("github/.github");
    expect(recommendationReport.recommendations[0].repository).toBe("github/.github");
  });

  it("rejects invalid GitHub owner components", () => {
    for (const owner of ["owner.name", "_owner", "-owner", "owner-", "a".repeat(40)]) {
      expect(() => parseMonthlyReport(
        monthlySample.replaceAll("Acme/Alpha", `${owner}/repo`),
        "2026-07.md",
      )).toThrow(/2026-07\.md/u);
    }
  });

  it("rejects repository link text that does not match its GitHub URL", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace("[Acme/Alpha](https://github.com/Acme/Alpha)", "[Acme/Other](https://github.com/Acme/Alpha)"),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*Acme\/Other.*GitHub URL/u);
  });

  it("downgrades signals without three supporting repositories", () => {
    const report = parseMonthlyReport(
      monthlySample.replace("Acme/Alpha、Acme/Beta、Acme/Gamma", "Acme/Alpha、Acme/Beta"),
      "2026-07.md",
    );

    expect(report.signals[0]).toMatchObject({
      direction: "编辑观察",
      evidenceStrength: "观察",
    });
  });

  it("downgrades signals when three citations name only one repository", () => {
    const report = parseMonthlyReport(
      monthlySample.replace("Acme/Alpha、Acme/Beta、Acme/Gamma", "Acme/Alpha、acme/alpha、ACME/ALPHA"),
      "2026-07.md",
    );

    expect(report.signals[0]).toMatchObject({
      direction: "编辑观察",
      evidenceStrength: "观察",
      supportingRepositories: ["Acme/Alpha"],
    });
  });

  it("rejects malformed signal repository identities", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace("Acme/Alpha、Acme/Beta、Acme/Gamma", "Acme/Alpha、not a repository、Acme/Gamma"),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*支撑项目.*not a repository/u);
  });

  it("requires every audience exactly once in recommendations", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace(/^### AI 产品创业者[\s\S]*?(?=\n## 本月观察信号)/mu, ""),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*分类推荐.*AI 产品创业者/u);
  });

  it("rejects duplicate audience groups in actions", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace(
        "### AI 产品创业者\n\n- 用真实用户任务检验产品差异，而非仅比较模型能力。",
        "### 技术负责人\n\n- 重复的角色分组。\n\n### AI 产品创业者\n\n- 用真实用户任务检验产品差异，而非仅比较模型能力。",
      ),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*行动建议.*技术负责人/u);
  });

  it("rejects duplicate metadata and metadata outside the header block", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace("> 数据截止：2026-07-20", "> 月度主题：重复主题。\n> 数据截止：2026-07-20"),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*月度主题/u);
    expect(() => parseMonthlyReport(
      monthlySample
        .replace("> 候选数量：18\n", "")
        .replace("\n## 三句话读懂这个月", "\n> 候选数量：18\n\n## 三句话读懂这个月"),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*候选数量.*header/u);
  });

  it("rejects a second H1 outside the header block", () => {
    expect(() => parseMonthlyReport(
      monthlySample.replace("本月值得优先关注可被团队实际采用的 AI 工具链。", "本月值得优先关注可被团队实际采用的 AI 工具链。\n\n# 第二个标题"),
      "2026-07.md",
    )).toThrow(/2026-07\.md.*标题.*header/u);
  });
});

describe("monthly discovery and search conversion", () => {
  it("discovers monthly reports newest first when publications exist", () => {
    const reports = loadMonthlyReports();

    expect(reports.map((report) => report.slug)).toEqual(
      [...reports.map((report) => report.slug)].sort().reverse(),
    );
    expect(reports.every((report) => /^\d{4}-\d{2}$/u.test(report.slug))).toBe(true);
  });

  it("loads and sorts non-empty monthly file maps by basename", () => {
    const reports = loadMonthlyReportsFromFiles({
      "../../data/github-project-digest/monthly/2026-05.md": monthlySample,
      "nested/monthly/2026-07.md": monthlySample,
      "2026-06.md": monthlySample,
    });

    expect(reports.map((report) => report.slug)).toEqual([
      "2026-07",
      "2026-06",
      "2026-05",
    ]);
    expect(loadMonthlyReportsFromFiles({})).toEqual([]);
  });

  it("converts Top 5 and recommendations to monthly search entries", () => {
    const report = parseMonthlyReport(monthlySample, "2026-07.md");
    const items = createMonthlySearchIndex([report]);

    expect(items).toHaveLength(8);
    expect(items[0]).toMatchObject({
      repository: "Acme/Alpha",
      reportType: "monthly",
      reportLabel: "2026-07",
      href: "/monthly/2026-07/#monthly-project-61636d652f616c706861",
    });
    expect(items.at(-1)?.href).toBe("/monthly/2026-07/#monthly-project-61636d652f70726f647563746c6f6f70");
  });
});
