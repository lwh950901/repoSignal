import { describe, expect, it } from "vitest";
import {
  createMonthlySearchIndex,
  loadMonthlyReports,
  loadMonthlyReportsFromFiles,
  parseMonthlyReport,
} from "./monthly";

function topProject(position: number, repository: string): string {
  return `### ${position}. ${repository.split("/").at(-1)}

- 仓库：[${repository}](https://github.com/${repository})
- 定位：解决一个边界清楚、能够验证的问题。
- 本月变化：v1.2.0 于 2026-07-18 发布。
- Stars：1200
- Forks：120
- Release：v1.2.0（2026-07-18）
- 最近有效活动：2026-07-18 release
- 许可证：MIT
- 核实日期：2026-07-20
- 验证等级：L2
- 本月重要性：17
- 实际价值：22
- 工程质量：18
- 差异化：12
- 维护可持续性：9
- 采用证据：8
- 总分：86
- 核心能力：把结构化输入转换为可复核输出。
- 工程成熟度：官方最小示例产生预期结果。
- 明确限制：尚未验证生产规模和长期升级。
- 反对理由：采用证据仍主要来自公开仓库。
- 最终判断：值得进入 Top 5，但采用前需要真实任务验证。
- 来源：[GitHub](https://github.com/${repository})、[官方文档](https://docs.example.com/${position})`;
}

function businessOpportunity(repository: string): string {
  return `### 1. 跨工具用量台账

- 形态：企业内部工具
- 目标用户：同时试用两种 AI 编程工具的研发效能负责人
- 需求状态：已确认需求
- 竞品数量：4
- 组合仓库数量：2
- 最高验证等级：L2
- 组合结论：部分可行
- 商业判断：值得做技术实验
- 核实日期：2026-07-20

#### 真实问题

管理员需要统一比较不同工具的聚合用量，两家厂商已经分别提供组织指标。

#### 市场与现有方案

商业产品、开源方案和人工导出流程都存在，但口径分散。

#### 产品定义

只保存聚合数据的内部台账，不读取提示词或代码。

#### 仓库组合

##### 1. Core

- 仓库：[${repository}](https://github.com/${repository})
- 来源身份：本月核心
- 职责：输出聚合 JSON
- 接入方式：CLI JSON → 隐私适配器
- 验证等级：L2

##### 2. Store

- 仓库：[Data/Duck](https://github.com/Data/Duck)
- 来源身份：补充组件
- 职责：保存并查询聚合数据
- 接入方式：JSON → read_json
- 验证等级：L0

#### 组合链路

本地会话 → 聚合 JSON → 分析表。

#### 自行开发部分

需要身份哈希、schema allowlist、权限和审计。

#### MVP 验证

连续运行两周；若无法对齐两种工具则停止。

#### 业务判断

先做技术实验，不声称已有商业市场。

#### 证据边界

组织指标是事实；跨工具付费意愿尚未验证。

#### 来源

- [商业产品](https://vendor.example.com/metrics)
- [开源项目](https://github.com/${repository})`;
}

