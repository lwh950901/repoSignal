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

// 双轨报告（成熟方向 + 探索方向）必须仍然可解析：新增的业务语义行不得破坏摘要字段。
const dualTrackMarkdown = `# GitHub 项目组合可行性方案｜2026-09-14

> 由定时任务自动生成：以今日日报项目为锚点，结合最近 90 天项目池。
> 方案 1-3 个：最多 1 个成熟方向 + 最多 2 个探索方向（待验证）。

## 可行性方案

### 1. 企业内部知识助手（组合 5 个项目，今日锚点 2 个）

**方案评分**：**82/100（中）**（组件可靠度 30/35 · 组件供给 14/15 · 风险敞口 12/15 · 今日锚点 10/15 · 来源多样性 8/10 · 许可证 5/5 · 完整度 3/5）

**方案身份**：plan_family=private-enterprise-rag-agent · variant=abc123

**业务轨道**：成熟方向（组件供给已核对）

**业务语义**：track=mature · customer=数据敏感的中大型企业 · problem=文档散落、问答没有出处 · workflow=私有化入库 → 带出处问答 · delivery=企业内网自托管 · expected_outcome=可追溯的问答 · evidence_status=supply-checked

**业务定位**：把散落的部门文档接进私有化知识库。

**目标客户**：数据敏感的中大型企业。

**市场机会**：企业愿意为数据不出境付费。

**组合方案**：

| 角色 | 项目 |
|---|---|
| 编排 | [adk](https://github.com/example/adk) |

### 2. 本地优先 · 知识增强 · Agent 工作台（组合 3 个项目，今日锚点 3 个）

**方案评分**：**76/100（中）**（组件可靠度 28/35 · 组件供给 12/15 · 风险敞口 11/15 · 今日锚点 15/15 · 来源多样性 4/10 · 许可证 3/5 · 完整度 3/5）

**方案身份**：plan_family=biz-4c35a981b564 · variant=def456

**业务轨道**：探索方向（待验证）

**业务语义**：track=exploratory · customer=重视数据留在本机的个人与小型团队 · problem=资料散落各处，答案没有出处可查 · workflow=自有语料入库 → 带引用检索 · delivery=本地/自托管交付 · expected_outcome=每条结论都能指回来源 · evidence_status=to-validate

**待验证说明**：组件可拼装 ≠ 需求成立；本方向需先小范围试用并记录产出。

**业务定位**：按本地优先 · 知识增强 · Agent 工作台方向拼接今日项目。

**目标客户**：重视数据留在本机的个人与小型团队。

**市场机会**：（待验证假设）客户问题：资料散落各处；只说明组件可拼装，不代表市场需求成立。

## 单点项目机会（供参考）

- example/tool → 可做独立服务。

## 行动建议

1. 先验证核心组件。
`;

describe("parseFeasibilityReport（双轨报告兼容）", () => {
  it("keeps dual-track lines and still parses summary fields for both tracks", () => {
    const report = parseFeasibilityReport(dualTrackMarkdown, "2026-09-14.md");

    expect(report.plans).toHaveLength(2);
    expect(report.plans[0]).toMatchObject({
      title: "企业内部知识助手（组合 5 个项目，今日锚点 2 个）",
      positioning: "把散落的部门文档接进私有化知识库。",
      audience: "数据敏感的中大型企业。",
      score: 82,
    });
    expect(report.plans[0].bodyHtml).toContain("成熟方向（组件供给已核对）");
    expect(report.plans[0].bodyHtml).toContain("业务语义");
    expect(report.plans[0].bodyHtml).not.toContain("方案评分");
    expect(report.plans[1]).toMatchObject({
      title: "本地优先 · 知识增强 · Agent 工作台（组合 3 个项目，今日锚点 3 个）",
      score: 76,
    });
    expect(report.plans[1].bodyHtml).toContain("待验证说明");
    // 探索方向的市场机会以“待验证假设”表述，作为摘要字段解析（不进正文 HTML）
    expect(report.plans[1].marketOpportunity).toContain("待验证假设");
    expect(report.plans[1].bodyHtml).not.toContain("待验证假设");
    expect(report.opportunitiesHtml).toContain("example/tool");
  });
});

