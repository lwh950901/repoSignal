#!/usr/bin/env python3
"""Bounded discovery and compact pre-screening for the GitHub daily digest."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from scripts import candidate_ledger
    from scripts import daily_digest_checkpoint as checkpoint
except ModuleNotFoundError:  # Allow direct execution from scripts/.
    import candidate_ledger
    import daily_digest_checkpoint as checkpoint


SLOT_LANES = {
    "爆发型": {"growth", "user_candidate"},
    "实用型": {"mature", "developer_tools", "cross_domain"},
    "潜力型": {"emerging", "cross_domain", "developer_tools"},
    "学习型": {"learning_rag"},
}
UNCLEAR_LICENSES = {"", "NOASSERTION", "OTHER", "UNKNOWN", "NONE"}
DISCOVERY_QUERIES = {
    "growth": "agent workflow stars:>5000 pushed:>={recent60} archived:false",
    "mature": "self-hosted automation stars:>1000 pushed:>={recent90} archived:false",
    "emerging": "AI application created:>={recent60} stars:>200 archived:false",
    "learning_rag": "RAG learning agent pushed:>={recent180} archived:false",
    "developer_tools": "developer tool AI pushed:>={recent90} archived:false",
    "cross_domain": "robotics edge AI pushed:>={recent90} archived:false",
}
DEFAULT_SCANNER = (
    Path.home()
    / ".codex"
    / "skills"
    / "find-github-projects"
    / "scripts"
    / "github_project_scan.py"
)
OUTPUT_FIELDS = (
    "repo",
    "url",
    "description",
    "language",
    "topics",
    "created",
    "updated",
    "stars",
    "forks",
    "license",
    "pushed",
    "lanes",
    "sources",
    "homepage",
    "openIssues",
    "riskFlags",
    "scoreHint",
    "readmeSignal",
    "latestRelease",
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        item = json.loads(raw)
        if not isinstance(item, dict):
            raise ValueError(f"{path} 第 {number} 行不是对象")
        records.append(item)
    return records


def _repo(value: Any) -> str:
    return str(value or "").strip().lower()


def _pending_user_candidates(root: Path) -> list[str]:
    pending: set[str] = set()
    for item in _read_jsonl(root / "feedback.jsonl"):
        if str(item.get("status", "")).lower() in {"rejected", "done", "processed", "resolved"}:
            continue
        repo = _repo(item.get("repo") or item.get("repository"))
        if "/" in repo:
            pending.add(repo)
    return sorted(pending)[:20]


def _recent_repos(run_date: str, root: Path) -> set[str]:
    end = date.fromisoformat(run_date)
    start = end - timedelta(days=90)
    recent: set[str] = set()
    for item in _read_jsonl(root / "history.jsonl"):
        try:
            observed = date.fromisoformat(str(item.get("date", "")))
        except ValueError:
            continue
        repo = _repo(item.get("repo"))
        if start <= observed < end and repo:
            recent.add(repo)
    return recent


def _timestamp(value: Any) -> float:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except ValueError:
        return 0.0


def _ranking_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(item.get("status") == "primary" and item.get("verified") is True),
        -int(bool(item.get("_userPriority"))),
        -int(item.get("scoreHint") or 0),
        -int(item.get("stars") or 0),
        -int(item.get("forks") or 0),
        -_timestamp(item.get("pushed") or item.get("updated")),
        str(item.get("repo") or ""),
    )


def _compact_candidate(item: dict[str, Any], *, repeated: bool) -> dict[str, Any]:
    compact = {
        field: item.get(field)
        for field in OUTPUT_FIELDS
        if item.get(field) not in (None, "", [], {})
    }
    compact["description"] = str(compact.get("description") or "")[:240]
    compact["topics"] = list(compact.get("topics") or [])[:8]
    compact["lanes"] = sorted(set(compact.get("lanes") or []))
    compact["sources"] = sorted(set(compact.get("sources") or []))
    compact["repeatRequiresEvidence"] = repeated
    return compact


def build_shortlist(run_date: str, data_root: Path) -> dict[str, Any]:
    """Apply deterministic hard filters and retain at most three options per slot."""
    date.fromisoformat(run_date)
    root = Path(data_root)
    candidates = _read_jsonl(root / "candidates" / f"{run_date}.jsonl")
    if not candidates:
        raise ValueError(f"缺少有效候选：{run_date}")
    user_candidates = _pending_user_candidates(root)
    user_set = set(user_candidates)
    recent = _recent_repos(run_date, root)
    rejected = {"archived": 0, "unclearLicense": 0, "recentDuplicate": 0}
    accepted: list[dict[str, Any]] = []

    for item in candidates:
        repo = _repo(item.get("repo"))
        if item.get("archived") is True:
            rejected["archived"] += 1
            continue
        if str(item.get("license") or "").upper() in UNCLEAR_LICENSES:
            rejected["unclearLicense"] += 1
            continue
        repeated = repo in recent
        is_user_candidate = repo in user_set or "user_candidate" in (item.get("lanes") or [])
        if repeated and not is_user_candidate:
            rejected["recentDuplicate"] += 1
            continue
        record = dict(item)
        record["repo"] = repo
        record["repeatRequiresEvidence"] = repeated
        record["_userPriority"] = is_user_candidate
        accepted.append(record)

    slots: dict[str, list[dict[str, Any]]] = {}
    for slot, allowed_lanes in SLOT_LANES.items():
        eligible = []
        for item in accepted:
            lanes = set(item.get("lanes") or [])
            repo = _repo(item.get("repo"))
            if repo in user_set:
                lanes.add("user_candidate")
            if not lanes & allowed_lanes:
                continue
            if slot == "爆发型" and int(item.get("stars") or 0) < 5000:
                continue
            eligible.append(item)
        slots[slot] = [
            _compact_candidate(item, repeated=bool(item.get("repeatRequiresEvidence")))
            for item in sorted(eligible, key=_ranking_key)[:3]
        ]

    return {
        "date": run_date,
        "candidateCount": len(candidates),
        "eligibleCount": len(accepted),
        "slots": slots,
        "userCandidates": user_candidates,
        "rejected": rejected,
    }


def _query_values(run_date: str) -> dict[str, str]:
    current = date.fromisoformat(run_date)
    return {
        "recent60": (current - timedelta(days=60)).isoformat(),
        "recent90": (current - timedelta(days=90)).isoformat(),
        "recent180": (current - timedelta(days=180)).isoformat(),
    }


def _tls_error(message: str) -> bool:
    lowered = message.lower()
    return any(
        marker in lowered
        for marker in (
            "certificate verify failed",
            "certificate_verify_failed",
            "ssl certificate",
            "tls certificate",
        )
    )


def _run_scanner(
    scanner: Path,
    query: str,
    *,
    timeout_seconds: float,
    env: dict[str, str] | None,
    insecure: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(scanner),
        "--query",
        query,
        "--limit",
        "12",
        "--format",
        "json",
        "--no-cache",
    ]
    if insecure:
        command.append("--insecure")
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=max(1.0, timeout_seconds),
        env=env,
        check=False,
    )


def _discover_lane(
    lane: str,
    query: str,
    scanner: Path,
    timeout_seconds: float,
    env: dict[str, str] | None,
    deadline: datetime,
) -> dict[str, Any]:
    first_timeout = min(
        timeout_seconds, (deadline - datetime.now(timezone.utc)).total_seconds()
    )
    if first_timeout <= 0:
        return {"lane": lane, "items": [], "error": "deadline reached before scanner"}
    try:
        first = _run_scanner(
            scanner, query, timeout_seconds=first_timeout, env=env, insecure=False
        )
    except subprocess.TimeoutExpired:
        return {"lane": lane, "items": [], "error": "scanner timeout"}
    result = first
    if first.returncode != 0 and _tls_error(first.stderr):
        retry_timeout = min(
            timeout_seconds, (deadline - datetime.now(timezone.utc)).total_seconds()
        )
        if retry_timeout <= 0:
            return {"lane": lane, "items": [], "error": "deadline reached before TLS retry"}
        try:
            result = _run_scanner(
                scanner, query, timeout_seconds=retry_timeout, env=env, insecure=True
            )
        except subprocess.TimeoutExpired:
            return {"lane": lane, "items": [], "error": "TLS retry timeout"}
    if result.returncode != 0:
        message = (result.stderr or result.stdout or f"exit {result.returncode}").strip()
        return {"lane": lane, "items": [], "error": message[:240]}
    try:
        items = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"lane": lane, "items": [], "error": "scanner returned invalid JSON"}
    if not isinstance(items, list):
        return {"lane": lane, "items": [], "error": "scanner JSON is not an array"}
    return {"lane": lane, "items": items, "error": None}


def discover(
    run_date: str,
    data_root: Path,
    scanner_path: Path = DEFAULT_SCANNER,
    *,
    env: dict[str, str] | None = None,
    timeout_seconds: float = 300,
) -> dict[str, Any]:
    """Run exactly six bounded search lanes and atomically create the daily ledger."""
    date.fromisoformat(run_date)
    root = Path(data_root)
    output = root / "candidates" / f"{run_date}.jsonl"
    if output.exists():
        raise FileExistsError(f"候选账本已存在，拒绝覆盖：{output}")
    scanner = Path(scanner_path)
    if not scanner.is_file():
        raise FileNotFoundError(f"扫描器不存在：{scanner}")

    runtime = checkpoint.start_run(run_date, root)
    deadline = datetime.fromisoformat(str(runtime["deadlineAt"]).replace("Z", "+00:00"))
    remaining_seconds = (deadline - datetime.now(timezone.utc)).total_seconds()
    if remaining_seconds <= 0:
        raise RuntimeError("90 分钟截止时间已到，禁止开始发现")
    per_lane_timeout = max(1.0, min(float(timeout_seconds), remaining_seconds))
    values = _query_values(run_date)
    queries = {
        lane: template.format(**values) for lane, template in DISCOVERY_QUERIES.items()
    }

    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=len(queries)) as executor:
        futures = {
            executor.submit(
                _discover_lane, lane, query, scanner, per_lane_timeout, env, deadline
            ): lane
            for lane, query in queries.items()
        }
        for future in as_completed(futures):
            lane = futures[future]
            try:
                results[lane] = future.result()
            except Exception as exc:  # Keep other successful lanes usable.
                results[lane] = {"lane": lane, "items": [], "error": str(exc)[:240]}

    successes = [results[lane] for lane in DISCOVERY_QUERIES if results[lane]["items"]]
    errors = [
        {"lane": lane, "error": results[lane]["error"]}
        for lane in DISCOVERY_QUERIES
        if results[lane]["error"]
    ]
    for item in errors:
        checkpoint.record_progress(
            run_date, root, "discovery", error=f"{item['lane']}: {item['error']}"
        )
    if not successes:
        checkpoint.record_progress(run_date, root, "discovery_failed")
        raise RuntimeError("六路 GitHub 发现全部失败")
    if output.exists():
        raise FileExistsError(f"候选账本已存在，拒绝覆盖：{output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="daily-discovery-") as temporary_dir:
        paths: list[str] = []
        lanes: list[str] = []
        for result in successes:
            path = Path(temporary_dir) / f"{result['lane']}.json"
            path.write_text(json.dumps(result["items"], ensure_ascii=False), encoding="utf-8")
            paths.append(str(path))
            lanes.append(result["lane"])
        records = candidate_ledger.build_ledger(
            paths,
            run_date,
            lanes=lanes,
            sources=["github-search"] * len(paths),
        )
    if not records:
        checkpoint.record_progress(run_date, root, "discovery_failed", error="no repositories")
        raise RuntimeError("发现成功但未返回有效仓库")
    candidate_ledger.write_ledger(records, output)
    status = "complete" if len(successes) == len(DISCOVERY_QUERIES) else "partial"
    checkpoint.record_progress(
        run_date,
        root,
        "candidates_ready",
        candidate_count=len(records),
    )
    return {
        "date": run_date,
        "status": status,
        "successfulLanes": len(successes),
        "candidateCount": len(records),
        "errors": errors[:5],
    }


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    discover_parser = subparsers.add_parser("discover", help="并发执行六路受限 GitHub 搜索")
    discover_parser.add_argument("date")
    discover_parser.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
    discover_parser.add_argument("--scanner", type=Path, default=DEFAULT_SCANNER)
    discover_parser.add_argument("--timeout-seconds", type=float, default=300)
    shortlist = subparsers.add_parser("shortlist", help="生成紧凑的四类候选预筛")
    shortlist.add_argument("date")
    shortlist.add_argument("--data-root", type=Path, default=Path("data/github-project-digest"))
    shortlist.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        rendered_result: dict[str, Any]
        if args.command == "discover":
            result = discover(
                args.date,
                args.data_root,
                args.scanner,
                timeout_seconds=args.timeout_seconds,
            )
            rendered_result = result
        else:
            audit = checkpoint.audit_run(args.date, args.data_root)
            if audit["action"] == "stop":
                raise RuntimeError("90 分钟运行预算已到，禁止生成短名单；请人工 resume")
            result = build_shortlist(args.date, args.data_root)
            if args.output:
                _atomic_json(args.output, result)
            checkpoint.record_progress(
                args.date,
                args.data_root,
                "shortlist_ready",
                candidate_count=result["candidateCount"],
            )
            rendered_result = result
            if args.output:
                rendered_result = {
                    "date": result["date"],
                    "candidateCount": result["candidateCount"],
                    "eligibleCount": result["eligibleCount"],
                    "slotCounts": {
                        slot: len(items) for slot, items in result["slots"].items()
                    },
                    "userCandidateCount": len(result["userCandidates"]),
                    "rejected": result["rejected"],
                    "output": str(args.output),
                }
        print(json.dumps(rendered_result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError, checkpoint.ValidationError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
