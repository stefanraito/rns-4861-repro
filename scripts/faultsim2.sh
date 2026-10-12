#!/usr/bin/env bash
# Fault-injection run: leak from the start, skip the headerless reset only for the onboarding steps.
set -uo pipefail
UDID="${1:?udid}"
cd "$(dirname "$0")/.."
rm -f /tmp/faultsim.enable
pkill -f "lldb -p" 2>/dev/null
xcrun simctl terminate "$UDID" com.example.rns4861 2>/dev/null; sleep 1
xcrun simctl launch "$UDID" com.example.rns4861 >/dev/null; sleep 4
PID=$(xcrun simctl spawn "$UDID" launchctl list | awk '/UIKitApplication:com.example.rns4861/ {print $1}')
xcrun lldb -p "$PID" --batch -o 'settings set auto-confirm true' -o 'settings set target.skip-prologue false' \
  -o "command script import $PWD/scripts/faultsim.py" -o 'faultsim_install' -o 'process continue' > /tmp/faultsim.lldb.log 2>&1 &
sleep 6
maestro --device "$UDID" test .maestro/part1.yaml > /tmp/faultsim.p1.log 2>&1; echo "part1 exit=$?"
touch /tmp/faultsim.enable
maestro --device "$UDID" test .maestro/part2.yaml > /tmp/faultsim.p2.log 2>&1; echo "part2 exit=$? $(grep -E 'Assertion is false' /tmp/faultsim.p2.log | head -1)"
rm -f /tmp/faultsim.enable
pkill -f "lldb -p $PID" 2>/dev/null; sleep 2
cat /tmp/faultsim.txt
scripts/scan.sh "$UDID"
xcrun simctl io "$UDID" screenshot /tmp/faultsim.png >/dev/null 2>&1
