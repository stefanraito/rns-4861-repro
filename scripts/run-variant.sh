#!/usr/bin/env bash
# Relaunch the app and run .maestro/variant.yaml with the given flag query string (no debugger).
# Usage: scripts/run-variant.sh <simulator-udid> '<flags query>' [flow]
set -uo pipefail
UDID="${1:?simulator udid}"; FLAGS="${2:-}"; FLOW="${3:-.maestro/variant.yaml}"
cd "$(dirname "$0")/.."
xcrun simctl terminate "$UDID" com.example.rns4861 2>/dev/null; sleep 1
xcrun simctl launch "$UDID" com.example.rns4861 >/dev/null; sleep 3
OUT=/tmp/variant-$$.log
maestro --device "$UDID" test -e "FLAGS=$FLAGS" "$FLOW" > "$OUT" 2>&1
RESULT=$?
echo "flags=[$FLAGS] exit=$RESULT $(grep -E 'Assertion is false|FAILED' "$OUT" | head -1)"
