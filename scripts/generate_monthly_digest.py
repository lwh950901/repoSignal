#!/usr/bin/env python3
"""Create a deterministic, non-published editorial monthly candidate draft.

Usage:
  python3 scripts/generate_monthly_digest.py YYYY-MM [--data-root path] [--output path]
  python3 scripts/generate_monthly_digest.py --check
"""

import argparse
import json
import re
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
GITHUB_RE = re.compile(r"https?://github\.com/([^/\s)\]#]+)/([^/\s)\]#]+)", re.IGNORECASE)
REPO_RE = re.compile(r"^[^/\s]+/[^/\s]+$")
DAILY_REPO_LINE_RE = re.compile(
    r"^-\s*仓库[：:]\s*\[[^\]]+\]\(https?://github\.com/([^/\s)]+/[^/\s)]+)\)\s*$",
    re.IGNORECASE,
)
DAILY_TITLE_RE = re.compile(
    r"^###\s+\d+\.\s+(?:爆发型|实用型|潜力型)[：:]\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?:\s|—|–|-|$)"
)
WEEKLY_TITLE_RE = re.compile(
    r"^##\s+\d+\.\s+(?:\[([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\]\(https?://github\.com/[^)]+\)|([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+))(?:\s|—|–|-|$)",
    re.IGNORECASE,
)
WEEKLY_ENTRY_RE = re.compile(r"^##\s+\d+\.\s+.+")


def validate_month(value):
    """Return a month anchor after strictly validating YYYY-MM."""
    match = MONTH_RE.fullmatch(value)
    if not match:
        raise ValueError(f"月份必须是有效的 YYYY-MM：{value!r}")
    return date(int(match.group(1)), int(match.group(2)), 1)


def normalize_repo(raw_repo):
    """Return the canonical lower-case owner/repo identity."""
    repo = (raw_repo or "").strip().strip("`")
    match = GITHUB_RE.search(repo)
    if match:
        repo = f"{match.group(1)}/{match.group(2)}"
    repo = repo.strip("/ ").lower()
    if not REPO_RE.fullmatch(repo):
        raise ValueError(f"无效的 GitHub 仓库名：{raw_repo!r}")
    return repo


def canonical_url(repo):
    return f"https://github.com/{repo}"


def parse_evidence_date(raw_date, context):
    """Validate and normalize a source evidence date."""
    if not isinstance(raw_date, str):
        raise ValueError(f"{context}: date 必须是 YYYY-MM-DD 字符串")
    try:
        return date.fromisoformat(raw_date).isoformat()
    except ValueError as error:
        raise ValueError(f"{context}: 无效 date {raw_date!r}") from error


def normalize_candidate(raw_repo, raw_date, source):
    """Make a merge-ready evidence item from one source occurrence."""
    return {
        "repo": normalize_repo(raw_repo),
        "date": parse_evidence_date(raw_date, source),
        "source": source,
    }


def add_evidence(merged, evidence):
    """Merge one normalized occurrence into the repository keyed mapping."""
    item = merged.setdefault(evidence["repo"], {
        "repo": evidence["repo"],
        "url": canonical_url(evidence["repo"]),
        "dates": set(),
        "sources": set(),
    })
    item["dates"].add(evidence["date"])
    item["sources"].add(evidence["source"])


