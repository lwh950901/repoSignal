import { access, readdir, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";

const periods = [
  { name: "monthly", pattern: /^\d{4}-(?:0[1-9]|1[0-2])$/u },
  { name: "weekly", pattern: /^\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])$/u },
  { name: "daily", pattern: /^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$/u },
  { name: "radar", pattern: /^\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])$/u },
];

async function readableIndex(path) {
  try {
    await access(path, constants.R_OK);
    return true;
  } catch {
    return false;
  }
}

async function validSlugs(root, period) {
  const periodRoot = join(root, period.name);
  let entries;
  try {
    entries = await readdir(periodRoot, { withFileTypes: true });
  } catch (error) {
    if (error && typeof error === "object" && "code" in error && error.code === "ENOENT") return [];
    throw error;
  }

  const candidates = entries
    .filter((entry) => entry.isDirectory() && period.pattern.test(entry.name))
    .map((entry) => entry.name);
  const checks = await Promise.all(candidates.map(async (slug) => ({
    slug,
    valid: await readableIndex(join(periodRoot, slug, "index.html")),
  })));
  return checks.filter((candidate) => candidate.valid).map((candidate) => candidate.slug);
}

export async function discoverLatestReports(root) {
  const latest = {};
  for (const period of periods) {
    const slugs = await validSlugs(root, period);
    slugs.sort((left, right) => right.localeCompare(left, "en"));
    if (!slugs[0]) {
      throw new Error(`No valid ${period.name} detail page found in ${join(root, period.name)}.`);
    }
    latest[period.name] = slugs[0];
  }
  return latest;
}

export function renderRedirects(latest) {
  const lines = [];
  for (const { name } of periods) {
    const target = `/${name}/${latest[name]}/`;
    lines.push(`/${name} ${target} 302`, `/${name}/ ${target} 302`);
  }
  return `${lines.join("\n")}\n`;
}

export async function writeLatestRedirects(root) {
  const latest = await discoverLatestReports(root);
  await writeFile(join(root, "_redirects"), renderRedirects(latest), "utf8");
  return latest;
}

async function main() {
  const scriptDirectory = dirname(fileURLToPath(import.meta.url));
  const outputRoot = resolve(scriptDirectory, "../dist");
  const latest = await writeLatestRedirects(outputRoot);
  const summary = periods.map(({ name }) => `${name}=${latest[name]}`).join(", ");
  console.log(`Latest report redirects written: ${summary}`);
}

const entryPath = process.argv[1] ? resolve(process.argv[1]) : "";
if (entryPath === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  });
}