function monthlyDocument(opportunities: string[] = [businessOpportunity("Acme/Alpha")]): string {
  const opportunityBody = opportunities.length > 0
    ? opportunities.map((item, index) => item.replace(/^### 1\./u, `### ${index + 1}.`)).join("\n\n")
    : "本月未发现通过完整验证的新机会。";
  return `# RepoSignal 月度精选｜2026-07

> 月度主题：核实单仓库价值与真实业务机会。
> 数据截止：2026-07-19
> 候选数量：120
> 深度候选：15
> 验证说明：全部候选完成 L0，领先候选完成 L2。

## 本月结论

Top 5 与业务研究独立判断。

## Top 5 仓库

${[
    "Acme/Alpha",
    "Acme/Beta",
    "Acme/Gamma",
    "Acme/Delta",
    "Acme/Epsilon",
  ].map((repository, index) => topProject(index + 1, repository)).join("\n\n")}

## 真实业务与项目机会

${opportunityBody}

## 研究说明

候选来自冻结的本地证据，外部事实在发布前核实，构建过程不联网。`;
}

describe("parseMonthlyReport", () => {
  it("parses scored Top 5 and a verified business opportunity", () => {
    const report = parseMonthlyReport(monthlyDocument(), "2026-07.md");

    expect(report).toMatchObject({
      type: "monthly",
      slug: "2026-07",
      cutoffDate: "2026-07-19",
      candidateCount: 120,
      deepCandidateCount: 15,
    });
    expect(report.topProjects).toHaveLength(5);
    expect(report.topProjects[0].scores.total).toBe(86);
    expect(report.topProjects[0].verificationLevel).toBe("L2");
    expect(report.topProjects[0].sources).toHaveLength(2);
    expect(report.opportunities[0].demandStatus).toBe("已确认需求");
    expect(report.opportunities[0].repositories[0].repository).toBe("Acme/Alpha");
    expect(report.opportunities[0].bodyHtml).toContain("真实问题");
  });

  it("accepts zero opportunities only with the explicit empty state", () => {
    expect(parseMonthlyReport(monthlyDocument([]), "2026-07.md").opportunities).toEqual([]);
    expect(() => parseMonthlyReport(
      monthlyDocument([]).replace("本月未发现通过完整验证的新机会。", "以后再补。"),
      "2026-07.md",
    )).toThrow(/真实业务与项目机会.*0–3/u);
  });

  it("rejects more than three opportunities", () => {
    expect(() => parseMonthlyReport(monthlyDocument([
      businessOpportunity("Acme/Alpha"),
      businessOpportunity("Acme/Beta"),
      businessOpportunity("Acme/Gamma"),
      businessOpportunity("Acme/Delta"),
    ]), "2026-07.md")).toThrow(/业务机会.*0–3/u);
  });

  it("rejects a score outside its dimension bound", () => {
    expect(() => parseMonthlyReport(
      monthlyDocument().replace("- 本月重要性：17", "- 本月重要性：21"),
      "2026-07.md",
    )).toThrow(/Acme\/Alpha.*本月重要性.*0.*20/u);
  });

  it("rejects a declared total that differs from the six scores", () => {
    expect(() => parseMonthlyReport(
      monthlyDocument().replace("- 总分：86", "- 总分：85"),
      "2026-07.md",
    )).toThrow(/Acme\/Alpha.*总分.*六项/u);
  });

  it("rejects invalid verification levels", () => {
    expect(() => parseMonthlyReport(
      monthlyDocument().replace("- 验证等级：L2", "- 验证等级：L9"),
      "2026-07.md",
    )).toThrow(/Acme\/Alpha.*验证等级.*L0/u);
  });

  it("rejects a project without HTTPS sources", () => {
    expect(() => parseMonthlyReport(
      monthlyDocument().replace(
        "- 来源：[GitHub](https://github.com/Acme/Alpha)、[官方文档](https://docs.example.com/1)",
        "- 来源：内部判断",
      ),
      "2026-07.md",
    )).toThrow(/Acme\/Alpha.*来源/u);
  });

  it("rejects a missing fixed business subsection", () => {
    expect(() => parseMonthlyReport(
      monthlyDocument().replace("#### 自行开发部分", "#### 可选开发"),
      "2026-07.md",
    )).toThrow(/跨工具用量台账.*自行开发部分/u);
  });

  it("rejects duplicate repositories within one combination", () => {
    expect(() => parseMonthlyReport(
      monthlyDocument().replaceAll("Data/Duck", "acme/alpha"),
      "2026-07.md",
    )).toThrow(/跨工具用量台账.*duplicate.*acme\/alpha/iu);
  });

  it("requires a July core repository and rejects invalid origins", () => {
    expect(() => parseMonthlyReport(
      monthlyDocument().replace("- 来源身份：本月核心", "- 来源身份：补充组件"),
      "2026-07.md",
    )).toThrow(/跨工具用量台账.*本月核心/u);
    expect(() => parseMonthlyReport(
      monthlyDocument().replace("- 来源身份：本月核心", "- 来源身份：本月猜测"),
      "2026-07.md",
    )).toThrow(/来源身份/u);
  });

  it("requires two to five repositories and one L2 repository", () => {
    const oneRepository = monthlyDocument().replace(/^##### 2\. Store[\s\S]*?(?=\n#### 组合链路)/mu, "");
    expect(() => parseMonthlyReport(oneRepository, "2026-07.md")).toThrow(/组合仓库.*2.*5/u);
    expect(() => parseMonthlyReport(
      monthlyDocument().replaceAll("- 验证等级：L2", "- 验证等级：L0"),
      "2026-07.md",
    )).toThrow(/跨工具用量台账.*L2/u);
  });

  it("requires exactly five unique Top 5 repositories with canonical GitHub links", () => {
    expect(() => parseMonthlyReport(
      monthlyDocument().replace(/^### 5\. Epsilon[\s\S]*?(?=\n## 真实业务与项目机会)/mu, ""),
      "2026-07.md",
    )).toThrow(/Top 5.*5/u);
    expect(() => parseMonthlyReport(
      monthlyDocument().replaceAll("Acme/Beta", "acme/alpha"),
      "2026-07.md",
    )).toThrow(/duplicate.*acme\/alpha/iu);
    expect(() => parseMonthlyReport(
      monthlyDocument().replace("https://github.com/Acme/Alpha", "https://gitlab.com/Acme/Alpha"),
      "2026-07.md",
    )).toThrow(/Acme\/Alpha.*GitHub URL/u);
  });

  it("rejects duplicate header metadata and invalid dates", () => {
    expect(() => parseMonthlyReport(
      monthlyDocument().replace("> 数据截止：2026-07-19", "> 月度主题：重复。\n> 数据截止：2026-07-19"),
      "2026-07.md",
    )).toThrow(/月度主题.*恰好出现一次/u);
    expect(() => parseMonthlyReport(
      monthlyDocument().replace("2026-07-19", "2026-02-30"),
      "2026-07.md",
    )).toThrow(/数据截止.*有效/u);
  });
});

describe("monthly discovery and search conversion", () => {
  it("discovers the researched July report and excludes internal research", () => {
    const reports = loadMonthlyReports();
    const july = reports.find((report) => report.slug === "2026-07");

    expect(reports.map((report) => report.slug)).toEqual(
      [...reports.map((report) => report.slug)].sort().reverse(),
    );
    expect(july).toBeDefined();
    expect(july?.topProjects).toHaveLength(5);
    expect(july?.opportunities.length).toBeLessThanOrEqual(3);
    expect(july?.topProjects.every((project) => project.sources.length > 0)).toBe(true);
  });

  it("loads by basename, sorts newest first and accepts an empty file map", () => {
    const sample = monthlyDocument([]);
    const reports = loadMonthlyReportsFromFiles({
      "../../data/github-project-digest/monthly/2026-05.md": sample,
      "nested/monthly/2026-07.md": sample,
      "2026-06.md": sample,
    });

    expect(reports.map((report) => report.slug)).toEqual(["2026-07", "2026-06", "2026-05"]);
    expect(loadMonthlyReportsFromFiles({})).toEqual([]);
  });

  it("creates search entries only for the independent Top 5", () => {
    const report = parseMonthlyReport(monthlyDocument(), "2026-07.md");
    const items = createMonthlySearchIndex([report]);

    expect(items).toHaveLength(5);
    expect(items[0]).toMatchObject({
      repository: "Acme/Alpha",
      positioning: "把结构化输入转换为可复核输出。 v1.2.0 于 2026-07-18 发布。",
      kind: "Top 5",
      reportType: "monthly",
      href: "/monthly/2026-07/#monthly-project-61636d652f616c706861",
    });
  });
});
