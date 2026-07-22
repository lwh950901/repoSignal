# Monthly Business Research Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the synthetic July monthly selection with an evidence-backed independent Top 5 and zero to three verified business opportunities built from feasible GitHub repository combinations.

**Architecture:** Keep the existing Astro routes, period navigation and local search. Store public frozen conclusions in `monthly/YYYY-MM.md`, store non-public research evidence in `monthly-research/YYYY-MM/`, parse only stable public fields into a revised `MonthlyReport`, and render long-form business analysis from fixed Markdown subsections. External access is allowed only during research; tests and production builds remain deterministic and offline.

**Tech Stack:** Astro 7, TypeScript 6, Vitest 4, `marked`, Python 3 standard library, OpenSpec spec-driven workflow, Markdown research artifacts.

---

## File Structure

- `data/github-project-digest/monthly/2026-07.md`: revised public frozen report; no unverified claims.
- `data/github-project-digest/monthly-research/2026-07/top5-scorecard.md`: deep-candidate facts, scores, objections and ranking decision.
- `data/github-project-digest/monthly-research/2026-07/business-<slug>.md`: one evidence file per investigated business hypothesis, including rejected hypotheses.
- `data/github-project-digest/monthly-research/2026-07/repository-verification.md`: L0–L4 checks, safe run commands, outputs and blockers.
- `src/lib/monthly.ts`: revised public Markdown types, parser, validation, discovery and search conversion.
- `src/lib/monthly.test.ts`: parser, enum, score, source, count and real-content regression tests.
- `src/components/MonthlyReportView.astro`: revised Top 5 and business-opportunity reading view.
- `src/styles/global.css`: responsive score, evidence, comparison and combination-flow styles using existing tokens.
- `scripts/generate_monthly_digest.py`: candidate aggregation remains editorial input; only adjust metadata output if the real candidate audit exposes a deterministic mismatch.
- `README.md`: documents candidate aggregation, external research, internal evidence and frozen publication.

Do not create a client-side research app, database, public research route, scoring package or new dependency.

### Task 1: Freeze the July Candidate Audit and Research Contracts

**Files:**
- Create: `data/github-project-digest/monthly-research/2026-07/top5-scorecard.md`
- Create: `data/github-project-digest/monthly-research/2026-07/repository-verification.md`
- Modify only if required by a reproduced mismatch: `scripts/generate_monthly_digest.py`

- [ ] **Step 1: Reproduce the candidate pool from local evidence**

Run:

```bash
python3 scripts/generate_monthly_digest.py 2026-07 --output /tmp/reposignal-2026-07-candidates.md
sed -n '1,12p' /tmp/reposignal-2026-07-candidates.md
```

Expected: the command succeeds, reports a deterministic qualified count, and the draft cutoff equals the latest included July evidence date. Record both values in the research files; do not copy the old public value `94` unless the fresh command returns it.

- [ ] **Step 2: Confirm rejected and prose-shaped false repositories stay excluded**

Run:

```bash
rg -n '^### (0xkaz/llm-governance-dashboard|docs/superpowers|cli/tui|\.github/workflows)$' /tmp/reposignal-2026-07-candidates.md
```

Expected: no matches. If a match appears, add the exact record or Markdown line to `self_check()` in `scripts/generate_monthly_digest.py`, run it red, make the smallest extraction/filter fix, and rerun until green.

- [ ] **Step 3: Create the scorecard contract**

The scorecard must start with these exact headings and rules:

```markdown
# 2026-07 Top 5 研究评分表

- 候选池数量：以生成器本次输出为准
- 候选池截止：以生成器本次输出为准
- 深度候选数量：记录实际入选数量
- GitHub 核实日期：记录实际核实日期
- 评分权重：本月重要性 20、实际价值 25、工程质量 20、差异化 15、维护可持续性 10、采用证据 10

## 深度候选

每个候选必须记录：仓库、官方 URL、本月变化、Stars、Forks、Release、最近有效活动、许可证、验证等级、六项得分、总分、主要反对理由、来源、核实日期。

## 权重校准

只记录一次校准；说明原权重的问题、修改内容和对所有候选统一生效的理由。没有修改时写“未调整”。

## 最终排名

记录 1–5 名、总分、人工调整及理由；没有人工调整时写“无”。
```

- [ ] **Step 4: Create the repository verification contract**

Use these fixed verification labels:

