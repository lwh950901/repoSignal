import { marked } from "marked";
import type { SearchItem } from "./search";

export type ProjectKind = "爆发型" | "实用型" | "潜力型" | "周精选" | "额外发现";

export interface ProjectRecord {
  id: string;
  kind: ProjectKind;
  repository: string;
  url: string;
  score: number | null;
  positioning: string;
  introduction: string;
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
  bonusProjects: ProjectRecord[];
  bonusHtml: string;
}

export type DigestIndexItem = SearchItem;

const dailyMarkdownFiles = import.meta.glob(
  "../../data/github-project-digest/daily/*.md",
  { eager: true, import: "default", query: "?raw" },
) as Record<string, string>;

const weeklyMarkdownFiles = import.meta.glob(
  "../../data/github-project-digest/weekly/*.md",
  { eager: true, import: "default", query: "?raw" },
) as Record<string, string>;

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

function stripField(body: string, label: string): string {
  return body
    .split("\n")
    .filter((line) => !new RegExp(`^-\\s+${label}：`).test(line))
    .join("\n")
    .trim();
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
    const introduction = getField(body, ["项目简介"]);
    const detailBody = introduction ? stripField(body, "项目简介") : body;
    const kind = type === "daily" ? (match[1] as ProjectKind) : "周精选";
    const score = type === "daily" && match[3] ? Number(match[3]) : null;

    return [{
      id: projectId(repo.repository),
      kind,
      repository: repo.repository,
      url: repo.url,
      score,
      positioning: getField(body, ["一句话定位", "入选理由"]),
      introduction,
      technologies: parseTechnologies(technologies),
      risk: getField(body, ["风险", "真实风险"]),
      recommendation: getField(body, ["推荐理由", "本周精选价值", "上手建议"]),
      markdown: body,
      html: marked.parse(detailBody) as string,
    }];
  });
}

function sectionText(markdown: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = markdown.match(new RegExp(`^##\\s+${escaped}\\s*$([\\s\\S]*?)(?=\\n##\\s+|$(?!\\n))`, "mu"));
  return match?.[1]?.trim() ?? "";
}

const bonusPattern = /^###\s+额外发现：(.+?)\s*[—\-]\s*(\d+)\/100\s*$/gmu;

function parseBonusProjects(markdown: string): { projects: ProjectRecord[]; html: string } {
  const section = sectionText(markdown, "额外发现");
  if (!section) return { projects: [], html: "" };

  const matches = [...section.matchAll(bonusPattern)];
  if (matches.length === 0) {
    return { projects: [], html: marked.parse(section) as string };
  }

  const projects: ProjectRecord[] = [];
  for (const match of matches) {
    const start = match.index ?? 0;
    const endIdx = matches.indexOf(match) + 1;
    const end = matches[endIdx]?.index ?? section.length;
    const body = section.slice(start, end).trim().replace(/^#{3}.+\n/u, "").trim();
    const repo = getRepository(body);
    if (!repo.repository || !repo.url) continue;

    const introduction = getField(body, ["项目简介"]);
    const detailBody = introduction ? stripField(body, "项目简介") : body;

    projects.push({
      id: projectId(repo.repository),
      kind: "额外发现",
      repository: repo.repository,
      url: repo.url,
      score: Number(match[2]),
      positioning: getField(body, ["一句话定位"]),
      introduction,
      technologies: parseTechnologies(getField(body, ["主要技术栈"])),
      risk: getField(body, ["风险"]),
      recommendation: getField(body, ["推荐理由"]),
      markdown: body,
      html: marked.parse(detailBody) as string,
    });
  }

  return { projects, html: "" };
}

export function parseDailyReport(markdown: string, filename: string): DigestReport {
  const slug = filename.replace(/\.md$/u, "");
  const title = cleanInline(markdown.match(/^#\s+(.+)$/mu)?.[1] ?? "GitHub 项目发现");
  const fullTheme = cleanInline(markdown.match(/^>\s*今日重点：(.+)$/mu)?.[1] ?? "");
  const theme = fullTheme.match(/^.+?[。！？]/u)?.[0] ?? fullTheme;
  const bonus = parseBonusProjects(markdown);
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
    bonusProjects: bonus.projects,
    bonusHtml: bonus.html,
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
    bonusProjects: [],
    bonusHtml: "",
  };
}

function loadReports(
  files: Record<string, string>,
  parser: (markdown: string, filename: string) => DigestReport,
): DigestReport[] {
  return Object.entries(files)
    .map(([path, markdown]) => parser(markdown, path.split("/").at(-1) ?? path))
    .sort((a, b) => b.slug.localeCompare(a.slug));
}

export function loadDailyReports(): DigestReport[] {
  return loadReports(dailyMarkdownFiles, parseDailyReport);
}

export function loadWeeklyReports(): DigestReport[] {
  return loadReports(weeklyMarkdownFiles, parseWeeklyReport);
}

export function selectDefaultReport(
  dailyReports: DigestReport[],
  weeklyReports: DigestReport[],
): DigestReport | undefined {
  return weeklyReports[0] ?? dailyReports[0];
}

export function createSearchIndex(reports: DigestReport[]): DigestIndexItem[] {
  return reports.flatMap((report) => {
    const allProjects = [...report.projects, ...(report.bonusProjects ?? [])];
    return allProjects.map((project) => ({
      id: `${report.type}-${report.slug}-${project.id}`,
      repository: project.repository,
      positioning: project.positioning,
      technologies: project.technologies,
      kind: project.kind,
      score: project.score,
      reportType: report.type,
      reportLabel: report.type === "daily" ? report.date : report.slug,
      href: `/${report.type}/${report.slug}/#${project.id}`,
    }));
  });
}
