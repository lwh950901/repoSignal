export type ReportPeriod = "monthly" | "weekly" | "daily";

function dateFor(period: ReportPeriod, slug: string): Date {
  if (period === "monthly") {
    const [year, month] = slug.split("-").map(Number);
    return new Date(Date.UTC(year, month, 0));
  }
  if (period === "daily") return new Date(`${slug}T00:00:00Z`);
  const match = slug.match(/^(\d{4})-W(\d{2})$/u);
  if (!match) return new Date(0);
  const jan4 = new Date(Date.UTC(Number(match[1]), 0, 4));
  const monday = new Date(jan4);
  monday.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() + 6) % 7) + (Number(match[2]) - 1) * 7);
  monday.setUTCDate(monday.getUTCDate() + 6);
  return monday;
}

function href(type: ReportPeriod, slug?: string): string {
  return `/${type}/${slug ? `${slug}/` : ""}`;
}

function nearest(type: ReportPeriod, anchor: Date, slugs: string[]): string | undefined {
  const containing = slugs.find((slug) => {
    if (type === "monthly") return slug === anchor.toISOString().slice(0, 7);
    if (type === "weekly") {
      const end = dateFor(type, slug);
      const start = new Date(end);
      start.setUTCDate(end.getUTCDate() - 6);
      return start.getTime() <= anchor.getTime() && anchor.getTime() <= end.getTime();
    }
    return slug === anchor.toISOString().slice(0, 10);
  });
  if (containing) return containing;
  return slugs
    .filter((slug) => dateFor(type, slug).getTime() <= anchor.getTime())
    .sort((a, b) => dateFor(type, b).getTime() - dateFor(type, a).getTime())[0];
}

export function resolvePeriodLinks(
  currentType: ReportPeriod,
  currentSlug: string,
  monthly: string[],
  weekly: string[],
  daily: string[],
): Record<ReportPeriod, string> {
  const anchor = dateFor(currentType, currentSlug);
  return {
    monthly: href("monthly", nearest("monthly", anchor, monthly)),
    weekly: href("weekly", nearest("weekly", anchor, weekly)),
    daily: href("daily", nearest("daily", anchor, daily)),
  };
}
