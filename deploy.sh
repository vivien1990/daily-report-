#!/bin/bash
# Deploy script: build site + push to GitHub Pages
set -e

cd "$(dirname "$0")"

HERMES_PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python"

echo "=== 1. Generate site ==="
$HERMES_PYTHON scripts/generate.py

echo ""
echo "=== 2. Copy to repo root ==="
cp output/index.html .
cp output/*.html .
cp -r output/audio .

echo ""
echo "=== 3. Git push ==="
git add -A
git commit -m "每日更新: $(date '+%Y-%m-%d %H:%M')" || echo "(no changes)"
git push origin main

echo ""
echo "=== ✅ 部署完成 ==="
