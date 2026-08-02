import { describe, expect, it } from "vitest";
import { resolvePeriodLinks } from "./periods";

describe("resolvePeriodLinks", () => {
  it("always links each period switcher option to its latest report", () => {
    expect(resolvePeriodLinks(
      "weekly",
      "2026-W29",
      ["2026-06", "2026-07"],
      ["2026-W30", "2026-W28", "2026-W29"],
      ["2026-07-18", "2026-07-29", "2026-07-25"],
      ["2026-W30", "2026-W31"],
    )).toEqual({
      monthly: "/monthly/2026-07/",
      weekly: "/weekly/2026-W30/",
      daily: "/daily/2026-07-29/",
      radar: "/radar/2026-W31/",
    });
  });

  it("falls back safely to a period index when no earlier report exists", () => {
    expect(resolvePeriodLinks("daily", "2026-07-01", [], [], [], [])).toEqual({
      monthly: "/monthly/", weekly: "/weekly/", daily: "/daily/", radar: "/radar/",
    });
  });
});
