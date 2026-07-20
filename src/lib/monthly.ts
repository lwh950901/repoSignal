import { marked } from "marked";
import type { SearchItem } from "./search";

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
  positioning: string;
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

export interface MonthlyReport {
  type: "monthly";
  slug: string;
  title: string;
  theme: string;
  cutoffDate: string;
  candidateCount: number;
  deepCandidateCount: number;
  verificationNote: string;
  conclusion: string;
  conclusionHtml: string;
  topProjects: MonthlyProject[];
  opportunities: MonthlyOpportunity[];
  methodology: string;
  methodologyHtml: string;
  markdown: string;
}

export type MonthlySearchIndexItem = SearchItem;

export class MonthlyValidationError extends Error {
  constructor(filename: string, problem: string) {
    super(`${filename}: ${problem}`);
    this.name = "MonthlyValidationError";
  }
}

const monthlyMarkdownFiles = import.meta.glob(
  "../../data/github-project-digest/monthly/*.md",
  { eager: true, import: "default", query: "?raw" },
) as Record<string, string>;

const verificationLevels = ["L0", "L1", "L2", "L3", "L4"] as const;
const demandStatuses = ["已确认需求", "有需求信号"] as const;
const opportunityKinds = ["商业产品", "企业内部工具", "新开源项目"] as const;
const combinationVerdicts = ["已验证可行", "文档层面可行", "部分可行", "暂不可行"] as const;
const businessVerdicts = ["值得进入用户验证", "值得做技术实验", "继续观察", "暂不建议"] as const;
const repositoryOrigins = ["本月核心", "补充组件"] as const;

function cleanInline(value: string): string {
  return value.replace(/\[([^\]]+)\]\([^)]+\)/gu, "$1").replace(/\*\*/gu, "").replace(/`/gu, "").trim();
}

function validation(filename: string, problem: string): never {
  throw new MonthlyValidationError(filename, problem);
}

function section(markdown: string, heading: string, level = 2): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  const marks = "#".repeat(level);
  const match = markdown.match(new RegExp(`^${marks}\\s+${escaped}\\s*$`, "mu"));
  if (!match || match.index === undefined) return "";
  const after = markdown.slice(match.index + match[0].length);
  const next = after.search(new RegExp(`\\n#{1,${level}}\\s+`, "u"));
  return (next === -1 ? after : after.slice(0, next)).trim();
}

function requiredSection(filename: string, markdown: string, heading: string, level = 2, subject = ""): string {
  const value = section(markdown, heading, level);
  return value || validation(filename, `${subject ? `${subject} ` : ""}缺少章节 ${"#".repeat(level)} ${heading}`);
}

function field(body: string, label: string): string {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  return cleanInline(body.match(new RegExp(`^-\\s+${escaped}[：:]\\s*(.+)$`, "mu"))?.[1] ?? "");
}

function requiredField(filename: string, subject: string, body: string, label: string): string {
  return field(body, label) || validation(filename, `${subject} 缺少必填字段 ${label}`);
}

function requiredInteger(
  filename: string,
  subject: string,
  body: string,
  label: string,
  min: number,
  max: number,
): number {
  const raw = requiredField(filename, subject, body, label);
  if (!/^\d+$/u.test(raw)) validation(filename, `${subject} 的${label}必须是 ${min}–${max} 的整数`);
  const value = Number(raw);
  if (value < min || value > max) validation(filename, `${subject} 的${label}必须在 ${min}–${max} 之间`);
  return value;
}

function requiredEnum<T extends string>(
  filename: string,
  subject: string,
  value: string,
  label: string,
  allowed: readonly T[],
): T {
  if (!(allowed as readonly string[]).includes(value)) {
    validation(filename, `${subject} 的${label}必须是 ${allowed.join("、")}`);
  }
  return value as T;
}

