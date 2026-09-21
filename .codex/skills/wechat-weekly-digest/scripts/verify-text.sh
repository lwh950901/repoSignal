#!/usr/bin/env bash
# Verify the visible text of a WeChat HTML matches the original digest
# (after stripping links, image lines, markdown markers, table pipes /
# separator rows, helper blocks, the one-click copy button, and the copy
# script). Whitespace is ignored; any missing/extra/reordered character fails.
# Usage: verify-text.sh <original.md> <wechat.html>
set -euo pipefail

md="${1:?usage: verify-text.sh <original.md> <wechat.html>}"
html="${2:?usage: verify-text.sh <original.md> <wechat.html>}"

md_flow() {
  sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$1" \
    | grep -v '^!\[' \
    | grep -v '^---$' \
    | grep -vE '^\|[|: -]*$' \
    | sed -e 's/\[\([^]]*\)\]([^)]*)/\1/g' \
          -e 's/[#*`|]//g' \
          -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
    | grep -v '^$' \
    | tr -d '[:space:]'
}

html_flow() {
  sed -e '/<head>/,/<\/head>/d' -e '/<script>/,/<\/script>/d' "$1" \
    | grep -v -e '<!--' -e '-->' \
    | grep -v '【发布前删除】' \
    | grep -v '大封面 900' \
    | grep -v '一键复制全文' \
    | sed -e 's/<[^>]*>//g' \
          -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
    | grep -v '^$' \
    | tr -d '[:space:]'
}

if diff <(md_flow "$md") <(html_flow "$html") >/dev/null; then
  echo "TEXT_OK: HTML 正文文字与原版逐字一致（忽略空白与 md 语法）"
else
  echo "TEXT_DIFF: 正文存在差异（见下方 diff）" >&2
  diff <(md_flow "$md") <(html_flow "$html") || true
  exit 1
fi
