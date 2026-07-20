import { describe, expect, it } from "vitest";
import { resolvePeriodLinks } from "./periods";

describe("resolvePeriodLinks", () => {
  it("uses month-end, ISO-week-end and day anchors with containing-period matches", () => {
    expect(resolvePeriodLinks("monthly", "2026-07", ["2026-07"], ["2026-W27", "2026-W29"], ["2026-07-18"])).toEqual({
      monthly: "/monthly/2026-07/", weekly: "/weekly/2026-W29/", daily: "/daily/2026-07-18/",
    });
    expect(resolvePeriodLinks("daily", "2026-07-18", ["2026-07"], ["2026-W29"], ["2026-07-18"])).toEqual({
      monthly: "/monthly/2026-07/", weekly: "/weekly/2026-W29/", daily: "/daily/2026-07-18/",
    });
  });

  it("falls back safely to a period index when no earlier report exists", () => {
    expect(resolvePeriodLinks("daily", "2026-07-01", [], [], [])).toEqual({
      monthly: "/monthly/", weekly: "/weekly/", daily: "/daily/",
    });
  });
});
