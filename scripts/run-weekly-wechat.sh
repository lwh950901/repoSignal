#!/usr/bin/env bash
# 每周日 09:30 由定时任务触发：把本周仓库雷达周报转成微信 HTML（雷达屏样式 + 一键复制按钮）。
# 完全自包含，不依赖外部 skill 目录。日志：data/weixin/.weekly-run.log
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/data/weixin/.weekly-run.log"

# 本周 ISO 周（如 2026-W33）；仓库命名可能带或不带前导零，两种都试
week="$(date +%G-W%V)"
md="$REPO/data/github-project-digest/radar/$week.md"
if [ ! -f "$md" ]; then
  week="$(date +%G-W)$(date +%-V)"
  md="$REPO/data/github-project-digest/radar/$week.md"
fi
if [ ! -f "$md" ]; then
  echo "$(date '+%F %T') SKIP: 未找到本周周报 ($md)" >> "$LOG"
  exit 0
fi

out_md="$REPO/data/weixin/$week.md"
out_html="$REPO/data/weixin/$week.html"

# 1. 去链接 md（保留显示文字、删除图片行）
sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$md" \
  | grep -v '^!\[' \
  | sed -e 's/\[\([^]]*\)\]([^)]*)/\1/g' \
  > "$out_md"

# 2. md -> 微信 HTML（雷达屏样式 + 一键复制按钮）
python3 "$REPO/scripts/digest-to-html.py" "$out_md" "$out_html"

# 3. 校验正文与原版逐字一致（过滤链接/图片/标记/注释/占位框/按钮/脚本）
if diff <(sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$md" | grep -v '^!\[' | grep -v '^---$' | sed -e 's/\[\([^]]*\)\]([^)]*)/\1/g' -e 's/[#*`]//g' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | grep -v '^$') <(sed -e '/<head>/,/<\/head>/d' -e '/<script>/,/<\/script>/d' "$out_html" | grep -v -e '<!--' -e '-->' -e '【发布前删除】' -e '大封面 900' -e '一键复制全文' | sed -e 's/<[^>]*>//g' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | grep -v '^$') >> "$LOG" 2>&1; then
  echo "$(date '+%F %T') OK: $week -> data/weixin/$week.html" >> "$LOG"
else
  echo "$(date '+%F %T') FAIL: $week 文案验证未通过，需人工处理" >> "$LOG"
fi
