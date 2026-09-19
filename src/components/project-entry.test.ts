import { experimental_AstroContainer as AstroContainer } from "astro/container";
import { describe, expect, test } from "vitest";
import ProjectEntry from "./ProjectEntry.astro";
import type { ProjectRecord } from "../lib/digests";

const project: ProjectRecord = {
  id: "project-example-repository",
  kind: "实用型",
  repository: "example/repository",
  url: "https://github.com/example/repository",
  score: 86,
  positioning: "定位文本",
  introduction: "简介文本",
  technologies: ["TypeScript"],
  risk: "风险文本",
  recommendation: "推荐文本",
  markdown: "",
  html: "<p>完整分析</p>",
};

async function render(overrides: Partial<ProjectRecord> = {}) {
  const container = await AstroContainer.create();
  return container.renderToString(ProjectEntry, {
    props: { project: { ...project, ...overrides }, index: 0 },
  });
}

function filledWidths(html: string) {
  return [...html.matchAll(/<rect\b[^>]*class="score-signal__fill"[^>]*>/g)]
    .map(([rect]) => Number(rect.match(/\bwidth="([^"]+)"/)?.[1]));
}

describe("project score rendering", () => {
  test.each([
    [0, Array(10).fill(0)],
    [86, [4, 4, 4, 4, 4, 4, 4, 4, 2.4, 0]],
    [100, Array(10).fill(4)],
  ])("renders score %s with an accurate static signal", async (score, widths) => {
    const html = await render({ score });
    expect(html).toContain(`<strong>${score}</strong>`);
    expect(html).toContain("/ 100");
    expect(html).not.toContain('aria-label="周选项目"');
    expect(filledWidths(html)).toEqual(widths);
    expect(html).toMatch(/<svg\b[^>]*aria-hidden="true"[^>]*focusable="false"/);
    expect(html).not.toMatch(/\s(?:style|tabindex)=|<script\b/);
  });

  test("keeps an unscored selection distinct from zero", async () => {
    const html = await render({ score: null });
    expect(html).toContain('aria-label="周选项目"');
    expect(html).toContain('<span class="project-selection">周选</span>');
    expect(html).not.toContain("score-signal");
    expect(html).not.toContain("/ 100");
  });

  test.each([-1, 101, NaN, Infinity])("does not invent a signal for %s", async (score) => {
    const html = await render({ score });
    expect(html).not.toContain("score-signal");
    if (Number.isFinite(score)) expect(html).toContain(`<strong>${score}</strong>`);
  });

  test.each([true, false])("keeps recommendation styling tied to its field (preceding fields: %s)", async (includeFields) => {
    const html = await render(includeFields ? {} : { technologies: [], risk: "" });
    expect(html).toMatch(/<div class="project-fact--recommendation">\s*<dt>为什么推荐<\/dt>\s*<dd>推荐文本<\/dd>/);
    expect(html.indexOf("定位文本")).toBeLessThan(html.indexOf("简介文本"));
    expect(html.indexOf("简介文本")).toBeLessThan(html.indexOf("推荐文本"));
    expect(html.indexOf("推荐文本")).toBeLessThan(html.indexOf("完整分析"));
    if (!includeFields) expect(html).not.toMatch(/<dt>技术栈|<dt>观察风险/);
  });
});
