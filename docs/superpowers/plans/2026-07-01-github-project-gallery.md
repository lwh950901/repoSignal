# GitHub Project Gallery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a responsive Astro static site that turns the existing daily and weekly GitHub digest Markdown files into an archive with a keyboard-driven local search.

**Architecture:** Astro performs all file discovery and report parsing during the production build. Focused TypeScript modules convert Markdown into typed report/project records; pages and components consume only those records. A small client-side search module receives a serialized index and progressively enhances otherwise readable static HTML.

**Tech Stack:** Astro, TypeScript, marked, Vitest, CSS, Cloudflare Pages static deployment

---

## File structure

- `package.json`, `astro.config.mjs`, `tsconfig.json`: project and build configuration.
- `src/lib/digests.ts`: discover, parse, normalize, and index digest Markdown.
- `src/lib/digests.test.ts`: parser tests against representative reports and malformed input.
- `src/layouts/BaseLayout.astro`: document shell, metadata, navigation, and global stylesheet.
- `src/components/DateRail.astro`: desktop date rail and mobile report selector.
- `src/components/ProjectEntry.astro`: one accessible project archive entry.
- `src/components/SearchPalette.astro`: search dialog markup, serialized index, and keyboard behavior.
- `src/pages/index.astro`: redirect-like latest-report landing page rendered as real HTML.
- `src/pages/daily/[date].astro`: static daily report routes.
- `src/pages/weekly/[week].astro`: static weekly report routes.
- `src/styles/global.css`: complete token system, responsive layout, focus, and reduced-motion rules.
- `public/_headers`: Cloudflare Pages security headers.

### Task 1: Scaffold the Astro build

**Files:**
- Create: `package.json`
- Create: `astro.config.mjs`
- Create: `tsconfig.json`
- Create: `.gitignore`

- [ ] **Step 1: Add scripts and exact dependencies**

Create `package.json` with `dev`, `build`, `preview`, `test`, and `check` scripts; add Astro and `marked` as runtime dependencies and Vitest plus TypeScript as development dependencies.

- [ ] **Step 2: Configure a static Astro output**

Set `output: "static"`, enable trailing slashes for portable static hosting, and extend Astro's strict TypeScript config.

- [ ] **Step 3: Install dependencies**

Run: `npm install`

Expected: exit 0 and a generated `package-lock.json`.

- [ ] **Step 4: Verify the scaffold**

Run: `npm run check`

Expected: Astro reports no project configuration errors.

### Task 2: Parse digest Markdown with tests

**Files:**
- Create: `src/lib/digests.ts`
- Create: `src/lib/digests.test.ts`

- [ ] **Step 1: Write failing parser tests**

Cover these exact behaviors:

```ts
expect(parseDailyReport(sample, "2026-07-01.md").date).toBe("2026-07-01");
expect(report.projects.map((project) => project.kind)).toEqual(["爆发型", "实用型", "潜力型"]);
expect(report.projects[0].repository).toBe("safishamsi/graphify");
expect(report.projects[0].score).toBe(82);
expect(report.projects[0].technologies).toContain("Python");
expect(parseDailyReport("# 只有标题", "2026-07-02.md").projects).toEqual([]);
```

- [ ] **Step 2: Run the tests to verify failure**

Run: `npm test -- src/lib/digests.test.ts`

Expected: FAIL because `digests.ts` does not exist.

- [ ] **Step 3: Implement typed parsing and discovery**

Define `ProjectRecord`, `DigestReport`, and `DigestIndexItem`. Parse project headings with a tolerant heading expression, extract repository links, scores, positioning, technology stacks, risk, and recommendation sections, and retain each project's Markdown body. Discover files with Node `fs` from `data/github-project-digest/daily` and `weekly`, sort newest first, and return empty arrays for missing directories.

- [ ] **Step 4: Run parser tests**

Run: `npm test -- src/lib/digests.test.ts`

Expected: all parser tests pass.

### Task 3: Build the static report interface

**Files:**
- Create: `src/layouts/BaseLayout.astro`
- Create: `src/components/DateRail.astro`
- Create: `src/components/ProjectEntry.astro`
- Create: `src/pages/index.astro`
- Create: `src/pages/daily/[date].astro`
- Create: `src/pages/weekly/[week].astro`

- [ ] **Step 1: Add report route tests through the build contract**

