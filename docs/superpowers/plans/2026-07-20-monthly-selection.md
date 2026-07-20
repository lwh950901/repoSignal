# RepoSignal Monthly Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a static monthly selection archive with Top 5 analysis, role-based recommendations, observation signals, and a shared month/week/day period switcher.

**Architecture:** Keep daily and weekly reports on the existing `DigestReport` path, and add a separate `MonthlyReport` parser and view because monthly content has different validation and presentation needs. Build every report from repository Markdown at Astro build time, generate editorial drafts with a standalone Python script, and share only navigation, search, layout tokens, and repository links across report types.

**Tech Stack:** Astro 7, TypeScript 6, Vitest 4, `marked`, Python 3 standard library, static Markdown data.

**Design reference:** `docs/superpowers/specs/2026-07-20-monthly-selection-design.md`

---

## File map

**Create**

- `src/lib/monthly.ts` — monthly types, Markdown parsing, validation, loading, and search-index conversion.
- `src/lib/monthly.test.ts` — parser, validation, discovery, and search-index tests.
- `src/lib/periods.ts` — pure month/week/day anchor and fallback-link resolution.
- `src/lib/periods.test.ts` — exact-date, missing-period, and empty-period tests.
- `src/components/PeriodSwitcher.astro` — accessible shared month/week/day navigation.
- `src/components/MonthlyArchiveRail.astro` — desktop month archive and mobile month selector.
- `src/components/MonthlyProjectEntry.astro` — Top 5 and compact recommendation rendering.
- `src/components/MonthlyReportView.astro` — complete monthly reading flow.
- `src/pages/monthly/index.astro` — latest monthly report or empty state.
- `src/pages/monthly/[month].astro` — static historical month route.
- `src/pages/weekly/index.astro` — latest weekly report or weekly empty state.
- `src/pages/daily/index.astro` — latest daily report or daily empty state.
- `scripts/generate_monthly_digest.py` — deterministic monthly candidate draft generator.
- `data/github-project-digest/monthly/2026-07.md` — first published monthly page using repository evidence through July 20.
- `.gitignore` — keep visual-companion artifacts and generated draft files out of commits.

**Modify**

- `src/lib/digests.ts` — return shared search items with an explicit `reportType`.
- `src/lib/digests.test.ts` — assert daily and weekly type labels in search items.
- `src/lib/search.ts` — own the shared search-item type and rank monthly results first.
- `src/lib/search.test.ts` — verify report-type matching and monthly priority.
- `src/layouts/BaseLayout.astro` — accept period links and render the shared switcher.
- `src/components/SearchPalette.astro` — render the 月/周/日 badge instead of score/kind.
- `src/pages/index.astro` — provide search items and period links while retaining latest-weekly homepage behavior.
- `src/pages/daily/[date].astro` — provide daily anchor and period links.
- `src/pages/weekly/[week].astro` — provide weekly anchor and period links.
- `src/styles/global.css` — add period-switcher and monthly-page styles, including mobile and reduced-motion rules.
- `package.json` — expose the monthly draft generator self-check.

---

### Task 1: Parse and validate monthly Markdown

**Files:**

- Create: `src/lib/monthly.ts`
- Create: `src/lib/monthly.test.ts`

- [ ] **Step 1: Write the failing parser and validation tests**

Create `src/lib/monthly.test.ts` with a fixture builder so all five Top 5 entries contain real required fields:

```ts
import { describe, expect, it } from "vitest";
import {
  MonthlyValidationError,
  createMonthlySearchIndex,
  parseMonthlyReport,
} from "./monthly";

function topProject(index: number, repository: string): string {
  return `### ${index}. ${repository.split("/")[1]}
- 仓库：[${repository}](https://github.com/${repository})
- 主要角色：${index % 2 ? "技术负责人" : "独立开发者"}
- 次要角色：AI 产品创业者
- 入选依据：项目 ${index} 已形成清晰的工程边界。
- 最佳使用场景：用于验证月报解析的场景 ${index}。
- 主要风险：接口仍在快速演进。
- 证据强度：高`;
}

const sample = `# 2026 年 7 月精选

> 月度主题：开源 Agent 正从能运行走向可交付
> 数据截止：2026-07-20
> 候选数量：94

## 本月结论

本月重点是工程交付能力。

## 三句话读懂这个月

1. 框架开始补齐评测能力。
2. 上下文工程成为独立工具层。
3. 权限边界仍是团队采用风险。

## Top 5

${topProject(1, "pydantic/pydantic-ai")}

${topProject(2, "bytedance/deer-flow")}

${topProject(3, "Egonex-AI/Understand-Anything")}

${topProject(4, "VoltAgent/voltagent")}

${topProject(5, "earendil-works/pi")}

## 分类推荐

### 独立开发者

#### zilliztech/claude-context
- 仓库：[zilliztech/claude-context](https://github.com/zilliztech/claude-context)
- 推荐理由：改善大型代码库上下文检索。
- 主要风险：索引成本需要实际验证。

## 本月观察信号

### 持续成熟：Agent 工程框架
- 支撑项目：pydantic/pydantic-ai、VoltAgent/voltagent、langchain4j/langchain4j
- 观察：类型、评测和可观测能力正在成为基础能力。
- 证据强度：高

## 行动建议

### 技术负责人
- 为 Agent 项目补充权限和评测清单。
`;

describe("parseMonthlyReport", () => {
  it("extracts metadata, Top 5, recommendations, signals, and actions", () => {
    const report = parseMonthlyReport(sample, "2026-07.md");

    expect(report.slug).toBe("2026-07");
    expect(report.theme).toContain("可交付");
    expect(report.cutoffDate).toBe("2026-07-20");
    expect(report.candidateCount).toBe(94);
    expect(report.topProjects).toHaveLength(5);
    expect(report.topProjects[0].repository).toBe("pydantic/pydantic-ai");
    expect(report.topProjects[0].primaryAudience).toBe("技术负责人");
    expect(report.recommendations[0].audience).toBe("独立开发者");
    expect(report.signals[0].supportingRepositories).toHaveLength(3);
    expect(report.actions[0].items).toEqual(["为 Agent 项目补充权限和评测清单。"]);
  });

  it("rejects a published report without exactly five Top 5 projects", () => {
    const invalid = sample.replace(topProject(5, "earendil-works/pi"), "");
    expect(() => parseMonthlyReport(invalid, "2026-07.md")).toThrowError(
      new MonthlyValidationError("2026-07.md: Top 5 必须恰好包含 5 个项目"),
    );
  });

  it("rejects duplicate repositories case-insensitively", () => {
    const invalid = sample.replace("earendil-works/pi", "PYDANTIC/PYDANTIC-AI");
    expect(() => parseMonthlyReport(invalid, "2026-07.md")).toThrow(/重复仓库 pydantic\/pydantic-ai/u);
  });

  it("rejects non-GitHub repository links", () => {
    const invalid = sample.replace(
      "https://github.com/pydantic/pydantic-ai",
      "https://example.com/pydantic-ai",
    );
    expect(() => parseMonthlyReport(invalid, "2026-07.md")).toThrow(/GitHub 链接无效/u);
  });

  it("downgrades a signal that has fewer than three supporting projects", () => {
    const weak = sample.replace(
      "pydantic/pydantic-ai、VoltAgent/voltagent、langchain4j/langchain4j",
      "pydantic/pydantic-ai、VoltAgent/voltagent",
    );
    const report = parseMonthlyReport(weak, "2026-07.md");
    expect(report.signals[0].direction).toBe("编辑观察");
    expect(report.signals[0].evidenceStrength).toBe("观察");
  });

  it("creates monthly search items for Top 5 and recommendations", () => {
    const report = parseMonthlyReport(sample, "2026-07.md");
    const items = createMonthlySearchIndex([report]);

    expect(items).toHaveLength(6);
    expect(items[0]).toMatchObject({
      repository: "pydantic/pydantic-ai",
      reportType: "monthly",
      reportLabel: "2026-07",
      href: "/monthly/2026-07/#monthly-project-pydantic-pydantic-ai",
    });
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
npm test -- src/lib/monthly.test.ts
```

Expected: FAIL because `./monthly` does not exist.

- [ ] **Step 3: Implement the monthly types, parser, validation, and search conversion**

Create `src/lib/monthly.ts`. The implementation must define these public contracts exactly:

```ts
import { marked } from "marked";
import type { SearchIndexItem } from "./search";

export type MonthlyAudience = "独立开发者" | "技术负责人" | "AI 产品创业者";
export type EvidenceStrength = "高" | "中" | "观察";

export interface MonthlyProject {
  id: string;
  repository: string;
  url: string;
  primaryAudience: MonthlyAudience;
  secondaryAudiences: MonthlyAudience[];
  selectionReason: string;
  bestUseCase: string;
  risk: string;
  evidenceStrength: EvidenceStrength;
  markdown: string;
  html: string;
}

export interface MonthlyRecommendation {
  id: string;
  audience: MonthlyAudience;
  repository: string;
  url: string;
  reason: string;
  risk: string;
}

export interface MonthlySignal {
  direction: "快速上升" | "持续成熟" | "值得观望" | "编辑观察";
  title: string;
  observation: string;
  supportingRepositories: string[];
  evidenceStrength: EvidenceStrength;
}

export interface MonthlyActionGroup {
  audience: MonthlyAudience;
  items: string[];
}

export interface MonthlyReport {
  type: "monthly";
  slug: string;
  title: string;
  theme: string;
  cutoffDate: string;
  candidateCount: number;
  conclusion: string;
  conclusionHtml: string;
  theses: string[];
  topProjects: MonthlyProject[];
  recommendations: MonthlyRecommendation[];
  signals: MonthlySignal[];
  actions: MonthlyActionGroup[];
  markdown: string;
}

export class MonthlyValidationError extends Error {
  override name = "MonthlyValidationError";
}

const monthlyMarkdownFiles = import.meta.glob(
  "../../data/github-project-digest/monthly/*.md",
  { eager: true, import: "default", query: "?raw" },
) as Record<string, string>;

const audienceValues: MonthlyAudience[] = ["独立开发者", "技术负责人", "AI 产品创业者"];
const evidenceValues: EvidenceStrength[] = ["高", "中", "观察"];

function cleanInline(value = ""): string {
  return value.replace(/\[([^\]]+)\]\([^)]+\)/gu, "$1").replace(/\*\*/gu, "").replace(/`/gu, "").trim();
}

