#!/usr/bin/env python3
"""Sync published monthly recommendations into the shared history ledger."""

import argparse
import json
import os
import re
import stat
import tempfile
from pathlib import Path


CUTOFF_RE = re.compile(r"^>\s*数据截止[：:]\s*(\d{4}-\d{2}-\d{2})\s*$")
REPO_RE = re.compile(
    r"^-\s*仓库[：:]\s*\[[^\]]+\]\(https://github\.com/([^/\s)]+/[^/\s)]+)\)\s*$",
    re.IGNORECASE,
)


def parse_monthly_recommendations(text, period):
    """Return the Top 5 and business-core repositories from one monthly report."""
    cutoff = None
    in_top5 = False
    current_repo = None
    selected = {}
    top5_repos = set()

    for line in text.splitlines():
        cutoff_match = CUTOFF_RE.match(line)
        if cutoff_match:
            cutoff = cutoff_match.group(1)

        if line == "## Top 5 仓库":
            in_top5 = True
            current_repo = None
            continue
        if line.startswith("## "):
            in_top5 = False
            current_repo = None
            continue
        if line.startswith("### ") or line.startswith("##### "):
            current_repo = None

        repo_match = REPO_RE.match(line)
        if repo_match:
            current_repo = repo_match.group(1).lower()
            if in_top5:
                selected[current_repo] = "monthly_top5"
                top5_repos.add(current_repo)
            continue

        if line.strip() == "- 来源身份：本月核心" and current_repo:
            selected.setdefault(current_repo, "monthly_core")

    if cutoff is None:
        raise ValueError(f"{period} 月报缺少数据截止日期")
    if not cutoff.startswith(f"{period}-"):
        raise ValueError(f"{period} 与数据截止日期 {cutoff} 不一致")
    if len(top5_repos) != 5:
        raise ValueError(f"{period} 月报 Top 5 应为 5 个不同仓库，实际为 {len(top5_repos)} 个")

    return [
        {
            "date": cutoff,
            "period": period,
            "repo": repo,
            "role": selected[repo],
            "url": f"https://github.com/{repo}",
        }
        for repo in sorted(selected)
    ]


def history_record(recommendation):
    role = recommendation["role"]
    slot = "月度 Top 5" if role == "monthly_top5" else "月度业务核心"
    return {
        "activity": f"入选 {recommendation['period']} {slot}。",
        "date": recommendation["date"],
        "forks": None,
        "license": None,
        "period": recommendation["period"],
        "reason": f"收录于公开月报的{slot}。",
        "repeat_exception": False,
        "repo": recommendation["repo"],
        "role": role,
        "score": None,
        "slot": slot,
        "stars": None,
        "url": recommendation["url"],
    }


def merge_history(existing_text, recommendations):
    """Append missing monthly events while preserving all existing JSONL lines."""
    existing_lines = existing_text.splitlines()
    existing_keys = set()
    for number, line in enumerate(existing_lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"history.jsonl:{number}: {error.msg}") from error
        if record.get("role") in {"monthly_top5", "monthly_core"}:
            existing_keys.add((record.get("period"), str(record.get("repo", "")).lower()))

    additions = []
    for recommendation in recommendations:
        key = (recommendation["period"], recommendation["repo"].lower())
        if key not in existing_keys:
            additions.append(json.dumps(history_record(recommendation), ensure_ascii=False, sort_keys=True))
            existing_keys.add(key)

    if not additions:
        return existing_text, 0
    merged_lines = existing_lines + additions
    return "\n".join(merged_lines) + "\n", len(additions)


def sync_month_file(monthly_path, history_path, period):
    monthly_text = monthly_path.read_text(encoding="utf-8")
    history_text = history_path.read_text(encoding="utf-8") if history_path.exists() else ""
    recommendations = parse_monthly_recommendations(monthly_text, period)
    merged, added = merge_history(history_text, recommendations)
    if added:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        original_mode = stat.S_IMODE(history_path.stat().st_mode) if history_path.exists() else None
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=history_path.parent,
            delete=False,
        ) as handle:
            handle.write(merged)
            temporary_path = Path(handle.name)
        if original_mode is not None:
            os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, history_path)
    return added