// 新格式报告（双评分 + 判断四档 + 无单点机会）必须可解析，旧格式仍兼容。
const dualScoreMarkdown = `# GitHub 项目组合可行性方案｜2026-09-20

> 双评分：技术组合成熟度与需求证据强度互不合并。
> 方案判断四档：值得用户访谈 / 值得技术试验 / 继续观察 / 暂不建议。

## 今日结论

- 本轮方案 1 个：成熟方向 1 个 + 探索方向 0 个。

## 可行性方案

### 1. 本地优先个人 AI 工作台

**方案判断**：继续观察（依据：技术组合成熟度 79/100 与需求证据强度 59/100 均未到推进线）

**业务定位**：把本地记忆、编排和网关拼成个人工作台。

**业务轨道**：成熟方向（组件供给已核对）

**业务语义**：track=mature · customer=重视隐私的个人与小型团队 · problem=数据留云端、记忆导不出来 · workflow=本地记忆写入 → Agent 读取 · delivery=桌面端本地安装 · expected_outcome=数据不出本机 · evidence_status=supply-checked

**方案身份**：plan_family=local-first-personal-ai-workbench · variant=83ec9016ac8a

**目标客户**：重视隐私的个人开发者与小型团队

**客户问题**：客户问题「个人数据留在云端」；预期结果「数据不出本机」；交付形态 桌面端本地安装。

**市场机会**：【待验证假设】付费意愿本轮无外部证据。

**需求证据**（59/100，最高等级：项目方自述）：

- 【项目方自述】\`owner/memory\`（2026-09-14）：提供会话记忆与导出。
- 【无证据】付费意愿、采购预算与市场规模：本轮无来源

**组件数据流**（起点 → 处理 → 终点）：

| 顺序 | 组件 | 角色 | 输入 | 输出 | 上下游 |
|---|---|---|---|---|---|
| 1 | [\`owner/memory\`](https://github.com/owner/memory) | 长期记忆 | 会话与运行记录 | 可召回的长期上下文 | 下游：agent |

**接入方式**：桌面端本地安装，无云依赖

**双评分**：技术组合成熟度 **79/100（中）**（组件可靠度 33/40 · 组件供给 18/20 · 风险敞口 8/20 · 许可证 10/10 · 完整度 10/10） · 需求证据强度 **59/100（低）**（证据等级 24/40 · 用户明确表态 0/25 · 独立来源 20/20 · 新鲜度 15/15）

**MVP 实验**：

- 周期：14 天
- 停止条件：周期结束未达到成功指标 → 停止
`;

describe("parseFeasibilityReport（双评分新格式）", () => {
  const report = parseFeasibilityReport(dualScoreMarkdown, "2026-09-20.md");

  it("parses the plan judgment and both score panels", () => {
    expect(report.plans).toHaveLength(1);
    const plan = report.plans[0];

    expect(plan.title).toBe("本地优先个人 AI 工作台");
    expect(plan.judgment).toBe("继续观察");
    expect(plan.judgmentReason).toContain("均未到推进线");
    expect(plan.techScore).toMatchObject({ name: "技术组合成熟度", score: 79, grade: "中" });
    expect(plan.demandScore).toMatchObject({ name: "需求证据强度", score: 59, grade: "低" });
    expect(plan.techScore?.parts).toContainEqual({ name: "风险敞口", points: 8, max: 20 });
    expect(plan.demandScore?.parts).toContainEqual({ name: "证据等级", points: 24, max: 40 });
    expect(plan.evidenceLevel).toBe("项目方自述");
    expect(plan.audience).toContain("重视隐私");
  });

  it("keeps the dual scores out of the prose body", () => {
    const plan = report.plans[0];

    expect(plan.bodyHtml).not.toContain("双评分");
    expect(plan.bodyHtml).not.toContain("方案判断");
    expect(plan.bodyHtml).toContain("需求证据");
    expect(plan.bodyHtml).toContain("组件数据流");
    // 旧字段在新格式下为空，由 techScore / demandScore 代替
    expect(plan.score).toBeNull();
    expect(report.opportunitiesHtml).toBe("");
    expect(report.actionsHtml).toBe("");
  });
});
