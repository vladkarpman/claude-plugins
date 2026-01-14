#!/usr/bin/env python3
"""scrcpy-helper entry point.

Starts the Unix socket server for fast screenshot and input injection.

Usage:
    python3 scrcpy-helper.py [--socket PATH]
"""

import argparse
import signal
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scrcpy_helper.server import ScrcpyHelperServer, DEFAULT_SOCKET_PATH


def main() -> int:
    parser = argparse.ArgumentParser(
        description="scrcpy-helper: Fast screenshot and input injection server"
    )
    parser.add_argument(
        "--socket",
        default=DEFAULT_SOCKET_PATH,
        help=f"Unix socket path (default: {DEFAULT_SOCKET_PATH})",
    )
    args = parser.parse_args()

    server = ScrcpyHelperServer(socket_path=args.socket)

    # Handle signals for graceful shutdown
    def signal_handler(signum: int, frame: object) -> None:
        print("\n[scrcpy-helper] Received shutdown signal", file=sys.stderr)
        server.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        server.start()
        return 0
    except RuntimeError as e:
        print(f"[scrcpy-helper] Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[scrcpy-helper] Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
