#!/usr/bin/env bash

# Mobile UI Testing Plugin - Session End Hook
# Stops scrcpy-helper server

PID_FILE="/tmp/scrcpy-helper.pid"
SOCKET_PATH="/tmp/scrcpy-helper.sock"

# Stop scrcpy-helper if running
stop_scrcpy_helper() {
    # Try graceful shutdown via socket first
    if [[ -S "$SOCKET_PATH" ]]; then
        echo "quit" | nc -U -w 1 "$SOCKET_PATH" 2>/dev/null || true
        sleep 0.5
    fi

    # Kill process if still running
    if [[ -f "$PID_FILE" ]]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            sleep 0.5
            # Force kill if still running
            kill -9 "$pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi

    # Remove socket file
    rm -f "$SOCKET_PATH"
}

stop_scrcpy_helper

exit 0