def self_check():
    monthly = """# RepoSignal 月度精选｜2026-07

> 数据截止：2026-07-31

## Top 5 仓库

### 1. Top project

- 仓库：[Owner/Top](https://github.com/Owner/Top)

### 2. Top two

- 仓库：[Owner/Two](https://github.com/Owner/Two)

### 3. Top three

- 仓库：[Owner/Three](https://github.com/Owner/Three)

### 4. Top four

- 仓库：[Owner/Four](https://github.com/Owner/Four)

### 5. Top five

- 仓库：[Owner/Five](https://github.com/Owner/Five)

## 真实业务与项目机会

##### 1. Top again

- 仓库：[Owner/Top](https://github.com/Owner/Top)
- 来源身份：本月核心

##### 2. Core project

- 仓库：[Owner/Core](https://github.com/Owner/Core)
- 来源身份：本月核心

##### 3. Supporting project

- 仓库：[Owner/Supporting](https://github.com/Owner/Supporting)
- 来源身份：补充组件
"""
    recommendations = parse_monthly_recommendations(monthly, "2026-07")
    assert recommendations == [
        {
            "date": "2026-07-31",
            "period": "2026-07",
            "repo": "owner/core",
            "role": "monthly_core",
            "url": "https://github.com/owner/core",
        },
        {
            "date": "2026-07-31",
            "period": "2026-07",
            "repo": "owner/five",
            "role": "monthly_top5",
            "url": "https://github.com/owner/five",
        },
        {
            "date": "2026-07-31",
            "period": "2026-07",
            "repo": "owner/four",
            "role": "monthly_top5",
            "url": "https://github.com/owner/four",
        },
        {
            "date": "2026-07-31",
            "period": "2026-07",
            "repo": "owner/three",
            "role": "monthly_top5",
            "url": "https://github.com/owner/three",
        },
        {
            "date": "2026-07-31",
            "period": "2026-07",
            "repo": "owner/top",
            "role": "monthly_top5",
            "url": "https://github.com/owner/top",
        },
        {
            "date": "2026-07-31",
            "period": "2026-07",
            "repo": "owner/two",
            "role": "monthly_top5",
            "url": "https://github.com/owner/two",
        },
    ]

    existing = "\n".join([
        json.dumps({"date": "2026-07-01", "repo": "owner/top", "role": "primary"}),
        json.dumps({
            "date": "2026-07-31",
            "period": "2026-07",
            "repo": "owner/core",
            "role": "monthly_core",
        }),
    ]) + "\n"
    merged, added = merge_history(existing, recommendations)
    records = [json.loads(line) for line in merged.splitlines()]
    assert added == 5
    assert len(records) == 7
    assert records[-1]["repo"] == "owner/two"
    assert records[-1]["role"] == "monthly_top5"
    assert records[-1]["repeat_exception"] is False
    assert merge_history(merged, recommendations) == (merged, 0)

    role_changed = json.dumps({
        "date": "2026-07-31",
        "period": "2026-07",
        "repo": "owner/top",
        "role": "monthly_core",
    }) + "\n"
    assert merge_history(role_changed, [recommendations[-2]]) == (role_changed, 0)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        monthly_path = root / "2026-07.md"
        history_path = root / "history.jsonl"
        monthly_path.write_text(monthly, encoding="utf-8")
        history_path.write_text(existing, encoding="utf-8")
        original_mode = stat.S_IMODE(history_path.stat().st_mode)
        assert sync_month_file(monthly_path, history_path, "2026-07") == 5
        assert stat.S_IMODE(history_path.stat().st_mode) == original_mode
        first = history_path.read_text(encoding="utf-8")
        assert sync_month_file(monthly_path, history_path, "2026-07") == 0
        assert history_path.read_text(encoding="utf-8") == first


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("period", nargs="?", help="已发布月报月份，格式 YYYY-MM")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data/github-project-digest"),
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        self_check()
        print("MONTHLY HISTORY SYNC SELF-CHECK: PASS")
        return 0
    if not args.period or not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", args.period):
        parser.error("需要有效的 YYYY-MM，或使用 --check")

    monthly_path = args.data_root / "monthly" / f"{args.period}.md"
    history_path = args.data_root / "history.jsonl"
    if not monthly_path.exists():
        parser.error(f"月报不存在：{monthly_path}")
    added = sync_month_file(monthly_path, history_path, args.period)
    print(f"已同步 {added} 条月度推荐到 {history_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
