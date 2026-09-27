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
DUAL_SCORE_RE = re.compile(
    r"\*\*双评分\*\*[：:]\s*技术组合成熟度\s*\*\*(\d+)/100（([^）]+)）\*\*"
)
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
    score_match = DUAL_SCORE_RE.search(block) or SCORE_RE.search(block)
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


def _prior_families(week, data_root, history_families_by_variant=None):
    families = set()
    weeks_read = []
    history_families_by_variant = history_families_by_variant or {}
    for prior_week in _previous_weeks(week):
        path = data_root / "radar" / f"{prior_week}.md"
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            continue
        weeks_read.append(prior_week)
        for item in analysis.parse_plan_identities(path.read_text(encoding="utf-8")):
            history_families = history_families_by_variant.get(item["variant"], set())
            if item["family"].startswith("custom-") and len(history_families) == 1:
                families.update(history_families)
            else:
                families.add(item["family"])
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
    prior_dates = {
        day.isoformat()
        for prior_week in _previous_weeks(week)
        for day in _week_dates(prior_week)
    }
    history_by_variant = {}
    prior_history_families_by_variant = {}
    history_path = data_root / "feasibility" / "plan-history.jsonl"
    if history_path.is_file():
        for line in history_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("date") in dates and record.get("variant") and record.get("family"):
                history_by_variant[(record["date"], record["variant"])] = record["family"]
            if record.get("date") in prior_dates and record.get("variant") and record.get("family"):
                prior_history_families_by_variant.setdefault(record["variant"], set()).add(record["family"])
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
        for block in _plan_blocks(markdown):
            candidate = _parse_candidate(block, source_date)
            if candidate is None:
                raise ValueError(
                    f"{source_date}: 无法解析可行性方案评分：{block.splitlines()[0]}"
                )
            candidate["family"] = history_by_variant.get(
                (source_date, candidate["variant"]), candidate["family"]
            )
            candidates.append(candidate)

    deduplicated = _deduplicate_current(candidates)
    prior_families, prior_weeks_read = _prior_families(
        week, data_root, prior_history_families_by_variant
    )
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
