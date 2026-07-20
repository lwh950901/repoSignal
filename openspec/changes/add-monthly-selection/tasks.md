## 1. Monthly content model

- [ ] 1.1 Add failing Vitest fixtures for valid monthly parsing, required fields, duplicate repositories, invalid GitHub URLs and weak-signal downgrade
- [ ] 1.2 Implement `MonthlyReport`, project, recommendation, signal and action types with strict Markdown parsing and validation
- [ ] 1.3 Add monthly report discovery and monthly search-index conversion tests

## 2. Editorial draft generator

- [ ] 2.1 Add a failing offline self-check for candidate normalization, source/date merging and deterministic rendering
- [ ] 2.2 Implement the Python standard-library generator for monthly candidate, daily and overlapping ISO-week inputs
- [ ] 2.3 Add the npm self-check command and keep `.superpowers`, `.worktrees` and `monthly-drafts` ignored

## 3. Period navigation logic

- [ ] 3.1 Add failing tests for month-end, ISO-week-end and daily anchors, containing-period selection and safe index fallbacks
- [ ] 3.2 Implement pure month/week/day link resolution with nearest-earlier fallback

## 4. Unified search contract

- [ ] 4.1 Add failing tests for report-type matching and monthly-before-weekly-before-daily ordering
- [ ] 4.2 Move the shared search item type into `search.ts` and add explicit report types to daily, weekly and monthly indexes
- [ ] 4.3 Update the search palette to render accessible 月/周/日 badges without regressing keyboard behavior

## 5. Monthly components and shared header

- [ ] 5.1 Implement the accessible `PeriodSwitcher` and make `BaseLayout` require active-period links plus canonical/Open Graph metadata
- [ ] 5.2 Implement the monthly archive rail with desktop links, mobile selector and no-JavaScript month links
- [ ] 5.3 Implement Top 5 project entries and the monthly report view with conclusions, personas, signals, actions and adjacent-month navigation

## 6. Static routes and approved visual design

- [ ] 6.1 Add `/monthly/`, `/monthly/[month]/`, `/weekly/` and `/daily/` type-index routes with explicit empty states
- [ ] 6.2 Migrate the homepage and existing daily/weekly routes to shared search and period links while keeping the homepage on the latest weekly report
- [ ] 6.3 Add desktop and 360px responsive styles for the approved editorial UI, visible focus and reduced-motion behavior
- [ ] 6.4 Run focused tests, Astro type checking and a production build before adding published monthly content

## 7. First monthly publication and final verification

- [ ] 7.1 Generate and inspect the July candidate draft without staging it
- [ ] 7.2 Publish the complete 2026-07 monthly report with a 2026-07-20 cutoff, five Top 5 entries, nine role recommendations, three signals and role actions
- [ ] 7.3 Update README documentation and add a real-content monthly discovery test
- [ ] 7.4 Run generator self-check, full Vitest suite, Astro check and production build
- [ ] 7.5 Inspect `/monthly/2026-07/` at desktop and 360px widths, including keyboard and no-JavaScript navigation
