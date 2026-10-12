#!/usr/bin/env bash
# Print every RNSScreenView / RNSScreenContentWrapper frame in the running app.
# Usage: scripts/dump-screens.sh <simulator-udid>
set -euo pipefail
UDID="${1:?simulator udid}"
PID=$(xcrun simctl spawn "$UDID" launchctl list | awk '/UIKitApplication:com.example.rns4861/ {print $1}')
if [[ -z "$PID" || "$PID" == "-" ]]; then echo "app not running" >&2; exit 1; fi
xcrun lldb -p "$PID" --batch \
  -o 'expr -l objc -O -- (id)[[[[UIApplication sharedApplication] windows] firstObject] recursiveDescription]' \
  2>/dev/null | grep -E 'RNSScreenView|RNSScreenContentWrapper' | sed -E 's/; (tag|layer|backgroundColor|gestureRecognizers|clipsToBounds|autoresize)[^;>]*//g'