function evidenceLinks(filename: string, subject: string, body: string): EvidenceLink[] {
  const links = [...body.matchAll(/\[([^\]]+)\]\((https:\/\/[^\s)]+)\)/gu)]
    .map((match) => ({ label: cleanInline(match[1]), url: match[2] }));
  if (links.length === 0) validation(filename, `${subject} 缺少有效 HTTPS 来源`);
  return links;
}

function isGitHubOwner(value: string): boolean {
  return /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$/u.test(value);
}

function isGitHubRepositoryName(value: string): boolean {
  return /^[A-Za-z0-9._-]{1,100}$/u.test(value);
}

function canonicalRepositoryIdentity(repository: string): string | undefined {
  const parts = repository.normalize("NFKC").trim().split("/");
  if (parts.length !== 2 || !isGitHubOwner(parts[0]) || !isGitHubRepositoryName(parts[1])) return undefined;
  return parts.map((part) => part.toLocaleLowerCase("en-US")).join("/");
}

function parseRepository(filename: string, body: string, subject: string): { repository: string; url: string; canonical: string } {
  const match = body.match(/^-\s+仓库[：:]\s*\[([^\]]+)\]\(([^)]+)\)\s*$/mu);
  if (!match) validation(filename, `${subject} 缺少必填字段 仓库`);
  const repository = cleanInline(match[1]);
  const canonical = canonicalRepositoryIdentity(repository);
  const urlMatch = match[2].match(/^https:\/\/github\.com\/([^/?#]+)\/([^/?#]+)\/?$/u);
  const urlCanonical = urlMatch ? canonicalRepositoryIdentity(`${urlMatch[1]}/${urlMatch[2]}`) : undefined;
  if (!canonical) validation(filename, `${subject} 的仓库 ${repository} 必须是 owner/repo 格式`);
  if (!urlCanonical) validation(filename, `${repository || subject} 的 GitHub URL 无效`);
  if (canonical !== urlCanonical) validation(filename, `${repository} 的 GitHub URL 与仓库名不匹配`);
  return { repository, url: match[2], canonical };
}

function encodedId(prefix: string, value: string): string {
  const hex = Array.from(value).map((character) => character.charCodeAt(0).toString(16).padStart(2, "0")).join("");
  return `${prefix}-${hex}`;
}

function numberedBlocks(value: string, pattern: RegExp): { match: RegExpMatchArray; body: string }[] {
  const matches = [...value.matchAll(pattern)];
  return matches.map((match, index) => ({
    match,
    body: value.slice(match.index ?? 0, matches[index + 1]?.index ?? value.length).trim(),
  }));
}

function isValidDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/u.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

function parseDate(filename: string, subject: string, value: string, label: string): string {
  if (!isValidDate(value)) validation(filename, `${subject} 的${label}必须是有效 YYYY-MM-DD 日期，当前为 ${value}`);
  return value;
}

function headerBlock(markdown: string): string {
  const firstSection = markdown.search(/^##\s+/mu);
  return firstSection === -1 ? markdown : markdown.slice(0, firstSection);
}

function singleHeaderField(filename: string, markdown: string, label: string): string {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  const pattern = new RegExp(`^>\\s*${escaped}[：:]\\s*(.*)$`, "gmu");
  const all = [...markdown.matchAll(pattern)];
  const header = [...headerBlock(markdown).matchAll(pattern)];
  if (all.length !== 1 || header.length !== 1) validation(filename, `${label} 必须在 header 区块内恰好出现一次`);
  return cleanInline(header[0][1]) || validation(filename, `header 区块中的${label}不能为空`);
}

function singleHeaderTitle(filename: string, markdown: string): string {
  const all = [...markdown.matchAll(/^#(?:\s+(.*))?$/gmu)];
  const header = [...headerBlock(markdown).matchAll(/^#(?:\s+(.*))?$/gmu)];
  if (all.length !== 1 || header.length !== 1) validation(filename, "标题必须在 header 区块内恰好出现一次");
  return cleanInline(header[0][1] ?? "") || validation(filename, "header 区块中的标题不能为空");
}

function sourceLine(filename: string, subject: string, body: string): EvidenceLink[] {
  const raw = body.match(/^-\s+来源[：:]\s*(.+)$/mu)?.[1] ?? "";
  return evidenceLinks(filename, subject, raw);
}

function parseTopProjects(filename: string, markdown: string): MonthlyProject[] {
  const top = requiredSection(filename, markdown, "Top 5 仓库");
  const blocks = numberedBlocks(top, /^###\s+(\d+)\.\s+(.+?)\s*$/gmu);
  if (blocks.length !== 5) validation(filename, `Top 5 必须恰好包含 5 个项目，当前为 ${blocks.length}`);
  const seen = new Set<string>();

  return blocks.map(({ match, body }, index) => {
    if (Number(match[1]) !== index + 1) validation(filename, "Top 5 项目必须按 1 到 5 编号");
    const { canonical, ...repository } = parseRepository(filename, body, cleanInline(match[2]));
    if (seen.has(canonical)) validation(filename, `duplicate repository ${repository.repository}`);
    seen.add(canonical);
    const scores: MonthlyScores = {
      monthlySignificance: requiredInteger(filename, repository.repository, body, "本月重要性", 0, 20),
      practicalValue: requiredInteger(filename, repository.repository, body, "实际价值", 0, 25),
      engineeringQuality: requiredInteger(filename, repository.repository, body, "工程质量", 0, 20),
      differentiation: requiredInteger(filename, repository.repository, body, "差异化", 0, 15),
      maintenance: requiredInteger(filename, repository.repository, body, "维护可持续性", 0, 10),
      adoption: requiredInteger(filename, repository.repository, body, "采用证据", 0, 10),
      total: requiredInteger(filename, repository.repository, body, "总分", 0, 100),
    };
    const calculated = scores.monthlySignificance + scores.practicalValue + scores.engineeringQuality
      + scores.differentiation + scores.maintenance + scores.adoption;
    if (scores.total !== calculated) validation(filename, `${repository.repository} 的总分必须等于六项评分之和 ${calculated}`);
    return {
      id: encodedId("monthly-project", canonical),
      ...repository,
      positioning: requiredField(filename, repository.repository, body, "定位"),
      monthlyChange: requiredField(filename, repository.repository, body, "本月变化"),
      stars: requiredInteger(filename, repository.repository, body, "Stars", 0, Number.MAX_SAFE_INTEGER),
      forks: requiredInteger(filename, repository.repository, body, "Forks", 0, Number.MAX_SAFE_INTEGER),
      release: requiredField(filename, repository.repository, body, "Release"),
      recentActivity: requiredField(filename, repository.repository, body, "最近有效活动"),
      license: requiredField(filename, repository.repository, body, "许可证"),
      verifiedAt: parseDate(filename, repository.repository, requiredField(filename, repository.repository, body, "核实日期"), "核实日期"),
      verificationLevel: requiredEnum(filename, repository.repository, requiredField(filename, repository.repository, body, "验证等级"), "验证等级", verificationLevels),
      scores,
      capability: requiredField(filename, repository.repository, body, "核心能力"),
      engineeringMaturity: requiredField(filename, repository.repository, body, "工程成熟度"),
      limitation: requiredField(filename, repository.repository, body, "明确限制"),
      objection: requiredField(filename, repository.repository, body, "反对理由"),
      judgment: requiredField(filename, repository.repository, body, "最终判断"),
      sources: sourceLine(filename, repository.repository, body),
    };
  });
}

const opportunitySections = [
  "真实问题",
  "市场与现有方案",
  "产品定义",
  "仓库组合",
  "组合链路",
  "自行开发部分",
  "MVP 验证",
  "业务判断",
  "证据边界",
  "来源",
] as const;

function parseOpportunityRepositories(filename: string, title: string, body: string): OpportunityRepository[] {
  const combination = requiredSection(filename, body, "仓库组合", 4, title);
  const blocks = numberedBlocks(combination, /^#####\s+(\d+)\.\s+(.+?)\s*$/gmu);
  if (blocks.length < 2 || blocks.length > 5) validation(filename, `${title} 的组合仓库必须包含 2–5 个仓库`);
  const seen = new Set<string>();
  const repositories = blocks.map(({ match, body: repositoryBody }, index) => {
    if (Number(match[1]) !== index + 1) validation(filename, `${title} 的组合仓库必须连续编号`);
    const { canonical, ...repository } = parseRepository(filename, repositoryBody, `${title}/${cleanInline(match[2])}`);
    if (seen.has(canonical)) validation(filename, `${title} duplicate repository ${repository.repository}`);
    seen.add(canonical);
    return {
      ...repository,
      origin: requiredEnum(filename, title, requiredField(filename, title, repositoryBody, "来源身份"), "来源身份", repositoryOrigins),
      role: requiredField(filename, title, repositoryBody, "职责"),
      integration: requiredField(filename, title, repositoryBody, "接入方式"),
      verificationLevel: requiredEnum(filename, title, requiredField(filename, title, repositoryBody, "验证等级"), "验证等级", verificationLevels),
    };
  });
  if (!repositories.some((repository) => repository.origin === "本月核心")) validation(filename, `${title} 必须包含至少一个本月核心仓库`);
  if (!repositories.some((repository) => Number(repository.verificationLevel.slice(1)) >= 2)) validation(filename, `${title} 必须包含至少一个达到 L2 的仓库`);
  return repositories;
}

function parseOpportunities(filename: string, markdown: string): MonthlyOpportunity[] {
  const content = requiredSection(filename, markdown, "真实业务与项目机会");
  const blocks = numberedBlocks(content, /^###\s+(\d+)\.\s+(.+?)\s*$/gmu);
  if (blocks.length === 0) {
    if (content !== "本月未发现通过完整验证的新机会。") {
      validation(filename, "真实业务与项目机会必须包含 0–3 个方案或明确空状态");
    }
    return [];
  }
  if (blocks.length > 3) validation(filename, `业务机会必须包含 0–3 个方案，当前为 ${blocks.length}`);
  return blocks.map(({ match, body }, index) => {
    if (Number(match[1]) !== index + 1) validation(filename, "业务机会必须从 1 连续编号");
    const title = cleanInline(match[2]);
    for (const heading of opportunitySections) requiredSection(filename, body, heading, 4, title);
    const headingPositions = opportunitySections.map((heading) => body.indexOf(`#### ${heading}`));
    if (headingPositions.some((position, headingIndex) => headingIndex > 0 && position < headingPositions[headingIndex - 1])) {
      validation(filename, `${title} 的固定章节顺序无效`);
    }
    const repositories = parseOpportunityRepositories(filename, title, body);
    const declaredRepositoryCount = requiredInteger(filename, title, body, "组合仓库数量", 2, 5);
    if (declaredRepositoryCount !== repositories.length) validation(filename, `${title} 的组合仓库数量与实际条目不一致`);
    const sourcesBody = requiredSection(filename, body, "来源", 4, title);
    const analysisMarkdown = body.slice(body.indexOf("#### 真实问题"), body.indexOf("#### 仓库组合"))
      + body.slice(body.indexOf("#### 组合链路"), body.indexOf("#### 来源"));
    const verificationLevel = requiredEnum(filename, title, requiredField(filename, title, body, "最高验证等级"), "最高验证等级", verificationLevels);
    const repositoryLevel = Math.max(...repositories.map((repository) => Number(repository.verificationLevel.slice(1))));
    if (Number(verificationLevel.slice(1)) !== repositoryLevel) {
      validation(filename, `${title} 的最高验证等级必须与仓库验证等级一致`);
    }
    const combinationVerdict = requiredEnum(filename, title, requiredField(filename, title, body, "组合结论"), "组合结论", combinationVerdicts);
    if (combinationVerdict === "已验证可行" && repositoryLevel < 3) {
      validation(filename, `${title} 标记已验证可行时必须达到 L3`);
    }
    const businessVerdict = requiredEnum(filename, title, requiredField(filename, title, body, "商业判断"), "商业判断", businessVerdicts);
    if (businessVerdict !== "值得进入用户验证" && businessVerdict !== "值得做技术实验") {
      validation(filename, `${title} 的${businessVerdict}不得进入公开月报`);
    }
    return {
      id: encodedId("monthly-opportunity", title),
      title,
      kind: requiredEnum(filename, title, requiredField(filename, title, body, "形态"), "形态", opportunityKinds),
      targetUser: requiredField(filename, title, body, "目标用户"),
      demandStatus: requiredEnum(filename, title, requiredField(filename, title, body, "需求状态"), "需求状态", demandStatuses),
      competitorCount: requiredInteger(filename, title, body, "竞品数量", 3, Number.MAX_SAFE_INTEGER),
      verificationLevel,
      combinationVerdict,
      businessVerdict,
      verifiedAt: parseDate(filename, title, requiredField(filename, title, body, "核实日期"), "核实日期"),
      repositories,
      bodyHtml: marked.parse(analysisMarkdown) as string,
      sources: evidenceLinks(filename, title, sourcesBody),
    };
  });
}

export function parseMonthlyReport(markdown: string, filename: string): MonthlyReport {
  const filenameMatch = filename.match(/^(\d{4}-\d{2})\.md$/u);
  if (!filenameMatch || !/^\d{4}-(0[1-9]|1[0-2])$/u.test(filenameMatch[1])) validation(filename, "文件名必须为 YYYY-MM.md");
  const slug = filenameMatch[1];
  const cutoffDate = singleHeaderField(filename, markdown, "数据截止");
  const candidateBody = `- 候选数量：${singleHeaderField(filename, markdown, "候选数量")}\n- 深度候选：${singleHeaderField(filename, markdown, "深度候选")}`;
  const conclusion = requiredSection(filename, markdown, "本月结论");
  const methodology = requiredSection(filename, markdown, "研究说明");
  return {
    type: "monthly",
    slug,
    title: singleHeaderTitle(filename, markdown),
    theme: singleHeaderField(filename, markdown, "月度主题"),
    cutoffDate: parseDate(filename, "月报", cutoffDate, "数据截止"),
    candidateCount: requiredInteger(filename, "月报", candidateBody, "候选数量", 0, Number.MAX_SAFE_INTEGER),
    deepCandidateCount: requiredInteger(filename, "月报", candidateBody, "深度候选", 1, Number.MAX_SAFE_INTEGER),
    verificationNote: singleHeaderField(filename, markdown, "验证说明"),
    conclusion,
    conclusionHtml: marked.parse(conclusion) as string,
    topProjects: parseTopProjects(filename, markdown),
    opportunities: parseOpportunities(filename, markdown),
    methodology,
    methodologyHtml: marked.parse(methodology) as string,
    markdown,
  };
}

export function loadMonthlyReports(): MonthlyReport[] {
  return loadMonthlyReportsFromFiles(monthlyMarkdownFiles);
}

export function loadMonthlyReportsFromFiles(files: Record<string, string>): MonthlyReport[] {
  return sortMonthlyReports(Object.entries(files).map(([path, markdown]) => (
    parseMonthlyReport(markdown, path.split("/").at(-1) ?? path)
  )));
}

export function sortMonthlyReports(reports: MonthlyReport[]): MonthlyReport[] {
  return [...reports].sort((a, b) => b.slug.localeCompare(a.slug));
}

export function createMonthlySearchIndex(reports: MonthlyReport[]): MonthlySearchIndexItem[] {
  return reports.flatMap((report) => report.topProjects.map((project) => ({
    id: `${report.type}-${report.slug}-${project.id}`,
    repository: project.repository,
    positioning: `${project.capability} ${project.monthlyChange}`,
    technologies: [],
    kind: "Top 5" as const,
    score: project.scores.total,
    reportType: "monthly" as const,
    reportLabel: report.slug,
    href: `/monthly/${report.slug}/#${project.id}`,
  })));
}
