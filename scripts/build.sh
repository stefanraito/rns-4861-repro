#!/usr/bin/env bash
# Build the Release simulator app and install it on the given simulator.
# Usage: scripts/build.sh <simulator-udid> [Release|Debug]
set -euo pipefail
UDID="${1:?simulator udid}"; CONFIG="${2:-Release}"
cd "$(dirname "$0")/../ios"
xcodebuild -workspace RNS4861.xcworkspace -scheme RNS4861 -configuration "$CONFIG" -sdk iphonesimulator \
  -destination "id=$UDID" -derivedDataPath ../build/dd build > "../build-$(echo "$CONFIG" | tr A-Z a-z).log" 2>&1 \
  || { tail -30 "../build-$(echo "$CONFIG" | tr A-Z a-z).log"; exit 1; }
xcrun simctl install "$UDID" "../build/dd/Build/Products/$CONFIG-iphonesimulator/RNS4861.app"
echo "installed $CONFIG"
