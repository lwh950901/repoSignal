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
BLOCKED_BURST_SLOTS = ["实用型", "潜力型", "学习型", "可复用型"]
BURST_BLOCKED_MARKER = "爆发型位置阻塞"
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
    r"^### (?P<number>\d+)\. (?P<slot>爆发型|实用型|潜力型|学习型|可复用型)："
    r"(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+) — (?P<score>\d{1,3})/100$",
    re.MULTILINE,
)


class ValidationError(ValueError):
    """Raised when finalization inputs violate the daily digest contract."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return _utc_now()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"时间必须为 ISO-8601：{value}") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"时间必须包含时区：{value}")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValidationError("运行时间必须包含时区")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def _checkpoint_path(run_date: str, root: Path) -> Path:
    return Path(root) / "daily-runs" / f"{run_date}.json"


def start_run(run_date: str, root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    """Create an idempotent 90-minute runtime checkpoint."""
    _parse_date(run_date)
    root = Path(root)
    current = _read_json(_checkpoint_path(run_date, root), {})
    if not isinstance(current, dict):
        raise ValidationError("运行检查点必须是 JSON 对象")
    moment = now or _utc_now()
    if moment.tzinfo is None:
        raise ValidationError("运行时间必须包含时区")
    started = _parse_datetime(current.get("startedAt")) if current.get("startedAt") else moment
    stage = current.get("stage") or inspect_run(run_date, root)["stage"]
    record = dict(current)
    record.update(
        {
            "date": run_date,
            "stage": stage,
            "startedAt": _iso(started),
            "lastProgressAt": current.get("lastProgressAt") or _iso(started),
            "deadlineAt": current.get("deadlineAt") or _iso(started + timedelta(minutes=90)),
            "updatedAt": _iso(moment),
            "attempt": max(1, int(current.get("attempt", 1) or 1)),
            "candidateCount": int(current.get("candidateCount", 0) or 0),
            "verifiedCount": int(current.get("verifiedCount", 0) or 0),
            "errors": list(current.get("errors") or [])[-5:],
        }
    )
    _stage_writes([(_checkpoint_path(run_date, root), _json_text(record))])
    return record


def resume_run(run_date: str, root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    """Explicitly start a fresh manual budget while preserving resumable progress."""
    _parse_date(run_date)
    root = Path(root)
    current = _read_json(_checkpoint_path(run_date, root), None)
    if not isinstance(current, dict):
        raise ValidationError("没有可人工续跑的检查点")
    if current.get("stage") == "complete":
        raise ValidationError("日报已经完成，无需人工续跑")
    moment = now or _utc_now()
    if moment.tzinfo is None:
        raise ValidationError("运行时间必须包含时区")
    record = dict(current)
    record.update(
        {
            "date": run_date,
            "startedAt": _iso(moment),
            "lastProgressAt": _iso(moment),
            "deadlineAt": _iso(moment + timedelta(minutes=90)),
            "updatedAt": _iso(moment),
            "attempt": max(1, int(current.get("attempt", 1) or 1)) + 1,
            "previousStartedAt": current.get("startedAt"),
            "errors": list(current.get("errors") or [])[-5:],
        }
    )
    _stage_writes([(_checkpoint_path(run_date, root), _json_text(record))])
    return record


def record_progress(
    run_date: str,
    root: Path,
    stage: str,
    *,
    now: datetime | None = None,
    candidate_count: int | None = None,
    verified_count: int | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Record one meaningful stage change without growing an unbounded log."""
    moment = now or _utc_now()
    record = start_run(run_date, root, now=moment)
    record["stage"] = stage
    record["lastProgressAt"] = _iso(moment)
    record["updatedAt"] = _iso(moment)
    if candidate_count is not None:
        record["candidateCount"] = max(0, int(candidate_count))
    if verified_count is not None:
        record["verifiedCount"] = max(0, int(verified_count))
    if error:
        record["errors"] = (list(record.get("errors") or []) + [str(error)])[-5:]
    _stage_writes([(_checkpoint_path(run_date, root), _json_text(record))])
    return record


