#!/usr/bin/env python3
"""Select 0-3 weekly feasibility plans with four-week family deduplication."""

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    from scripts import opportunity_analysis as analysis
except ImportError:  # Direct execution from scripts/.
    import opportunity_analysis as analysis


SCORE_RE = re.compile(r"\*\*方案评分\*\*[：:]\*\*(\d+)/100（([^）]+)）\*\*")
HEADING_RE = re.compile(r"^###\s+(?:可行性方案\s+\d+[：:]\s*|\d+\.\s+)(.+)$", re.MULTILINE)
MIN_SCORE = 70
MAX_PLANS = 3
OVERLAP_PENALTY = 8


def _week_dates(week):
    match = analysis.WEEK_RE.fullmatch(week)
    if not match:
        raise ValueError(f"周次必须是 YYYY-Www：{week!r}")
    monday = date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)
    return [monday + timedelta(days=offset) for offset in range(6)]


def _previous_weeks(week, count=4):
    monday = _week_dates(week)[0]
    result = []
    for offset in range(1, count + 1):
        previous = monday - timedelta(weeks=offset)
        iso = previous.isocalendar()
        result.append(f"{iso.year}-W{iso.week:02d}")
    return result


def _plan_blocks(markdown):
    source = markdown or ""
    start = source.find("## 可行性方案")
    if start < 0:
        return []
    source = source[source.find("\n", start) + 1:]
    end = re.search(r"^##\s+", source, re.MULTILINE)
    if end:
        source = source[:end.start()]
    matches = list(HEADING_RE.finditer(source))
    return [
        source[match.start():matches[index + 1].start() if index + 1 < len(matches) else len(source)]
        for index, match in enumerate(matches)
    ]


def _parse_candidate(block, source_date):
    heading = HEADING_RE.search(block)
    score_match = SCORE_RE.search(block)
    if not heading or not score_match:
        return None
    identity = analysis.parse_plan_identities("## 可行性方案\n" + block)[0]
    return {
        "sourceDate": source_date,
        "title": identity["name"],
        "score": int(score_match.group(1)),
        "grade": score_match.group(2),
        "family": identity["family"],
        "variant": identity["variant"],
        "repositories": identity["repositories"],
    }


def _prior_families(week, data_root):
    families = set()
    weeks_read = []
    for prior_week in _previous_weeks(week):
        path = data_root / "radar" / f"{prior_week}.md"
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            continue
        weeks_read.append(prior_week)
        families.update(
            item["family"]
            for item in analysis.parse_plan_identities(path.read_text(encoding="utf-8"))
        )
    return families, weeks_read


def _deduplicate_current(candidates):
    best_by_family = {}
    for candidate in candidates:
        current = best_by_family.get(candidate["family"])
        rank = (candidate["score"], candidate["sourceDate"], candidate["variant"])
        if current is None or rank > (
            current["score"], current["sourceDate"], current["variant"]
        ):
            best_by_family[candidate["family"]] = candidate
    return list(best_by_family.values())


def _select_portfolio(candidates):
    remaining = list(candidates)
    selected = []
    used_repositories = set()
    while remaining and len(selected) < MAX_PLANS:
        ranked = []
        for candidate in remaining:
            overlap = len(set(candidate["repositories"]) & used_repositories)
            adjusted = candidate["score"] - OVERLAP_PENALTY * overlap
            ranked.append((adjusted, candidate["score"], candidate["sourceDate"], candidate))
        adjusted, _, _, best = max(ranked, key=lambda row: row[:3])
        if adjusted < MIN_SCORE:
            break
        chosen = dict(best)
        chosen["selectionScore"] = adjusted
        selected.append(chosen)
        used_repositories.update(best["repositories"])
        remaining.remove(best)
    return selected


def select_weekly_plans(week, data_root):
    data_root = Path(data_root)
    dates = [day.isoformat() for day in _week_dates(week)]
    candidates = []
    dates_read = []
    for source_date in dates:
        path = data_root / "feasibility" / f"{source_date}.md"
        if not path.is_file():
            continue
        markdown = path.read_text(encoding="utf-8")
        if not markdown.strip():
            continue
        dates_read.append(source_date)
        candidates.extend(
            candidate
            for block in _plan_blocks(markdown)
            if (candidate := _parse_candidate(block, source_date)) is not None
        )

    deduplicated = _deduplicate_current(candidates)
    prior_families, prior_weeks_read = _prior_families(week, data_root)
    blocked_families = sorted({
        candidate["family"] for candidate in deduplicated
        if candidate["family"] in prior_families
    })
    eligible = [
        candidate for candidate in deduplicated
        if candidate["family"] not in prior_families
    ]
    selected = _select_portfolio(eligible)
    return {
        "week": week,
        "datesRead": dates_read,
        "missingDates": [source_date for source_date in dates if source_date not in dates_read],
        "priorWeeksRead": prior_weeks_read,
        "candidateCount": len(candidates),
        "deduplicatedCount": len(deduplicated),
        "blockedFamilies": blocked_families,
        "eligibleCount": len(eligible),
        "selected": selected,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("week", help="ISO 周，例如 2026-W36")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=analysis.DEFAULT_DATA_ROOT,
        help="github-project-digest 数据目录",
    )
    args = parser.parse_args(argv)
    try:
        result = select_weekly_plans(args.week, args.data_root)
    except ValueError as error:
        print(f"错误: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
