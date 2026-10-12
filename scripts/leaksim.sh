#!/usr/bin/env bash
# Relaunch, attach lldb with scripts/leaksim.py, run a flow. Usage: scripts/leaksim.sh <udid> <flow>
set -uo pipefail
UDID="${1:?udid}"; FLOW="${2:?flow}"
cd "$(dirname "$0")/.."
pkill -f "lldb -p" 2>/dev/null
xcrun simctl terminate "$UDID" com.example.rns4861 2>/dev/null; sleep 1
xcrun simctl launch "$UDID" com.example.rns4861 >/dev/null; sleep 4
PID=$(xcrun simctl spawn "$UDID" launchctl list | awk '/UIKitApplication:com.example.rns4861/ {print $1}')
xcrun lldb -p "$PID" --batch -o 'settings set auto-confirm true' -o 'settings set target.skip-prologue false' \
  -o "command script import $PWD/scripts/leaksim.py" -o 'leaksim_install' -o 'process continue' > /tmp/leaksim.lldb.log 2>&1 &
sleep 6
maestro --device "$UDID" test ${MAESTRO_ARGS:-} "$FLOW" > /tmp/leaksim.maestro.log 2>&1
RESULT=$?
pkill -f "lldb -p $PID" 2>/dev/null; sleep 1
echo "maestro exit=$RESULT $(grep -E 'Assertion is false' /tmp/leaksim.maestro.log | head -1)"; cat /tmp/leaksim.txt
