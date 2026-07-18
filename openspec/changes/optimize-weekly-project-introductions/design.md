## Context

Weekly reports serve two consumers: automation that verifies Markdown source fields, and the Astro gallery that turns those fields into project cards. A recent display preference moved `项目简介` ahead of `仓库` in source Markdown, but that couples presentation order to source order and makes repository-first verification less direct.

The UI already has a primary positioning area (`.project-positioning`) derived from `一句话定位` for daily reports and `入选理由` for weekly reports. Weekly `项目简介` should become a separate card summary shown immediately below that positioning, while the expandable details should avoid repeating the same line.

## Goals / Non-Goals

**Goals:**

- Preserve weekly report source Markdown in the stable field order `仓库` then `项目简介`.
- Keep `project.positioning` focused on the concise positioning/reason text already used by search and card summaries.
- Add `project.introduction` as a separate parsed field for weekly introductions.
- Render `project.introduction` below `.project-positioning` with a distinct, lightweight visual style.
- Remove the already-rendered `项目简介` field from expanded card details to avoid duplicate reading.
- Keep daily report parsing and extra findings behavior compatible with existing data.

**Non-Goals:**

- Redesign the full project card layout.
- Change daily report source format.
- Change recommendation scoring or weekly project selection logic.
- Add a new external dependency or change routing.

## Decisions

### Keep Markdown Source Repository-First

Weekly Markdown should remain source-friendly with `仓库` before `项目简介`. The repository field is the stable identity/link anchor used by automation and parsing, while introduction placement is a presentation concern.

Alternative considered: keep `项目简介` first in Markdown. This makes the raw report read closer to the desired UI order, but it weakens the separation between report source semantics and card presentation.

### Parse Introduction as a Separate Field

Extend `ProjectRecord` with `introduction: string` populated from `项目简介`. Do not reuse `positioning` for this field. For weekly reports, `positioning` continues to come from `入选理由`; for daily reports, it continues to come from `一句话定位`.

Alternative considered: render the introduction only from the raw Markdown body. That would make de-duplication and search/card behavior harder to reason about.

### Strip Introduction from Expanded Details

When rendering `project.html` for the expandable analysis block, remove the `- 项目简介：...` line if it has already been parsed into `project.introduction`. The full Markdown source remains unchanged; only the card detail HTML is de-duplicated.

Alternative considered: leave details untouched. This preserves exact source rendering but repeats the introduction directly below the card summary.

### Use Lightweight Styling, Not a New Card

Add a compact `.project-introduction` paragraph below `.project-positioning`, using softer text color and restrained spacing. Do not wrap it in a nested card or add heavy decoration.

Alternative considered: use a labeled fact-row in `.project-facts`. That would push the introduction into evidence metadata instead of keeping it near the project positioning.

## Risks / Trade-offs

- Parser field drift → Cover with tests for weekly `项目简介`, repository link parsing, and real weekly reports.
- Detail de-duplication accidentally removes similar content → Strip only exact Markdown list lines whose label is `项目简介`.
- Search behavior may not include introductions → Keep search based on positioning for now; add introduction search later only if needed.
- Existing weekly files currently have `项目简介` first → Migrate only weekly files back to repository-first source order while keeping UI placement controlled by the component.
