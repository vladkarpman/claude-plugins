#!/bin/bash
# Touch Event Recording Script for mobile-ui-testing
# Captures both touch events AND UI snapshots for element correlation
#
# Usage:
#   Start: ./record-touches.sh start <device-id> <output-dir>
#   Stop:  ./record-touches.sh stop <output-dir>
#   Status: ./record-touches.sh status <output-dir>

ACTION=$1
DEVICE=$2
OUTPUT_DIR=$3

PID_FILE="$OUTPUT_DIR/.recording.pid"
SNAPSHOT_PID_FILE="$OUTPUT_DIR/.snapshot.pid"
TOUCH_LOG="$OUTPUT_DIR/touch_log.txt"
COORD_LOG="$OUTPUT_DIR/max_coords.txt"
SNAPSHOTS_DIR="$OUTPUT_DIR/snapshots"

case "$ACTION" in
  start)
    if [ -z "$DEVICE" ] || [ -z "$OUTPUT_DIR" ]; then
      echo "Usage: $0 start <device-id> <output-dir>"
      exit 1
    fi

    # Create output directories
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$SNAPSHOTS_DIR"

    # Check if already recording
    if [ -f "$PID_FILE" ]; then
      OLD_PID=$(cat "$PID_FILE")
      if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "ERROR: Recording already in progress (PID: $OLD_PID)"
        exit 1
      fi
    fi

    # Get max coordinates for later conversion
    echo "Capturing device touch coordinate bounds..."
    adb -s "$DEVICE" shell getevent -p 2>/dev/null | grep -A 10 "ABS_MT_POSITION" > "$COORD_LOG"

    # Get screen size
    SCREEN_SIZE=$(adb -s "$DEVICE" shell wm size 2>/dev/null | grep -oE "[0-9]+x[0-9]+")
    echo "$SCREEN_SIZE" > "$OUTPUT_DIR/screen_size.txt"
    echo "Screen size: $SCREEN_SIZE"

    # Detect foreground app package
    FOREGROUND_APP=$(adb -s "$DEVICE" shell dumpsys activity activities 2>/dev/null | grep -E "mResumedActivity|topResumedActivity" | head -1 | grep -oE "[a-z][a-z0-9_.]+/[a-zA-Z0-9_.]+" | cut -d'/' -f1)
    if [ -n "$FOREGROUND_APP" ]; then
      echo "{\"app\": \"$FOREGROUND_APP\", \"device\": \"$DEVICE\"}" > "$OUTPUT_DIR/config.json"
      echo "Foreground app: $FOREGROUND_APP"
    fi

    # Start getevent in background (touch events)
    echo "Starting touch event capture..."
    adb -s "$DEVICE" shell getevent -lt > "$TOUCH_LOG" 2>/dev/null &
    GETEVENT_PID=$!
    echo "$GETEVENT_PID" > "$PID_FILE"

    # Start UI snapshot capture in background (every 100ms)
    echo "Starting UI snapshot capture (~10/sec)..."
    (
      COUNTER=0
      while true; do
        TIMESTAMP=$(python3 -c "import time; print(int(time.time()*1000))")
        SNAPSHOT_FILE="$SNAPSHOTS_DIR/${TIMESTAMP}.txt"
        adb -s "$DEVICE" shell "dumpsys activity top" 2>/dev/null | grep -A 500 "View Hierarchy" > "$SNAPSHOT_FILE"
        COUNTER=$((COUNTER + 1))
        # Small sleep to avoid overwhelming the device
        sleep 0.08
      done
    ) &
    SNAPSHOT_PID=$!
    echo "$SNAPSHOT_PID" > "$SNAPSHOT_PID_FILE"

    # Verify both processes started
    sleep 0.5
    if ps -p "$GETEVENT_PID" > /dev/null 2>&1 && ps -p "$SNAPSHOT_PID" > /dev/null 2>&1; then
      echo ""
      echo "OK: Recording started"
      echo "  Touch capture PID: $GETEVENT_PID"
      echo "  Snapshot capture PID: $SNAPSHOT_PID"
      echo "  Touch log: $TOUCH_LOG"
      echo "  Snapshots: $SNAPSHOTS_DIR/"
      echo ""
      echo "Run '$0 stop $OUTPUT_DIR' to stop recording"
      exit 0
    else
      echo "ERROR: Failed to start recording"
      kill "$GETEVENT_PID" 2>/dev/null
      kill "$SNAPSHOT_PID" 2>/dev/null
      rm -f "$PID_FILE" "$SNAPSHOT_PID_FILE"
      exit 1
    fi
    ;;

  stop)
    if [ -z "$OUTPUT_DIR" ]; then
      # Try to find from second argument position
      OUTPUT_DIR=$2
    fi

    if [ -z "$OUTPUT_DIR" ]; then
      echo "Usage: $0 stop <output-dir>"
      exit 1
    fi

    PID_FILE="$OUTPUT_DIR/.recording.pid"
    SNAPSHOT_PID_FILE="$OUTPUT_DIR/.snapshot.pid"
    SNAPSHOTS_DIR="$OUTPUT_DIR/snapshots"

    if [ ! -f "$PID_FILE" ] && [ ! -f "$SNAPSHOT_PID_FILE" ]; then
      echo "ERROR: No recording in progress (no PID files found)"
      exit 1
    fi

    # Stop touch capture
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      echo "Stopping touch capture (PID: $PID)..."
      kill "$PID" 2>/dev/null
      pkill -P "$PID" 2>/dev/null
      rm -f "$PID_FILE"
    fi

    # Stop snapshot capture
    if [ -f "$SNAPSHOT_PID_FILE" ]; then
      SNAPSHOT_PID=$(cat "$SNAPSHOT_PID_FILE")
      echo "Stopping snapshot capture (PID: $SNAPSHOT_PID)..."
      kill "$SNAPSHOT_PID" 2>/dev/null
      pkill -P "$SNAPSHOT_PID" 2>/dev/null
      rm -f "$SNAPSHOT_PID_FILE"
    fi

    # Also kill any lingering adb processes
    pkill -f "adb.*getevent" 2>/dev/null
    pkill -f "adb.*dumpsys" 2>/dev/null

    # Report results
    echo ""
    echo "OK: Recording stopped"

    TOUCH_LOG="$OUTPUT_DIR/touch_log.txt"
    if [ -f "$TOUCH_LOG" ]; then
      LINE_COUNT=$(wc -l < "$TOUCH_LOG")
      echo "  Touch events: $LINE_COUNT lines"
    fi

    if [ -d "$SNAPSHOTS_DIR" ]; then
      SNAPSHOT_COUNT=$(ls -1 "$SNAPSHOTS_DIR"/*.txt 2>/dev/null | wc -l)
      echo "  UI snapshots: $SNAPSHOT_COUNT files"
    fi

    echo ""
    echo "Output directory: $OUTPUT_DIR"
    ;;

  status)
    if [ -z "$OUTPUT_DIR" ]; then
      OUTPUT_DIR=$2
    fi

    PID_FILE="$OUTPUT_DIR/.recording.pid"
    SNAPSHOT_PID_FILE="$OUTPUT_DIR/.snapshot.pid"
    SNAPSHOTS_DIR="$OUTPUT_DIR/snapshots"

    TOUCH_RUNNING=false
    SNAPSHOT_RUNNING=false

    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if ps -p "$PID" > /dev/null 2>&1; then
        TOUCH_RUNNING=true
      fi
    fi

    if [ -f "$SNAPSHOT_PID_FILE" ]; then
      SNAPSHOT_PID=$(cat "$SNAPSHOT_PID_FILE")
      if ps -p "$SNAPSHOT_PID" > /dev/null 2>&1; then
        SNAPSHOT_RUNNING=true
      fi
    fi

    if [ "$TOUCH_RUNNING" = false ] && [ "$SNAPSHOT_RUNNING" = false ]; then
      echo "STATUS: Not recording"
      exit 0
    fi

    echo "STATUS: Recording in progress"

    TOUCH_LOG="$OUTPUT_DIR/touch_log.txt"
    if [ -f "$TOUCH_LOG" ]; then
      LINE_COUNT=$(wc -l < "$TOUCH_LOG")
      echo "  Touch events: $LINE_COUNT lines"
    fi

    if [ -d "$SNAPSHOTS_DIR" ]; then
      SNAPSHOT_COUNT=$(ls -1 "$SNAPSHOTS_DIR"/*.txt 2>/dev/null | wc -l)
      echo "  UI snapshots: $SNAPSHOT_COUNT files"
    fi
    ;;

  *)
    echo "Touch Event Recording Script"
    echo ""
    echo "Usage:"
    echo "  $0 start <device-id> <output-dir>  - Start recording"
    echo "  $0 stop <output-dir>               - Stop recording"
    echo "  $0 status <output-dir>             - Check recording status"
    echo ""
    echo "Example:"
    echo "  $0 start RFCW318P7NV ./tests/my-test"
    echo "  # ... interact with device ..."
    echo "  $0 stop ./tests/my-test"
    exit 1
    ;;
esac
