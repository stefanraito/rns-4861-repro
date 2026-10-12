#!/usr/bin/env bash
# Attach to the running app and list every RNSScreenContentWrapper (see scripts/scanwrappers.py).
set -uo pipefail
UDID="${1:?udid}"
cd "$(dirname "$0")/.."
PID=$(xcrun simctl spawn "$UDID" launchctl list | awk '/UIKitApplication:com.example.rns4861/ {print $1}')
xcrun lldb -p "$PID" --batch -o "command script import $PWD/scripts/scanwrappers.py" -o scanwrappers 2>&1 \
  | grep -E "^W |no wrappers|error" 
