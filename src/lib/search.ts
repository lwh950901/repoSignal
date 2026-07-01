import type { DigestIndexItem } from "./digests";

function normalize(value: string): string {
  return value.normalize("NFKC").toLocaleLowerCase("zh-CN");
}

export function searchProjects(
  items: DigestIndexItem[],
  query: string,
  limit = 8,
): DigestIndexItem[] {
  const terms = normalize(query).split(/\s+/u).filter(Boolean);

  return items
    .filter((item) => {
      if (terms.length === 0) return true;
      const haystack = normalize([
        item.repository,
        item.positioning,
        item.technologies.join(" "),
        item.kind,
        item.reportLabel,
      ].join(" "));
      return terms.every((term) => haystack.includes(term));
    })
    .slice(0, limit);
}