Extend the parser tests to assert that the real digest directories return at least one daily report and that every generated slug matches the appropriate route parameter.

- [ ] **Step 2: Implement the document shell**

Create semantic landmarks, a skip link, Chinese metadata, compact top navigation, and a slot for page content. Keep all data access outside components except the route pages.

- [ ] **Step 3: Implement archive navigation and entries**

Render a real ordered date list on desktop and a labeled select on mobile. Render each project as an `article` with type stamp, repository link, score, positioning, technologies, risks, recommendation, and a collapsible full analysis.

- [ ] **Step 4: Implement static routes**

Use `getStaticPaths()` for daily and weekly routes. Render the latest daily report directly at `/` so the homepage remains useful without redirects or JavaScript.

- [ ] **Step 5: Verify generated HTML**

Run: `npm run build`

Expected: exit 0; `dist/index.html`, at least one `dist/daily/*/index.html`, and at least one `dist/weekly/*/index.html` exist.

### Task 4: Apply the archive visual system

**Files:**
- Create: `src/styles/global.css`
- Modify: `src/layouts/BaseLayout.astro`
- Modify: `src/components/DateRail.astro`
- Modify: `src/components/ProjectEntry.astro`

- [ ] **Step 1: Implement tokens and typography**

Declare the approved paper, ink, moss, yellow, and divider tokens; use a Chinese system sans stack for prose and a local monospace stack for repositories, dates, and scores. Do not require remote font requests.

- [ ] **Step 2: Implement the desktop archive composition**

Use a restrained two-column grid with a sticky date rail. Project entries are separated by rules rather than floating cards. The type stamp is the sole saturated visual signature.

- [ ] **Step 3: Implement responsive behavior**

At 760px, replace the sticky rail with a compact top selector, stack metadata without horizontal overflow, and preserve a minimum 44px interactive target.

- [ ] **Step 4: Add interaction states**

Provide visible `:focus-visible` outlines, subtle entry-link movement, and reduced-motion overrides. Ensure native disclosure controls remain legible.

### Task 5: Add the command search palette

**Files:**
- Create: `src/components/SearchPalette.astro`
- Create: `src/lib/search.ts`
- Create: `src/lib/search.test.ts`
- Modify: `src/layouts/BaseLayout.astro`

- [ ] **Step 1: Write failing search tests**

Test case-insensitive matching across repository, positioning, technologies, and kind; verify an empty query returns the newest items and an unmatched query returns an empty result.

- [ ] **Step 2: Run the tests to verify failure**

Run: `npm test -- src/lib/search.test.ts`

Expected: FAIL because the search module does not exist.

- [ ] **Step 3: Implement deterministic local search**

Normalize fields to lowercase, split whitespace terms, require every term to match the combined searchable text, and cap results at eight.

- [ ] **Step 4: Implement the accessible palette**

Render a native `dialog`, search input, result list, and empty state. Support the search button, `Meta+K`, `Ctrl+K`, arrows, Enter, and Escape; restore focus when the dialog closes. Each result links to the report route plus the project's stable fragment.

- [ ] **Step 5: Run unit tests**

Run: `npm test`

Expected: all parser and search tests pass.

### Task 6: Deployment hardening and visual verification

**Files:**
- Create: `public/_headers`
- Modify: `README.md`

- [ ] **Step 1: Add static security headers**

Configure `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and a CSP compatible with Astro's emitted static scripts and styles.

- [ ] **Step 2: Document Cloudflare Pages settings**

Document build command `npm run build`, output directory `dist`, Node compatibility, local commands, data source, and the automatic rebuild flow after digest commits.

- [ ] **Step 3: Run the full verification suite**

Run: `npm test && npm run check && npm run build`

Expected: all commands exit 0.

- [ ] **Step 4: Inspect production pages in the browser**

Serve `dist`, inspect homepage and one historical route at desktop and 390px widths, verify the palette entirely by keyboard, confirm no horizontal overflow, and confirm no console errors.

- [ ] **Step 5: Verify progressive enhancement**

Disable JavaScript and reload the homepage and a daily route.

Expected: report navigation, repository links, and full report content remain readable; only command search is unavailable.

- [ ] **Step 6: Commit the implementation**

Stage only the site source, configuration, tests, lockfile, deployment header, and README. Preserve unrelated digest and learning changes.