def candidate_evidence(candidates_dir, month):
    """Read monthly candidate JSONL evidence, rejecting malformed JSON with context."""
    for path in sorted(candidates_dir.glob(f"{month}-*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}:{number}: JSON 格式错误：{error.msg}") from error
                if not isinstance(record, dict):
                    raise ValueError(f"{path}:{number}: JSONL 条目必须是对象")
                context = f"{path}:{number}"
                if not isinstance(record.get("repo"), str):
                    raise ValueError(f"{context}: 缺少字符串 repo 字段")
                if not isinstance(record.get("url"), str):
                    raise ValueError(f"{context}: 缺少字符串 url 字段")
                if "date" not in record:
                    raise ValueError(f"{context}: 缺少 date 字段")
                yield normalize_candidate(record["repo"], record["date"], "候选账本")


def repository_names_from_markdown(text, source_path, main_only=False):
    """Extract only exact report fields or approved selection headings, never prose."""
    in_main_recommendations = not main_only
    weekly_entry = False
    found = []
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+)$", line)
        if main_only and heading:
            title = heading.group(1).strip()
            if title == "主推荐":
                in_main_recommendations = True
                continue
            if in_main_recommendations:
                break
        if not in_main_recommendations:
            continue
        if main_only:
            repo_line = DAILY_REPO_LINE_RE.match(line)
            title = DAILY_TITLE_RE.match(line)
            if repo_line:
                found.append(normalize_repo(repo_line.group(1)))
            elif title:
                found.append(normalize_repo(title.group(1)))
        else:
            if WEEKLY_ENTRY_RE.match(line):
                weekly_entry = True
            title = WEEKLY_TITLE_RE.match(line)
            if title:
                found.append(normalize_repo(title.group(1) or title.group(2)))
            elif weekly_entry:
                repo_line = DAILY_REPO_LINE_RE.match(line)
                if repo_line:
                    found.append(normalize_repo(repo_line.group(1)))
    return found


def daily_evidence(daily_dir, month):
    for path in sorted(daily_dir.glob(f"{month}-*.md")):
        evidence_date = parse_evidence_date(path.stem, str(path))
        for repo in repository_names_from_markdown(
            path.read_text(encoding="utf-8"), path, main_only=True
        ):
            yield normalize_candidate(repo, evidence_date, "日报")


def iso_week_dates(stem):
    match = WEEK_RE.fullmatch(stem)
    if not match:
        return None
    try:
        start = date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)
    except ValueError:
        return None
    return start, start + timedelta(days=6)


