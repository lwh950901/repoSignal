> Source of truth: `docs/superpowers/specs/2026-07-20-monthly-business-research-redesign.md`

## 1. Research contracts and fixtures

- [x] 1.1 Define the public monthly Markdown contract for scored Top 5 projects, 0–3 business opportunities and research methodology
- [x] 1.2 Add internal July research templates for the Top 5 scorecard, business investigations and repository verification
- [x] 1.3 Add failing parser fixtures for valid revised content, score bounds, enums, missing sources, duplicate repositories and zero opportunities

## 2. July Top 5 research

- [x] 2.1 Regenerate the qualified July candidate pool and record its deterministic count and cutoff
- [x] 2.2 Select about 15 deep candidates using only documented monthly signals, without final ranking
- [x] 2.3 Re-verify each deep candidate against GitHub and official documentation, including license, releases, meaningful activity, install path and adoption evidence
- [x] 2.4 Run the minimum safe verification for leading candidates and assign L0–L4 without overstating blocked checks
- [x] 2.5 Score all deep candidates with the six-dimension rubric, calibrate the weights once and freeze the independent Top 5 with objections and sources

## 3. July business research

- [x] 3.1 Derive 5–10 internal hypotheses from July repository capabilities, upstream/downstream gaps, commercial gaps and costly manual workflows
- [x] 3.2 Verify demand and investigate commercial, open-source and real-process alternatives for at most three leading hypotheses
- [x] 3.3 Identify 2–5 non-overlapping repositories per surviving opportunity, including clearly marked supporting components outside July when required
- [x] 3.4 Verify repository interfaces, inputs, outputs, licenses and deployment constraints; complete at least one L2 per published opportunity
- [x] 3.5 Attempt one safe L3 combination experiment, recording success, blockers and required custom development without forcing publication
- [x] 3.6 Publish only the 0–3 opportunities that satisfy demand, alternative, feasibility, MVP and evidence gates

## 4. Revised publication contract and parser

- [x] 4.1 Freeze a revised `2026-07.md` derived only from completed research before changing the parser
- [x] 4.2 Replace audience, recommendation, signal and action types with score, metric, source, verification and business-opportunity types
- [x] 4.3 Parse and strictly validate the revised Top 5 fields, six scores, 100-point total, dates, GitHub links and sources
- [x] 4.4 Parse 0–3 business opportunities, repository roles, validation enums and fixed analysis subsections
- [x] 4.5 Preserve report discovery, canonical repository identity and monthly search conversion with revised summaries
- [x] 4.6 Make all focused monthly parser tests pass before changing the page component

## 5. Revised monthly page

- [x] 5.1 Replace the current hero ledger with research scope and verification metadata
- [x] 5.2 Render independent Top 5 entries with score breakdown, monthly evidence, objections and source links
- [x] 5.3 Render 0–3 business opportunities with decision summary, alternatives, repository combination, gaps, MVP and evidence boundaries
- [x] 5.4 Remove persona selection, fixed signals and audience actions while preserving archive, adjacent-month and period navigation
- [x] 5.5 Add responsive styles for scorecards, evidence links, comparison tables and combination flow without adding client dependencies

## 6. Publication documentation and isolation

- [x] 6.1 Update README to distinguish candidate aggregation, external research, internal evidence and published frozen content
- [x] 6.2 Add a real-content discovery regression for the researched July report
- [x] 6.3 Confirm internal research files are absent from search items and production output

## 7. Verification and review

- [ ] 7.1 Run monthly generator self-check and focused Vitest tests
- [ ] 7.2 Run the full Vitest suite, Astro check, production build and OpenSpec strict validation
- [ ] 7.3 Inspect `/monthly/2026-07/` at desktop and 360px, including source links, tables, keyboard focus and no-JavaScript navigation
- [ ] 7.4 Review the complete change for factual overstatement, spec compliance, security of repository experiments and unnecessary implementation complexity
