## Why

Weekly project recommendations currently mix source-data concerns with presentation concerns: the Markdown field order was changed to make introductions visible earlier, while the UI also needs to present introductions below the existing project positioning. This creates avoidable parser/display coupling and can duplicate the same introduction inside the expanded analysis.

The weekly recommendation view should keep Markdown reports stable for automation and verification, while presenting project introductions as a distinct, readable summary under the project positioning in the gallery UI.

## What Changes

- Keep weekly Markdown reports and the weekly generation baseline in a source-friendly field order where `仓库` remains before `项目简介`.
- Parse `项目简介` as a separate project introduction field instead of folding it into positioning or recommendation text.
- Render project introductions directly below `.project-positioning` in project cards.
- Avoid repeating the `项目简介` line inside the expanded full-analysis details when the introduction is already shown in the card.
- Add a lightweight visual treatment for project introductions so readers can distinguish them from positioning and evidence fields.
- Update tests to cover weekly introduction parsing, placement, and supported daily project counts.

## Capabilities

### New Capabilities

- `weekly-project-introductions`: Covers how weekly project introductions are represented in report source Markdown, parsed into project data, displayed in project cards, and de-duplicated from expanded analysis.

### Modified Capabilities

None.

## Impact

- Weekly digest Markdown files under `data/github-project-digest/weekly/`.
- Weekly digest design baseline at `docs/superpowers/specs/2026-06-29-github-project-digest-design.md`.
- Digest parsing in `src/lib/digests.ts` and related tests in `src/lib/digests.test.ts`.
- Project card rendering in `src/components/ProjectEntry.astro`.
- Project card styling in `src/styles/global.css`.
