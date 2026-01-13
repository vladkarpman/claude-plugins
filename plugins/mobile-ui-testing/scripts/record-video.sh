#!/bin/bash
# Record device screen to video file
# Usage: record-video.sh <device-id> <output-file> [duration]
#
# STOPPING: Do NOT kill this script directly. Instead:
#   adb -s <device> shell pkill -2 screenrecord
# This sends SIGINT to screenrecord, which finalizes the video file properly.
# The script will then complete normally and pull the file.

set -euo pipefail

DEVICE=${1:-}
OUTPUT=${2:-}
DURATION=${3:-180}  # Default 3 minutes max

if [ -z "$DEVICE" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: record-video.sh <device-id> <output-file> [duration]" >&2
    exit 1
fi

# Validate duration is numeric
if ! [[ "$DURATION" =~ ^[0-9]+$ ]]; then
    echo "Error: Duration must be a number, got: $DURATION" >&2
    exit 1
fi

# Check device is connected
if ! adb -s "$DEVICE" shell true 2>/dev/null; then
    echo "Error: Device not found: $DEVICE" >&2
    exit 1
fi

# Cleanup device file
cleanup_device() {
    adb -s "$DEVICE" shell rm -f /sdcard/recording.mp4 2>/dev/null || true
}

# Stop screenrecord gracefully on device (SIGINT triggers moov atom write)
stop_recording() {
    echo "Stopping screenrecord on device..." >&2
    adb -s "$DEVICE" shell pkill -2 screenrecord 2>/dev/null || true
}

# Handle signals: stop recording gracefully, then exit
trap 'stop_recording; exit 130' INT
trap 'stop_recording; exit 143' TERM

echo "Recording to $OUTPUT (max ${DURATION}s)..." >&2

# Start recording - blocks until complete or stopped via pkill -2
# screenrecord needs SIGINT (not SIGTERM) to write moov atom and finalize file
adb -s "$DEVICE" shell screenrecord --time-limit "$DURATION" /sdcard/recording.mp4
RECORD_EXIT=$?

# Small delay to ensure file is fully written
sleep 0.5

# Pull the file
echo "Pulling recording from device..." >&2
if ! adb -s "$DEVICE" pull /sdcard/recording.mp4 "$OUTPUT" 2>&1; then
    echo "Error: Failed to pull recording" >&2
    cleanup_device
    exit 1
fi

# Cleanup device
cleanup_device

# Verify output exists and is valid
if [ ! -f "$OUTPUT" ]; then
    echo "Error: Output file not created: $OUTPUT" >&2
    exit 1
fi

# Quick validation that file has moov atom (not corrupted)
if ! ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUTPUT" >/dev/null 2>&1; then
    echo "Warning: Video file may be corrupted (missing moov atom)" >&2
    echo "This can happen if recording was not stopped gracefully" >&2
fi

echo "Recording saved: $OUTPUT" >&2
