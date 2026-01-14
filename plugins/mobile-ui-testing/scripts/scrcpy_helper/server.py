"""Unix socket server for scrcpy-helper."""

import json
import os
import socket
import struct
import sys
import threading
from pathlib import Path
from typing import Any, Callable

DEFAULT_SOCKET_PATH = "/tmp/scrcpy-helper.sock"


class ScrcpyHelperServer:
    """Unix socket server handling scrcpy commands."""

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH):
        self.socket_path = socket_path
        self.server_socket: socket.socket | None = None
        self.running = False
        self.lock = threading.Lock()

        # Device state (will be managed by client module in Task 2)
        self.connected = False
        self.device_id: str | None = None

        # Command handlers
        self.commands: dict[str, Callable[[list[str]], str]] = {
            "status": self._cmd_status,
            "connect": self._cmd_connect,
            "disconnect": self._cmd_disconnect,
            "quit": self._cmd_quit,
        }

    def _log(self, message: str) -> None:
        """Log to stderr (stdout reserved for protocol)."""
        print(f"[scrcpy-helper] {message}", file=sys.stderr)

    def _cmd_status(self, args: list[str]) -> str:
        """Return server status as JSON."""
        status = {
            "connected": self.connected,
            "device": self.device_id,
        }
        return json.dumps(status)

    def _cmd_connect(self, args: list[str]) -> str:
        """Connect to device (stub - actual implementation in Task 2)."""
        device_id = args[0] if args else None
        with self.lock:
            self.device_id = device_id
            self.connected = True
        self._log(f"Connected to device: {device_id or 'default'}")
        return "OK"

    def _cmd_disconnect(self, args: list[str]) -> str:
        """Disconnect from device."""
        with self.lock:
            self.connected = False
            self.device_id = None
        self._log("Disconnected")
        return "OK"

    def _cmd_quit(self, args: list[str]) -> str:
        """Shutdown the server."""
        self._log("Shutdown requested")
        self.running = False
        return "OK"

    def handle_command(self, command_line: str) -> bytes:
        """Parse and execute a command, return response bytes."""
        command_line = command_line.strip()
        if not command_line:
            return b"ERROR: empty command\n"

        parts = command_line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else []

        handler = self.commands.get(cmd)
        if handler is None:
            return f"ERROR: unknown command '{cmd}'\n".encode()

        try:
            result = handler(args)
            # Ensure response ends with newline
            if not result.endswith("\n"):
                result += "\n"
            return result.encode()
        except Exception as e:
            self._log(f"Error handling '{cmd}': {e}")
            return f"ERROR: {e}\n".encode()

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
                response = self.handle_command(command)
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

    def register_command(self, name: str, handler: Callable[[list[str]], str]) -> None:
        """Register a new command handler."""
        self.commands[name.lower()] = handler

    def send_binary_response(self, client_socket: socket.socket, data: bytes) -> None:
        """Send binary response with length prefix."""
        length = struct.pack(">I", len(data))
        client_socket.sendall(length + data)