def audit_run(run_date: str, root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    """Return the deterministic action for the current runtime boundary."""
    moment = now or _utc_now()
    record = start_run(run_date, root, now=moment)
    started = _parse_datetime(str(record["startedAt"]))
    last_progress = _parse_datetime(str(record["lastProgressAt"]))
    elapsed = max(0, int((moment - started).total_seconds() // 60))
    stalled_minutes = max(0, (moment - last_progress).total_seconds() / 60)
    if record.get("stage") == "complete":
        action = "complete"
    elif elapsed >= 90:
        action = "stop"
    elif elapsed >= 85:
        action = "finalize_now"
    elif elapsed >= 60:
        action = "start_report"
    elif elapsed >= 30:
        action = "stop_discovery"
    else:
        action = "continue_discovery"
    return {
        "date": run_date,
        "stage": record.get("stage"),
        "action": action,
        "elapsedMinutes": elapsed,
        "remainingMinutes": max(0, 90 - elapsed),
        "stalled": record.get("stage") != "complete" and stalled_minutes >= 15,
        "candidateCount": record.get("candidateCount", 0),
        "verifiedCount": record.get("verifiedCount", 0),
        "errors": list(record.get("errors") or [])[-5:],
    }


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
    for heading in re.findall(r"^###\s+.*$", section, re.MULTILINE):
        if not HEADING_RE.fullmatch(heading):
            raise ValidationError(
                f"主推荐标题格式错误：{heading}；应为 ### 1. 类型：owner/repo — 85/100"
            )
    matches = list(HEADING_RE.finditer(section))
    if not 4 <= len(matches) <= 5:
        raise ValidationError(f"正式推荐数量必须为 4–5，实际识别 {len(matches)} 项")

    slots = [match.group("slot") for match in matches]
    if BURST_BLOCKED_MARKER in text:
        if slots != BLOCKED_BURST_SLOTS:
            raise ValidationError("爆发型位置阻塞时，推荐顺序必须为实用型、潜力型、学习型、可复用型")
    elif slots != EXPECTED_SLOTS[: len(slots)] + (["可复用型"] if len(slots) == 5 else []):
        raise ValidationError("前四类顺序必须为爆发型、实用型、潜力型、学习型")

    parsed: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        expected_number = index + 1
        if int(match.group("number")) != expected_number:
            raise ValidationError("正式推荐序号必须连续")
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


def _validated_inputs(
    run_date: str, root: Path, draft_path: Path, selections_path: Path,
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Shared read-only validation for preflight and finalization."""
    _parse_date(run_date)
    try:
        draft = Path(draft_path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"无法读取日报草稿：{draft_path}") from exc
    report_items = validate_report(draft, run_date)
    candidates = _candidate_records(run_date, root)
    candidate_by_repo = {_norm_repo(item.get("repo")): item for item in candidates}
    selections = _load_selections(Path(selections_path))
    history = _read_jsonl(root / "history.jsonl")
    _validate_selections(
        selections, report_items, candidate_by_repo, set(_recent_repos(run_date, history))
    )
    return draft, candidates, selections, history


def preflight_run(
    run_date: str, root: Path, draft_path: Path, selections_path: Path,
) -> dict[str, Any]:
    """Validate report, selections, candidates and deduplication without writing."""
    _, candidates, selections, _ = _validated_inputs(
        run_date, Path(root), draft_path, selections_path
    )
    return {"date": run_date, "status": "valid", "candidateCount": len(candidates),
            "selectedCount": len(selections)}


def finalize_run(
    run_date: str,
    root: Path,
    draft_path: Path,
    selections_path: Path,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    _parse_date(run_date)
    root = Path(root)
    completed_at = now or _utc_now()
    runtime_checkpoint = _read_json(_checkpoint_path(run_date, root), {})
    if isinstance(runtime_checkpoint, dict) and runtime_checkpoint.get("deadlineAt"):
        deadline = _parse_datetime(str(runtime_checkpoint["deadlineAt"]))
        if runtime_checkpoint.get("stage") != "complete" and completed_at >= deadline:
            raise ValidationError("90 分钟运行预算已到，禁止 finalize；请人工 resume 后续跑")
    draft, candidates, selections, history = _validated_inputs(
        run_date, root, draft_path, selections_path
    )
    candidate_by_repo = {_norm_repo(item.get("repo")): item for item in candidates}
    history_path = root / "history.jsonl"

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

    existing_checkpoint = _read_json(_checkpoint_path(run_date, root), {})
    if not isinstance(existing_checkpoint, dict):
        raise ValidationError("运行检查点必须是 JSON 对象")
    checkpoint_record = dict(existing_checkpoint)
    checkpoint_record.update({
        "date": run_date,
        "stage": "complete",
        "updatedAt": _iso(completed_at),
        "lastProgressAt": _iso(completed_at),
        "candidateCount": len(candidates),
        "verifiedCount": len(selections),
        "selectedCount": len(selections),
        "report": f"daily/{run_date}.md",
        "historyEntries": len(history),
    })

    _stage_writes(
        [
            (root / "daily" / f"{run_date}.md", draft),
            (root / "candidates" / f"{run_date}.jsonl", _jsonl_text(updated_candidates)),
            (history_path, _jsonl_text(history)),
            (status_path, _json_text(trial_status)),
            (_checkpoint_path(run_date, root), _json_text(checkpoint_record)),
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
    start_parser = subparsers.add_parser("start", help="创建或恢复 90 分钟运行预算")
    start_parser.add_argument("date")
    start_parser.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
    start_parser.add_argument("--now", help="用于测试的 ISO-8601 时间")
    resume_parser = subparsers.add_parser("resume", help="人工开启新的 90 分钟续跑预算")
    resume_parser.add_argument("date")
    resume_parser.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
    resume_parser.add_argument("--now", help="用于测试的 ISO-8601 时间")
    progress_parser = subparsers.add_parser("progress", help="记录有意义的阶段进度")
    progress_parser.add_argument("date")
    progress_parser.add_argument("stage")
    progress_parser.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
    progress_parser.add_argument("--now", help="用于测试的 ISO-8601 时间")
    progress_parser.add_argument("--candidate-count", type=int)
    progress_parser.add_argument("--verified-count", type=int)
    progress_parser.add_argument("--error")
    audit_parser = subparsers.add_parser("audit", help="输出当前时间预算动作")
    audit_parser.add_argument("date")
    audit_parser.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
    audit_parser.add_argument("--now", help="用于测试的 ISO-8601 时间")
    for name, help_text in (("preflight", "只读检查草稿、选择、候选归属与去重"),
                            ("finalize", "校验并幂等写入日报产物")):
        input_parser = subparsers.add_parser(name, help=help_text)
        input_parser.add_argument("date")
        input_parser.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
        input_parser.add_argument("--draft", type=Path, required=True)
        input_parser.add_argument("--selections", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect_run(args.date, args.data_root)
        elif args.command == "start":
            result = start_run(args.date, args.data_root, now=_parse_datetime(args.now))
        elif args.command == "resume":
            result = resume_run(args.date, args.data_root, now=_parse_datetime(args.now))
        elif args.command == "progress":
            result = record_progress(
                args.date,
                args.data_root,
                args.stage,
                now=_parse_datetime(args.now),
                candidate_count=args.candidate_count,
                verified_count=args.verified_count,
                error=args.error,
            )
        elif args.command == "audit":
            result = audit_run(args.date, args.data_root, now=_parse_datetime(args.now))
        elif args.command == "preflight":
            result = preflight_run(args.date, args.data_root, args.draft, args.selections)
        else:
            result = finalize_run(args.date, args.data_root, args.draft, args.selections)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except ValidationError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
