import { marked } from "marked";

export interface FeasibilityPlan {
  id: string;
  title: string;
  positioning: string;
  audience: string;
  marketOpportunity: string;
  markdown: string;
  bodyHtml: string;
}

export interface FeasibilityReport {
  slug: string;
  date: string;
  title: string;
  noticeHtml: string;
  markdown: string;
  html: string;
  plans: FeasibilityPlan[];
  opportunitiesHtml: string;
  actionsHtml: string;
}

type MarkdownFiles = Record<string, string>;

const feasibilityMarkdownFiles = import.meta.glob(
  "../../data/github-project-digest/feasibility/20??-??-??.md",
  { eager: true, import: "default", query: "?raw" },
) as MarkdownFiles;

const datedFilename = /^\d{4}-\d{2}-\d{2}\.md$/u;

function cleanInline(value = ""): string {
  return value.replace(/\*\*/gu, "").replace(/`/gu, "").trim();
}

function sectionText(markdown: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = markdown.match(new RegExp(`^##\\s+${escaped}\\s*$([\\s\\S]*?)(?=\\n##\\s+|$(?!\\n))`, "mu"));
  return match?.[1]?.trim() ?? "";
}

function getSummaryField(markdown: string, label: string): string {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = markdown.match(new RegExp(`^\\*\\*${escaped}\\*\\*：(.+)$`, "mu"));
  return cleanInline(match?.[1]);
}

function removeSummaryFields(markdown: string): string {
  const labels = ["业务定位", "目标客户", "市场机会"];
  return markdown
    .split("\n")
    .filter((line) => !labels.some((label) => line.startsWith(`**${label}**：`)))
    .join("\n")
    .replace(/\n{3,}/gu, "\n\n")
    .trim();
}

function parsePlans(markdown: string): FeasibilityPlan[] {
  const section = sectionText(markdown, "可行性方案");
  const headings = [...section.matchAll(/^###\s+(\d+)\.\s+(.+)$/gmu)];

  return headings.map((heading, index) => {
    const start = (heading.index ?? 0) + heading[0].length;
    const end = headings[index + 1]?.index ?? section.length;
    const body = section.slice(start, end).trim();
    const bodyMarkdown = removeSummaryFields(body);

    return {
      id: `plan-${heading[1]}`,
      title: cleanInline(heading[2]),
      positioning: getSummaryField(body, "业务定位"),
      audience: getSummaryField(body, "目标客户"),
      marketOpportunity: getSummaryField(body, "市场机会"),
      markdown: body,
      bodyHtml: marked.parse(bodyMarkdown) as string,
    };
  });
}

export function parseFeasibilityReport(markdown: string, filename: string): FeasibilityReport {
  const slug = filename.replace(/\.md$/u, "");
  const title = cleanInline(markdown.match(/^#\s+(.+)$/mu)?.[1] ?? "每日可行性方案");
  const firstSectionIndex = markdown.search(/^##\s+/mu);
  const preamble = markdown
    .slice(markdown.indexOf("\n") + 1, firstSectionIndex >= 0 ? firstSectionIndex : markdown.length)
    .trim();
  const opportunities = sectionText(markdown, "单点项目机会（供参考）");
  const actions = sectionText(markdown, "行动建议");

  return {
    slug,
    date: slug,
    title,
    noticeHtml: preamble ? marked.parse(preamble) as string : "",
    markdown,
    html: marked.parse(markdown) as string,
    plans: parsePlans(markdown),
    opportunitiesHtml: opportunities ? marked.parse(opportunities) as string : "",
    actionsHtml: actions ? marked.parse(actions) as string : "",
  };
}

export function loadFeasibilityReports(files: MarkdownFiles = feasibilityMarkdownFiles): FeasibilityReport[] {
  return Object.entries(files)
    .flatMap(([path, markdown]) => {
      const filename = path.split("/").at(-1) ?? path;
      return datedFilename.test(filename) ? [parseFeasibilityReport(markdown, filename)] : [];
    })
    .sort((a, b) => b.slug.localeCompare(a.slug));
}
