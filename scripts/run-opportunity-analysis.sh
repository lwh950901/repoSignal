#!/usr/bin/env bash
# 每天 08:30 由 launchd 触发：生成"业务可行性方案"（今日锚点 + 近 90 天组合）。
# 输入：当天日报 + 近 90 天全部日报/周报（当天无日报则跳过，不生成方案）；输出：data/github-project-digest/feasibility/
# 日志：data/.opportunity-analysis.log
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/data/.opportunity-analysis.log"
mkdir -p "$(dirname "$LOG")"

cd "$REPO"
trap 'echo "$(date "+%F %T") FAIL: 分析生成失败 (exit $?)" >> "$LOG"' ERR

if python3 scripts/opportunity_analysis.py; then
  echo "$(date "+%F %T") OK: 分析已生成" >> "$LOG"
else
  code=$?
  if [ "$code" -eq 2 ]; then
    echo "$(date "+%F %T") SKIP: 当天无日报，未执行可行性分析" >> "$LOG"
  else
    echo "$(date "+%F %T") FAIL: 分析生成失败 (exit $code)" >> "$LOG"
    exit "$code"
  fi
fi
