import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { marked } from "marked";

export type ProjectKind = "爆发型" | "实用型" | "潜力型" | "周精选";

export interface ProjectRecord {
  id: string;
  kind: ProjectKind;
  repository: string;
  url: string;
  score: number | null;
  positioning: string;
  technologies: string[];
  risk: string;
  recommendation: string;
  markdown: string;
  html: string;
}

export interface DigestReport {
  type: "daily" | "weekly";
  slug: string;
  date: string;
  title: string;
  theme: string;
  introduction: string;
  markdown: string;
  html: string;
  projects: ProjectRecord[];
}

export interface DigestIndexItem {
  id: string;
  repository: string;
  positioning: string;
  technologies: string[];
  kind: ProjectKind;
  score: number | null;
  reportLabel: string;
  href: string;
}

const DATA_ROOT = resolve(process.cwd(), "data/github-project-digest");

function cleanInline(value = ""): string {
  return value
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .trim();
}

function getField(body: string, labels: string[]): string {
  for (const label of labels) {
    const match = body.match(new RegExp(`^-\\s+${label}：(.+)$`, "mu"));
    if (match) return cleanInline(match[1]);
  }
  return "";
}

function getRepository(body: string): { repository: string; url: string } {
  const match = body.match(
    /^-\s+仓库：\[([^\]]+)\]\((https:\/\/github\.com\/[^)]+)\)/mu,
  );
  return {
    repository: match?.[1]?.trim() ?? "",
    url: match?.[2]?.trim() ?? "",
  };
}

function projectId(repository: string): string {
  return `project-${repository.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
}

function parseTechnologies(value: string): string[] {
  return value
    .replace(/[。.]$/, "")
    .split(/[、,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseProjects(markdown: string, type: DigestReport["type"]): ProjectRecord[] {
  const headingPattern = type === "daily"
    ? /^###\s+\d+\.\s+(爆发型|实用型|潜力型)：(.+?)(?:\s+[—-]\s+(\d+)\/100)?\s*$/gmu
    : /^##\s+\d+\.\s+(.+?)\s*$/gmu;
  const matches = [...markdown.matchAll(headingPattern)];

  return matches.flatMap((match, index) => {
    const start = match.index ?? 0;
    const end = matches[index + 1]?.index ?? markdown.length;
    const section = markdown.slice(start, end).trim();
    const body = section.replace(/^#{2,3}.+\n/u, "").trim();
    const repo = getRepository(body);
    if (!repo.repository || !repo.url) return [];

    const technologies = getField(body, ["主要技术栈"]);
    const kind = type === "daily" ? (match[1] as ProjectKind) : "周精选";
    const score = type === "daily" && match[3] ? Number(match[3]) : null;

    return [{
      id: projectId(repo.repository),
      kind,
      repository: repo.repository,
      url: repo.url,
      score,
      positioning: getField(body, ["一句话定位", "入选理由"]),
      technologies: parseTechnologies(technologies),
      risk: getField(body, ["风险", "真实风险"]),
      recommendation: getField(body, ["推荐理由", "本周精选价值", "上手建议"]),
      markdown: body,
      html: marked.parse(body) as string,
    }];
  });
}

function sectionText(markdown: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = markdown.match(new RegExp(`^##\\s+${escaped}\\s*$([\\s\\S]*?)(?=^##\\s+|$)`, "mu"));
  return match?.[1]?.trim() ?? "";
}

export function parseDailyReport(markdown: string, filename: string): DigestReport {
  const slug = filename.replace(/\.md$/u, "");
  const title = cleanInline(markdown.match(/^#\s+(.+)$/mu)?.[1] ?? "GitHub 项目发现");
  const fullTheme = cleanInline(markdown.match(/^>\s*今日重点：(.+)$/mu)?.[1] ?? "");
  const theme = fullTheme.match(/^.+?[。！？]/u)?.[0] ?? fullTheme;
  return {
    type: "daily",
    slug,
    date: slug,
    title,
    theme,
    introduction: sectionText(markdown, "今日结论"),
    markdown,
    html: marked.parse(markdown) as string,
    projects: parseProjects(markdown, "daily"),
  };
}

export function parseWeeklyReport(markdown: string, filename: string): DigestReport {
  const slug = filename.replace(/\.md$/u, "");
  const title = cleanInline(markdown.match(/^#\s+(.+)$/mu)?.[1] ?? "GitHub 每周精选");
  const firstParagraph = markdown
    .replace(/^#.+$/mu, "")
    .split(/^##\s+/mu)[0]
    .trim();
  return {
    type: "weekly",
    slug,
    date: slug,
    title,
    theme: "本周深度精选",
    introduction: firstParagraph,
    markdown,
    html: marked.parse(markdown) as string,
    projects: parseProjects(markdown, "weekly"),
  };
}

function loadReports(
  directory: "daily" | "weekly",
  parser: (markdown: string, filename: string) => DigestReport,
): DigestReport[] {
  const path = join(DATA_ROOT, directory);
  if (!existsSync(path)) return [];

  return readdirSync(path)
    .filter((filename) => filename.endsWith(".md"))
    .sort()
    .reverse()
    .map((filename) => parser(readFileSync(join(path, filename), "utf8"), filename));
}

export function loadDailyReports(): DigestReport[] {
  return loadReports("daily", parseDailyReport);
}

export function loadWeeklyReports(): DigestReport[] {
  return loadReports("weekly", parseWeeklyReport);
}

export function selectDefaultReport(
  dailyReports: DigestReport[],
  weeklyReports: DigestReport[],
): DigestReport | undefined {
  return weeklyReports[0] ?? dailyReports[0];
}

export function createSearchIndex(reports: DigestReport[]): DigestIndexItem[] {
  return reports.flatMap((report) =>
    report.projects.map((project) => ({
      id: `${report.type}-${report.slug}-${project.id}`,
      repository: project.repository,
      positioning: project.positioning,
      technologies: project.technologies,
      kind: project.kind,
      score: project.score,
      reportLabel: report.type === "daily" ? report.date : report.slug,
      href: `/${report.type}/${report.slug}/#${project.id}`,
    })),
  );
}
