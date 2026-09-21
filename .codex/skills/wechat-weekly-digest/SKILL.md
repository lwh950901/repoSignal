---
name: wechat-weekly-digest
description: Convert the weekly open-source "radar" digest into a WeChat Official Account article. Strips markdown links while keeping every word identical to the original, applies the inline-styled "radar screen" layout (signal-orange circular number badges, deep-sea blue headings, 14px gray intro, left-aligned), embeds a one-click copy button, and ships a publish checklist. Use when the user asks for WeChat / Weixin formatting, 公众号排版, or turning a weekly digest into a paste-ready article.
---

# WeChat Weekly Digest

Turn `data/github-project-digest/radar/2026-WXX.md` into:

- `data/weixin/2026-WXX.md` — link-free markdown (text identical to the original)
- `data/weixin/2026-WXX.html` — paste-ready WeChat HTML (inline styles only, with a one-click copy button)

## Hard constraints

1. **Verbatim copy.** Visible text in the HTML must match the original digest character for character — including numbering ("1. "), full-width punctuation, and spaces. Allowed transforms only: drop link syntax (keep the display text); drop image reference lines; drop the `---` divider; drop markdown table pipes and `|---|---|`-style separator rows (tables become styled vertical cards, cell text order preserved); `- ` risk bullets keep the "-" glyph and drop only the trailing space (the gap is CSS `margin`). The verifier ignores whitespace and md syntax, so any real added/removed/reordered character still fails.
2. **No added content.** No one-line summaries, table of contents, engagement prompts, or emoji that are absent from the original.
3. **WeChat-compatible.** Inline styles only; no external fonts/images/scripts in the article body; no animation; no flex/grid. Block/inline elements are enough.
4. **Keep the "阅读全文" text.** `**阅读全文：** [text](url)` becomes `**阅读全文：** text` (link removed, words kept).

## 本周可行性精选 styling

The optional "本周可行性精选" section gets its own hierarchy (full spec in `references/wechat-style-guide.md`):

- The intro paragraph right under the `## 本周可行性精选` heading renders in the 14px gray intro style (same as the lead under the title).
- Proposal headings (`### 可行性方案 N：…`) use the h2-family treatment: deep-sea blue text with a 4px signal-orange left border.
- Score lines (`**方案评分**：**83/100（中）**`) render the value as a deep-sea-blue pill with white text.
- Markdown tables (组合方案) are rendered as real WeChat tables: a deep-sea-blue header row, column semantics inferred from the header text (角色/项目/来源/许可证 → fixed widths 13/20/15/10%, except a 角色 column holding a full project tagline — today's anchor combos, >20 chars — which widens to 35%; the 入选理由 column always gets the remaining width, so 5-column, 4-column and slimmed 3-column tables all render cleanly), role cells signal-orange bold, repo cells monospace deep-sea blue, source 12px gray, license as a bordered chip, and the reason in the widest column; every cell wraps (`word-break:break-all`) so the table never overflows a phone viewport. Pipes and separator rows are syntax, not content.
- Risk lines starting with `- ` keep the dash character (signal orange, bold) and never invent bullet glyphs.

## Workflow

1. Generate the link-free markdown:

   ```bash
   bash scripts/strip-links.sh data/github-project-digest/radar/2026-WXX.md data/weixin/2026-WXX.md
   ```

2. Build the HTML — two equivalent paths:

   - **Automated** (preferred): `python3 scripts/digest-to-html.py data/weixin/2026-WXX.md data/weixin/2026-WXX.html` produces the full article (head checklist, cover placeholder, radar-screen styles, one-click copy button, read-original placeholder).
   - **Manual**: copy `templates/wechat-template.html` and replace the body while keeping the style skeleton, placeholders, button, and head checklist. Update `<title>`, the checklist, and the A/B/C title candidates (see below).

3. Follow the style spec in `references/wechat-style-guide.md` (radar-screen scheme: signal-orange circular number badges, deep-sea blue headings, 14px gray intro under the title, everything left-aligned).

4. Verify verbatim copy:

   ```bash
   bash scripts/verify-text.sh data/github-project-digest/radar/2026-WXX.md data/weixin/2026-WXX.html
   # expect: TEXT_OK
   ```

   The verifier strips links, image lines, markdown markers (including `|` pipes and table separator rows), comments, placeholders, the copy button text, and the `<script>` block, then ignores whitespace before comparing. On `TEXT_DIFF`, fix per the diff. Common causes: a sentence dropped or reordered, numbering format changed, a label accidentally rewritten.

5. Remind the user of the publish checklist (also embedded in the HTML head comment):

   - 3 title candidates (≤30 chars), abstract ≤120 chars — **the A/B/C lines embedded in the generated head are static example text from an early issue, not derived from this week's content; always rewrite them from the current week's lead paragraphs**
   - Cover: `public/covers/repository-radar-weekly-subtitle.png` resized to 900×383 (large) plus a 1:1 square (the small cover crops the middle)
   - Delete the two 【发布前删除】 placeholder boxes before publishing
   - Set 阅读原文 to the full report URL in the WeChat backend if the site is deployed
   - Mark 原创 (body >300 chars); topic tags #开源项目 #开发者工具 #AI 编程
   - Re-check time-sensitive numbers (versions, dates) before publishing

## One-click copy button

Every generated HTML carries a floating "一键复制全文" button (bottom-right, fixed, outside the article container):

- Works on `file://` (uses `document.execCommand('copy')` on a Range selection — no server needed)
- Copies the article body **with inline styles**, so pasting into the WeChat editor keeps the layout
- Temporarily hides the two 【发布前删除】 placeholder boxes during copy, then restores them
- The button itself is outside the copied container and never appears in the article

## Automation

A scheduled job (every Sunday 09:30) runs the same pipeline headlessly. It is **fully self-contained** in the target repo (does not depend on this skill directory):

- Entry point: `repo-signal/scripts/run-weekly-wechat.sh` — detects the current ISO week (`date +%G-W%V`, with a fallback for week names without a leading zero), skips with a log line when this week's digest does not exist yet, then runs strip-links → `repo-signal/scripts/digest-to-html.py` → inline verbatim check (same filters as `verify-text.sh`).
- Log: `data/weixin/.weekly-run.log` (SKIP / OK / FAIL lines). On FAIL the HTML is still written but needs human review.
- In Kun, create a scheduled task: daily 09:30 (Kun has no weekly schedule; the prompt checks "only run on Sunday") or weekly if the GUI exposes it, workspace `/Users/elvis/Desktop/repo-signal`, prompt: run `bash scripts/run-weekly-wechat.sh` and check the log.

## Notes

- Keep `scripts/digest-to-html.py` **byte-identical** with `repo-signal/scripts/digest-to-html.py`: the scheduled automation runs the repo copy, manual runs use this one. After changing either, copy it to the other (the repo copy is the newer baseline).
- The verbatim-check filters live in two places with the same rules: this `scripts/verify-text.sh` and the inline check in `repo-signal/scripts/run-weekly-wechat.sh`. Update both together whenever placeholder wording or md-syntax handling changes (keywords: `【发布前删除】`, `大封面 900`, `一键复制全文`).
- Covers live in `public/covers/`.
- Alternative schemes (B terminal / C spec) exist as samples in `data/weixin/2026-W32-b-terminal.html` and `data/weixin/2026-W32-c-spec.html`; the default is scheme A (radar screen).
