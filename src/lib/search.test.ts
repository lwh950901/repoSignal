import { describe, expect, it } from "vitest";
import type { DigestIndexItem } from "./digests";
import { searchProjects } from "./search";

const items: DigestIndexItem[] = [
  {
    id: "daily-graphify",
    repository: "safishamsi/graphify",
    positioning: "把代码结构提取成知识图谱",
    technologies: ["Python", "MCP"],
    kind: "爆发型",
    score: 82,
    reportLabel: "2026-07-01",
    href: "/daily/2026-07-01/#project-graphify",
  },
  {
    id: "daily-obscura",
    repository: "h4ckf0r0day/obscura",
    positioning: "面向 Agent 的无头浏览器",
    technologies: ["Rust", "CDP"],
    kind: "潜力型",
    score: 84,
    reportLabel: "2026-07-01",
    href: "/daily/2026-07-01/#project-obscura",
  },
];

describe("searchProjects", () => {
  it("matches every query term across searchable fields", () => {
    expect(searchProjects(items, "PYTHON 图谱").map((item) => item.repository)).toEqual([
      "safishamsi/graphify",
    ]);
    expect(searchProjects(items, "rust 潜力型").map((item) => item.repository)).toEqual([
      "h4ckf0r0day/obscura",
    ]);
  });

  it("returns newest input order for an empty query and nothing for no match", () => {
    expect(searchProjects(items, "").map((item) => item.id)).toEqual([
      "daily-graphify",
      "daily-obscura",
    ]);
    expect(searchProjects(items, "TypeScript")).toEqual([]);
  });

  it("caps results at eight", () => {
    const many = Array.from({ length: 12 }, (_, index) => ({ ...items[0], id: `item-${index}` }));
    expect(searchProjects(many, "")).toHaveLength(8);
  });
});
