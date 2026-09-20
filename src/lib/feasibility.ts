import { marked } from "marked";

export interface ScorePart {
  name: string;
  points: number;
  max: number;
}

export interface ScoreSummary {
  name: string;
  score: number;
  grade: string;
  parts: ScorePart[];
}

export interface FeasibilityPlan {
  id: string;
  title: string;
  positioning: string;
  audience: string;
  marketOpportunity: string;
  judgment: string;
  judgmentReason: string;
  evidenceLevel: string;
  score: number | null;
  grade: string | null;
  scoreParts: ScorePart[];
  techScore: ScoreSummary | null;
  demandScore: ScoreSummary | null;
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
  const labels = ["业务定位", "目标客户", "市场机会", "方案评分", "方案判断", "双评分"];
  return markdown
    .split("\n")
    .filter((line) => !labels.some((label) => line.startsWith(`**${label}**：`)))
    .join("\n")
    .replace(/\n{3,}/gu, "\n\n")
    .trim();
}

function parseScoreParts(detail: string): ScorePart[] {
  return detail
    .split("·")
    .map((item) => {
      const part = item.trim().match(/^(.+?)\s+(\d+)\/(\d+)$/u);
      return part ? { name: part[1], points: Number(part[2]), max: Number(part[3]) } : null;
    })
    .filter((part): part is ScorePart => part !== null);
}

// 方案评分行（旧格式）：**方案评分**：**79/100（中）**（组件可靠度 30/35 · ...）
const SCORE_LINE_RE = /^\*\*方案评分\*\*：\*\*(\d+)\/100（([高中低])）\*\*（(.+)）$/mu;
// 双评分行（新格式）：**双评分**：技术组合成熟度 **79/100（中）**（...） · 需求证据强度 **59/100（低）**（...）
const TECH_SCORE_RE = /技术组合成熟度\s*\*\*(\d+)\/100（([高中低])）\*\*（([^）]*)）/u;
const DEMAND_SCORE_RE = /需求证据强度\s*\*\*(\d+)\/100（([高中低])）\*\*（([^）]*)）/u;
const JUDGMENT_RE = /^\*\*方案判断\*\*：([^（(]+)(?:[（(]依据：(.+?)[）)])?$/mu;
const EVIDENCE_LEVEL_RE = /^\*\*需求证据\*\*（\d+\/100，最高等级：(.+?)）/mu;

function parsePlanScore(markdown: string): { score: number; grade: string; scoreParts: ScorePart[] } | null {
  const match = markdown.match(SCORE_LINE_RE);
  if (!match) return null;
  return { score: Number(match[1]), grade: match[2], scoreParts: parseScoreParts(match[3]) };
}

function parseScoreSide(markdown: string, re: RegExp, name: string): ScoreSummary | null {
  const match = markdown.match(re);
  if (!match) return null;
  return {
    name,
    score: Number(match[1]),
    grade: match[2],
    parts: parseScoreParts(match[3]),
  };
}

function parseDualScores(markdown: string): {
  techScore: ScoreSummary | null;
  demandScore: ScoreSummary | null;
} {
  return {
    techScore: parseScoreSide(markdown, TECH_SCORE_RE, "技术组合成熟度"),
    demandScore: parseScoreSide(markdown, DEMAND_SCORE_RE, "需求证据强度"),
  };
}

function parsePlans(markdown: string): FeasibilityPlan[] {
  const section = sectionText(markdown, "可行性方案");
  const headings = [...section.matchAll(/^###\s+(\d+)\.\s+(.+)$/gmu)];

  return headings.map((heading, index) => {
    const start = (heading.index ?? 0) + heading[0].length;
    const end = headings[index + 1]?.index ?? section.length;
    const body = section.slice(start, end).trim();
    const parsedScore = parsePlanScore(body);
    const { techScore, demandScore } = parseDualScores(body);
    const judgment = body.match(JUDGMENT_RE);
    const bodyMarkdown = removeSummaryFields(body);

    return {
      id: `plan-${heading[1]}`,
      title: cleanInline(heading[2]),
      positioning: getSummaryField(body, "业务定位"),
      audience: getSummaryField(body, "目标客户"),
      marketOpportunity: getSummaryField(body, "市场机会"),
      judgment: judgment ? cleanInline(judgment[1]) : "",
      judgmentReason: judgment?.[2] ? cleanInline(judgment[2]) : "",
      evidenceLevel: cleanInline(body.match(EVIDENCE_LEVEL_RE)?.[1] ?? ""),
      score: parsedScore?.score ?? null,
      grade: parsedScore?.grade ?? null,
      scoreParts: parsedScore?.scoreParts ?? [],
      techScore,
      demandScore,
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
