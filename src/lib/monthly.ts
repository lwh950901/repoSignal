import { marked } from "marked";
import type { SearchItem } from "./search";

export type MonthlyAudience = "独立开发者" | "技术负责人" | "AI 产品创业者";
export type EvidenceStrength = "高" | "中" | "观察";
export type MonthlySignalDirection = "快速上升" | "持续成熟" | "值得观望" | "编辑观察";

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
  direction: MonthlySignalDirection;
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
  methodology: string;
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

const audiences: readonly MonthlyAudience[] = ["独立开发者", "技术负责人", "AI 产品创业者"];
const strengths: readonly EvidenceStrength[] = ["高", "中", "观察"];
const signalDirections: readonly MonthlySignalDirection[] = ["快速上升", "持续成熟", "值得观望", "编辑观察"];

function cleanInline(value: string): string {
  return value
    .replace(/\[([^\]]+)\]\([^)]+\)/gu, "$1")
    .replace(/\*\*/gu, "")
    .replace(/`/gu, "")
    .trim();
}

function validation(filename: string, problem: string): never {
  throw new MonthlyValidationError(filename, problem);
}

function section(markdown: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  const match = markdown.match(new RegExp(`^##\\s+${escaped}\\s*$`, "mu"));
  if (!match || match.index === undefined) return "";
  const afterHeading = markdown.slice(match.index + match[0].length);
  const nextHeading = afterHeading.search(/\n##\s+/u);
  return (nextHeading === -1 ? afterHeading : afterHeading.slice(0, nextHeading)).trim();
}

function requiredSection(filename: string, markdown: string, heading: string): string {
  const value = section(markdown, heading);
  return value || validation(filename, `缺少章节 ## ${heading}`);
}

function field(body: string, label: string): string {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  return cleanInline(body.match(new RegExp(`^-\\s+${escaped}[：:]\\s*(.+)$`, "mu"))?.[1] ?? "");
}

function requiredField(filename: string, repository: string, body: string, label: string): string {
  const value = field(body, label);
  return value || validation(filename, `${repository || "Top 5 项目"} 缺少必填字段 ${label}`);
}

function isGitHubOwner(value: string): boolean {
  return /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$/u.test(value);
}

function isGitHubRepositoryName(value: string): boolean {
  return /^[A-Za-z0-9._-]{1,100}$/u.test(value);
}

function canonicalRepositoryIdentity(repository: string): string | undefined {
  const components = repository.normalize("NFKC").trim().split("/");
  if (
    components.length !== 2
    || !isGitHubOwner(components[0])
    || !isGitHubRepositoryName(components[1])
  ) return undefined;
  return components.map((component) => component.toLocaleLowerCase("en-US")).join("/");
}

function requireCanonicalRepository(
  filename: string,
  repository: string,
  subject: string,
  fieldName: string,
): string {
  const canonical = canonicalRepositoryIdentity(repository);
  if (!canonical) validation(filename, `${subject} 的${fieldName} ${repository} 必须是 owner/repo 格式`);
  return canonical;
}

function repositoryId(canonicalRepository: string): string {
  const hex = Array.from(canonicalRepository)
    .map((character) => character.charCodeAt(0).toString(16).padStart(2, "0"))
    .join("");
  return `monthly-project-${hex}`;
}

function isAudience(value: string): value is MonthlyAudience {
  return (audiences as readonly string[]).includes(value);
}

function isStrength(value: string): value is EvidenceStrength {
  return (strengths as readonly string[]).includes(value);
}

function parseAudience(filename: string, repository: string, value: string, label: string): MonthlyAudience {
  if (!isAudience(value)) validation(filename, `${repository} 的${label}必须是独立开发者、技术负责人或 AI 产品创业者`);
  return value;
}

function parseStrength(filename: string, subject: string, value: string): EvidenceStrength {
  if (!isStrength(value)) validation(filename, `${subject} 的证据强度必须是高、中或观察`);
  return value;
}

function parseRepository(
  filename: string,
  body: string,
  subject: string,
): { repository: string; url: string; canonical: string } {
  const raw = field(body, "仓库");
  if (!raw) validation(filename, `${subject} 缺少必填字段 仓库`);
  const markdownLink = body.match(/^-\s+仓库[：:]\s*\[([^\]]+)\]\(([^)]+)\)\s*$/mu);
  const repository = cleanInline(markdownLink?.[1] ?? raw);
  const url = markdownLink?.[2]?.trim() ?? "";
  const urlMatch = url.match(/^https:\/\/github\.com\/([^/?#]+)\/([^/?#]+)\/?$/u);
  const urlCanonical = urlMatch
    ? canonicalRepositoryIdentity(`${urlMatch[1]}/${urlMatch[2]}`)
    : undefined;
  if (!urlCanonical) {
    validation(filename, `${repository || subject} 的 GitHub URL 无效`);
  }
  const canonical = requireCanonicalRepository(filename, repository, repository || subject, "仓库");
  if (canonical !== urlCanonical) validation(filename, `${repository} 的 GitHub URL 与仓库名不匹配`);
  return { repository, url, canonical };
}

function parseSecondaryAudiences(filename: string, repository: string, body: string): MonthlyAudience[] {
  const value = field(body, "次要角色");
  if (!value) return [];
  return value.split(/[、,，]/u).map((item) => item.trim()).filter(Boolean).map((item) => (
    parseAudience(filename, repository, item, "次要角色")
 ));
}

function numberedBlocks(value: string, headingPattern: RegExp): { match: RegExpMatchArray; body: string }[] {
  const matches = [...value.matchAll(headingPattern)];
  return matches.map((match, index) => {
    const start = match.index ?? 0;
    const end = matches[index + 1]?.index ?? value.length;
    return { match, body: value.slice(start, end).trim() };
  });
}

function parseTopProjects(filename: string, markdown: string): MonthlyProject[] {
  const topSection = requiredSection(filename, markdown, "Top 5");
  const blocks = numberedBlocks(topSection, /^###\s+(\d+)\.\s+(.+?)\s*$/gmu);
  if (blocks.length !== 5) validation(filename, `Top 5 必须恰好包含 5 个项目，当前为 ${blocks.length}`);

  return blocks.map(({ match, body }, index) => {
    if (Number(match[1]) !== index + 1) validation(filename, "Top 5 项目必须按 1 到 5 编号");
    const { canonical, ...repo } = parseRepository(filename, body, cleanInline(match[2]));
    const primaryAudience = parseAudience(
      filename,
      repo.repository,
      requiredField(filename, repo.repository, body, "主要角色"),
      "主要角色",
    );
    const evidenceStrength = field(body, "证据强度");
    return {
      id: repositoryId(canonical),
      ...repo,
      primaryAudience,
      secondaryAudiences: parseSecondaryAudiences(filename, repo.repository, body),
      selectionReason: requiredField(filename, repo.repository, body, "入选依据"),
      bestUseCase: requiredField(filename, repo.repository, body, "最佳使用场景"),
      risk: requiredField(filename, repo.repository, body, "主要风险"),
      evidenceStrength: evidenceStrength
        ? parseStrength(filename, repo.repository, evidenceStrength)
        : "观察",
      markdown: body,
      html: marked.parse(body) as string,
    };
  });
}

function parseRecommendations(filename: string, markdown: string): MonthlyRecommendation[] {
  const recommendationSection = requiredSection(filename, markdown, "分类推荐");
  const audienceMatches = [...recommendationSection.matchAll(/^###\s+(.+?)\s*$/gmu)];
  if (audienceMatches.length === 0) validation(filename, "分类推荐必须包含至少一个角色");

  const groups = audienceMatches.map((match) => ({
    match,
    audience: parseAudience(filename, "分类推荐", cleanInline(match[1]), "角色"),
  }));
  validateAudienceGroups(filename, "分类推荐", groups.map((group) => group.audience));

  return groups.flatMap(({ match, audience }, index) => {
    const start = match.index ?? 0;
    const end = audienceMatches[index + 1]?.index ?? recommendationSection.length;
    const audienceSection = recommendationSection.slice(start, end);
    const projects = numberedBlocks(audienceSection, /^####\s+(.+?)\s*$/gmu);
    if (projects.length === 0) {
      const concise = [...audienceSection.matchAll(/^[*-]\s+`?([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)`?(?:[：:]\s*(.+))?$/gmu)];
      if (concise.length === 0) validation(filename, `${audience} 分类推荐缺少项目`);
      return concise.map((item) => {
        const repository = item[1];
        return {
          id: repositoryId(requireCanonicalRepository(filename, repository, repository, "仓库")),
          audience,
          repository,
          url: "",
          reason: cleanInline(item[2] ?? ""),
          risk: "",
        };
      });
    }
    return projects.map(({ match: projectMatch, body }) => {
      const repository = field(body, "仓库") || cleanInline(projectMatch[1]);
      const canonical = requireCanonicalRepository(filename, repository, repository || cleanInline(projectMatch[1]), "仓库");
      const url = body.match(/^-\s+仓库[：:]\s*\[[^\]]+\]\((https:\/\/github\.com\/[^)]+)\)\s*$/mu)?.[1] ?? "";
      return {
        id: repositoryId(canonical),
        audience,
        repository,
        url,
        reason: field(body, "推荐理由"),
        risk: field(body, "主要风险"),
      };
    });
  });
}

function parseSupportingRepositories(filename: string, title: string, value: string): string[] {
  const seen = new Set<string>();
  return value
    .split(/[、,，]/u)
    .map((item) => cleanInline(item))
    .filter(Boolean)
    .filter((repository) => {
      const canonical = requireCanonicalRepository(filename, repository, title, "支撑项目");
      if (seen.has(canonical)) return false;
      seen.add(canonical);
      return true;
    });
}

function validateAudienceGroups(
  filename: string,
  sectionName: "分类推荐" | "行动建议",
  groups: MonthlyAudience[],
): void {
  for (const audience of audiences) {
    const count = groups.filter((group) => group === audience).length;
    if (count !== 1) validation(filename, `${sectionName} 必须恰好包含一次 ${audience} 角色分组`);
  }
}

function parseSignals(filename: string, markdown: string): MonthlySignal[] {
  const signalSection = requiredSection(filename, markdown, "本月观察信号");
  const blocks = numberedBlocks(signalSection, /^###\s+([^：:]+)[：:]\s*(.+?)\s*$/gmu);
  if (blocks.length === 0) validation(filename, "本月观察信号缺少信号");

  return blocks.map(({ match, body }) => {
    const suppliedDirection = cleanInline(match[1]);
    if (!(signalDirections as readonly string[]).includes(suppliedDirection)) {
      validation(filename, `信号方向 ${suppliedDirection} 无效`);
    }
    const title = cleanInline(match[2]);
    if (!title) validation(filename, "信号缺少标题");
    const supportingRepositories = parseSupportingRepositories(
      filename,
      title,
      requiredField(filename, title, body, "支撑项目"),
    );
    const observation = requiredField(filename, title, body, "观察");
    const evidenceStrength = parseStrength(filename, title, requiredField(filename, title, body, "证据强度"));
    if (supportingRepositories.length < 3) {
      return { direction: "编辑观察", title, observation, supportingRepositories, evidenceStrength: "观察" };
    }
    return {
      direction: suppliedDirection as MonthlySignalDirection,
      title,
      observation,
      supportingRepositories,
      evidenceStrength,
    };
  });
}

function parseActions(filename: string, markdown: string): MonthlyActionGroup[] {
  const actionSection = requiredSection(filename, markdown, "行动建议");
  const audienceMatches = [...actionSection.matchAll(/^###\s+(.+?)\s*$/gmu)];
  if (audienceMatches.length === 0) validation(filename, "行动建议必须包含至少一个角色");
  const groups = audienceMatches.map((match) => ({
    match,
    audience: parseAudience(filename, "行动建议", cleanInline(match[1]), "角色"),
  }));
  validateAudienceGroups(filename, "行动建议", groups.map((group) => group.audience));
  return groups.map(({ match, audience }, index) => {
    const start = (match.index ?? 0) + match[0].length;
    const end = audienceMatches[index + 1]?.index ?? actionSection.length;
    const items = actionSection.slice(start, end)
      .match(/^[-*]\s+(.+)$/gmu)
      ?.map((item) => cleanInline(item.replace(/^[-*]\s+/u, "")))
      .filter(Boolean) ?? [];
    if (items.length === 0) validation(filename, `${audience} 行动建议缺少条目`);
    return { audience, items };
  });
}

function validateUniqueRepositories(
  filename: string,
  topProjects: MonthlyProject[],
  recommendations: MonthlyRecommendation[],
): void {
  const seen = new Set<string>();
  for (const item of [...topProjects, ...recommendations]) {
    const canonical = requireCanonicalRepository(filename, item.repository, item.repository, "仓库");
    if (seen.has(canonical)) validation(filename, `duplicate repository ${item.repository}`);
    seen.add(canonical);
  }
}

function isValidDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/u.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

function headerBlock(markdown: string): string {
  const firstSection = markdown.search(/^##\s+/mu);
  return firstSection === -1 ? markdown : markdown.slice(0, firstSection);
}

function singleHeaderField(filename: string, markdown: string, label: string): string {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  const pattern = new RegExp(`^>\\s*${escaped}[：:]\\s*(.*)$`, "gmu");
  const allMatches = [...markdown.matchAll(pattern)];
  const headerMatches = [...headerBlock(markdown).matchAll(pattern)];
  if (allMatches.length !== 1 || headerMatches.length !== 1) {
    validation(filename, `${label} 必须在 header 区块内恰好出现一次`);
  }
  const value = cleanInline(headerMatches[0][1]);
  return value || validation(filename, `header 区块中的${label}不能为空`);
}

function singleHeaderTitle(filename: string, markdown: string): string {
  const pattern = /^#(?:\s+(.*))?$/gmu;
  const allMatches = [...markdown.matchAll(pattern)];
  const headerMatches = [...headerBlock(markdown).matchAll(pattern)];
  if (allMatches.length !== 1 || headerMatches.length !== 1) {
    validation(filename, "标题必须在 header 区块内恰好出现一次");
  }
  return cleanInline(headerMatches[0][1] ?? "") || validation(filename, "header 区块中的标题不能为空");
}

export function parseMonthlyReport(markdown: string, filename: string): MonthlyReport {
  const filenameMatch = filename.match(/^(\d{4}-\d{2})\.md$/u);
  if (!filenameMatch || !/^\d{4}-(0[1-9]|1[0-2])$/u.test(filenameMatch[1])) {
    validation(filename, "文件名必须为 YYYY-MM.md");
  }
  const slug = filenameMatch[1];
  const title = singleHeaderTitle(filename, markdown);
  const theme = singleHeaderField(filename, markdown, "月度主题");
  const cutoffDate = singleHeaderField(filename, markdown, "数据截止");
  if (!isValidDate(cutoffDate)) validation(filename, `数据截止必须是有效 YYYY-MM-DD 日期，当前为 ${cutoffDate}`);
  const candidateText = singleHeaderField(filename, markdown, "候选数量");
  if (!/^\d+$/u.test(candidateText)) validation(filename, `候选数量必须是非负整数，当前为 ${candidateText}`);

  const conclusion = requiredSection(filename, markdown, "本月结论");
  const thesesSection = requiredSection(filename, markdown, "三句话读懂这个月");
  const theses = thesesSection.match(/^\d+[.)、]\s+(.+)$/gmu)
    ?.map((item) => cleanInline(item.replace(/^\d+[.)、]\s+/u, "")))
    .filter(Boolean) ?? [];
  if (theses.length !== 3) validation(filename, `三句话读懂这个月必须恰好包含 3 条，当前为 ${theses.length}`);

  const topProjects = parseTopProjects(filename, markdown);
  const recommendations = parseRecommendations(filename, markdown);
  validateUniqueRepositories(filename, topProjects, recommendations);

  return {
    type: "monthly",
    slug,
    title,
    theme,
    cutoffDate,
    candidateCount: Number(candidateText),
    conclusion,
    conclusionHtml: marked.parse(conclusion) as string,
    theses,
    topProjects,
    recommendations,
    signals: parseSignals(filename, markdown),
    actions: parseActions(filename, markdown),
    methodology: requiredSection(filename, markdown, "方法说明"),
    markdown,
  };
}

export function loadMonthlyReports(): MonthlyReport[] {
  return loadMonthlyReportsFromFiles(monthlyMarkdownFiles);
}

export function loadMonthlyReportsFromFiles(files: Record<string, string>): MonthlyReport[] {
  return sortMonthlyReports(
    Object.entries(files)
      .map(([path, markdown]) => parseMonthlyReport(markdown, path.split("/").at(-1) ?? path)),
  );
}

export function sortMonthlyReports(reports: MonthlyReport[]): MonthlyReport[] {
  return [...reports].sort((a, b) => b.slug.localeCompare(a.slug));
}

export function createMonthlySearchIndex(reports: MonthlyReport[]): MonthlySearchIndexItem[] {
  return reports.flatMap((report) => [
    ...report.topProjects.map((project) => ({
      id: `${report.type}-${report.slug}-${project.id}`,
      repository: project.repository,
      positioning: project.selectionReason,
      technologies: [],
      kind: "Top 5" as const,
      score: null,
      reportType: "monthly" as const,
      reportLabel: report.slug,
      href: `/monthly/${report.slug}/#${project.id}`,
    })),
    ...report.recommendations.map((recommendation) => ({
      id: `${report.type}-${report.slug}-${recommendation.id}`,
      repository: recommendation.repository,
      positioning: recommendation.reason,
      technologies: [],
      kind: "分类推荐" as const,
      score: null,
      reportType: "monthly" as const,
      reportLabel: report.slug,
      href: `/monthly/${report.slug}/#${recommendation.id}`,
    })),
  ]);
}