function projectId(repository: string): string {
  return `monthly-project-${repository.toLowerCase().replace(/[^a-z0-9]+/gu, "-").replace(/^-|-$/gu, "")}`;
}

function sectionText(markdown: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  return markdown.match(new RegExp(`^##\\s+${escaped}\\s*$([\\s\\S]*?)(?=\\n##\\s+|$)`, "mu"))?.[1]?.trim() ?? "";
}

function field(body: string, label: string): string {
  return cleanInline(body.match(new RegExp(`^-\\s+${label}：(.+)$`, "mu"))?.[1] ?? "");
}

function repositoryField(body: string, filename: string): { repository: string; url: string } {
  const match = body.match(/^-\s+仓库：\[([^\]]+)\]\(([^)]+)\)$/mu);
  if (!match) throw new MonthlyValidationError(`${filename}: 项目缺少仓库字段`);
  const repository = match[1].trim();
  const url = match[2].trim();
  if (!/^https:\/\/github\.com\/[^/]+\/[^/]+\/?$/u.test(url)) {
    throw new MonthlyValidationError(`${filename}: ${repository} 的 GitHub 链接无效`);
  }
  return { repository, url };
}

function audience(value: string, filename: string, repository: string): MonthlyAudience {
  if (!audienceValues.includes(value as MonthlyAudience)) {
    throw new MonthlyValidationError(`${filename}: ${repository} 的主要角色无效`);
  }
  return value as MonthlyAudience;
}

function evidence(value: string): EvidenceStrength {
  return evidenceValues.includes(value as EvidenceStrength) ? value as EvidenceStrength : "观察";
}

