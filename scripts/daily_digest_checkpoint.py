#!/usr/bin/env python3
"""Compact, resumable state and finalization for the GitHub daily digest."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


EXPECTED_SLOTS = ["爆发型", "实用型", "潜力型", "学习型"]
REQUIRED_FIELDS = [
    "仓库",
    "一句话定位",
    "类型与适合用途",
    "核心亮点与场景",
    "主要技术栈",
    "实时指标",
    "近期有意义活动",
    "质量证据",
    "风险",
    "推荐理由",
]
HEADING_RE = re.compile(
    r"^### (?P<number>\d+)\. (?P<slot>爆发型|实用型|潜力型|学习型)："
    r"(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+) — (?P<score>\d{1,3})/100$",
    re.MULTILINE,
)


class ValidationError(ValueError):
    """Raised when finalization inputs violate the daily digest contract."""


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"日期必须为 YYYY-MM-DD：{value}") from exc


def _norm_repo(value: Any) -> str:
    return str(value or "").strip().lower()


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"JSON 损坏：{path}") from exc


def _read_jsonl(path: Path, *, required: bool = False) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            raise ValidationError(f"缺少文件：{path}")
        return []
    records: list[dict[str, Any]] = []
    try:
        for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValidationError(f"JSONL 第 {number} 行不是对象：{path}")
            records.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"JSONL 损坏：{path}") from exc
    return records


def _jsonl_text(records: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        for record in records
    )


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _stage_writes(writes: list[tuple[Path, str]]) -> None:
    """Stage every target before replacing any target; each replacement is atomic."""
    staged: list[tuple[Path, Path]] = []
    try:
        for target, content in writes:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
                staged.append((Path(handle.name), target))
        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _ in staged:
            if temporary.exists():
                temporary.unlink()


def _candidate_records(run_date: str, root: Path) -> list[dict[str, Any]]:
    path = root / "candidates" / f"{run_date}.jsonl"
    records = _read_jsonl(path, required=True)
    if not records:
        raise ValidationError(f"候选文件为空：{path}")
    seen: set[str] = set()
    for record in records:
        repo = _norm_repo(record.get("repo"))
        if not repo or "/" not in repo:
            raise ValidationError(f"候选仓库名无效：{record.get('repo')!r}")
        if repo in seen:
            raise ValidationError(f"候选仓库重复：{repo}")
        if record.get("date") != run_date:
            raise ValidationError(f"候选日期不一致：{repo}")
        seen.add(repo)
    return records


def _recent_repos(run_date: str, history: list[dict[str, Any]]) -> list[str]:
    end = _parse_date(run_date)
    start = end - timedelta(days=90)
    repos: set[str] = set()
    for item in history:
        try:
            item_date = _parse_date(str(item.get("date", "")))
        except ValidationError:
            continue
        if start <= item_date < end:
            repo = _norm_repo(item.get("repo"))
            if repo:
                repos.add(repo)
    return sorted(repos)


def _user_candidates(root: Path) -> list[str]:
    repos: set[str] = set()
    for item in _read_jsonl(root / "feedback.jsonl"):
        status = str(item.get("status", "")).lower()
        if status in {"rejected", "done", "processed", "resolved"}:
            continue
        repo = _norm_repo(item.get("repo") or item.get("repository"))
        if repo and "/" in repo:
            repos.add(repo)
    return sorted(repos)[:20]


def validate_report(text: str, run_date: str) -> list[dict[str, Any]]:
    title = f"# GitHub 优质项目每日发现｜{run_date}"
    if not text.startswith(title):
        raise ValidationError(f"日报标题或日期错误，应为：{title}")
    marker = "## 主推荐"
    if marker not in text:
        raise ValidationError("日报缺少“## 主推荐”")
    section = text.split(marker, 1)[1]
    section = re.split(r"\n## (?!主推荐)", section, maxsplit=1)[0]
    matches = list(HEADING_RE.finditer(section))
    if not 4 <= len(matches) <= 5:
        raise ValidationError("正式推荐数量必须为 4–5")

    parsed: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        expected_number = index + 1
        if int(match.group("number")) != expected_number:
            raise ValidationError("正式推荐序号必须连续")
        if index < 4 and match.group("slot") != EXPECTED_SLOTS[index]:
            raise ValidationError("前四类顺序必须为爆发型、实用型、潜力型、学习型")
        score = int(match.group("score"))
        if not 0 <= score <= 100:
            raise ValidationError("评分必须在 0–100")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        block = section[match.end() : end]
        positions = []
        for field in REQUIRED_FIELDS:
            found = re.search(rf"^- {re.escape(field)}：", block, re.MULTILINE)
            if not found:
                raise ValidationError(f"{match.group('repo')} 缺少字段：{field}")
            positions.append(found.start())
        if positions != sorted(positions):
            raise ValidationError(f"{match.group('repo')} 十个字段顺序错误")
        parsed.append(
            {
                "repo": match.group("repo"),
                "repo_norm": _norm_repo(match.group("repo")),
                "slot": match.group("slot"),
                "score": score,
            }
        )
    return parsed


def _trial_has_date(status: Any, run_date: str) -> bool:
    if not isinstance(status, dict):
        return False
    if isinstance(status.get(f"daily_run_{run_date}"), dict):
        return True
    latest = status.get("latest_daily_run")
    if isinstance(latest, dict) and latest.get("date") == run_date:
        return True
    return any(
        isinstance(item, dict) and item.get("date") == run_date
        for item in status.get("runs", [])
        if isinstance(status.get("runs"), list)
    )


def inspect_run(run_date: str, root: Path) -> dict[str, Any]:
    _parse_date(run_date)
    root = Path(root)
    candidate_path = root / "candidates" / f"{run_date}.jsonl"
    report_path = root / "daily" / f"{run_date}.md"
    history_path = root / "history.jsonl"
    status_path = root / "trial-status.json"
    missing: list[str] = []
    errors: list[str] = []

    try:
        candidates = _candidate_records(run_date, root)
    except ValidationError as exc:
        candidates = []
        missing.append("candidate_ledger")
        if candidate_path.exists():
            errors.append(str(exc))

    try:
        history = _read_jsonl(history_path)
    except ValidationError as exc:
        history = []
        errors.append(str(exc))

    candidate_repos = {_norm_repo(item.get("repo")) for item in candidates}
    recent = [repo for repo in _recent_repos(run_date, history) if repo in candidate_repos]
    report_items: list[dict[str, Any]] = []
    if report_path.exists():
        try:
            report_items = validate_report(report_path.read_text(encoding="utf-8"), run_date)
        except (OSError, ValidationError) as exc:
            errors.append(str(exc))
    else:
        missing.append("daily_report")

    stage = "needs_discovery" if not candidates else "candidates_ready"
    selected_count = 0
    if report_items:
        stage = "report_ready"
        report_repos = {item["repo_norm"] for item in report_items}
        selected = {
            _norm_repo(item.get("repo"))
            for item in candidates
            if item.get("status") == "primary" and item.get("verified") is True
        }
        selected_count = len(selected & report_repos)
        history_repos = {
            _norm_repo(item.get("repo"))
            for item in history
            if item.get("date") == run_date and item.get("role", "primary") == "primary"
        }
        try:
            trial = _read_json(status_path, {})
            trial_ready = _trial_has_date(trial, run_date)
        except ValidationError as exc:
            trial_ready = False
            errors.append(str(exc))
        if report_repos == selected and report_repos == history_repos and trial_ready:
            stage = "complete"
        else:
            if not report_repos <= selected:
                missing.append("candidate_selection_sync")
            if not report_repos <= history_repos:
                missing.append("history_sync")
            if not trial_ready:
                missing.append("trial_status_sync")

    result: dict[str, Any] = {
        "date": run_date,
        "stage": stage,
        "candidateCount": len(candidates),
        "selectedCount": selected_count,
        "userCandidates": _user_candidates(root),
        "recentDuplicateRepos": recent,
        "missing": sorted(set(missing)),
    }
    if errors:
        result["errors"] = errors[:5]
    return result


def _load_selections(path: Path) -> list[dict[str, Any]]:
    value = _read_json(path)
    if not isinstance(value, list) or not 4 <= len(value) <= 5:
        raise ValidationError("选择 JSON 必须是包含 4–5 项的数组")
    if not all(isinstance(item, dict) for item in value):
        raise ValidationError("选择 JSON 的每一项必须是对象")
    return value


def _validate_selections(
    selections: list[dict[str, Any]],
    report_items: list[dict[str, Any]],
    candidate_by_repo: dict[str, dict[str, Any]],
    recent_repos: set[str],
) -> None:
    if len(selections) != len(report_items):
        raise ValidationError("选择数量与日报正式推荐数量不一致")
    seen: set[str] = set()
    for index, (selection, report_item) in enumerate(zip(selections, report_items)):
        repo = _norm_repo(selection.get("repo"))
        if repo not in candidate_by_repo:
            raise ValidationError(f"选择不在当日候选中：{selection.get('repo')}")
        if repo in seen:
            raise ValidationError(f"选择仓库重复：{repo}")
        seen.add(repo)
        if repo != report_item["repo_norm"]:
            raise ValidationError("选择顺序或仓库与日报不一致")
        if selection.get("slot") != report_item["slot"]:
            raise ValidationError("选择类型与日报不一致")
        if int(selection.get("score", -1)) != report_item["score"]:
            raise ValidationError("选择评分与日报不一致")
        if index < 4 and selection.get("slot") != EXPECTED_SLOTS[index]:
            raise ValidationError("前四类顺序错误")
        if selection.get("verified") is not True:
            raise ValidationError(f"候选尚未核验：{repo}")
        if not str(selection.get("reason", "")).strip():
            raise ValidationError(f"候选缺少推荐理由：{repo}")
        if not str(selection.get("activity", "")).strip():
            raise ValidationError(f"候选缺少近期活动：{repo}")
        sources = selection.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValidationError(f"候选缺少事实来源：{repo}")
        license_id = str(candidate_by_repo[repo].get("license") or "").upper()
        if license_id in {"", "NOASSERTION", "OTHER", "UNKNOWN"}:
            raise ValidationError(f"候选许可证不明确：{repo}")
        if repo in recent_repos and selection.get("repeat_exception") is not True:
            raise ValidationError(f"候选命中 90 天去重且没有重复例外：{repo}")
        if selection.get("repeat_exception") is True and not str(
            selection.get("repeat_reason", "")
        ).strip():
            raise ValidationError(f"重复例外缺少理由：{repo}")


def finalize_run(
    run_date: str,
    root: Path,
    draft_path: Path,
    selections_path: Path,
) -> dict[str, Any]:
    _parse_date(run_date)
    root = Path(root)
    try:
        draft = Path(draft_path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"无法读取日报草稿：{draft_path}") from exc
    report_items = validate_report(draft, run_date)
    candidates = _candidate_records(run_date, root)
    candidate_by_repo = {_norm_repo(item.get("repo")): item for item in candidates}
    selections = _load_selections(Path(selections_path))
    history_path = root / "history.jsonl"
    history = _read_jsonl(history_path)
    recent = set(_recent_repos(run_date, history))
    _validate_selections(selections, report_items, candidate_by_repo, recent)

    selection_by_repo = {_norm_repo(item["repo"]): item for item in selections}
    updated_candidates: list[dict[str, Any]] = []
    for original in candidates:
        record = dict(original)
        repo = _norm_repo(record.get("repo"))
        selected = selection_by_repo.get(repo)
        if selected:
            record["status"] = "primary"
            record["verified"] = True
            record["reason"] = selected["reason"]
            record["sources"] = sorted(
                set(record.get("sources") or []) | set(selected.get("sources") or [])
            )
        elif record.get("status") == "primary":
            record["status"] = "rejected"
            record["reason"] = "未进入本次最终推荐"
        updated_candidates.append(record)

    existing_today = {
        _norm_repo(item.get("repo")): item
        for item in history
        if item.get("date") == run_date and item.get("role", "primary") == "primary"
    }
    selected_repos = set(selection_by_repo)
    stale_today = sorted(set(existing_today) - selected_repos)
    if stale_today:
        raise ValidationError(f"同日 history 含不在本次选择中的仓库：{', '.join(stale_today)}")
    added = 0
    for selection in selections:
        repo = _norm_repo(selection["repo"])
        candidate = candidate_by_repo[repo]
        history_record = {
            "date": run_date,
            "repo": selection["repo"],
            "url": candidate.get("url") or f"https://github.com/{repo}",
            "slot": selection["slot"],
            "stars": candidate.get("stars"),
            "forks": candidate.get("forks"),
            "license": candidate.get("license"),
            "activity": selection["activity"],
            "score": selection["score"],
            "reason": selection["reason"],
            "role": "primary",
            "repeat_exception": bool(selection.get("repeat_exception", False)),
        }
        if selection.get("repeat_reason"):
            history_record["repeat_reason"] = selection["repeat_reason"]
        existing = existing_today.get(repo)
        if existing:
            for key in ("slot", "score", "role"):
                if existing.get(key) != history_record.get(key):
                    raise ValidationError(f"同日 history 冲突：{repo} 的 {key}")
            continue
        history.append(history_record)
        existing_today[repo] = history_record
        added += 1

    status_path = root / "trial-status.json"
    trial_status = _read_json(status_path, {})
    if not isinstance(trial_status, dict):
        raise ValidationError("trial-status.json 必须是 JSON 对象")
    summary = {
        "date": run_date,
        "status": "complete",
        "candidate_count": len(candidates),
        "primary_count": len(selections),
        "history_entries_added": added,
        "history_entries_after_append": len(history),
        "report": f"data/github-project-digest/daily/{run_date}.md",
        "checkpoint": f"data/github-project-digest/daily-runs/{run_date}.json",
        "checks": {
            "fixed_format": True,
            "candidate_jsonl": True,
            "history_jsonl": True,
            "dedupe_90d": True,
        },
    }
    trial_status[f"daily_run_{run_date}"] = summary
    trial_status["latest_daily_run"] = summary

    checkpoint_record = {
        "date": run_date,
        "stage": "complete",
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidateCount": len(candidates),
        "selectedCount": len(selections),
        "report": f"daily/{run_date}.md",
        "historyEntries": len(history),
        "feasibility": "complete"
        if (root / "feasibility" / f"{run_date}.md").exists()
        else "pending",
    }

    _stage_writes(
        [
            (root / "daily" / f"{run_date}.md", draft),
            (root / "candidates" / f"{run_date}.jsonl", _jsonl_text(updated_candidates)),
            (history_path, _jsonl_text(history)),
            (status_path, _json_text(trial_status)),
            (root / "daily-runs" / f"{run_date}.json", _json_text(checkpoint_record)),
        ]
    )
    result = inspect_run(run_date, root)
    if result["stage"] != "complete":
        raise RuntimeError(f"finalize 后对账失败：{result}")
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="输出紧凑恢复状态")
    inspect_parser.add_argument("date")
    inspect_parser.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
    finalize_parser = subparsers.add_parser("finalize", help="校验并幂等写入日报产物")
    finalize_parser.add_argument("date")
    finalize_parser.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
    finalize_parser.add_argument("--draft", type=Path, required=True)
    finalize_parser.add_argument("--selections", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect_run(args.date, args.data_root)
        else:
            result = finalize_run(args.date, args.data_root, args.draft, args.selections)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except ValidationError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
