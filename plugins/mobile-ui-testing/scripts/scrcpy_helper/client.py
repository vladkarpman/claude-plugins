"""scrcpy client connection management."""

from __future__ import annotations

import sys
import threading
import time
from typing import Callable, Optional

import numpy as np

try:
    import scrcpy
    SCRCPY_AVAILABLE = True
except ImportError:
    SCRCPY_AVAILABLE = False


class ScrcpyClient:
    """Manages scrcpy connection to an Android device."""

    def __init__(self):
        self.client: "scrcpy.Client | None" = None
        self.device_id: str | None = None
        self.connected = False
        self.last_frame: np.ndarray | None = None
        self.last_frame_time: float = 0
        self.frame_count = 0
        self.lock = threading.Lock()
        self._on_frame_callbacks: list[Callable[[np.ndarray, float], None]] = []

    def _log(self, message: str) -> None:
        """Log to stderr."""
        print(f"[scrcpy-client] {message}", file=sys.stderr)

    def _on_frame(self, frame: np.ndarray) -> None:
        """Called when a new frame is received."""
        if frame is None:
            return

        timestamp = time.time()
        with self.lock:
            self.last_frame = frame
            self.last_frame_time = timestamp
            self.frame_count += 1

        # Notify callbacks
        for callback in self._on_frame_callbacks:
            try:
                callback(frame, timestamp)
            except Exception as e:
                self._log(f"Frame callback error: {e}")

    def add_frame_callback(self, callback: Callable[[np.ndarray, float], None]) -> None:
        """Add a callback for new frames."""
        self._on_frame_callbacks.append(callback)

    def remove_frame_callback(self, callback: Callable[[np.ndarray, float], None]) -> None:
        """Remove a frame callback."""
        if callback in self._on_frame_callbacks:
            self._on_frame_callbacks.remove(callback)

    def connect(self, device_id: str | None = None, max_fps: int = 60) -> bool:
        """Connect to device via scrcpy."""
        if not SCRCPY_AVAILABLE:
            self._log("scrcpy-client package not installed")
            return False

        if self.connected:
            self.disconnect()

        try:
            self.device_id = device_id

            # Create scrcpy client
            self.client = scrcpy.Client(
                device=device_id,
                max_fps=max_fps,
            )

            # Register frame listener
            self.client.add_listener(scrcpy.EVENT_FRAME, self._on_frame)

            # Start in a thread
            self.client.start(threaded=True)

            # Wait for first frame to confirm connection
            start_time = time.time()
            while self.last_frame is None and (time.time() - start_time) < 10:
                time.sleep(0.1)

            if self.last_frame is not None:
                self.connected = True
                self._log(f"Connected to {device_id or 'default device'}")
                return True
            else:
                self._log("Timeout waiting for first frame")
                self.disconnect()
                return False

        except Exception as e:
            self._log(f"Connection failed: {e}")
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Disconnect from device."""
        if self.client is not None:
            try:
                self.client.stop()
            except Exception as e:
                self._log(f"Error stopping client: {e}")
            self.client = None

        self.connected = False
        self.last_frame = None
        self.device_id = None
        self._log("Disconnected")

    def get_frame(self) -> tuple[np.ndarray | None, float]:
        """Get the most recent frame and its timestamp."""
        with self.lock:
            return self.last_frame, self.last_frame_time

    def get_resolution(self) -> tuple[int, int] | None:
        """Get current screen resolution."""
        if self.client is not None and self.connected:
            try:
                return self.client.resolution
            except Exception:
                pass
        return None

    def get_device_name(self) -> str | None:
        """Get device name."""
        if self.client is not None and self.connected:
            try:
                return self.client.device_name
            except Exception:
                pass
        return self.device_id

    @property
    def control(self) -> "scrcpy.ControlSender | None":
        """Get control sender for input injection."""
        if self.client is not None:
            return self.client.control
        return None

    def tap(self, x: int, y: int) -> bool:
        """Tap at coordinates."""
        if self.control is None:
            return False
        try:
            self.control.touch(x, y, scrcpy.ACTION_DOWN)
            self.control.touch(x, y, scrcpy.ACTION_UP)
            return True
        except Exception as e:
            self._log(f"Tap failed: {e}")
            return False

    def long_press(self, x: int, y: int, duration_ms: int = 500) -> bool:
        """Long press at coordinates."""
        if self.control is None:
            return False
        try:
            self.control.touch(x, y, scrcpy.ACTION_DOWN)
            time.sleep(duration_ms / 1000.0)
            self.control.touch(x, y, scrcpy.ACTION_UP)
            return True
        except Exception as e:
            self._log(f"Long press failed: {e}")
            return False

    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        steps: int = 20,
        duration_ms: int = 300
    ) -> bool:
        """Swipe from (x1,y1) to (x2,y2)."""
        if self.control is None:
            return False
        try:
            self.control.swipe(x1, y1, x2, y2, steps, duration_ms / steps / 1000.0)
            return True
        except Exception as e:
            self._log(f"Swipe failed: {e}")
            return False

    def scroll(self, x: int, y: int, h: int, v: int) -> bool:
        """Scroll at position (horizontal, vertical units)."""
        if self.control is None:
            return False
        try:
            self.control.scroll(x, y, h, v)
            return True
        except Exception as e:
            self._log(f"Scroll failed: {e}")
            return False

    def type_text(self, text: str) -> bool:
        """Type text."""
        if self.control is None:
            return False
        try:
            self.control.text(text)
            return True
        except Exception as e:
            self._log(f"Type failed: {e}")
            return False

    def key(self, keycode: int, action: int | None = None) -> bool:
        """Send keycode."""
        if self.control is None:
            return False
        try:
            if action is None:
                # Press and release
                self.control.keycode(keycode, scrcpy.ACTION_DOWN)
                self.control.keycode(keycode, scrcpy.ACTION_UP)
            else:
                self.control.keycode(keycode, action)
            return True
        except Exception as e:
            self._log(f"Key failed: {e}")
            return False

    def rotate(self) -> bool:
        """Rotate device."""
        if self.control is None:
            return False
        try:
            self.control.rotate_device()
            return True
        except Exception as e:
            self._log(f"Rotate failed: {e}")
            return False

    def set_screen_power(self, on: bool) -> bool:
        """Set screen power mode."""
        if self.control is None:
            return False
        try:
            mode = scrcpy.POWER_MODE_NORMAL if on else scrcpy.POWER_MODE_OFF
            self.control.set_screen_power_mode(mode)
            return True
        except Exception as e:
            self._log(f"Screen power failed: {e}")
            return False

    def expand_notifications(self) -> bool:
        """Expand notification panel."""
        if self.control is None:
            return False
        try:
            self.control.expand_notification_panel()
            return True
        except Exception as e:
            self._log(f"Expand notifications failed: {e}")
            return False

    def collapse_panels(self) -> bool:
        """Collapse notification/settings panels."""
        if self.control is None:
            return False
        try:
            self.control.collapse_panels()
            return True
        except Exception as e:
            self._log(f"Collapse panels failed: {e}")
            return False

    def expand_settings(self) -> bool:
        """Expand settings panel."""
        if self.control is None:
            return False
        try:
            self.control.expand_settings_panel()
            return True
        except Exception as e:
            self._log(f"Expand settings failed: {e}")
            return False

    def get_clipboard(self) -> str | None:
        """Get clipboard content."""
        if self.control is None:
            return None
        try:
            return self.control.get_clipboard()
        except Exception as e:
            self._log(f"Get clipboard failed: {e}")
            return None

    def set_clipboard(self, text: str, paste: bool = False) -> bool:
        """Set clipboard content."""
        if self.control is None:
            return False
        try:
            self.control.set_clipboard(text, paste)
            return True
        except Exception as e:
            self._log(f"Set clipboard failed: {e}")
            return False

    def status(self) -> dict:
        """Get client status."""
        resolution = self.get_resolution()
        return {
            "connected": self.connected,
            "device": self.device_id or self.get_device_name(),
            "resolution": list(resolution) if resolution else None,
            "frame_count": self.frame_count,
            "scrcpy_available": SCRCPY_AVAILABLE,
        }
