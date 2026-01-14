#!/usr/bin/env bash

# Mobile UI Testing Plugin - Session Start Hook
# - Auto-approves mobile-mcp tools for seamless test execution
# - Starts scrcpy-helper server for faster screenshots/input

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(realpath "$0")")")}"
SCRCPY_HELPER="${PLUGIN_ROOT}/scripts/scrcpy-helper.py"
PID_FILE="/tmp/scrcpy-helper.pid"
SOCKET_PATH="/tmp/scrcpy-helper.sock"

# Start scrcpy-helper if not already running
start_scrcpy_helper() {
    # Check if already running
    if [[ -f "$PID_FILE" ]]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # Already running
        fi
        # Stale PID file
        rm -f "$PID_FILE"
    fi

    # Remove stale socket
    rm -f "$SOCKET_PATH"

    # Check if scrcpy-helper script exists
    if [[ ! -f "$SCRCPY_HELPER" ]]; then
        return 1
    fi

    # Start in background
    python3 "$SCRCPY_HELPER" > /dev/null 2>&1 &
    echo $! > "$PID_FILE"

    # Wait briefly for startup
    sleep 0.5

    # Verify running
    if [[ -S "$SOCKET_PATH" ]]; then
        return 0
    else
        rm -f "$PID_FILE"
        return 1
    fi
}

# Try to start scrcpy-helper (non-blocking, don't fail if it doesn't work)
scrcpy_status="not started"
if start_scrcpy_helper; then
    scrcpy_status="running (faster screenshots enabled)"
fi

cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Mobile UI Testing plugin is active.\n\n**Auto-approved tools:** All mobile-mcp tools (tap, swipe, type, screenshot, etc.) are pre-approved for this session. Tests will run without requiring manual approval for each action.\n\n**scrcpy-helper:** ${scrcpy_status}\n\nAvailable commands:\n- \`/run-test <file>\` - Execute a YAML test file\n- \`/create-test <name>\` - Create a new test from template\n- \`/generate-test <description>\` - Generate test from natural language\n- \`/record-test <name>\` - Start recording user actions\n- \`/stop-recording\` - Stop recording and generate YAML\n\nFor help writing tests, just ask about YAML test syntax."
  }
}
EOF

exit 0
