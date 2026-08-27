export type ReportPeriod = "monthly" | "weekly" | "daily" | "feasibility" | "radar";

function href(type: ReportPeriod, slug?: string): string {
  return `/${type}/${slug ? `${slug}/` : ""}`;
}

function latest(slugs: string[]): string | undefined {
  return [...slugs].sort((a, b) => b.localeCompare(a))[0];
}

export function resolvePeriodLinks(
  _currentType: ReportPeriod,
  _currentSlug: string,
  monthly: string[],
  weekly: string[],
  daily: string[],
  feasibility: string[],
  radar: string[],
): Record<ReportPeriod, string> {
  return {
    monthly: href("monthly", latest(monthly)),
    weekly: href("weekly", latest(weekly)),
    daily: href("daily", latest(daily)),
    feasibility: href("feasibility", latest(feasibility)),
    radar: href("radar", latest(radar)),
  };
}
