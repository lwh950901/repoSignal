import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";

const issues = new Map([
  ["2026-W27", 10],
  ["2026-W28", 10],
  ["2026-W29", 10],
  ["2026-W30", 10],
  ["2026-W31", 10],
]);
const indexPath = new URL("../dist/radar/index.html", import.meta.url);
const indexHtml = await readFile(indexPath, "utf8");
const redirectsPath = new URL("../dist/_redirects", import.meta.url);
const redirects = await readFile(redirectsPath, "utf8");

for (const [week, projectCount] of issues) {
  const issuePath = new URL(`../dist/radar/${week}/index.html`, import.meta.url);
  const issueHtml = await readFile(issuePath, "utf8");
  assert.ok(issueHtml.includes(`<link rel="canonical" href="/radar/${week}/">`));
  assert.ok(issueHtml.includes(`<title>开源雷达周刊｜${week}</title>`));
  assert.match(issueHtml, /src="\/covers\/repository-radar-weekly-subtitle\.png"/u);
  assert.ok(issueHtml.includes(`href="/weekly/${week}/"`));
  assert.ok(issueHtml.includes(`<a href="/radar/${week}/" aria-current="page">`));
  assert.match(issueHtml, /<noscript>[\s\S]*class="archive-links"[\s\S]*<\/noscript>/u);
  assert.equal((issueHtml.match(/href="https:\/\/github\.com\//gu) ?? []).length, projectCount);
  assert.doesNotMatch(issueHtml, /SITE_BASE_URL|utm_/iu);
  assert.doesNotMatch(issueHtml, /reportType&quot;:&quot;radar|reportType":"radar/iu);
}
assert.match(indexHtml, /http-equiv="refresh" content="2;url=\/radar\/2026-W31\/"/u);
assert.match(indexHtml, /<link rel="canonical" href="\/radar\/2026-W31\/">/u);
assert.ok(redirects.includes("/radar /radar/2026-W31/ 302"));
assert.ok(redirects.includes("/radar/ /radar/2026-W31/ 302"));

console.log(`Radar build output verified: /radar/ and ${issues.size} weekly issues.`);
