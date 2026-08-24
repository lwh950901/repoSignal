#!/usr/bin/env bash
# 每天 08:30 由 launchd 触发：生成"业务可行性方案"（今日锚点 + 近 90 天组合）。
# 输入：当天日报（无则最近一份）+ 近 90 天全部日报/周报；输出：data/github-project-digest/feasibility/
# 日志：data/.opportunity-analysis.log
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/data/.opportunity-analysis.log"
mkdir -p "$(dirname "$LOG")"

cd "$REPO"
trap 'echo "$(date "+%F %T") FAIL: 分析生成失败 (exit $?)" >> "$LOG"' ERR

python3 scripts/opportunity_analysis.py
echo "$(date "+%F %T") OK: 分析已生成" >> "$LOG"
