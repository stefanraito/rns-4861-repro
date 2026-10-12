#!/usr/bin/env bash
# Relaunch the app, attach lldb with the wrapper probes, run a Maestro flow, then dump frames.
# Usage: scripts/trace.sh <simulator-udid> [flow=.maestro/sequence.yaml] [out=/tmp/wrapwatch.txt]
set -uo pipefail
UDID="${1:?simulator udid}"; FLOW="${2:-.maestro/sequence.yaml}"; OUT="${3:-/tmp/wrapwatch.txt}"
cd "$(dirname "$0")/.."
pkill -f "lldb -p" 2>/dev/null
xcrun simctl terminate "$UDID" com.example.rns4861 2>/dev/null; sleep 1
xcrun simctl launch "$UDID" com.example.rns4861 >/dev/null; sleep 4
PID=$(xcrun simctl spawn "$UDID" launchctl list | awk '/UIKitApplication:com.example.rns4861/ {print $1}')
xcrun lldb -p "$PID" --batch \
  -o 'settings set auto-confirm true' \
  -o "command script import $PWD/scripts/wrapwatch.py" \
  -o "wrapwatch_install $OUT" \
  -o 'process continue' > "$OUT.lldb.log" 2>&1 &
sleep 6
maestro --device "$UDID" test "$FLOW" > "$OUT.maestro.log" 2>&1
RESULT=$?
pkill -f "lldb -p $PID" 2>/dev/null; sleep 2
echo "maestro exit=$RESULT"; grep -E "FAILED|Assertion is false" "$OUT.maestro.log" | head -3
scripts/dump-screens.sh "$UDID"