def weekly_evidence(weekly_dir, month_anchor):
    """Use ISO week end as deterministic weekly evidence date for month overlap."""
    month_end = (month_anchor.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    for path in sorted(weekly_dir.glob("????-W??.md")):
        week = iso_week_dates(path.stem)
        if not week:
            continue
        week_start, week_end = week
        if week_start > month_end or week_end < month_anchor:
            continue
        for repo in repository_names_from_markdown(path.read_text(encoding="utf-8"), path):
            yield normalize_candidate(repo, week_end.isoformat(), "周报")


def collect_candidates(data_root, month):
    """Collect and merge candidate, daily, and calendar-overlapping weekly evidence."""
    month_anchor = validate_month(month)
    merged = {}
    for evidence in candidate_evidence(data_root / "candidates", month):
        add_evidence(merged, evidence)
    for evidence in daily_evidence(data_root / "daily", month):
        add_evidence(merged, evidence)
    for evidence in weekly_evidence(data_root / "weekly", month_anchor):
        add_evidence(merged, evidence)
    return sorted(
        (
            {
                **item,
                "dates": sorted(item["dates"]),
                "sources": sorted(item["sources"]),
            }
            for item in merged.values()
        ),
        key=lambda item: (-len(item["sources"]), -len(item["dates"]), item["repo"]),
    )


def render_draft(month, candidates):
    """Render an editorial-only Markdown draft without selecting a Top 5."""
    month_anchor = validate_month(month)
    month_end = (month_anchor.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    dates = [date.fromisoformat(day) for item in candidates for day in item["dates"]]
    cutoff = min(max(max(dates), month_anchor), month_end).isoformat() if dates else month_end.isoformat()
    lines = [
        f"# GitHub 优质项目月度编辑候选初稿｜{month}",
        "",
        "> 草稿主题：汇总本月候选、日报与周报的本地证据，供编辑复核后再决定月度叙事与 Top 5；本文件不是已发布月报。",
        "",
        f"- 截止日期：{cutoff}",
        f"- 候选数量：{len(candidates)}",
        "- 发布状态：未发布（编辑候选初稿）",
        "",
        "## 候选池",
        "",
    ]
    for item in candidates:
        lines.extend([
            f"### {item['repo']}",
            "",
            f"- 仓库：[{item['repo']}]({item['url']})",
            f"- 发现日期：{'、'.join(item['dates'])}",
            f"- 来源：{'、'.join(item['sources'])}",
            f"- 当月出现次数：{len(item['dates'])}",
            "- 审核状态：待编辑确认",
            "",
        ])
    return "\n".join(lines)


def write_draft(output, content):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")


def assert_raises(action, expected_text):
    try:
        action()
    except ValueError as error:
        assert expected_text in str(error), str(error)
    else:
        raise AssertionError("预期 ValueError")


def self_check():
    """Run a fully offline temporary-fixture integration check."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "data"
        for directory in ("candidates", "daily", "weekly"):
            (root / directory).mkdir(parents=True)
        (root / "candidates" / "2026-07-03.jsonl").write_text(
            json.dumps({"repo": "Owner/Repo", "url": "https://github.com/Owner/Repo", "date": "2026-07-03"}) + "\n",
            encoding="utf-8",
        )
        (root / "daily" / "2026-07-04.md").write_text(
            "# 日报\n\n## 主推荐\n\n### 1. 实用型：owner/REPO — 示例\n\n- 仓库：[owner/REPO](https://github.com/owner/REPO)\n- 仓库相关的 docs/superpowers、cli/tui 和 .github/workflows 需要审查。\n\n## 额外发现\n- 仓库：[skip/me](https://github.com/skip/me)\n",
            encoding="utf-8",
        )
        # 2026-W27 ends on July 5, so it proves ISO weeks spanning June/July count.
        (root / "weekly" / "2026-W27.md").write_text(
            "# 周报\n\n## 1. OWNER/repo\n\n仓库内 docs/superpowers、cli/tui 和 .github/workflows 不是项目条目。\n",
            encoding="utf-8",
        )
        candidates = collect_candidates(root, "2026-07")
        assert len(candidates) == 1, candidates
        item = candidates[0]
        assert item["repo"] == "owner/repo", item
        assert item["url"] == "https://github.com/owner/repo", item
        assert item["sources"] == ["候选账本", "周报", "日报"], item
        assert item["dates"] == ["2026-07-03", "2026-07-04", "2026-07-05"], item
        first = render_draft("2026-07", candidates)
        second = render_draft("2026-07", collect_candidates(root, "2026-07"))
        assert first == second
        assert "- 候选数量：1" in first
        assert "审核状态：待编辑确认" in first
        assert "Top 5" in first and "未发布" in first
        assert_raises(lambda: validate_month("2026-13"), "YYYY-MM")
        malformed = root / "candidates" / "2026-07-bad.jsonl"
        malformed.write_text("{not json}\n", encoding="utf-8")
        assert_raises(lambda: collect_candidates(root, "2026-07"), f"{malformed}:1")


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("month", nargs="?", help="目标自然月，格式 YYYY-MM")
    parser.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true", help="运行离线自检")
    args = parser.parse_args(argv)
    if args.check:
        if args.month or args.output != None or args.data_root != Path("data/github-project-digest"):
            parser.error("--check 不接受月份或路径参数")
        return args
    if not args.month:
        parser.error("需要 YYYY-MM")
    try:
        validate_month(args.month)
    except ValueError as error:
        parser.error(str(error))
    if args.output is None:
        args.output = args.data_root / "monthly-drafts" / f"{args.month}.md"
    return args


def main(argv=None):
    args = parse_args(argv)
    if args.check:
        self_check()
        print("MONTHLY GENERATOR SELF-CHECK: PASS")
        return 0
    try:
        candidates = collect_candidates(args.data_root, args.month)
        content = render_draft(args.month, candidates)
        write_draft(args.output, content)
    except ValueError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2
    print(f"已写入 {len(candidates)} 条编辑候选到 {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
