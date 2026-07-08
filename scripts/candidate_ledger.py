#!/usr/bin/env python3
"""candidate_ledger.py — 候选账本工具

读取扫描器输出的 JSON 数组，规范化去重仓库，
保留发现通道和来源，原子写入日期键 JSONL 文件。

用法:
  python3 candidate_ledger.py <date> <scanner_json>... [-o <candidates_dir>]

自检:
  python3 candidate_ledger.py --check
"""

import json
import os
import sys
import tempfile
from pathlib import Path

RECORD_FIELDS = [
    "date", "repo", "url", "lanes", "sources",
    "stars", "forks", "license", "archived", "pushed",
    "status", "verified", "reason",
]


def parse_scanner_input(paths):
    """读取一个或多个扫描器 JSON 文件，返回 repo 对象列表."""
    items = []
    seen = set()
    for p in paths:
        raw = Path(p).read_text(encoding="utf-8").strip()
        if not raw:
            continue
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise ValueError(f"{p} 不是 JSON 数组")
        for item in data:
            if not isinstance(item, dict):
                raise ValueError(f"{p} 包含非对象元素")
            repo = item.get("full_name") or item.get("repo") or item.get("name") or ""
            repo_norm = repo.lower().strip()
            if repo_norm and repo_norm not in seen:
                seen.add(repo_norm)
                items.append(item)
    return items


def normalize_repo(raw_repo):
    """规范化仓库名为小写 owner/repo."""
    r = (raw_repo or "").strip()
    if not r:
        return ""
    return r.lower()


def build_record(item, date, lane, source):
    """从扫描器条目构建候选记录."""
    repo = normalize_repo(
        item.get("full_name") or item.get("repo") or item.get("name") or ""
    )
    if not repo:
        return None
    return {
        "date": date,
        "repo": repo,
        "url": item.get("html_url")
               or item.get("url")
               or f"https://github.com/{repo}",
        "lanes": [lane],
        "sources": [source],
        "stars": item.get("stargazers_count") or item.get("stars"),
        "forks": item.get("forks_count") or item.get("forks"),
        "license": _get_license(item),
        "archived": item.get("archived", False),
        "pushed": item.get("pushed_at") or item.get("pushed"),
        "status": "discovered",
        "verified": False,
        "reason": None,
    }


def _get_license(item):
    """从扫描器条目提取许可证字符串."""
    lic = item.get("license")
    if isinstance(lic, dict):
        return lic.get("spdx_id") or lic.get("key") or lic.get("name")
    return lic


def merge_lanes(existing, new_lane, new_source):
    """合并通道和来源，去重后排序."""
    if new_lane not in existing["lanes"]:
        existing["lanes"].append(new_lane)
    if new_source not in existing["sources"]:
        existing["sources"].append(new_source)
    existing["lanes"].sort()
    existing["sources"].sort()
    return existing


def merge_record(existing, item, lane, source):
    """合并重复仓库记录，使用与 build_record 相同的字段提取逻辑."""
    existing["lanes"] = sorted(set(existing["lanes"] + [lane]))
    existing["sources"] = sorted(set(existing["sources"] + [source]))
    # 使用与 build_record 相同的字段提取
    for key, src_key in [
        ("stars", "stargazers_count"), ("stars", "stars"),
        ("forks", "forks_count"), ("forks", "forks"),
        ("archived", "archived"),
        ("pushed", "pushed_at"), ("pushed", "pushed"),
    ]:
        val = item.get(src_key)
        if val is not None:
            existing[key] = val
    # 结构化许可证提取
    lic_val = _get_license(item)
    if lic_val is not None:
        existing["license"] = lic_val
    # url 可用时覆盖
    url_val = item.get("html_url") or item.get("url")
    if url_val:
        existing["url"] = url_val
    return existing


def build_ledger(scanner_paths, date, lanes=None, sources=None):
    """构建去重后的候选列表."""
    if lanes is None:
        lanes = [f"lane-{i}" for i in range(len(scanner_paths))]
    if sources is None:
        sources = ["scanner"] * len(scanner_paths)

    records = {}
    for path, lane, source in zip(scanner_paths, lanes, sources):
        items = parse_scanner_input([path])
        for item in items:
            repo = normalize_repo(
                item.get("full_name") or item.get("repo") or item.get("name") or ""
            )
            if not repo:
                continue
            if repo in records:
                merge_record(records[repo], item, lane, source)
            else:
                rec = build_record(item, date, lane, source)
                if rec:
                    records[repo] = rec

    # 按仓库名确定性排序
    result = sorted(records.values(), key=lambda r: r["repo"])
    return result