```markdown
# 2026-07 仓库验证记录

验证等级：
- L0：官方仓库、许可证、维护状态和文档已检查
- L1：安装成功并能启动最小命令
- L2：官方最小示例产生预期输出
- L3：两个或多个仓库完成最小数据连接
- L4：使用真实数据完成一项业务任务

每条记录必须包含：仓库、是否本月核心项目、核实日期、许可证、最近活动、安装方式、输入、输出、接口、外部依赖、安全限制、执行命令、执行结果、最终等级、阻塞项、来源。
```

- [ ] **Step 5: Run the offline generator check and commit the contracts**

Run:

```bash
npm run check:monthly-generator
git diff --check
git add scripts/generate_monthly_digest.py data/github-project-digest/monthly-research/2026-07
git commit -m "research: establish July monthly evidence contracts"
```

Expected: generator self-check passes and the commit contains no generated `monthly-drafts/` file.

### Task 2: Research and Freeze the Independent July Top 5

**Files:**
- Modify: `data/github-project-digest/monthly-research/2026-07/top5-scorecard.md`
- Modify: `data/github-project-digest/monthly-research/2026-07/repository-verification.md`

- [ ] **Step 1: Select approximately 15 deep candidates without assigning final ranks**

Use only documented signals from the July candidate draft, daily reports and overlapping weekly reports. For each selected candidate, record which local files justified deeper research. Selection may use repeated sources, a meaningful July release, a verified first discovery or unusually strong engineering evidence; Stars alone are insufficient.

- [ ] **Step 2: Re-verify every deep candidate from primary sources**

For each candidate, inspect the official GitHub repository, LICENSE, releases, meaningful July commits, official documentation, installation path, security/contribution material and official adoption evidence. Save direct URLs and the date checked. Treat social posts, search snippets and repository self-promotion as supporting evidence rather than independent adoption proof.

- [ ] **Step 3: Perform safe runtime checks for leading candidates**

Use a fresh temporary directory for every repository experiment. Never provide repository code with credentials, the main repository path or broad filesystem access. Record the exact command and result. Stop and mark the blocker when a check requires paid credentials, a GPU, privileged containers or destructive host access.

Minimum acceptance: all deep candidates reach L0; every eventual Top 5 candidate has an explicit run status; at least the strongest practical candidates reach L2 when their official minimal example can run safely.

- [ ] **Step 4: Score every deep candidate with the same rubric**

For each candidate, calculate:

```text
total = monthly_significance + practical_value + engineering_quality + differentiation + maintenance + adoption
```

Validate the bounds `0–20`, `0–25`, `0–20`, `0–15`, `0–10`, `0–10`, and total `0–100`. Every non-zero score must cite at least one fact in the candidate record.

- [ ] **Step 5: Calibrate the weights once and freeze the ranking**

Check whether the first scoring result is dominated by Stars, company reputation or mature frameworks without meaningful July change. If a weight changes, apply the new rubric to every candidate and record the before/after rule. Do not adjust projects individually to create category diversity.

- [ ] **Step 6: Commit the Top 5 research**

Run:

```bash
git diff --check
git add data/github-project-digest/monthly-research/2026-07/top5-scorecard.md data/github-project-digest/monthly-research/2026-07/repository-verification.md
git commit -m "research: verify and rank July Top 5 candidates"
```

Expected: the scorecard contains the complete deep-candidate table, one calibration decision and a frozen 1–5 ranking with objections and sources.

### Task 3: Research Real Business Opportunities and Repository Combinations

**Files:**
- Create: `data/github-project-digest/monthly-research/2026-07/business-<slug>.md` for each investigated hypothesis
- Modify: `data/github-project-digest/monthly-research/2026-07/repository-verification.md`

- [ ] **Step 1: Produce 5–10 internal hypotheses from July evidence**

Each hypothesis must name the July repository signal, a specific target user, the current workflow and the proposed output. Reject any hypothesis whose only basis is shared technology, shared language, Stars or an Agent label.

- [ ] **Step 2: Shortlist at most three hypotheses for external research**

Prefer hypotheses where the target user and current cost can be investigated and where 2–5 repositories cover non-overlapping stages. Creating fewer than three research files is correct when evidence is weak.

- [ ] **Step 3: Investigate demand and alternatives for each shortlist item**

Every business research file must use these exact top-level sections:

```markdown
# 业务研究：明确名称

## 摘要
## 真实需求证据
## 商业产品
## 开源或自托管替代
## 当前人工或内部流程
## 未满足需求与差异化
## 产品定义
## 仓库组合
## 组合数据流
## 自行开发部分
## MVP 与停止条件
## 商业判断
## 证据边界
## 来源
```

