## 1. Source Report Format

- [x] 1.1 Restore weekly report files to `仓库` before `项目简介` for every project entry in `data/github-project-digest/weekly/*.md`.
- [x] 1.2 Update the weekly digest design baseline so future weekly reports require `仓库` before `项目简介` and keep `项目简介` before `入选理由`.
- [x] 1.3 Add or update a field-order check that verifies weekly source reports follow `仓库` → `项目简介` → `入选理由`.

## 2. Parsing and Detail Rendering

- [x] 2.1 Extend `ProjectRecord` with an `introduction` field parsed from `项目简介`.
- [x] 2.2 Keep weekly `positioning` parsed from `入选理由` and daily `positioning` parsed from `一句话定位`.
- [x] 2.3 Generate project detail HTML from a de-duplicated body that removes the raw `项目简介` list item after parsing it into `introduction`.
- [x] 2.4 Preserve the original project Markdown source unchanged for auditing and source display use.

## 3. Card Presentation

- [x] 3.1 Render `project.introduction` immediately below `.project-positioning` when present.
- [x] 3.2 Add a dedicated `.project-introduction` class with lightweight styling distinct from positioning and fact rows.
- [x] 3.3 Ensure the introduction is not moved into `.project-facts` and does not create nested card styling.

## 4. Verification

- [x] 4.1 Add unit tests for weekly introduction parsing, positioning separation, and detail de-duplication.
- [x] 4.2 Add tests or assertions covering real weekly report field order and non-empty introductions.
- [x] 4.3 Keep daily report parsing compatible with 3–5 primary projects.
- [x] 4.4 Run `npm test` and `npm run check`.
