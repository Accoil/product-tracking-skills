#!/usr/bin/env bash
# Build the skills-only ZIP for OpenAI's plugin directory (platform.openai.com/plugins).
#
# Copies plugin.json, LICENSE, assets/ and skills/ into dist/openai/product-tracking/,
# checks them against OpenAI's submission rules, then writes
# dist/openai/product-tracking-v<version>.zip.
#
# Repo-only files (.claude-plugin/, agents/, README, CHANGELOG, ...) are left out:
# OpenAI rejects Claude-specific agents and hooks.
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
out="$repo/dist/openai"
name="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$repo/plugin.json")"
version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$repo/plugin.json")"
stage="$out/$name"
zip_path="$out/$name-v$version.zip"

rm -rf "$stage" "$zip_path"
mkdir -p "$stage"
cp "$repo/plugin.json" "$repo/LICENSE" "$stage/"
cp -R "$repo/assets" "$repo/skills" "$stage/"
find "$stage" \( -name '.DS_Store' -o -name '._*' -o -name 'Thumbs.db' \) -delete

python3 "$repo/scripts/check-openai-package.py" "$stage" "$repo"

(cd "$out" && zip -qrX "$zip_path" "$name")
echo "Built $zip_path ($(du -h "$zip_path" | cut -f1))"
