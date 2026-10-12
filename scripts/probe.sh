#!/usr/bin/env bash
# Relaunch the app, attach lldb with scripts/probe4861.py, run a Maestro flow, then dump frames.
# Usage: scripts/probe.sh <simulator-udid> <flow.yaml> [out=/tmp/probe.txt]
set -uo pipefail
UDID="${1:?simulator udid}"; FLOW="${2:?flow}"; OUT="${3:-/tmp/probe.txt}"
cd "$(dirname "$0")/.."
pkill -f "lldb -p" 2>/dev/null
xcrun simctl terminate "$UDID" com.example.rns4861 2>/dev/null; sleep 1
xcrun simctl launch "$UDID" com.example.rns4861 >/dev/null; sleep 4
PID=$(xcrun simctl spawn "$UDID" launchctl list | awk '/UIKitApplication:com.example.rns4861/ {print $1}')
xcrun lldb -p "$PID" --batch \
  -o 'settings set auto-confirm true' -o 'settings set target.skip-prologue false' \
  -o "command script import $PWD/scripts/probe4861.py" \
  -o "probe_install $OUT ${PROBE_MODE:-}" \
  -o 'process continue' > "$OUT.lldb.log" 2>&1 &
sleep 8
maestro --device "$UDID" test ${MAESTRO_ARGS:-} "$FLOW" > "$OUT.maestro.log" 2>&1
RESULT=$?
sleep 1
pkill -f "lldb -p $PID" 2>/dev/null; sleep 2
echo "maestro exit=$RESULT"; grep -E "FAILED|Assertion is false" "$OUT.maestro.log" | head -3
grep -cE "MISMATCH|STALE|LEAKED|CFG_SCREENVIEW" "$OUT"
