import { describe, expect, it } from "vitest";
import type { SearchItem } from "./search";
import { searchProjects } from "./search";

const items: SearchItem[] = [
  {
    id: "daily-graphify",
    repository: "safishamsi/graphify",
    positioning: "把代码结构提取成知识图谱",
    technologies: ["Python", "MCP"],
    kind: "爆发型",
    score: 82,
    reportType: "daily",
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
    reportType: "daily",
    reportLabel: "2026-07-01",
    href: "/daily/2026-07-01/#project-obscura",
  },
];

describe("searchProjects", () => {
  it("matches type labels and ranks monthly before weekly before daily", () => {
    const typed = [
      { ...items[0], id: "daily", reportType: "daily" as const },
      { ...items[0], id: "weekly", reportType: "weekly" as const },
      { ...items[0], id: "monthly", reportType: "monthly" as const },
    ];
    expect(searchProjects(typed, "月").map((item) => item.id)).toEqual(["monthly"]);
    expect(searchProjects(typed, "graphify").map((item) => item.id)).toEqual(["monthly", "weekly", "daily"]);
  });

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
