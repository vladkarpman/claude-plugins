#!/usr/bin/env bash

# scrcpy-or-mcp.sh - Unified interface for screenshot/input commands
# Falls back to mobile-mcp if scrcpy-helper is not available
#
# Usage:
#   scrcpy-or-mcp.sh screenshot [output.png]
#   scrcpy-or-mcp.sh tap <x> <y>
#   scrcpy-or-mcp.sh swipe <x1> <y1> <x2> <y2>
#   scrcpy-or-mcp.sh type <text>
#   scrcpy-or-mcp.sh status
#
# Environment:
#   SCRCPY_SOCKET - Socket path (default: /tmp/scrcpy-helper.sock)
#   PREFER_MCP    - Set to "1" to force mobile-mcp usage
#   DEVICE_ID     - Device ID for commands

set -e

SOCKET_PATH="${SCRCPY_SOCKET:-/tmp/scrcpy-helper.sock}"

# Check if scrcpy-helper is available
scrcpy_available() {
    [[ -S "$SOCKET_PATH" ]] && [[ "$PREFER_MCP" != "1" ]]
}

# Send command to scrcpy-helper, return response
scrcpy_cmd() {
    echo "$*" | nc -U -w 5 "$SOCKET_PATH"
}

# Main command dispatcher
case "${1:-help}" in
    screenshot)
        output="${2:-/dev/stdout}"
        if scrcpy_available; then
            # Use scrcpy-helper (binary response with length prefix)
            # For binary, we need to handle the 4-byte length prefix
            {
                echo "screenshot" | nc -U -w 5 "$SOCKET_PATH"
            } | {
                # Read 4-byte length
                read -r -n 4 length_bytes
                # Read rest as PNG
                cat
            } > "$output"
            echo "scrcpy"  # Indicate which method was used
        else
            # Fall back to mobile-mcp
            echo "mobile-mcp (scrcpy-helper not available)" >&2
            echo "mcp"
        fi
        ;;

    screenshot-base64)
        if scrcpy_available; then
            scrcpy_cmd "screenshot base64"
        else
            echo "ERROR: base64 screenshot requires scrcpy-helper" >&2
            exit 1
        fi
        ;;

    tap)
        x="$2"
        y="$3"
        if [[ -z "$x" ]] || [[ -z "$y" ]]; then
            echo "Usage: $0 tap <x> <y>" >&2
            exit 1
        fi

        if scrcpy_available; then
            scrcpy_cmd "tap $x $y"
        else
            echo "mcp"  # Caller should use mobile-mcp
        fi
        ;;

    swipe)
        x1="$2"
        y1="$3"
        x2="$4"
        y2="$5"
        if [[ -z "$x1" ]] || [[ -z "$y1" ]] || [[ -z "$x2" ]] || [[ -z "$y2" ]]; then
            echo "Usage: $0 swipe <x1> <y1> <x2> <y2>" >&2
            exit 1
        fi

        if scrcpy_available; then
            scrcpy_cmd "swipe $x1 $y1 $x2 $y2"
        else
            echo "mcp"
        fi
        ;;

    type)
        shift
        text="$*"
        if [[ -z "$text" ]]; then
            echo "Usage: $0 type <text>" >&2
            exit 1
        fi

        if scrcpy_available; then
            scrcpy_cmd "type $text"
        else
            echo "mcp"
        fi
        ;;

    key)
        keycode="$2"
        if [[ -z "$keycode" ]]; then
            echo "Usage: $0 key <keycode>" >&2
            exit 1
        fi

        if scrcpy_available; then
            scrcpy_cmd "key $keycode"
        else
            echo "mcp"
        fi
        ;;

    connect)
        device_id="${2:-$DEVICE_ID}"
        if scrcpy_available; then
            if [[ -n "$device_id" ]]; then
                scrcpy_cmd "connect $device_id"
            else
                scrcpy_cmd "connect"
            fi
        else
            echo "mcp"
        fi
        ;;

    status)
        if scrcpy_available; then
            scrcpy_cmd "status"
        else
            echo '{"available": false, "reason": "scrcpy-helper not running"}'
        fi
        ;;

    available)
        # Just check if scrcpy-helper is available
        if scrcpy_available; then
            echo "true"
            exit 0
        else
            echo "false"
            exit 1
        fi
        ;;

    frames-stable)
        timeout_ms="${2:-5000}"
        if scrcpy_available; then
            scrcpy_cmd "frames stable $timeout_ms"
        else
            # No equivalent in mobile-mcp, just return OK
            echo "OK"
        fi
        ;;

    help|--help|-h|"")
        cat << 'EOF'
Usage: scrcpy-or-mcp.sh <command> [args...]

Commands:
  screenshot [output]    Take screenshot (PNG)
  screenshot-base64      Take screenshot (base64)
  tap <x> <y>           Tap at coordinates
  swipe <x1> <y1> <x2> <y2>  Swipe between points
  type <text>           Type text
  key <keycode>         Send key (back, home, enter, etc.)
  connect [device]      Connect to device
  status                Get connection status
  available             Check if scrcpy-helper is running
  frames-stable [ms]    Wait for screen to stabilize

Returns:
  "OK" on success
  "mcp" if fallback to mobile-mcp needed
  "ERROR: ..." on failure

Environment:
  SCRCPY_SOCKET - Socket path (default: /tmp/scrcpy-helper.sock)
  PREFER_MCP    - Set to "1" to force mobile-mcp usage
  DEVICE_ID     - Default device ID
EOF
        ;;

    *)
        echo "Unknown command: $1" >&2
        echo "Run '$0 help' for usage" >&2
        exit 1
        ;;
esac