Use direct official sources for product capabilities, pricing and customer claims. Mark unavailable price, revenue, customer count and market size as `未知`; do not estimate them.

- [ ] **Step 4: Verify the repository combination**

Every core repository must reach L0 and at least one core repository per publishable opportunity must reach L2. Record whether each repository is a July core or supporting component, its role, input, output and connection method. Competitors and functionally overlapping applications belong in alternatives, not in the combination.

- [ ] **Step 5: Attempt one safe L3 experiment**

Choose the shortest combination whose output can be passed to another repository through an official API, SDK, CLI, file or documented adapter. Run it in a temporary directory and record the exact data boundary. If blocked, preserve the failed command and classify the opportunity as documentation-level or partial rather than replacing the experiment with a claim.

- [ ] **Step 6: Apply the publication gate**

Publishable opportunities must have two independent demand evidence types, at least one commercial product, one open-source/self-hosted alternative, one real process, complete L0 checks, one L2 core repository, explicit inputs/outputs, custom-development gaps, an executable MVP, success metrics, stop conditions, sources and verification dates.

Use only these verdicts: `值得进入用户验证`, `值得做技术实验`, `继续观察`, `暂不建议`. Only the first two may enter the public July report.

- [ ] **Step 7: Commit the business research**

Run:

```bash
git diff --check
git add data/github-project-digest/monthly-research/2026-07
git commit -m "research: assess July business opportunities"
```

Expected: zero to three research files pass the gate; rejected research remains factual internal evidence and does not force a public section.

### Task 4: Freeze the Revised July Contract and Add Failing Parser Tests

**Files:**
- Modify: `data/github-project-digest/monthly/2026-07.md`
- Modify: `src/lib/monthly.test.ts`
- Modify: `src/lib/monthly.ts`

- [ ] **Step 1: Write the revised public report only from frozen research**

Use the exact candidate count/cutoff from Task 1, the frozen Top 5 and scores from Task 2, and only business opportunities that passed Task 3. Every fact must have a source; every repository must use its verified level. Do not preserve existing July wording unless the research independently supports it.

- [ ] **Step 2: Replace the test fixture builder**

Create test helpers with these signatures so five projects can be generated without duplicating the fixture body:

```ts
function topProject(position: number, repository: string): string;
function businessOpportunity(repository: string): string;
function monthlyDocument(opportunities: string[] = [businessOpportunity("Acme/Alpha")]): string;
```

`topProject` must emit all revised facts, six scores totaling 86, an L2 level, objection, judgment and two Markdown source links. `businessOpportunity` must emit all summary fields, one core repository, all fixed analysis subsections and sources. `monthlyDocument([])` must represent a valid month with zero opportunities and an explicit empty-state sentence.

- [ ] **Step 3: Add failing public-contract tests**

Add focused tests that assert:

```ts
expect(report.topProjects).toHaveLength(5);
expect(report.topProjects[0].scores.total).toBe(86);
expect(report.topProjects[0].verificationLevel).toBe("L2");
expect(report.opportunities[0].demandStatus).toBe("已确认需求");
expect(report.opportunities[0].repositories[0].repository).toBe("Acme/Alpha");
expect(parseMonthlyReport(monthlyDocument([]), "2026-07.md").opportunities).toEqual([]);
```

Also assert rejection for a sixth opportunity, score out of range, incorrect total, invalid verification level, missing source, missing fixed business subsection, duplicate repository within one combination and a supporting repository mislabeled as a July core.

- [ ] **Step 4: Run focused tests and confirm they fail for the old parser**

Run:

```bash
npm test -- src/lib/monthly.test.ts
```

Expected: FAIL because the old model still requires audiences, recommendations, signals and actions and has no score or opportunity fields.

- [ ] **Step 5: Define the revised types**

Replace the old audience/recommendation/signal/action contracts with:

```ts
export type VerificationLevel = "L0" | "L1" | "L2" | "L3" | "L4";
export type DemandStatus = "已确认需求" | "有需求信号";
export type OpportunityKind = "商业产品" | "企业内部工具" | "新开源项目";
export type CombinationVerdict = "已验证可行" | "文档层面可行" | "部分可行" | "暂不可行";
export type BusinessVerdict = "值得进入用户验证" | "值得做技术实验" | "继续观察" | "暂不建议";

export interface MonthlyScores {
  monthlySignificance: number;
  practicalValue: number;
  engineeringQuality: number;
  differentiation: number;
  maintenance: number;
  adoption: number;
  total: number;
}

export interface EvidenceLink { label: string; url: string }

export interface MonthlyProject {
  id: string;
  repository: string;
  url: string;
  monthlyChange: string;
  stars: number;
  forks: number;
  release: string;
  recentActivity: string;
  license: string;
  verifiedAt: string;
  verificationLevel: VerificationLevel;
  scores: MonthlyScores;
  capability: string;
  engineeringMaturity: string;
  limitation: string;
  objection: string;
  judgment: string;
  sources: EvidenceLink[];
}

export interface OpportunityRepository {
  repository: string;
  url: string;
  origin: "本月核心" | "补充组件";
  role: string;
  integration: string;
  verificationLevel: VerificationLevel;
}

export interface MonthlyOpportunity {
  id: string;
  title: string;
  kind: OpportunityKind;
  targetUser: string;
  demandStatus: DemandStatus;
  competitorCount: number;
  verificationLevel: VerificationLevel;
  combinationVerdict: CombinationVerdict;
  businessVerdict: BusinessVerdict;
  verifiedAt: string;
  repositories: OpportunityRepository[];
  bodyHtml: string;
  sources: EvidenceLink[];
}
```

- [ ] **Step 6: Inspect the red-state diff and continue immediately to Task 5**

Run:

```bash
git diff --check
git diff -- data/github-project-digest/monthly/2026-07.md src/lib/monthly.test.ts src/lib/monthly.ts
```

Expected: the diff contains the researched public contract, focused red tests and revised types. Do not commit an intentionally failing state; continue immediately to Task 5.

### Task 5: Implement the Revised Parser and Search Summary

**Files:**
- Modify: `src/lib/monthly.ts`
- Modify: `src/lib/monthly.test.ts`

- [ ] **Step 1: Add bounded enum and number parsers**

Implement small helpers with these contracts:

```ts
function requiredInteger(filename: string, subject: string, body: string, label: string, min: number, max: number): number;
function requiredEnum<T extends string>(filename: string, subject: string, value: string, label: string, allowed: readonly T[]): T;
function evidenceLinks(filename: string, subject: string, body: string): EvidenceLink[];
```

`requiredInteger` rejects non-integers and values outside the inclusive bounds. `evidenceLinks` accepts only Markdown links whose URL starts with `https://` and requires at least one link.

- [ ] **Step 2: Parse and validate Top 5 scores**

Map the six fields to bounds `20, 25, 20, 15, 10, 10`, sum them, and reject a declared total that differs from the sum. Reuse the existing canonical GitHub identity and collision-free ID functions.

- [ ] **Step 3: Parse business opportunities and fixed subsections**

Allow zero to three numbered `###` opportunity blocks. For each non-empty block, require all summary fields, at least one `本月核心` repository, no duplicate canonical repository, all fixed `####` analysis headings and at least one source. Render the fixed analysis body with `marked.parse` after validation.

- [ ] **Step 4: Remove old content requirements**

Delete the parser requirements and model fields for `三句话读懂这个月`, `分类推荐`, `本月观察信号`, `行动建议`, primary/secondary audiences and best-use-case. Preserve month metadata, candidate count, conclusion, methodology, discovery order and GitHub URL validation.

- [ ] **Step 5: Update monthly search summaries**

Keep one search item per Top 5 project. Build the subtitle from rank-independent capability and monthly change, not audience or business membership. Do not add internal research files or business-source URLs to the search index.

- [ ] **Step 6: Run focused and full tests**

Run:

```bash
npm test -- src/lib/monthly.test.ts src/lib/search.test.ts src/lib/periods.test.ts
npm test
```

Expected: all focused tests pass, then the complete Vitest suite passes with zero failures.

- [ ] **Step 7: Commit the parser**

```bash
git add data/github-project-digest/monthly/2026-07.md src/lib/monthly.ts src/lib/monthly.test.ts src/lib/search.test.ts
git commit -m "feat: parse evidence-backed monthly reports"
```

### Task 6: Rebuild the Monthly Report View Around Real Content

**Files:**
- Modify: `src/components/MonthlyReportView.astro`
- Modify: `src/styles/global.css`

- [ ] **Step 1: Render the revised hero and research ledger**

The hero must show the frozen cutoff, candidate count, five Top 5 projects, opportunity count and the methodology summary. Remove recommendation and signal counts.

- [ ] **Step 2: Render independent Top 5 entries**

For each project render repository link, monthly change, verified facts, verification level, six-score breakdown, capability, maturity, limitation, objection, judgment and source links. Use semantic `dl`, `meter` or labelled text; never encode score only by color.

