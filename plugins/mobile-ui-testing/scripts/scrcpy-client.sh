#!/bin/bash
# scrcpy-client.sh - Send commands to scrcpy-helper server
#
# Usage:
#   scrcpy-client.sh <command> [args...]
#
# Examples:
#   scrcpy-client.sh status
#   scrcpy-client.sh connect DEVICE_ID
#   scrcpy-client.sh tap 540 800
#   scrcpy-client.sh screenshot > frame.png

set -e

SOCKET_PATH="${SCRCPY_SOCKET:-/tmp/scrcpy-helper.sock}"

if [[ $# -eq 0 ]]; then
    echo "Usage: scrcpy-client.sh <command> [args...]" >&2
    echo "" >&2
    echo "Commands:" >&2
    echo "  status              Show connection status" >&2
    echo "  connect [device]    Connect to device" >&2
    echo "  disconnect          Disconnect from device" >&2
    echo "  quit                Shutdown server" >&2
    exit 1
fi

# Check if socket exists
if [[ ! -S "$SOCKET_PATH" ]]; then
    echo "ERROR: scrcpy-helper not running (socket not found: $SOCKET_PATH)" >&2
    exit 1
fi

# Join all arguments into a single command
COMMAND="$*"

# Send command and receive response
# Using timeout to prevent hanging
if command -v nc &> /dev/null; then
    echo "$COMMAND" | nc -U -w 5 "$SOCKET_PATH"
elif command -v socat &> /dev/null; then
    echo "$COMMAND" | socat -t 5 - "UNIX-CONNECT:$SOCKET_PATH"
else
    echo "ERROR: Neither 'nc' (netcat) nor 'socat' found. Install one of them." >&2
    exit 1
fi
