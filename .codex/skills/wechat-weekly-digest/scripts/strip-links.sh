#!/usr/bin/env bash
# Strip markdown links from a digest while keeping the link text, and drop
# image reference lines. Produces the "WeChat-safe" markdown.
# Usage: strip-links.sh <input.md> [output.md]   (default output: stdout)
set -euo pipefail

input="${1:?usage: strip-links.sh <input.md> [output.md]}"
output="${2:-/dev/stdout}"

sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$input" \
  | grep -v '^!\[' \
  | sed -e 's/\[\([^]]*\)\]([^)]*)/\1/g' \
  > "$output"
