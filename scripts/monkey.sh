#!/usr/bin/env bash
# Relaunch, attach the light probe, run the seeded navigation monkey, then scan mounted wrappers.
# Usage: scripts/monkey.sh <udid> <steps> <seed> [extra flag query]
set -uo pipefail
UDID="${1:?udid}"; STEPS="${2:-100}"; SEED="${3:-1}"; EXTRA="${4:-}"
cd "$(dirname "$0")/.."
OUT=/tmp/monkey-$SEED.txt
pkill -f "lldb -p" 2>/dev/null
xcrun simctl terminate "$UDID" com.example.rns4861 2>/dev/null; sleep 1
xcrun simctl launch "$UDID" com.example.rns4861 >/dev/null; sleep 4
PID=$(xcrun simctl spawn "$UDID" launchctl list | awk '/UIKitApplication:com.example.rns4861/ {print $1}')
if [[ "${NOPROBE:-0}" != "1" ]]; then
xcrun lldb -p "$PID" --batch -o 'settings set auto-confirm true' -o 'settings set target.skip-prologue false' \
  -o "command script import $PWD/scripts/probe4861.py" -o "probe_install $OUT light" -o 'process continue' > "$OUT.lldb.log" 2>&1 &
LLDB=$!
sleep 6
fi
xcrun simctl openurl "$UDID" "rns4861://control?monkey=$STEPS&seed=$SEED$EXTRA"
# Wait for the readout to say done (poll the accessibility tree through a screenshot-free check).
for i in $(seq 1 $(( STEPS * 2 + 60 ))); do
  sleep 1
  if [[ "${NOPROBE:-0}" != "1" ]] && grep -q "LEAKED\|MISMATCH" "$OUT" 2>/dev/null; then :; fi
  # crude: wait for the expected duration
  if (( i > STEPS + 20 )); then break; fi
done
[[ "${NOPROBE:-0}" != "1" ]] && { pkill -f "lldb -p $PID" 2>/dev/null; sleep 2; }
echo "seed=$SEED flags: $(grep -cE 'LEAKED|MISMATCH|CFG_SCREENVIEW' "$OUT" 2>/dev/null)"
scripts/scan.sh "$UDID"
xcrun simctl io "$UDID" screenshot "/tmp/monkey-$SEED.png" >/dev/null 2>&1
