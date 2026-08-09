import { marked } from "marked";

export interface RadarReport {
  slug: string;
  date: string;
  title: string;
  description: string;
  cover: string;
  coverAlt: string;
  markdown: string;
  html: string;
}

const radarMarkdownFiles = import.meta.glob(
  "../../data/github-project-digest/radar/*.md",
  { eager: true, import: "default", query: "?raw" },
) as Record<string, string>;

function invalid(filename: string, reason: string): never {
  throw new Error(`${filename}: ${reason}`);
}

function cleanInline(value: string): string {
  return value.replace(/\*\*/gu, "").replace(/`/gu, "").trim();
}

function firstParagraph(markdown: string): string {
  return markdown
    .split(/\n\s*\n/gu)
    .map((block) => block.trim())
    .find((block) => Boolean(block) && !/^(?:#{1,6}\s|[-*+]\s|>|```)/u.test(block))
    ?.replace(/\s*\n\s*/gu, " ") ?? "";
}

function validateProjectNoteOrder(markdown: string, filename: string, slug: string): void {
  const projectSections = markdown.split(/^###\s+\d+\..*$/gmu).slice(1);
  for (const section of projectSections) {
    if (slug >= "2026-W32") {
      const hasFourLabeledBlocks = /^\*\*介绍：\*\*[^\n]*\n(?:[ \t]*\n)*\*\*推荐依据：\*\*[^\n]*\n(?:[ \t]*\n)*\*\*适合：\*\*[^\n]*\n(?:[ \t]*\n)*\*\*注意：\*\*[^\n]*/mu.test(section);
      if (!hasFourLabeledBlocks) {
        invalid(filename, "每个项目必须依次使用“介绍、推荐依据、适合、注意”四个标签");
      }
      continue;
    }
    const hasAudience = /^\*\*适合：\*\*/mu.test(section);
    const hasRisk = /^\*\*注意：\*\*/mu.test(section);
    if (
      (hasAudience || hasRisk) &&
      !/^\*\*适合：\*\*[^\n]*\n(?:[ \t]*\n)*\*\*注意：\*\*/mu.test(section)
    ) {
      invalid(filename, "每个项目的“适合”后必须直接接“注意”");
    }
  }
}

export function parseRadarReport(markdown: string, filename: string): RadarReport {
  const basename = filename.split("/").at(-1) ?? filename;
  const slug = basename.replace(/\.md$/u, "");
  if (!/^\d{4}-W\d{2}$/u.test(slug)) invalid(basename, "文件名必须使用 ISO 周格式 YYYY-Www.md");
  if (markdown.includes("SITE_BASE_URL")) invalid(basename, "公开内容不能包含 SITE_BASE_URL");
  if (/utm_/iu.test(markdown)) invalid(basename, "公开内容不能包含 utm_ 参数");

  const titleMatch = markdown.match(/^#\s+(.+)$/mu);
  if (!titleMatch) invalid(basename, "缺少一级标题");
  const coverMatch = markdown.match(/^!\[([^\]]*)\]\(([^)]+)\)\s*$/mu);
  if (!coverMatch) invalid(basename, "缺少封面图片");
  validateProjectNoteOrder(markdown, basename, slug);

  const body = markdown
    .replace(titleMatch[0], "")
    .replace(coverMatch[0], "")
    .replace(/^\s+/u, "")
    .trim();

  return {
    slug,
    date: slug,
    title: cleanInline(titleMatch[1]),
    description: cleanInline(firstParagraph(body)),
    cover: coverMatch[2].trim(),
    coverAlt: cleanInline(coverMatch[1]),
    markdown: body,
    html: marked.parse(body) as string,
  };
}

export function loadRadarReports(): RadarReport[] {
  return Object.entries(radarMarkdownFiles)
    .map(([path, markdown]) => parseRadarReport(markdown, path))
    .sort((a, b) => b.slug.localeCompare(a.slug));
}
