"""Unix socket server for scrcpy-helper."""

from __future__ import annotations

import json
import socket
import struct
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Optional, Union

from .client import ScrcpyClient

DEFAULT_SOCKET_PATH = "/tmp/scrcpy-helper.sock"

# Response type: either string or ("BINARY", bytes)
ResponseType = Union[str, tuple]


class ScrcpyHelperServer:
    """Unix socket server handling scrcpy commands."""

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH):
        self.socket_path = socket_path
        self.server_socket: socket.socket | None = None
        self.running = False
        self.lock = threading.Lock()

        # scrcpy client
        self.scrcpy = ScrcpyClient()

        # Command handlers - can return str or ("BINARY", bytes)
        self.commands: dict[str, Callable[[list[str]], ResponseType]] = {
            "status": self._cmd_status,
            "connect": self._cmd_connect,
            "disconnect": self._cmd_disconnect,
            "quit": self._cmd_quit,
        }

        # Register all commands from commands module
        self._register_all_commands()

    def _register_all_commands(self) -> None:
        """Register commands from commands module."""
        try:
            from .commands import register_all_commands
            register_all_commands(self)
        except ImportError as e:
            self._log(f"Warning: Could not load commands: {e}")

    def _log(self, message: str) -> None:
        """Log to stderr (stdout reserved for protocol)."""
        print(f"[scrcpy-helper] {message}", file=sys.stderr)

    def _cmd_status(self, args: list[str]) -> str:
        """Return server status as JSON."""
        status = self.scrcpy.status()
        # Add frame buffer info
        status["buffer"] = {
            "count": self.scrcpy.frame_buffer.get_frame_count(),
            "duration": round(self.scrcpy.frame_buffer.get_duration(), 3),
            "fps": round(self.scrcpy.frame_buffer.get_fps(), 1),
        }
        return json.dumps(status)

    def _cmd_connect(self, args: list[str]) -> str:
        """Connect to device via scrcpy."""
        device_id = args[0] if args else None
        max_fps = 60

        # Parse optional max_fps argument
        if len(args) > 1:
            try:
                max_fps = int(args[1])
            except ValueError:
                pass

        if self.scrcpy.connect(device_id, max_fps=max_fps):
            return "OK"
        else:
            return "ERROR: connection failed"

    def _cmd_disconnect(self, args: list[str]) -> str:
        """Disconnect from device."""
        self.scrcpy.disconnect()
        return "OK"

    def _cmd_quit(self, args: list[str]) -> str:
        """Shutdown the server."""
        self._log("Shutdown requested")
        self.scrcpy.disconnect()
        self.running = False
        return "OK"

    def handle_command(self, command_line: str) -> tuple[bool, bytes]:
        """
        Parse and execute a command.

        Returns:
            Tuple of (is_binary, response_bytes)
        """
        command_line = command_line.strip()
        if not command_line:
            return False, b"ERROR: empty command\n"

        parts = command_line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else []

        handler = self.commands.get(cmd)
        if handler is None:
            return False, f"ERROR: unknown command '{cmd}'\n".encode()

        try:
            result = handler(args)

            # Check for binary response
            if isinstance(result, tuple) and len(result) == 2 and result[0] == "BINARY":
                return True, result[1]

            # Text response
            if not result.endswith("\n"):
                result += "\n"
            return False, result.encode()

        except Exception as e:
            self._log(f"Error handling '{cmd}': {e}")
            return False, f"ERROR: {e}\n".encode()

    def handle_client(self, client_socket: socket.socket, addr: Any) -> None:
        """Handle a single client connection."""
        try:
            # Read until newline
            data = b""
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break

            if data:
                command = data.decode("utf-8", errors="replace")
                is_binary, response = self.handle_command(command)

                if is_binary:
                    # Send length-prefixed binary data
                    length = struct.pack(">I", len(response))
                    client_socket.sendall(length + response)
                else:
                    # Send text response
                    client_socket.sendall(response)

        except Exception as e:
            self._log(f"Client error: {e}")
        finally:
            client_socket.close()

    def cleanup_socket(self) -> None:
        """Remove stale socket file if it exists."""
        socket_file = Path(self.socket_path)
        if socket_file.exists():
            try:
                # Try to connect to see if server is running
                test_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                test_socket.settimeout(1)
                test_socket.connect(self.socket_path)
                test_socket.close()
                raise RuntimeError(f"Server already running at {self.socket_path}")
            except ConnectionRefusedError:
                # Stale socket, remove it
                self._log(f"Removing stale socket: {self.socket_path}")
                socket_file.unlink()
            except socket.timeout:
                # Stale socket, remove it
                self._log(f"Removing stale socket: {self.socket_path}")
                socket_file.unlink()

    def start(self) -> None:
        """Start the server."""
        self.cleanup_socket()

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)  # Allow periodic shutdown check

        self.running = True
        self._log(f"Server listening on {self.socket_path}")

        try:
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    self.handle_client(client_socket, addr)
                except socket.timeout:
                    continue
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the server and cleanup."""
        self.running = False

        # Disconnect scrcpy
        self.scrcpy.disconnect()

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        # Remove socket file
        socket_file = Path(self.socket_path)
        if socket_file.exists():
            try:
                socket_file.unlink()
                self._log("Socket file removed")
            except Exception as e:
                self._log(f"Failed to remove socket: {e}")

        self._log("Server stopped")

    def register_command(self, name: str, handler: Callable[[list[str]], ResponseType]) -> None:
        """Register a new command handler."""
        self.commands[name.lower()] = handler