def write_ledger(records, output_path):
    """原子写入 JSONL 文件."""
    lines = "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records)
    if lines:
        lines += "\n"
    tmp = Path(output_path).with_suffix(".tmp")
    tmp.write_text(lines, encoding="utf-8")
    os.replace(tmp, output_path)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--check":
        return self_check()

    if len(sys.argv) < 3:
        print("用法: python3 candidate_ledger.py <date> <scanner_json>... [-o <dir>] [--lane <name>]... [--source <name>]...", file=sys.stderr)
        sys.exit(1)

    date = sys.argv[1]
    args = sys.argv[2:]

    out_dir = Path("data/github-project-digest/candidates")
    lanes = []
    sources = []

    # 解析命名参数
    positional = []
    skip_next = False
    for i, a in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if a == "-o" and i + 1 < len(args):
            out_dir = Path(args[i + 1])
            skip_next = True
        elif a == "--lane" and i + 1 < len(args):
            lanes.append(args[i + 1])
            skip_next = True
        elif a == "--source" and i + 1 < len(args):
            sources.append(args[i + 1])
            skip_next = True
        elif not a.startswith("-"):
            positional.append(a)

    scanner_paths = positional
    if not scanner_paths:
        print("错误: 未提供扫描器 JSON 文件", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"{date}.jsonl"

    if output.exists():
        print(f"错误: {output} 已存在", file=sys.stderr)
        sys.exit(1)

    # 如果未提供 lanes/sources，使用文件名推测
    if not lanes:
        lanes = [Path(p).stem for p in scanner_paths]
    if not sources:
        sources = lanes[:]
    # 补齐到与 scanner_paths 同长
    while len(lanes) < len(scanner_paths):
        lanes.append(f"lane-{len(lanes)}")
    while len(sources) < len(scanner_paths):
        sources.append("scanner")

    records = build_ledger(scanner_paths, date, lanes=lanes, sources=sources)
    write_ledger(records, output)
    print(f"已写入 {len(records)} 条候选记录到 {output}")


# ── 自检 ──────────────────────────────────────────────────


def self_check():
    """运行自检，退出码 0 表示全部通过."""
    errors = []

    # 1. 大小写去重
    json1 = json.dumps([
        {"full_name": "Owner/Repo", "html_url": "https://github.com/Owner/Repo"},
        {"full_name": "owner/repo", "html_url": "https://github.com/owner/repo"},
        {"full_name": "other/project", "html_url": "https://github.com/other/project"},
    ])
    json2 = json.dumps([
        {"full_name": "OWNER/REPO", "html_url": "https://github.com/OWNER/REPO"},
    ])
    p1 = Path(tempfile.mkstemp(suffix=".json")[1])
    p2 = Path(tempfile.mkstemp(suffix=".json")[1])
    p1.write_text(json1)
    p2.write_text(json2)

    records = build_ledger([str(p1), str(p2)], "2026-07-08",
                           lanes=["test-growth", "test-mature"],
                           sources=["check-1", "check-2"])
    # 应去重为 2 条: owner/repo, other/project
    repos = [r["repo"] for r in records]
    if len(records) != 2:
        errors.append(f"去重失败: 期望 2 条, 得到 {len(records)}")
    if "owner/repo" not in repos:
        errors.append("去重失败: owner/repo 缺失")
    if "other/project" not in repos:
        errors.append("去重失败: other/project 缺失")

    # 验证通道合并
    owner_rec = next(r for r in records if r["repo"] == "owner/repo")
    if len(owner_rec["lanes"]) != 2:
        errors.append(f"通道合并失败: 期望 2 个, 得到 {len(owner_rec['lanes'])}")
    if len(owner_rec["sources"]) != 2:
        errors.append(f"来源合并失败: 期望 2 个, 得到 {len(owner_rec['sources'])}")

    p1.unlink()
    p2.unlink()

    # 2. 必需字段完整性
    required = {"date", "repo", "url", "lanes", "sources", "status", "verified"}
    for r in records:
        missing = required - set(r.keys())
        if missing:
            errors.append(f"{r['repo']} 缺少字段: {missing}")

    # 3. 确定性顺序
    sorted_repos = sorted(repos)
    if repos != sorted_repos:
        errors.append("输出顺序不是确定性的")

    # 4. 非法输入保护
    tmp3 = Path(tempfile.mkstemp(suffix=".json")[1])
    tmp3.write_text("not json")
    try:
        parse_scanner_input([str(tmp3)])
        errors.append("非法 JSON 应抛出异常但未抛出")
    except (json.JSONDecodeError, ValueError):
        pass
    tmp3.unlink()

    # 5. 重复观测字段覆盖（回归）
    # 第一条有旧数据，第二条有更新后的 stargazers_count 和结构化 license
    j_old = json.dumps([
        {"full_name": "test/regression", "html_url": "https://github.com/test/regression",
         "stars": 100, "stargazers_count": None, "license": "MIT"}
    ])
    j_new = json.dumps([
        {"full_name": "test/regression", "html_url": "https://github.com/test/regression",
         "stargazers_count": 200, "forks_count": 50,
         "license": {"spdx_id": "Apache-2.0", "key": "apache-2.0"},
         "pushed_at": "2026-07-08T00:00:00Z"}
    ])
    p4 = Path(tempfile.mkstemp(suffix=".json")[1])
    p5 = Path(tempfile.mkstemp(suffix=".json")[1])
    p4.write_text(j_old)
    p5.write_text(j_new)
    recs = build_ledger([str(p4), str(p5)], "2026-07-08")
    p4.unlink()
    p5.unlink()
    if len(recs) != 1:
        errors.append(f"回归去重失败: 期望 1 条, 得到 {len(recs)}")
    else:
        r = recs[0]
        if r["stars"] != 200:
            errors.append(f"回归字段覆盖失败: stars 应为 200, 得到 {r['stars']}")
        if r["forks"] != 50:
            errors.append(f"回归字段覆盖失败: forks 应为 50, 得到 {r['forks']}")
        if r.get("license") != "Apache-2.0":
            errors.append(f"回归结构化许可失败: license 应为 Apache-2.0, 得到 {r.get('license')}")
        if r.get("pushed") != "2026-07-08T00:00:00Z":
            errors.append(f"回归 pushed_at 覆盖失败: 得到 {r.get('pushed')}")

    if errors:
        print("自检失败:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print("自检通过: 去重/字段/顺序/非法输入均正常")
        sys.exit(0)


if __name__ == "__main__":
    main()