- [ ] **Step 3: Render business opportunities or the explicit empty state**

When opportunities are empty, render exactly one explanatory paragraph and no placeholder cards. Otherwise render the summary fields, repository table, validated `bodyHtml` and source links. Label supporting components separately from July core repositories.

- [ ] **Step 4: Preserve navigation and remove obsolete sections**

Keep the monthly archive rail, mobile selector, no-JavaScript month links and adjacent-month navigation. Remove persona columns, fixed signal cards, audience action lists and the three-theses section.

- [ ] **Step 5: Add responsive styles using existing tokens**

Use existing paper, ink, moss, rule and mono tokens. At widths below 768px, stack score details and convert repository comparison rows to labelled blocks. Keep source links visible, focusable and wrapping. Do not add JavaScript beyond the existing month selector.

- [ ] **Step 6: Run Astro checks before content migration**

Run:

```bash
npm run check
npm run build
```

Expected: Astro reports zero errors and the build produces the monthly index and historical route using the test-compatible public fixture state.

- [ ] **Step 7: Commit the view**

```bash
git add src/components/MonthlyReportView.astro src/styles/global.css
git commit -m "feat: present monthly rankings and business research"
```

### Task 7: Document and Verify the Revised Publication Pipeline

**Files:**
- Modify: `README.md`
- Modify: `src/lib/monthly.test.ts`

- [ ] **Step 1: Add the real-content discovery regression**

Assert:

```ts
const july = loadMonthlyReports().find((report) => report.slug === "2026-07");
expect(july).toBeDefined();
expect(july?.topProjects).toHaveLength(5);
expect(july?.opportunities.length).toBeLessThanOrEqual(3);
expect(july?.topProjects.every((project) => project.sources.length > 0)).toBe(true);
```

- [ ] **Step 2: Document the publication pipeline**

README must state that candidate generation uses local ledgers/daily/weekly reports, external research happens before publication, internal evidence is stored under `monthly-research/`, and production builds consume only frozen `monthly/` files without network access.

- [ ] **Step 3: Verify internal research is not published**

Run:

```bash
npm run build
rg -n 'monthly-research|top5-scorecard|repository-verification' dist
```

Expected: build succeeds and `rg` returns no matches.

- [ ] **Step 4: Commit the publication documentation and regression**

```bash
git add README.md src/lib/monthly.test.ts
git commit -m "docs: document researched monthly publication"
```

### Task 8: Complete Verification, Visual Inspection and Code Review

**Files:**
- Modify if findings require it: files changed in Tasks 1–7
- Update: `openspec/changes/redesign-monthly-business-research/tasks.md`

- [ ] **Step 1: Run the complete fresh verification chain**

Run:

```bash
npm run check:monthly-generator
npm test
npm run check
npm run build
openspec validate redesign-monthly-business-research --strict --no-interactive
git diff --check
```

Expected: generator self-check passes, all Vitest tests pass, Astro reports zero diagnostics, the production build succeeds, OpenSpec is valid and no whitespace errors appear.

- [ ] **Step 2: Inspect the real page at desktop and mobile widths**

Start `npm run dev`, open `/monthly/2026-07/`, and inspect at 1440px and 360px. Verify Top 5 score labels, long source URLs, business tables, combination flow, explicit empty state when applicable, keyboard focus, month selection, month/week/day links and no horizontal scrolling.

- [ ] **Step 3: Inspect the no-JavaScript path**

Disable JavaScript and confirm the report, repository links, sources, month links, adjacent navigation and period links remain reachable. The mobile `<select>` may stop enhancing navigation, but ordinary month links must remain visible.

- [ ] **Step 4: Perform one consolidated review**

Review the complete diff against the redesign spec and OpenSpec. Treat factual overstatement, unsupported business claims, missing sources, unsafe repository execution, incorrect scoring, internal evidence leakage, route/search regression and inaccessible mobile content as blocking. Ignore optional abstractions and stylistic preferences that do not affect correctness.

- [ ] **Step 5: Fix blocking findings and rerun the full verification chain**

Apply the smallest corrections, add a regression test for every code defect, and repeat Step 1. Recheck modified factual claims against their source rather than editing prose from memory.

- [ ] **Step 6: Mark OpenSpec tasks and commit the verified result**

```bash
git add openspec/changes/redesign-monthly-business-research
git commit -m "docs: complete monthly research redesign change"
git status --short
```

Expected: every completed OpenSpec checkbox is checked and `git status --short` is empty.
