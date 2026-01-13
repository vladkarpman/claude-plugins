#!/bin/bash
# Record touches and capture screenshots on each touch
# Usage: ./record-with-screenshots.sh <device-id> <output-dir>

set -euo pipefail

DEVICE=$1
OUTPUT_DIR=$2

if [ -z "$DEVICE" ] || [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 <device-id> <output-dir>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCREENSHOTS_DIR="$OUTPUT_DIR/screenshots"

mkdir -p "$SCREENSHOTS_DIR"

# Cleanup handler for graceful exit
cleanup() {
    echo ""
    echo "Recording stopped."
    echo "Screenshots saved to: $SCREENSHOTS_DIR"
    echo "Events saved to: $OUTPUT_DIR/touch_events.json"
}
trap cleanup EXIT

echo "Starting recording..."
echo "Device: $DEVICE"
echo "Output: $OUTPUT_DIR"
echo ""

# Start touch monitor and process each event
python3 "$SCRIPT_DIR/monitor-touches.py" "$DEVICE" "$OUTPUT_DIR" | while read -r event; do
    # Parse all JSON fields at once (optimization: single python call instead of 5)
    read -r INDEX SCREENSHOT_NAME GESTURE X Y <<< $(echo "$event" | python3 -c "
import sys, json
e = json.load(sys.stdin)
print(e['index'], e['screenshot'], e['gesture'], e['x'], e['y'])
")

    # Small delay to let UI settle after touch
    sleep 0.2

    # Take screenshot with error handling
    SCREENSHOT_PATH="$SCREENSHOTS_DIR/$SCREENSHOT_NAME"
    if ! adb -s "$DEVICE" exec-out screencap -p > "$SCREENSHOT_PATH" 2>&1; then
        echo "Warning: Failed to capture screenshot $SCREENSHOT_NAME" >&2
    fi

    echo "[$INDEX] $GESTURE at ($X, $Y) -> $SCREENSHOT_NAME"
done
