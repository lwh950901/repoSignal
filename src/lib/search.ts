export type ReportType = "monthly" | "weekly" | "daily";

export interface SearchItem {
  id: string;
  repository: string;
  positioning: string;
  technologies: string[];
  kind: string;
  score: number | null;
  reportType: ReportType;
  reportLabel: string;
  href: string;
}

function normalize(value: string): string {
  return value.normalize("NFKC").toLocaleLowerCase("zh-CN");
}

export function searchProjects(
  items: SearchItem[],
  query: string,
  limit = 8,
): SearchItem[] {
  const terms = normalize(query).split(/\s+/u).filter(Boolean);

  return items
    .filter((item) => {
      if (terms.length === 0) return true;
      const haystack = normalize([
        item.repository,
        item.positioning,
        item.technologies.join(" "),
        item.kind,
        ({ monthly: "月", weekly: "周", daily: "日" } as const)[item.reportType],
        item.reportType,
        item.reportLabel,
      ].join(" "));
      return terms.every((term) => haystack.includes(term));
    })
    .sort((a, b) => (["monthly", "weekly", "daily"].indexOf(a.reportType) - ["monthly", "weekly", "daily"].indexOf(b.reportType)))
    .slice(0, limit);
}