function parseTopProjects(markdown: string, filename: string): MonthlyProject[] {
  const section = sectionText(markdown, "Top 5");
  const headings = [...section.matchAll(/^###\s+\d+\.\s+(.+)$/gmu)];
  const projects = headings.map((heading, index) => {
    const body = section.slice(heading.index, headings[index + 1]?.index ?? section.length).replace(/^###.+$/mu, "").trim();
    const repo = repositoryField(body, filename);
    const required = {
      selectionReason: field(body, "入选依据"),
      bestUseCase: field(body, "最佳使用场景"),
      risk: field(body, "主要风险"),
    };
    for (const [label, value] of Object.entries(required)) {
      if (!value) throw new MonthlyValidationError(`${filename}: ${repo.repository} 缺少 ${label}`);
    }
    const secondary = field(body, "次要角色").split(/[、,，]/u).map((item) => item.trim()).filter(Boolean);
    return {
      id: projectId(repo.repository),
      ...repo,
      primaryAudience: audience(field(body, "主要角色"), filename, repo.repository),
      secondaryAudiences: secondary.filter((item): item is MonthlyAudience => audienceValues.includes(item as MonthlyAudience)),
      ...required,
      evidenceStrength: evidence(field(body, "证据强度")),
      markdown: body,
      html: marked.parse(body) as string,
    };
  });
  if (projects.length !== 5) throw new MonthlyValidationError(`${filename}: Top 5 必须恰好包含 5 个项目`);
  return projects;
}

function parseRecommendations(markdown: string, filename: string): MonthlyRecommendation[] {
  const section = sectionText(markdown, "分类推荐");
  const audiences = [...section.matchAll(/^###\s+(.+)$/gmu)];
  return audiences.flatMap((heading, audienceIndex) => {
    const audienceName = audience(cleanInline(heading[1]), filename, "分类推荐");
    const group = section.slice(heading.index, audiences[audienceIndex + 1]?.index ?? section.length);
    const projects = [...group.matchAll(/^####\s+(.+)$/gmu)];
    return projects.map((projectHeading, projectIndex) => {
      const body = group.slice(projectHeading.index, projects[projectIndex + 1]?.index ?? group.length).replace(/^####.+$/mu, "").trim();
      const repo = repositoryField(body, filename);
      return {
        id: projectId(repo.repository),
        audience: audienceName,
        ...repo,
        reason: field(body, "推荐理由"),
        risk: field(body, "主要风险"),
      };
    });
  });
}

function parseSignals(markdown: string): MonthlySignal[] {
  const section = sectionText(markdown, "本月观察信号");
  const headings = [...section.matchAll(/^###\s+(快速上升|持续成熟|值得观望|编辑观察)：(.+)$/gmu)];
  return headings.map((heading, index) => {
    const body = section.slice(heading.index, headings[index + 1]?.index ?? section.length).replace(/^###.+$/mu, "").trim();
    const supportingRepositories = field(body, "支撑项目").split(/[、,，]/u).map((item) => item.trim()).filter(Boolean);
    const hasEnoughEvidence = supportingRepositories.length >= 3;
    const direction = hasEnoughEvidence ? heading[1] as MonthlySignal["direction"] : "编辑观察";
    return {
      direction,
      title: cleanInline(heading[2]),
      observation: field(body, "观察"),
      supportingRepositories,
      evidenceStrength: hasEnoughEvidence ? evidence(field(body, "证据强度")) : "观察",
    };
  });
}

function parseActions(markdown: string, filename: string): MonthlyActionGroup[] {
  const section = sectionText(markdown, "行动建议");
  const headings = [...section.matchAll(/^###\s+(.+)$/gmu)];
  return headings.map((heading, index) => {
    const body = section.slice(heading.index, headings[index + 1]?.index ?? section.length);
    return { audience: audience(cleanInline(heading[1]), filename, "行动建议"), items: [...body.matchAll(/^-\s+(.+)$/gmu)].map((item) => cleanInline(item[1])) };
  });
}

function assertUniqueRepositories(report: MonthlyReport, filename: string): void {
  const seen = new Set<string>();
  for (const project of [...report.topProjects, ...report.recommendations]) {
    const key = project.repository.toLowerCase();
    if (seen.has(key)) throw new MonthlyValidationError(`${filename}: 重复仓库 ${key}`);
    seen.add(key);
  }
}

export function parseMonthlyReport(markdown: string, filename: string): MonthlyReport {
  const slug = filename.replace(/\.md$/u, "");
  if (!/^\d{4}-\d{2}$/u.test(slug)) throw new MonthlyValidationError(`${filename}: 月份文件名无效`);
  const title = cleanInline(markdown.match(/^#\s+(.+)$/mu)?.[1] ?? "");
  const theme = cleanInline(markdown.match(/^>\s*月度主题：(.+)$/mu)?.[1] ?? "");
  const cutoffDate = cleanInline(markdown.match(/^>\s*数据截止：(.+)$/mu)?.[1] ?? "");
  const candidateCount = Number(markdown.match(/^>\s*候选数量：(\d+)$/mu)?.[1] ?? "0");
  if (!title || !theme || !/^\d{4}-\d{2}-\d{2}$/u.test(cutoffDate)) {
    throw new MonthlyValidationError(`${filename}: 标题、月度主题或数据截止日期无效`);
  }
  const conclusion = sectionText(markdown, "本月结论");
  const theses = [...sectionText(markdown, "三句话读懂这个月").matchAll(/^\d+\.\s+(.+)$/gmu)].map((item) => cleanInline(item[1]));
  const report: MonthlyReport = {
    type: "monthly", slug, title, theme, cutoffDate, candidateCount, conclusion,
    conclusionHtml: marked.parse(conclusion) as string, theses,
    topProjects: parseTopProjects(markdown, filename),
    recommendations: parseRecommendations(markdown, filename),
    signals: parseSignals(markdown), actions: parseActions(markdown, filename), markdown,
  };
  assertUniqueRepositories(report, filename);
  return report;
}

export function loadMonthlyReports(): MonthlyReport[] {
  return Object.entries(monthlyMarkdownFiles)
    .map(([path, markdown]) => parseMonthlyReport(markdown, path.split("/").at(-1) ?? path))
    .sort((a, b) => b.slug.localeCompare(a.slug));
}

export function createMonthlySearchIndex(reports: MonthlyReport[]): SearchIndexItem[] {
  return reports.flatMap((report) => [...report.topProjects, ...report.recommendations].map((project) => ({
    id: `monthly-${report.slug}-${project.id}`,
    repository: project.repository,
    positioning: "selectionReason" in project ? project.selectionReason : project.reason,
    technologies: [], kind: "月度精选", score: null, reportType: "monthly" as const,
    reportLabel: report.slug, href: `/monthly/${report.slug}/#${project.id}`,
  })));
}
```

- [ ] **Step 4: Run the focused test**

Run:

```bash
npm test -- src/lib/monthly.test.ts
```

Expected: PASS with 6 tests.

- [ ] **Step 5: Commit the parser slice**

```bash
git add src/lib/monthly.ts src/lib/monthly.test.ts
git commit -m "feat: parse monthly selection reports"
```

---

### Task 2: Generate a deterministic monthly editorial draft

**Files:**

- Create: `scripts/generate_monthly_digest.py`
- Modify: `package.json:5-11`
- Create: `.gitignore`

- [ ] **Step 1: Write the generator self-check before the CLI implementation**

Create `scripts/generate_monthly_digest.py` with imports, data types, and this executable self-check first:

```py
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import tempfile
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

REPO_HEADING = re.compile(r"^###\s+\d+\.\s+(?:爆发型|实用型|潜力型)：([^\s—]+)", re.M)
WEEKLY_HEADING = re.compile(r"^##\s+\d+\.\s+([^\s]+)", re.M)

@dataclass
class Candidate:
    repository: str
    url: str
    dates: set[str] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)

def normalize_repository(value: str) -> str:
    return value.strip().lower()

def self_check() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "candidates").mkdir()
        (root / "daily").mkdir()
        (root / "weekly").mkdir()
        (root / "candidates/2026-07-02.jsonl").write_text(
            json.dumps({"repo": "Owner/Repo", "url": "https://github.com/Owner/Repo"}) + "\n",
            encoding="utf-8",
        )
        (root / "daily/2026-07-03.md").write_text(
            "### 1. 实用型：owner/repo — 88/100\n", encoding="utf-8"
        )
        (root / "weekly/2026-W27.md").write_text(
            "## 1. owner/repo\n", encoding="utf-8"
        )
        candidates = collect_candidates(root, "2026-07")
        assert list(candidates) == ["owner/repo"]
        assert candidates["owner/repo"].dates == {"2026-07-02", "2026-07-03"}
        assert candidates["owner/repo"].sources == {"候选账本", "日报", "周报"}
        draft = render_draft("2026-07", candidates)
        assert "候选数量：1" in draft
        assert "owner/repo" in draft
        assert "候选账本、日报、周报" in draft
    print("monthly draft generator self-check: PASS")
    return 0
```

- [ ] **Step 2: Run the self-check to verify it fails**

Run:

```bash
python3 scripts/generate_monthly_digest.py --check
```

Expected: FAIL because `collect_candidates` and `render_draft` are not defined.

- [ ] **Step 3: Add candidate collection, deterministic rendering, and CLI entry point**

Insert the following functions before `self_check()` and add the `main()` block after it:

```py
def merge_candidate(
    candidates: dict[str, Candidate], repository: str, url: str, date: str, source: str
) -> None:
    key = normalize_repository(repository)
    if not key or "/" not in key:
        return
    candidate = candidates.setdefault(
        key, Candidate(repository=key, url=url or f"https://github.com/{key}")
    )
    if date:
        candidate.dates.add(date)
    candidate.sources.add(source)

def iso_week_overlaps_month(slug: str, month: str) -> bool:
    match = re.fullmatch(r"(\d{4})-W(\d{2})", slug)
    if not match:
        return False
    monday = date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)
    return any((monday + timedelta(days=offset)).strftime("%Y-%m") == month for offset in range(7))

def collect_candidates(root: Path, month: str) -> dict[str, Candidate]:
    candidates: dict[str, Candidate] = {}
    for path in sorted((root / "candidates").glob(f"{month}-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            merge_candidate(candidates, item.get("repo", ""), item.get("url", ""), item.get("date", path.stem), "候选账本")
    for path in sorted((root / "daily").glob(f"{month}-*.md")):
        markdown = path.read_text(encoding="utf-8")
        for repository in REPO_HEADING.findall(markdown):
            merge_candidate(candidates, repository, "", path.stem, "日报")
    for path in sorted((root / "weekly").glob("*.md")):
        if not iso_week_overlaps_month(path.stem, month):
            continue
        markdown = path.read_text(encoding="utf-8")
        for repository in WEEKLY_HEADING.findall(markdown):
            merge_candidate(candidates, repository, "", "", "周报")
    return dict(sorted(candidates.items(), key=lambda item: (-len(item[1].sources), -len(item[1].dates), item[0])))

def render_draft(month: str, candidates: dict[str, Candidate]) -> str:
    year, month_number = month.split("-")
    lines = [
        f"# {year} 年 {int(month_number)} 月编辑候选稿",
        "",
        f"> 月度主题：本稿由候选账本、日报、周报聚合生成，发布前由编辑确定主题",
        f"> 数据截止：{max((date for item in candidates.values() for date in item.dates), default=f'{month}-01')}",
        f"> 候选数量：{len(candidates)}",
        "",
        "## 候选池",
        "",
    ]
    for index, candidate in enumerate(candidates.values(), start=1):
        dates = "、".join(sorted(candidate.dates)) or "未记录日期"
        sources = "、".join(sorted(candidate.sources))
        lines.extend([
            f"### {index}. {candidate.repository}",
            f"- 仓库：[{candidate.repository}]({candidate.url})",
            f"- 发现日期：{dates}",
            f"- 来源：{sources}",
            f"- 当月出现次数：{len(candidate.dates)}",
            "- 审核状态：待编辑确认",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"

def main() -> int:
    parser = argparse.ArgumentParser(description="生成 RepoSignal 月度候选初稿")
    parser.add_argument("month", nargs="?", help="YYYY-MM")
    parser.add_argument("--data-root", default="data/github-project-digest")
    parser.add_argument("--output")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return self_check()
    if not args.month or not re.fullmatch(r"\d{4}-\d{2}", args.month):
        parser.error("month 必须使用 YYYY-MM")
    root = Path(args.data_root)
    output = Path(args.output or root / "monthly-drafts" / f"{args.month}.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_draft(args.month, collect_candidates(root, args.month)), encoding="utf-8")
    print(f"monthly draft written: {output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Add scripts and ignore generated artifacts**

Add this script to `package.json`:

```json
"check:monthly-generator": "python3 scripts/generate_monthly_digest.py --check"
```

Create `.gitignore`:

```gitignore
.superpowers/
data/github-project-digest/monthly-drafts/
```

- [ ] **Step 5: Run the generator checks**

Run:

```bash
npm run check:monthly-generator
python3 scripts/generate_monthly_digest.py 2026-07 --output /tmp/repo-signal-2026-07-draft.md
```

Expected: the self-check prints `PASS`; the second command writes a draft and prints its absolute or relative output path.

- [ ] **Step 6: Commit the generator slice**

```bash
git add .gitignore package.json scripts/generate_monthly_digest.py
git commit -m "feat: generate monthly editorial drafts"
```

---

### Task 3: Resolve month/week/day links while preserving time context

**Files:**

- Create: `src/lib/periods.ts`
- Create: `src/lib/periods.test.ts`

- [ ] **Step 1: Write failing period-resolution tests**

Create `src/lib/periods.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { resolvePeriodLinks } from "./periods";

const monthly = [{ slug: "2026-06" }, { slug: "2026-07" }];
const weekly = [{ slug: "2026-W27" }, { slug: "2026-W28" }, { slug: "2026-W29" }];
const daily = [{ slug: "2026-07-01" }, { slug: "2026-07-18" }, { slug: "2026-07-20" }];

describe("resolvePeriodLinks", () => {
  it("keeps July context when switching from a July monthly report", () => {
    expect(resolvePeriodLinks("monthly", "2026-07", { monthly, weekly, daily })).toEqual({
      monthly: "/monthly/2026-07/",
      weekly: "/weekly/2026-W29/",
      daily: "/daily/2026-07-20/",
    });
  });

  it("maps a daily report to its containing week and month", () => {
    expect(resolvePeriodLinks("daily", "2026-07-18", { monthly, weekly, daily })).toEqual({
      monthly: "/monthly/2026-07/",
      weekly: "/weekly/2026-W29/",
      daily: "/daily/2026-07-18/",
    });
  });

  it("falls back to the nearest earlier report and then to type index", () => {
    expect(resolvePeriodLinks("daily", "2026-06-15", { monthly, weekly: [], daily: [] })).toEqual({
      monthly: "/monthly/",
      weekly: "/weekly/",
      daily: "/daily/",
    });
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run `npm test -- src/lib/periods.test.ts`.

Expected: FAIL because `./periods` does not exist.

- [ ] **Step 3: Implement pure date-anchor and fallback resolution**

Create `src/lib/periods.ts`:

```ts
export type ReportPeriod = "monthly" | "weekly" | "daily";
export interface PeriodReportRef { slug: string }
export interface PeriodCollections {
  monthly: PeriodReportRef[];
  weekly: PeriodReportRef[];
  daily: PeriodReportRef[];
}
export type PeriodLinks = Record<ReportPeriod, string>;

function isoWeekEnd(slug: string): Date {
  const match = slug.match(/^(\d{4})-W(\d{2})$/u);
  if (!match) throw new Error(`Invalid ISO week slug: ${slug}`);
  const year = Number(match[1]);
  const week = Number(match[2]);
  const januaryFourth = new Date(Date.UTC(year, 0, 4));
  const mondayOffset = (januaryFourth.getUTCDay() + 6) % 7;
  const weekOneMonday = new Date(Date.UTC(year, 0, 4 - mondayOffset));
  return new Date(weekOneMonday.getTime() + ((week - 1) * 7 + 6) * 86_400_000);
}

function monthEnd(slug: string): Date {
  const match = slug.match(/^(\d{4})-(\d{2})$/u);
  if (!match) throw new Error(`Invalid month slug: ${slug}`);
  return new Date(Date.UTC(Number(match[1]), Number(match[2]), 0));
}

export function reportAnchor(period: ReportPeriod, slug: string): Date {
  if (period === "monthly") return monthEnd(slug);
  if (period === "weekly") return isoWeekEnd(slug);
  const date = new Date(`${slug}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) throw new Error(`Invalid daily slug: ${slug}`);
  return date;
}

function choose(period: ReportPeriod, reports: PeriodReportRef[], anchor: Date): string {
  const eligible = reports
    .map((report) => ({ report, anchor: reportAnchor(period, report.slug) }))
    .filter((item) => item.anchor.getTime() <= anchor.getTime())
    .sort((a, b) => b.anchor.getTime() - a.anchor.getTime());
  return eligible[0]?.report.slug ?? "";
}

export function resolvePeriodLinks(
  currentPeriod: ReportPeriod,
  currentSlug: string,
  reports: PeriodCollections,
): PeriodLinks {
  const anchor = reportAnchor(currentPeriod, currentSlug);
  const monthly = choose("monthly", reports.monthly, anchor);
  const weekly = choose("weekly", reports.weekly, anchor);
  const daily = choose("daily", reports.daily, anchor);
  return {
    monthly: monthly ? `/monthly/${monthly}/` : "/monthly/",
    weekly: weekly ? `/weekly/${weekly}/` : "/weekly/",
    daily: daily ? `/daily/${daily}/` : "/daily/",
  };
}
```

- [ ] **Step 4: Run the period tests**

Run `npm test -- src/lib/periods.test.ts`.

Expected: PASS with 3 tests.

- [ ] **Step 5: Commit the period slice**

```bash
git add src/lib/periods.ts src/lib/periods.test.ts
git commit -m "feat: preserve context across report periods"
```

---

### Task 4: Share and prioritize month/week/day search results

**Files:**

- Modify: `src/lib/search.ts`
- Modify: `src/lib/search.test.ts`
- Modify: `src/lib/digests.ts:20-31,226-240`
- Modify: `src/lib/digests.test.ts`
- Modify: `src/components/SearchPalette.astro`

- [ ] **Step 1: Extend failing search tests with monthly priority**

Replace the item type import in `src/lib/search.test.ts` with `SearchIndexItem` from `./search`, add `reportType` to existing fixtures, and add:

```ts
it("prioritizes monthly selections over weekly and daily matches", () => {
  const repeated: SearchIndexItem[] = [
    { ...items[0], id: "daily", reportType: "daily", reportLabel: "2026-07-01" },
    { ...items[0], id: "monthly", reportType: "monthly", reportLabel: "2026-07" },
    { ...items[0], id: "weekly", reportType: "weekly", reportLabel: "2026-W29" },
  ];
  expect(searchProjects(repeated, "graphify").map((item) => item.id)).toEqual([
    "monthly", "weekly", "daily",
  ]);
});

it("matches the localized report type label", () => {
  expect(searchProjects([{ ...items[0], reportType: "monthly" }], "月")).toHaveLength(1);
});
```

- [ ] **Step 2: Run the search tests to verify they fail**

Run `npm test -- src/lib/search.test.ts`.

Expected: FAIL because `SearchIndexItem` and report-type ranking are absent.

- [ ] **Step 3: Move the shared item contract into `search.ts` and rank matches**

Replace `src/lib/search.ts` with:

```ts
export type SearchReportType = "monthly" | "weekly" | "daily";

export interface SearchIndexItem {
  id: string;
  repository: string;
  positioning: string;
  technologies: string[];
  kind: string;
  score: number | null;
  reportType: SearchReportType;
  reportLabel: string;
  href: string;
}

export const reportTypeLabel: Record<SearchReportType, "月" | "周" | "日"> = {
  monthly: "月",
  weekly: "周",
  daily: "日",
};

const priority: Record<SearchReportType, number> = { monthly: 0, weekly: 1, daily: 2 };

function normalize(value: string): string {
  return value.normalize("NFKC").toLocaleLowerCase("zh-CN");
}

export function searchProjects(items: SearchIndexItem[], query: string, limit = 8): SearchIndexItem[] {
  const terms = normalize(query).split(/\s+/u).filter(Boolean);
  return items
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => {
      if (terms.length === 0) return true;
      const haystack = normalize([
        item.repository, item.positioning, item.technologies.join(" "), item.kind,
        item.reportLabel, reportTypeLabel[item.reportType],
      ].join(" "));
      return terms.every((term) => haystack.includes(term));
    })
    .sort((a, b) => priority[a.item.reportType] - priority[b.item.reportType] || a.index - b.index)
    .slice(0, limit)
    .map(({ item }) => item);
}
```

In `src/lib/digests.ts`, remove `DigestIndexItem`, import `SearchIndexItem`, return that type from `createSearchIndex`, and set:

```ts
reportType: report.type === "daily" ? "daily" : "weekly",
```

Update `src/lib/digests.test.ts` to assert the created daily and weekly items use those exact values.

- [ ] **Step 4: Update the search palette badge**

In `src/components/SearchPalette.astro`, import `SearchIndexItem` and `reportTypeLabel` from `../lib/search`. Replace the badge assignment with:

```ts
badge.textContent = reportTypeLabel[item.reportType];
badge.setAttribute("aria-label", `${item.reportLabel} ${reportTypeLabel[item.reportType]}报`);
```

- [ ] **Step 5: Run focused and existing tests**

Run:

```bash
npm test -- src/lib/search.test.ts src/lib/digests.test.ts src/lib/monthly.test.ts
```

Expected: PASS for all search, digest, and monthly tests.

- [ ] **Step 6: Commit the search slice**

```bash
git add src/lib/search.ts src/lib/search.test.ts src/lib/digests.ts src/lib/digests.test.ts src/components/SearchPalette.astro
git commit -m "feat: add report periods to project search"
```

---

### Task 5: Add the shared period switcher and monthly page components

**Files:**

- Create: `src/components/PeriodSwitcher.astro`
- Create: `src/components/MonthlyArchiveRail.astro`
- Create: `src/components/MonthlyProjectEntry.astro`
- Create: `src/components/MonthlyReportView.astro`
- Modify: `src/layouts/BaseLayout.astro`

- [ ] **Step 1: Create the accessible shared period switcher**

Create `src/components/PeriodSwitcher.astro`:

```astro
---
import type { PeriodLinks, ReportPeriod } from "../lib/periods";
interface Props { activePeriod: ReportPeriod; links: PeriodLinks }
const { activePeriod, links } = Astro.props;
const periods: { key: ReportPeriod; short: string; long: string }[] = [
  { key: "monthly", short: "月", long: "MONTHLY" },
  { key: "weekly", short: "周", long: "WEEKLY" },
  { key: "daily", short: "日", long: "DAILY" },
];
---
<nav class="period-switcher" aria-label="报告周期">
  {periods.map((period) => (
    <a
      class:list={["period-switcher__item", { active: activePeriod === period.key }]}
      href={links[period.key]}
      aria-current={activePeriod === period.key ? "page" : undefined}
    >
      <strong>{period.short}</strong><small>{period.long}</small>
    </a>
  ))}
</nav>
```

- [ ] **Step 2: Create the monthly archive rail**

Create `src/components/MonthlyArchiveRail.astro`:

```astro
---
import type { MonthlyReport } from "../lib/monthly";
interface Props { reports: MonthlyReport[]; currentSlug: string }
const { reports, currentSlug } = Astro.props;
---
<aside class="date-rail monthly-archive" aria-label="月报归档">
  <div class="date-rail__heading"><span>MONTHLY ARCHIVE</span><span>{reports.length} 期</span></div>
  <label class="report-select">
    <span>选择月份</span>
    <select data-month-select>
      {reports.map((report) => <option value={`/monthly/${report.slug}/`} selected={report.slug === currentSlug}>{report.slug}</option>)}
    </select>
  </label>
  <ol class="month-list">
    {reports.map((report, index) => (
      <li class:list={{ active: report.slug === currentSlug }}>
        <a href={`/monthly/${report.slug}/`} aria-current={report.slug === currentSlug ? "page" : undefined}>
          <span>{report.slug}</span><small>{report.topProjects.length + report.recommendations.length} 项</small>{index === 0 && <em>最新</em>}
        </a>
      </li>
    ))}
  </ol>
  <noscript>
    <ol class="month-list month-list--noscript">
      {reports.map((report) => <li><a href={`/monthly/${report.slug}/`}><span>{report.slug}</span><small>{report.topProjects.length + report.recommendations.length} 项</small></a></li>)}
    </ol>
  </noscript>
  <nav class="monthly-on-page" aria-label="本页目录">
    <span>ON THIS PAGE</span>
    <a href="#monthly-conclusion">01 本月结论</a><a href="#monthly-top-five">02 Top 5</a>
    <a href="#monthly-recommendations">03 按场景选择</a><a href="#monthly-signals">04 观察信号</a>
    <a href="#monthly-actions">05 行动建议</a>
  </nav>
</aside>
<script>
  document.querySelector<HTMLSelectElement>("[data-month-select]")?.addEventListener("change", (event) => {
    window.location.href = (event.currentTarget as HTMLSelectElement).value;
  });
</script>
```

- [ ] **Step 3: Create the monthly project entry**

Create `src/components/MonthlyProjectEntry.astro`:

```astro
---
import type { MonthlyProject } from "../lib/monthly";
interface Props { project: MonthlyProject; index: number }
const { project, index } = Astro.props;
---
<article class="monthly-project" id={project.id}>
  <div class="monthly-project__rank">{String(index + 1).padStart(2, "0")} / 05</div>
  <div>
    <header class="monthly-project__header">
      <div><span class="project-stamp">{project.primaryAudience}</span><h3><a href={project.url} target="_blank" rel="noreferrer">{project.repository}</a></h3></div>
      <span class="evidence-badge">{project.evidenceStrength}置信</span>
    </header>
    <p class="monthly-project__verdict">{project.selectionReason}</p>
    <dl class="monthly-project__facts">
      <div><dt>为什么入选</dt><dd>{project.selectionReason}</dd></div>
      <div><dt>最佳使用场景</dt><dd>{project.bestUseCase}</dd></div>
      <div><dt>主要风险</dt><dd>{project.risk}</dd></div>
    </dl>
    {project.secondaryAudiences.length > 0 && <p class="monthly-project__secondary">也适合：{project.secondaryAudiences.join("、")}</p>}
  </div>
</article>
```

- [ ] **Step 4: Create the complete monthly report view**

Create `src/components/MonthlyReportView.astro`:

```astro
---
import type { MonthlyReport } from "../lib/monthly";
import MonthlyArchiveRail from "./MonthlyArchiveRail.astro";
import MonthlyProjectEntry from "./MonthlyProjectEntry.astro";
interface Props { report: MonthlyReport; reports: MonthlyReport[] }
const { report, reports } = Astro.props;
const audienceOrder = ["独立开发者", "技术负责人", "AI 产品创业者"] as const;
const currentIndex = reports.findIndex((item) => item.slug === report.slug);
const newerReport = currentIndex > 0 ? reports[currentIndex - 1] : undefined;
const olderReport = currentIndex >= 0 ? reports[currentIndex + 1] : undefined;
---
<main id="main-content" class="archive-shell monthly-shell">
  <MonthlyArchiveRail reports={reports} currentSlug={report.slug} />
  <article class="monthly-report">
    <header class="monthly-hero">
      <div class="report-kicker"><span>MONTHLY EDITOR'S SELECTION</span><time datetime={report.cutoffDate}>{report.slug} · 数据截至 {report.cutoffDate}</time></div>
      <h1>{report.theme}</h1>
      <div class="report-intro prose" set:html={report.conclusionHtml}></div>
      <div class="monthly-ledger" aria-label="本期摘要">
        <span><strong>{report.candidateCount}</strong> 当月候选</span><span><strong>5</strong> 深度精选</span>
        <span><strong>{report.recommendations.length}</strong> 分类推荐</span><span><strong>{report.signals.length}</strong> 观察信号</span>
      </div>
    </header>
    <section class="monthly-section" id="monthly-conclusion">
      <div class="monthly-section__label">01 / EDITOR'S NOTE</div><h2>三句话读懂这个月</h2>
      <ol class="monthly-theses">{report.theses.map((thesis) => <li>{thesis}</li>)}</ol>
    </section>
    <section class="monthly-section" id="monthly-top-five">
      <div class="monthly-section__label">02 / TOP FIVE</div><h2>本月最值得投入时间的 5 个项目</h2>
      <div class="monthly-top-five">{report.topProjects.map((project, index) => <MonthlyProjectEntry project={project} index={index} />)}</div>
    </section>
    <section class="monthly-section" id="monthly-recommendations">
      <div class="monthly-section__label">03 / CHOOSE BY CONTEXT</div><h2>不是所有好项目都适合你现在采用</h2>
      <div class="monthly-personas">
        {audienceOrder.map((audience) => <article><h3>{audience}</h3>{report.recommendations.filter((item) => item.audience === audience).map((item) => <div class="monthly-pick" id={item.id}><a href={item.url} target="_blank" rel="noreferrer">{item.repository}</a><p>{item.reason}</p>{item.risk && <small>风险：{item.risk}</small>}</div>)}</article>)}
      </div>
    </section>
    <section class="monthly-section" id="monthly-signals">
      <div class="monthly-section__label">04 / REPOSIGNAL OBSERVATIONS</div><h2>本月观察信号</h2>
      <div class="monthly-signals">{report.signals.map((signal) => <article><header><strong>{signal.direction}</strong><span>{signal.evidenceStrength}置信</span></header><h3>{signal.title}</h3><p>{signal.observation}</p><small>支撑项目：{signal.supportingRepositories.join("、")}</small></article>)}</div>
    </section>
    <section class="monthly-section monthly-actions" id="monthly-actions">
      <div class="monthly-section__label">05 / NEXT ACTION</div><h2>下个月前，建议做这些事</h2>
      <div>{report.actions.map((group) => <article><h3>{group.audience}</h3><ul>{group.items.map((item) => <li>{item}</li>)}</ul></article>)}</div>
    </section>
    <nav class="monthly-pagination" aria-label="相邻月报">
      {olderReport ? <a href={`/monthly/${olderReport.slug}/`}>← {olderReport.slug}</a> : <span></span>}
      {newerReport ? <a href={`/monthly/${newerReport.slug}/`}>{newerReport.slug} →</a> : <span></span>}
    </nav>
    <footer class="monthly-method">方法：候选账本初筛 + 人工定稿 · 发布后冻结，后续变化在新月报中说明</footer>
  </article>
</main>
```

- [ ] **Step 5: Render the switcher from `BaseLayout`**

In `BaseLayout.astro`, add the imports and props:

```astro
import PeriodSwitcher from "../components/PeriodSwitcher.astro";
import type { PeriodLinks, ReportPeriod } from "../lib/periods";
import type { SearchIndexItem } from "../lib/search";

interface Props {
  title: string;
  description?: string;
  searchItems: SearchIndexItem[];
  activePeriod: ReportPeriod;
  periodLinks: PeriodLinks;
}
```

Destructure `activePeriod` and `periodLinks` from `Astro.props`, then replace the existing site header with:

```astro
<header class="site-header">
  <a class="brand" href="/" aria-label="RepoSignal 首页">
    <span class="brand-mark" aria-hidden="true">⌁</span>
    <span>RepoSignal</span>
  </a>
  <PeriodSwitcher activePeriod={activePeriod} links={periodLinks} />
  <nav class="site-actions" aria-label="站点工具">
    <button class="search-trigger" type="button" data-search-open aria-label="打开项目搜索">
      <span>搜索</span><kbd>⌘ K</kbd>
    </button>
  </nav>
</header>
```

Inside `<head>`, after the description meta tag, add canonical and Open Graph metadata shared by every report page:

```astro
<link rel="canonical" href={Astro.url.pathname} />
<meta property="og:type" content="article" />
<meta property="og:title" content={title} />
<meta property="og:description" content={description} />
<meta property="og:url" content={Astro.url.pathname} />
<meta property="og:site_name" content="RepoSignal" />
```

- [ ] **Step 6: Run Astro type checking**

Run `npm run check`.

Expected: FAIL only in existing pages because they do not yet provide the new required `BaseLayout` props. This confirms the layout contract is enforced before routes are migrated.

- [ ] **Step 7: Commit the component slice**

```bash
git add src/components/PeriodSwitcher.astro src/components/MonthlyArchiveRail.astro src/components/MonthlyProjectEntry.astro src/components/MonthlyReportView.astro src/layouts/BaseLayout.astro
git commit -m "feat: add monthly report components"
```

---

### Task 6: Add monthly routes, migrate existing routes, and apply the approved UI

**Files:**

- Create: `src/pages/monthly/index.astro`
- Create: `src/pages/monthly/[month].astro`
- Create: `src/pages/weekly/index.astro`
- Create: `src/pages/daily/index.astro`
- Modify: `src/pages/index.astro`
- Modify: `src/pages/daily/[date].astro`
- Modify: `src/pages/weekly/[week].astro`
- Modify: `src/styles/global.css`

- [ ] **Step 1: Create the monthly index route**

Create `src/pages/monthly/index.astro`:

```astro
---
import BaseLayout from "../../layouts/BaseLayout.astro";
import MonthlyReportView from "../../components/MonthlyReportView.astro";
import { createSearchIndex, loadDailyReports, loadWeeklyReports } from "../../lib/digests";
import { createMonthlySearchIndex, loadMonthlyReports } from "../../lib/monthly";
import { resolvePeriodLinks } from "../../lib/periods";
const monthlyReports = loadMonthlyReports();
const dailyReports = loadDailyReports();
const weeklyReports = loadWeeklyReports();
const report = monthlyReports[0];
const anchorSlug = report?.slug ?? weeklyReports[0]?.slug ?? dailyReports[0]?.slug;
const anchorType = report ? "monthly" : weeklyReports.length ? "weekly" : "daily";
const periodLinks = anchorSlug ? resolvePeriodLinks(anchorType, anchorSlug, { monthly: monthlyReports, weekly: weeklyReports, daily: dailyReports }) : { monthly: "/monthly/", weekly: "/weekly/", daily: "/daily/" };
const searchItems = [...createMonthlySearchIndex(monthlyReports), ...createSearchIndex([...dailyReports, ...weeklyReports])];
---
<BaseLayout title="月度精选｜RepoSignal" searchItems={searchItems} activePeriod="monthly" periodLinks={periodLinks}>
  {report ? <MonthlyReportView report={report} reports={monthlyReports} /> : <main id="main-content" class="empty-state empty-state--page"><h1>月度精选正在准备中</h1><p>月报会从日报和周报中进一步筛选项目，并提供场景化选型与趋势判断。</p></main>}
</BaseLayout>
```

- [ ] **Step 2: Create daily and weekly type-index routes for safe fallback**

Create `src/pages/daily/index.astro`:

```astro
---
import BaseLayout from "../../layouts/BaseLayout.astro";
import ReportView from "../../components/ReportView.astro";
import { createSearchIndex, loadDailyReports, loadWeeklyReports } from "../../lib/digests";
import { createMonthlySearchIndex, loadMonthlyReports } from "../../lib/monthly";
import { resolvePeriodLinks } from "../../lib/periods";
const dailyReports = loadDailyReports();
const weeklyReports = loadWeeklyReports();
const monthlyReports = loadMonthlyReports();
const report = dailyReports[0];
const periodLinks = report
  ? resolvePeriodLinks("daily", report.slug, { monthly: monthlyReports, weekly: weeklyReports, daily: dailyReports })
  : { monthly: "/monthly/", weekly: "/weekly/", daily: "/daily/" };
const searchItems = [...createMonthlySearchIndex(monthlyReports), ...createSearchIndex([...dailyReports, ...weeklyReports])];
---
<BaseLayout title="每日发现｜RepoSignal" searchItems={searchItems} activePeriod="daily" periodLinks={periodLinks}>
  {report ? <ReportView report={report} dailyReports={dailyReports} weeklyReports={weeklyReports} /> : <main id="main-content" class="empty-state empty-state--page"><h1>还没有日报</h1><p>日报发布后会在这里显示最新一期。</p></main>}
</BaseLayout>
```

Create `src/pages/weekly/index.astro`:

```astro
---
import BaseLayout from "../../layouts/BaseLayout.astro";
import ReportView from "../../components/ReportView.astro";
import { createSearchIndex, loadDailyReports, loadWeeklyReports } from "../../lib/digests";
import { createMonthlySearchIndex, loadMonthlyReports } from "../../lib/monthly";
import { resolvePeriodLinks } from "../../lib/periods";
const dailyReports = loadDailyReports();
const weeklyReports = loadWeeklyReports();
const monthlyReports = loadMonthlyReports();
const report = weeklyReports[0];
const periodLinks = report
  ? resolvePeriodLinks("weekly", report.slug, { monthly: monthlyReports, weekly: weeklyReports, daily: dailyReports })
  : { monthly: "/monthly/", weekly: "/weekly/", daily: "/daily/" };
const searchItems = [...createMonthlySearchIndex(monthlyReports), ...createSearchIndex([...dailyReports, ...weeklyReports])];
---
<BaseLayout title="每周精选｜RepoSignal" searchItems={searchItems} activePeriod="weekly" periodLinks={periodLinks}>
  {report ? <ReportView report={report} dailyReports={dailyReports} weeklyReports={weeklyReports} /> : <main id="main-content" class="empty-state empty-state--page"><h1>还没有周报</h1><p>周报发布后会在这里显示最新一期。</p></main>}
</BaseLayout>
```

- [ ] **Step 3: Create historical month routes**

Create `src/pages/monthly/[month].astro`:

```astro
---
import BaseLayout from "../../layouts/BaseLayout.astro";
import MonthlyReportView from "../../components/MonthlyReportView.astro";
import { createSearchIndex, loadDailyReports, loadWeeklyReports } from "../../lib/digests";
import { createMonthlySearchIndex, loadMonthlyReports, type MonthlyReport } from "../../lib/monthly";
import { resolvePeriodLinks } from "../../lib/periods";

export function getStaticPaths() {
  return loadMonthlyReports().map((report) => ({ params: { month: report.slug }, props: { report } }));
}

interface Props { report: MonthlyReport }
const { report } = Astro.props;
const monthlyReports = loadMonthlyReports();
const dailyReports = loadDailyReports();
const weeklyReports = loadWeeklyReports();
const periodLinks = resolvePeriodLinks("monthly", report.slug, {
  monthly: monthlyReports,
  weekly: weeklyReports,
  daily: dailyReports,
});
const searchItems = [
  ...createMonthlySearchIndex(monthlyReports),
  ...createSearchIndex([...dailyReports, ...weeklyReports]),
];
---
<BaseLayout
  title={`${report.slug} 开源项目精选｜RepoSignal`}
  description={report.theme}
  searchItems={searchItems}
  activePeriod="monthly"
  periodLinks={periodLinks}
>
  <MonthlyReportView report={report} reports={monthlyReports} />
</BaseLayout>
```

- [ ] **Step 4: Migrate homepage, daily, and weekly pages**

Replace `src/pages/index.astro` with:

```astro
---
import BaseLayout from "../layouts/BaseLayout.astro";
import ReportView from "../components/ReportView.astro";
import { createSearchIndex, loadDailyReports, loadWeeklyReports, selectDefaultReport } from "../lib/digests";
import { createMonthlySearchIndex, loadMonthlyReports } from "../lib/monthly";
import { resolvePeriodLinks } from "../lib/periods";
const dailyReports = loadDailyReports();
const weeklyReports = loadWeeklyReports();
const monthlyReports = loadMonthlyReports();
const report = selectDefaultReport(dailyReports, weeklyReports);
const activePeriod = report?.type === "daily" ? "daily" : "weekly";
const periodLinks = report
  ? resolvePeriodLinks(activePeriod, report.slug, { monthly: monthlyReports, weekly: weeklyReports, daily: dailyReports })
  : { monthly: "/monthly/", weekly: "/weekly/", daily: "/daily/" };
const searchItems = [...createMonthlySearchIndex(monthlyReports), ...createSearchIndex([...dailyReports, ...weeklyReports])];
---
<BaseLayout title="RepoSignal｜GitHub 优质项目" searchItems={searchItems} activePeriod={activePeriod} periodLinks={periodLinks}>
  {report ? <ReportView report={report} dailyReports={dailyReports} weeklyReports={weeklyReports} /> : <main id="main-content" class="empty-state empty-state--page"><h1>还没有项目报告</h1><p>将 Markdown 放入 <code>data/github-project-digest/daily</code> 后重新构建。</p></main>}
</BaseLayout>
```

Replace `src/pages/daily/[date].astro` with:

```astro
---
import BaseLayout from "../../layouts/BaseLayout.astro";
import ReportView from "../../components/ReportView.astro";
import { createSearchIndex, loadDailyReports, loadWeeklyReports, type DigestReport } from "../../lib/digests";
import { createMonthlySearchIndex, loadMonthlyReports } from "../../lib/monthly";
import { resolvePeriodLinks } from "../../lib/periods";
export function getStaticPaths() {
  return loadDailyReports().map((report) => ({ params: { date: report.slug }, props: { report } }));
}
interface Props { report: DigestReport }
const { report } = Astro.props;
const dailyReports = loadDailyReports();
const weeklyReports = loadWeeklyReports();
const monthlyReports = loadMonthlyReports();
const periodLinks = resolvePeriodLinks("daily", report.slug, { monthly: monthlyReports, weekly: weeklyReports, daily: dailyReports });
const searchItems = [...createMonthlySearchIndex(monthlyReports), ...createSearchIndex([...dailyReports, ...weeklyReports])];
---
<BaseLayout title={`${report.date}｜RepoSignal`} description={report.theme} searchItems={searchItems} activePeriod="daily" periodLinks={periodLinks}>
  <ReportView report={report} dailyReports={dailyReports} weeklyReports={weeklyReports} />
</BaseLayout>
```

Replace `src/pages/weekly/[week].astro` with:

```astro
---
import BaseLayout from "../../layouts/BaseLayout.astro";
import ReportView from "../../components/ReportView.astro";
import { createSearchIndex, loadDailyReports, loadWeeklyReports, type DigestReport } from "../../lib/digests";
import { createMonthlySearchIndex, loadMonthlyReports } from "../../lib/monthly";
import { resolvePeriodLinks } from "../../lib/periods";
export function getStaticPaths() {
  return loadWeeklyReports().map((report) => ({ params: { week: report.slug }, props: { report } }));
}
interface Props { report: DigestReport }
const { report } = Astro.props;
const dailyReports = loadDailyReports();
const weeklyReports = loadWeeklyReports();
const monthlyReports = loadMonthlyReports();
const periodLinks = resolvePeriodLinks("weekly", report.slug, { monthly: monthlyReports, weekly: weeklyReports, daily: dailyReports });
const searchItems = [...createMonthlySearchIndex(monthlyReports), ...createSearchIndex([...dailyReports, ...weeklyReports])];
---
<BaseLayout title={`${report.slug}｜每周精选`} description={report.introduction} searchItems={searchItems} activePeriod="weekly" periodLinks={periodLinks}>
  <ReportView report={report} dailyReports={dailyReports} weeklyReports={weeklyReports} />
</BaseLayout>
```

- [ ] **Step 5: Add the approved visual system to `global.css`**

Append styles for these exact class groups:

```css
.site-header { display: grid; grid-template-columns: 1fr auto 1fr; }
.site-actions { justify-self: end; }
.period-switcher { align-self: stretch; display: flex; align-items: stretch; gap: .25rem; }
.period-switcher__item { min-width: 5.5rem; display: grid; place-content: center; text-align: center; border-bottom: 3px solid transparent; color: var(--ink-soft); text-decoration: none; line-height: 1.2; }
.period-switcher__item strong { font-size: .8rem; }
.period-switcher__item small { margin-top: .2rem; font: .52rem var(--font-mono); letter-spacing: .1em; }
.period-switcher__item.active { border-bottom-color: var(--moss); color: var(--ink); }
.monthly-report { min-width: 0; }
.monthly-hero { padding: clamp(2rem, 4vw, 4rem) 0 var(--space-7); }
.monthly-hero h1 { max-width: 18ch; margin: var(--space-5) 0; font-size: clamp(2.2rem, 5vw, 4.5rem); line-height: 1.04; letter-spacing: -.055em; text-wrap: balance; }
.monthly-ledger { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: var(--space-7); border-top: 1px solid var(--ink); border-bottom: 1px solid var(--rule); }
.monthly-ledger span { padding: var(--space-4); border-right: 1px solid var(--rule); color: var(--ink-soft); font: .7rem var(--font-mono); }
.monthly-ledger span:last-child { border-right: 0; }
.monthly-ledger strong { display: block; color: var(--ink); font-size: 1.5rem; font-weight: 500; }
.monthly-section { padding: clamp(2rem, 4vw, 4rem) 0; border-bottom: 1px solid var(--rule); scroll-margin-top: 1rem; }
.monthly-section__label { color: var(--moss); font: .65rem var(--font-mono); letter-spacing: .14em; }
.monthly-section > h2 { margin: .6rem 0 var(--space-6); font-size: clamp(1.55rem, 3vw, 2.4rem); letter-spacing: -.035em; }
.monthly-theses { display: grid; grid-template-columns: repeat(3, 1fr); margin: 0; padding: 0; counter-reset: thesis; list-style: none; border: 1px solid var(--rule); }
.monthly-theses li { min-height: 9rem; padding: var(--space-5); border-right: 1px solid var(--rule); background: var(--white); counter-increment: thesis; }
.monthly-theses li::before { content: "0" counter(thesis); display: block; margin-bottom: var(--space-5); color: var(--moss); font: 1.5rem var(--font-mono); }
.monthly-theses li:last-child { border-right: 0; }
.monthly-project { display: grid; grid-template-columns: 4rem minmax(0, 1fr); gap: var(--space-5); padding: var(--space-7) 0; border-top: 1px solid var(--ink); }
.monthly-project__rank { color: var(--ink-soft); font: .7rem var(--font-mono); }
.monthly-project__header { display: flex; justify-content: space-between; gap: var(--space-5); }
.monthly-project__header h3 { margin: .7rem 0; font: 500 clamp(1.5rem, 3vw, 2.4rem)/1.1 var(--font-mono); letter-spacing: -.045em; }
.monthly-project__header h3 a { text-decoration: none; }
.evidence-badge { height: fit-content; padding: .18rem .45rem; background: var(--paper-deep); color: var(--moss); font: .62rem var(--font-mono); }
.monthly-project__verdict { max-width: 50rem; font-size: 1.05rem; }
.monthly-project__facts { display: grid; grid-template-columns: repeat(3, 1fr); margin: var(--space-5) 0 0; border-top: 1px solid var(--rule); }
.monthly-project__facts > div { padding: var(--space-4) var(--space-4) 0 0; }
.monthly-project__facts dt { color: var(--ink-soft); font: .62rem var(--font-mono); letter-spacing: .08em; }
.monthly-project__facts dd { margin: .4rem 0 0; font-size: .85rem; }
.monthly-project__secondary { color: var(--ink-soft); font-size: .78rem; }
.monthly-personas { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
.monthly-personas > article { padding: var(--space-5); border-top: 3px solid var(--moss); background: var(--paper-deep); }
.monthly-personas h3 { margin-top: 0; }
.monthly-pick { margin-top: var(--space-3); padding: var(--space-4); border: 1px solid var(--rule); background: var(--white); }
.monthly-pick a { font-family: var(--font-mono); font-size: .78rem; font-weight: 600; }
.monthly-pick p, .monthly-pick small { font-size: .78rem; line-height: 1.55; }
.monthly-pick small { color: var(--danger); }
.monthly-signals { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
.monthly-signals article { padding: var(--space-5); border: 1px solid var(--rule); background: var(--white); }
.monthly-signals header { display: flex; justify-content: space-between; color: var(--moss); font: .65rem var(--font-mono); }
.monthly-signals h3 { line-height: 1.3; }
.monthly-signals p, .monthly-signals small { font-size: .8rem; }
.monthly-actions { padding: var(--space-7); background: var(--ink); color: var(--white); }
.monthly-actions > div { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-5); }
.monthly-actions li { color: var(--paper-deep); font-size: .85rem; }
.monthly-method { padding: var(--space-5) 0; color: var(--ink-soft); font: .65rem var(--font-mono); }
.monthly-pagination { display: flex; justify-content: space-between; padding: var(--space-5) 0; border-bottom: 1px solid var(--rule); font: .72rem var(--font-mono); }
.monthly-pagination a { color: var(--moss); text-decoration: none; }
.month-list { margin: 0; padding: 0; list-style: none; }
.month-list a { display: grid; grid-template-columns: 1fr auto auto; gap: .5rem; padding: .55rem 0; color: var(--ink-soft); font-size: .75rem; text-decoration: none; }
.month-list .active a { color: var(--ink); font-weight: 600; }
.month-list small, .month-list em { color: var(--moss); font-size: .6rem; font-style: normal; }
.monthly-on-page { display: grid; gap: .4rem; margin-top: var(--space-6); padding-top: var(--space-5); border-top: 1px solid var(--rule); font-size: .7rem; }
.monthly-on-page span { color: var(--ink-soft); font-size: .6rem; letter-spacing: .12em; }
.monthly-on-page a { text-decoration: none; }
```

Inside the existing `@media (max-width: 768px)` block, add:

```css
.site-header { grid-template-columns: 1fr auto; }
.period-switcher { grid-column: 1 / -1; grid-row: 2; width: 100%; border: 1px solid var(--rule); }
.period-switcher__item { flex: 1; min-width: 0; min-height: 2.5rem; border-right: 1px solid var(--rule); border-bottom: 0; }
.period-switcher__item:last-child { border-right: 0; }
.period-switcher__item small { display: none; }
.period-switcher__item.active { background: var(--ink); color: var(--white); }
.monthly-hero h1 { font-size: clamp(2rem, 10vw, 3rem); }
.monthly-ledger { grid-template-columns: repeat(2, 1fr); }
.monthly-ledger span:nth-child(2) { border-right: 0; }
.monthly-ledger span:nth-child(-n+2) { border-bottom: 1px solid var(--rule); }
.monthly-theses, .monthly-personas, .monthly-signals, .monthly-actions > div { grid-template-columns: 1fr; }
.monthly-theses li { min-height: 0; border-right: 0; border-bottom: 1px solid var(--rule); }
.monthly-theses li:last-child { border-bottom: 0; }
.monthly-project { grid-template-columns: 1fr; }
.monthly-project__rank { display: none; }
.monthly-project__facts { grid-template-columns: 1fr; }
.monthly-project__facts > div { padding-right: 0; }
.month-list, .monthly-on-page { display: none; }
.month-list--noscript { display: block; }
.monthly-actions { padding: var(--space-5); }
```

- [ ] **Step 6: Run type checking and production build**

Run:

```bash
npm run check
npm run build
```

Expected: both commands succeed. Before Task 7 adds published content, `/monthly/` builds with the empty state and no historical month routes.

- [ ] **Step 7: Commit routes and styling**

```bash
git add src/pages src/styles/global.css
git commit -m "feat: add monthly archive routes and navigation"
```

---

### Task 7: Publish the first monthly report and verify the complete feature

**Files:**

- Create: `data/github-project-digest/monthly/2026-07.md`
- Modify: `README.md`

- [ ] **Step 1: Generate and inspect the July candidate draft**

Run:

```bash
python3 scripts/generate_monthly_digest.py 2026-07
sed -n '1,220p' data/github-project-digest/monthly-drafts/2026-07.md
```

Expected: the draft contains deduplicated July candidates, their source channels, dates, and occurrence counts. Do not stage the draft directory.

- [ ] **Step 2: Write the first published monthly Markdown**

Create `data/github-project-digest/monthly/2026-07.md` using the exact schema from the design. Use repository evidence already present in July daily and weekly reports. The published file must contain:

```md
# 2026 年 7 月精选

> 月度主题：开源 Agent 正从“能运行”走向“可交付”
> 数据截止：2026-07-20
> 候选数量：285

## 本月结论

本月值得投入时间的项目，开始集中解决评测、上下文、编排与团队采用问题。重点不再只是模型能力或 Demo 效果，而是能否形成可测试、可观察、可持续维护的交付路径。

## 三句话读懂这个月

1. Agent 框架开始补齐类型、安全、评测与可观测能力。
2. 上下文工程正在成为独立工具层，而不只是 Coding Agent 的附属功能。
3. 团队采用时最需要关注的仍是权限边界、维护成本和迁移风险。

## Top 5

### 1. pydantic-ai
- 仓库：[pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai)
- 主要角色：技术负责人
- 次要角色：独立开发者
- 入选依据：在类型约束、结构化输出、依赖注入与测试体验之间形成了清晰的工程边界，适合把 Python Agent 原型推进到生产服务。
- 最佳使用场景：需要可靠结构化输出、可测试性和明确依赖边界的生产 Agent 服务。
- 主要风险：项目仍处于快速演进阶段，采用前需要确认版本策略和接口稳定性。
- 证据强度：高

### 2. deer-flow
- 仓库：[bytedance/deer-flow](https://github.com/bytedance/deer-flow)
- 主要角色：AI 产品创业者
- 次要角色：技术负责人
- 入选依据：把深度研究、工具调用、内容组织和结果交付组合成相对完整的产品工作流，适合研究 Agent 产品化路径。
- 最佳使用场景：验证研究型 Agent 的任务拆解、资料汇总和最终交付体验。
- 主要风险：完整工作流带来较高部署和维护成本，真实业务采用前需要拆分验证关键环节。
- 证据强度：高

### 3. Understand-Anything
- 仓库：[Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything)
- 主要角色：独立开发者
- 次要角色：技术负责人
- 入选依据：把复杂代码库理解转化为可交互知识图谱，使用价值直观，并回应了大型仓库上下文组织的真实需求。
- 最佳使用场景：接手陌生代码库、梳理模块关系或为后续 Agent 工作流建立知识底座。
- 主要风险：索引成本、图谱准确性和大型仓库上的稳定性需要用真实项目验证。
- 证据强度：中

### 4. VoltAgent
- 仓库：[VoltAgent/voltagent](https://github.com/VoltAgent/voltagent)
- 主要角色：技术负责人
- 次要角色：AI 产品创业者
- 入选依据：面向团队补齐 Agent 编排、可观测和工程治理能力，代表框架竞争从快速原型转向持续运营。
- 最佳使用场景：团队评估多 Agent 编排、运行观察和统一工程工具链。
- 主要风险：与现有基础设施可能存在能力重叠，采用前需要明确替换边界和迁移成本。
- 证据强度：中

### 5. pi
- 仓库：[earendil-works/pi](https://github.com/earendil-works/pi)
- 主要角色：独立开发者
- 次要角色：AI 产品创业者
- 入选依据：以克制的产品边界支持个人智能工作流，适合观察轻量 Agent 工具如何减少配置和平台负担。
- 最佳使用场景：快速组合个人开发、研究或内容处理流程，并验证日常使用频率。
- 主要风险：优势在于轻量而不是平台完整度，复杂团队协作场景可能需要其他基础设施。
- 证据强度：中

## 分类推荐

### 独立开发者

#### zilliztech/claude-context
- 仓库：[zilliztech/claude-context](https://github.com/zilliztech/claude-context)
- 推荐理由：适合改善大型代码库的上下文检索，并验证独立上下文层的实际价值。
- 主要风险：需要评估索引耗时、存储成本和召回稳定性。

#### affaan-m/ECC
- 仓库：[affaan-m/ECC](https://github.com/affaan-m/ECC)
- 推荐理由：提供可直接借鉴的工程方法与使用范式，适合个人开发者快速试验。
- 主要风险：方法有效性依赖个人工作流，不能仅凭仓库热度判断收益。

#### CodeBendKit/codeseek
- 仓库：[CodeBendKit/codeseek](https://github.com/CodeBendKit/codeseek)
- 推荐理由：面向代码检索和理解场景，适合比较不同上下文方案的真实效果。
- 主要风险：需要在大型、多语言仓库上验证召回质量。

### 技术负责人

#### langchain4j/langchain4j
- 仓库：[langchain4j/langchain4j](https://github.com/langchain4j/langchain4j)
- 推荐理由：为 Java 团队提供较完整的 AI 应用路径，适合评估与既有服务体系的整合方式。
- 主要风险：框架抽象和模型供应商接口持续变化，升级策略需要提前设计。

#### microsoft/agent-framework
- 仓库：[microsoft/agent-framework](https://github.com/microsoft/agent-framework)
- 推荐理由：适合观察企业级 Agent 基础设施在编排、治理和生态整合上的方向。
- 主要风险：平台边界和成熟度仍需结合实际文档与样例验证。

#### UiPath/coder_eval
- 仓库：[UiPath/coder_eval](https://github.com/UiPath/coder_eval)
- 推荐理由：为编码 Agent 补充评测视角，适合作为团队质量反馈闭环的参考。
- 主要风险：评测集与真实业务代码的相关性需要单独验证。

### AI 产品创业者

#### MemPalace/mempalace
- 仓库：[MemPalace/mempalace](https://github.com/MemPalace/mempalace)
- 推荐理由：展示长期记忆能力的产品化方向，适合验证记忆检索与用户体验的结合点。
- 主要风险：记忆准确性、隐私和删除机制是产品落地的核心约束。

#### open-multi-agent/open-multi-agent
- 仓库：[open-multi-agent/open-multi-agent](https://github.com/open-multi-agent/open-multi-agent)
- 推荐理由：适合观察通用多 Agent 协作产品的交互与编排边界。
- 主要风险：真实团队采用案例有限，复杂协作可能增加不可预测性。

#### SolaceLabs/solace-agent-mesh
- 仓库：[SolaceLabs/solace-agent-mesh](https://github.com/SolaceLabs/solace-agent-mesh)
- 推荐理由：为事件驱动的 Agent 协作提供组合思路，适合探索企业集成机会。
- 主要风险：基础设施复杂度较高，不适合尚未验证核心需求的早期产品。

## 本月观察信号

### 持续成熟：Agent 工程框架
- 支撑项目：pydantic/pydantic-ai、VoltAgent/voltagent、langchain4j/langchain4j
- 观察：类型、安全、评测与可观测能力正在成为 Agent 框架的基础能力。
- 证据强度：高

### 快速上升：代码库上下文工具
- 支撑项目：Egonex-AI/Understand-Anything、zilliztech/claude-context、CodeBendKit/codeseek
- 观察：代码库上下文和知识图谱开始形成独立工具层，不再只是 Coding Agent 的附属能力。
- 证据强度：中

### 值得观望：通用多 Agent 协作平台
- 支撑项目：open-multi-agent/open-multi-agent、SolaceLabs/solace-agent-mesh、VoltAgent/voltagent
- 观察：平台数量增加，但真实团队采用案例、权限治理和稳定收益仍然不足。
- 证据强度：观察

## 行动建议

### 独立开发者
- 实际试用一个代码库上下文工具，并记录它是否减少了重复查找和解释成本。
- 选择一个轻量 Agent 工作流连续使用一周，用真实频率而不是 Demo 效果判断价值。

### 技术负责人
- 为现有 Agent 项目补充权限边界、离线评测和运行可观测清单。
- 在引入新框架前明确它替代什么，并估算迁移、升级和退出成本。

### AI 产品创业者
- 优先验证一个“研究—生成—评估”闭环，而不是继续增加孤立功能。
- 把长期记忆的隐私、可纠正和删除机制纳入首轮产品验证。
```

- [ ] **Step 3: Update README data-source and navigation documentation**

Add monthly reports and the top period switch to `README.md`:

```md
- 月报：`data/github-project-digest/monthly/*.md`

月报由候选账本、日报和周报生成编辑初稿，再由人工确定 Top 5、角色建议、风险和观察信号。顶部“月 / 周 / 日”导航会尽量保留当前时间上下文。
```

- [ ] **Step 4: Add a real-content discovery assertion**

Import `loadMonthlyReports` in `src/lib/monthly.test.ts` and add:

```ts
describe("monthly discovery", () => {
  it("loads published reports newest first", () => {
    const reports = loadMonthlyReports();
    expect(reports.length).toBeGreaterThan(0);
    expect(reports[0].slug).toBe("2026-07");
    expect(reports[0].topProjects).toHaveLength(5);
    expect(reports.map((report) => report.slug)).toEqual(
      [...reports.map((report) => report.slug)].sort().reverse(),
    );
  });
});
```

- [ ] **Step 5: Run focused parser and generator verification**

Run:

```bash
npm test -- src/lib/monthly.test.ts src/lib/periods.test.ts src/lib/search.test.ts src/lib/digests.test.ts
npm run check:monthly-generator
```

Expected: all Vitest files pass and the Python self-check prints `PASS`.

- [ ] **Step 6: Run full repository verification**

Run each command separately:

```bash
npm test
npm run check
npm run build
```

Expected: all tests pass, Astro reports no type errors, and the build output includes `/monthly/index.html` plus `/monthly/2026-07/index.html`.

- [ ] **Step 7: Inspect responsive output**

Start `npm run dev`, open `/monthly/2026-07/`, and verify at 1440px and 360px:

- The month/week/day switch is visible and keyboard reachable.
- The month archive collapses to the select control at 360px.
- Top 5 facts stack without horizontal scrolling.
- All repository links open the correct GitHub URL.
- With JavaScript disabled, report content and navigation links remain usable.

- [ ] **Step 8: Commit the complete feature content**

```bash
git add data/github-project-digest/monthly/2026-07.md README.md src/lib/monthly.test.ts
git commit -m "content: publish July monthly selection"
```

---

## Final review checklist

- [ ] Every requirement in `docs/superpowers/specs/2026-07-20-monthly-selection-design.md` maps to a task above.
- [ ] `rg -n 'T[B]D|T[O]DO|implement l[a]ter|fill i[n]|similar t[o]' docs/superpowers/plans/2026-07-20-monthly-selection.md` returns no unresolved planning placeholders.
- [ ] The type names `MonthlyReport`, `MonthlyProject`, `SearchIndexItem`, `ReportPeriod`, and `PeriodLinks` are consistent in all tasks.
- [ ] `git status --short` shows no generated `monthly-drafts/` or `.superpowers/` files staged.
- [ ] Final verification runs `npm test`, `npm run check`, and `npm run build` from the repository root.
