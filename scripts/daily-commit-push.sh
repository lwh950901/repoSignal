#!/usr/bin/env bash
# 每天 07:30 由 launchd 触发：暂存仓库全部改动并推送到 origin。
# 无改动时跳过；结果写入日志。日志：data/.daily-commit-push.log
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/data/.daily-commit-push.log"
mkdir -p "$(dirname "$LOG")"

cd "$REPO"
trap 'echo "$(date "+%F %T") FAIL: 提交或推送失败 (exit $?)" >> "$LOG"' ERR

git add -A
if git diff --cached --quiet; then
  echo "$(date "+%F %T") SKIP: 无待提交改动" >> "$LOG"
  exit 0
fi

git commit -m "chore: daily auto commit $(date '+%F %T')"
branch="$(git symbolic-ref --short HEAD)"
git push origin "$branch"

echo "$(date "+%F %T") OK: 已提交并推送 $(git rev-parse --short HEAD) ($branch)" >> "$LOG"
