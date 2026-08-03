import { afterEach, describe, expect, test } from "vitest";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

interface RedirectModule {
  discoverLatestReports(root: string): Promise<Record<"monthly" | "weekly" | "daily" | "radar", string>>;
  renderRedirects(latest: Record<"monthly" | "weekly" | "daily" | "radar", string>): string;
}

const moduleUrl = new URL("./generate_latest_redirects.mjs", import.meta.url);
const redirectsModule = await import(moduleUrl.href).catch(() => null) as RedirectModule | null;
const tempRoots: string[] = [];

async function temporaryRoot(): Promise<string> {
  const root = await mkdtemp(join(tmpdir(), "reposignal-redirects-"));
  tempRoots.push(root);
  return root;
}

async function addDetail(root: string, period: string, slug: string, withIndex = true): Promise<void> {
  const directory = join(root, period, slug);
  await mkdir(directory, { recursive: true });
  if (withIndex) await writeFile(join(directory, "index.html"), "<!doctype html>", "utf8");
}

afterEach(async () => {
  await Promise.all(tempRoots.splice(0).map((root) => rm(root, { recursive: true, force: true })));
});

describe("latest report redirect generation", () => {
  test("selects the newest valid built detail for every report type", async () => {
    expect(redirectsModule).not.toBeNull();
    if (!redirectsModule) return;

    const root = await temporaryRoot();
    await Promise.all([
      addDetail(root, "monthly", "2026-07"),
      addDetail(root, "monthly", "2026-08"),
      addDetail(root, "monthly", "2026-09", false),
      addDetail(root, "monthly", "draft"),
      addDetail(root, "weekly", "2026-W31"),
      addDetail(root, "weekly", "2026-W32"),
      addDetail(root, "daily", "2026-08-02"),
      addDetail(root, "daily", "2026-08-03"),
      addDetail(root, "radar", "2026-W30"),
      addDetail(root, "radar", "2026-W31"),
    ]);

    await expect(redirectsModule.discoverLatestReports(root)).resolves.toEqual({
      monthly: "2026-08",
      weekly: "2026-W32",
      daily: "2026-08-03",
      radar: "2026-W31",
    });
  });

  test("rejects a build missing a valid detail page and names the period", async () => {
    expect(redirectsModule).not.toBeNull();
    if (!redirectsModule) return;

    const root = await temporaryRoot();
    await Promise.all([
      addDetail(root, "monthly", "2026-08"),
      addDetail(root, "weekly", "2026-W32"),
      addDetail(root, "daily", "2026-08-03"),
      addDetail(root, "radar", "2026-W31", false),
    ]);

    await expect(redirectsModule.discoverLatestReports(root)).rejects.toThrow(/radar/u);
  });

  test("renders exactly eight deterministic temporary redirect rules", () => {
    expect(redirectsModule).not.toBeNull();
    if (!redirectsModule) return;

    const output = redirectsModule.renderRedirects({
      monthly: "2026-08",
      weekly: "2026-W32",
      daily: "2026-08-03",
      radar: "2026-W31",
    });

    expect(output).toBe([
      "/monthly /monthly/2026-08/ 302",
      "/monthly/ /monthly/2026-08/ 302",
      "/weekly /weekly/2026-W32/ 302",
      "/weekly/ /weekly/2026-W32/ 302",
      "/daily /daily/2026-08-03/ 302",
      "/daily/ /daily/2026-08-03/ 302",
      "/radar /radar/2026-W31/ 302",
      "/radar/ /radar/2026-W31/ 302",
      "",
    ].join("\n"));
    expect(output).not.toContain("*");
  });
});
