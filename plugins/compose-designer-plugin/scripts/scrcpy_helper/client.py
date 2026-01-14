"""scrcpy client connection management using MYScrcpy for scrcpy 3.x support."""

from __future__ import annotations

import sys
import threading
import time
from typing import Callable, Optional, TYPE_CHECKING

import numpy as np

from .frame_buffer import FrameBuffer
from .video import VideoRecorder

try:
    from adbutils import adb
    from myscrcpy.core import Session, VideoArgs, ControlArgs
    from myscrcpy.utils import Action, ScalePointR
    MYSCRCPY_AVAILABLE = True
except ImportError:
    MYSCRCPY_AVAILABLE = False
    adb = None
    Session = None
    VideoArgs = None
    ControlArgs = None
    Action = None
    ScalePointR = None


class ScrcpyClient:
    """Manages scrcpy connection to an Android device using MYScrcpy."""

    def __init__(self, max_buffer_frames: int = 120, max_buffer_seconds: float = 2.0):
        self.session: "Session | None" = None
        self.device_id: str | None = None
        self.connected = False
        self.last_frame: np.ndarray | None = None
        self.last_frame_time: float = 0
        self.frame_count = 0
        self.lock = threading.Lock()
        self._on_frame_callbacks: list[Callable[[np.ndarray, float], None]] = []
        self._frame_thread: threading.Thread | None = None
        self._running = False

        # Screen dimensions
        self._width = 0
        self._height = 0

        # Frame buffer for analysis
        self.frame_buffer = FrameBuffer(
            max_frames=max_buffer_frames,
            max_seconds=max_buffer_seconds
        )

        # Video recorder
        self.video_recorder = VideoRecorder()

    def _log(self, message: str) -> None:
        """Log to stderr."""
        print(f"[scrcpy-client] {message}", file=sys.stderr)

    def _frame_polling_loop(self) -> None:
        """Continuously poll for new frames."""
        while self._running and self.session is not None:
            try:
                if self.session.va is not None:
                    frame = self.session.va.get_frame()
                    if frame is not None:
                        self._on_frame(frame)
                time.sleep(0.016)  # ~60 fps polling
            except Exception as e:
                self._log(f"Frame polling error: {e}")
                time.sleep(0.1)

    def _on_frame(self, frame: np.ndarray) -> None:
        """Called when a new frame is received."""
        if frame is None:
            return

        timestamp = time.time()
        with self.lock:
            self.last_frame = frame
            self.last_frame_time = timestamp
            self.frame_count += 1
            if self._height == 0 and frame is not None:
                self._height, self._width = frame.shape[:2]

        # Add to frame buffer
        self.frame_buffer.add_frame(frame, timestamp)

        # Add to video recorder if recording
        self.video_recorder.add_frame(frame, timestamp)

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
        if not MYSCRCPY_AVAILABLE:
            self._log("MYScrcpy package not installed")
            return False

        if self.connected:
            self.disconnect()

        try:
            # Find device
            devices = adb.device_list()
            if not devices:
                self._log("No Android devices found")
                return False

            device = None
            if device_id:
                for d in devices:
                    if d.serial == device_id:
                        device = d
                        break
                if device is None:
                    self._log(f"Device {device_id} not found")
                    return False
            else:
                device = devices[0]

            self.device_id = device.serial

            # Create session with video and control
            self.session = Session(
                device,
                video_args=VideoArgs(max_size=1920, fps=max_fps),
                control_args=ControlArgs()
            )

            # Wait for video and control to be ready
            start_time = time.time()
            while (time.time() - start_time) < 10:
                if self.session.is_video_ready and self.session.is_control_ready:
                    break
                time.sleep(0.1)

            if not self.session.is_video_ready:
                self._log("Timeout waiting for video")
                self.disconnect()
                return False

            # Start frame polling thread
            self._running = True
            self._frame_thread = threading.Thread(target=self._frame_polling_loop, daemon=True)
            self._frame_thread.start()

            # Wait for first frame
            start_time = time.time()
            while self.last_frame is None and (time.time() - start_time) < 5:
                time.sleep(0.1)

            if self.last_frame is not None:
                self.connected = True
                self._log(f"Connected to {self.device_id}")
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
        self._running = False
        if self._frame_thread is not None:
            self._frame_thread.join(timeout=2)
            self._frame_thread = None

        if self.session is not None:
            try:
                self.session.disconnect()
            except Exception as e:
                self._log(f"Error stopping session: {e}")
            self.session = None

        self.connected = False
        self.last_frame = None
        self.device_id = None
        self._width = 0
        self._height = 0
        self._log("Disconnected")

    def get_frame(self) -> tuple[np.ndarray | None, float]:
        """Get the most recent frame and its timestamp."""
        with self.lock:
            return self.last_frame, self.last_frame_time

    def get_resolution(self) -> tuple[int, int] | None:
        """Get current screen resolution."""
        if self._width > 0 and self._height > 0:
            return (self._width, self._height)
        return None

    def get_device_name(self) -> str | None:
        """Get device name."""
        return self.device_id

    @property
    def control(self) -> "ControlArgs | None":
        """Get control adapter for input injection."""
        if self.session is not None and self.session.ca is not None:
            return self.session.ca
        return None

    def tap(self, x: int, y: int) -> bool:
        """Tap at coordinates."""
        if self.control is None or self._width == 0:
            return False
        try:
            # f_touch(action, x, y, width, height, touch_id)
            self.control.f_touch(Action.DOWN, x, y, self._width, self._height, 0)
            time.sleep(0.05)
            self.control.f_touch(Action.RELEASE, x, y, self._width, self._height, 0)
            return True
        except Exception as e:
            self._log(f"Tap failed: {e}")
            return False

    def long_press(self, x: int, y: int, duration_ms: int = 500) -> bool:
        """Long press at coordinates."""
        if self.control is None or self._width == 0:
            return False
        try:
            self.control.f_touch(Action.DOWN, x, y, self._width, self._height, 0)
            time.sleep(duration_ms / 1000.0)
            self.control.f_touch(Action.RELEASE, x, y, self._width, self._height, 0)
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
        if self.control is None or self._width == 0:
            return False
        try:
            step_delay = duration_ms / 1000.0 / steps
            dx = (x2 - x1) / steps
            dy = (y2 - y1) / steps

            # Touch down
            self.control.f_touch(Action.DOWN, x1, y1, self._width, self._height, 0)

            # Move through intermediate points
            for i in range(1, steps + 1):
                x = int(x1 + dx * i)
                y = int(y1 + dy * i)
                self.control.f_touch(Action.MOVE, x, y, self._width, self._height, 0)
                time.sleep(step_delay)

            # Touch up
            self.control.f_touch(Action.RELEASE, x2, y2, self._width, self._height, 0)
            return True
        except Exception as e:
            self._log(f"Swipe failed: {e}")
            return False

    def scroll(self, x: int, y: int, h: int, v: int) -> bool:
        """Scroll at position (horizontal, vertical units)."""
        if self.control is None or self._width == 0:
            return False
        try:
            # Simulate scroll as a series of small swipes
            scroll_distance = 100
            if v != 0:
                y2 = y - (v * scroll_distance)
                return self.swipe(x, y, x, y2, steps=10, duration_ms=200)
            elif h != 0:
                x2 = x - (h * scroll_distance)
                return self.swipe(x, y, x2, y, steps=10, duration_ms=200)
            return True
        except Exception as e:
            self._log(f"Scroll failed: {e}")
            return False

    def type_text(self, text: str) -> bool:
        """Type text using clipboard paste."""
        if self.control is None:
            return False
        try:
            self.control.f_text_paste(text, paste=True)
            return True
        except Exception as e:
            self._log(f"Type failed: {e}")
            return False

    def key(self, keycode: int, action: int | None = None) -> bool:
        """Send keycode."""
        if self.control is None:
            return False
        try:
            # MYScrcpy uses different key handling - use inject method if available
            # For now, fallback to adb for key events
            if self.device_id:
                import subprocess
                subprocess.run(['adb', '-s', self.device_id, 'shell', 'input', 'keyevent', str(keycode)],
                              capture_output=True, timeout=5)
                return True
            return False
        except Exception as e:
            self._log(f"Key failed: {e}")
            return False

    def rotate(self) -> bool:
        """Rotate device."""
        # Use adb to toggle rotation
        if self.device_id:
            try:
                import subprocess
                subprocess.run(['adb', '-s', self.device_id, 'shell', 'settings', 'put', 'system',
                               'accelerometer_rotation', '0'], capture_output=True, timeout=5)
                # Toggle between 0 and 1
                result = subprocess.run(['adb', '-s', self.device_id, 'shell', 'settings', 'get', 'system',
                                        'user_rotation'], capture_output=True, timeout=5, text=True)
                current = int(result.stdout.strip() or '0')
                new_rotation = (current + 1) % 4
                subprocess.run(['adb', '-s', self.device_id, 'shell', 'settings', 'put', 'system',
                               'user_rotation', str(new_rotation)], capture_output=True, timeout=5)
                return True
            except Exception as e:
                self._log(f"Rotate failed: {e}")
        return False

    def set_screen_power(self, on: bool) -> bool:
        """Set screen power mode."""
        if self.device_id:
            try:
                import subprocess
                if on:
                    subprocess.run(['adb', '-s', self.device_id, 'shell', 'input', 'keyevent', '224'],
                                  capture_output=True, timeout=5)  # WAKEUP
                else:
                    subprocess.run(['adb', '-s', self.device_id, 'shell', 'input', 'keyevent', '223'],
                                  capture_output=True, timeout=5)  # SLEEP
                return True
            except Exception as e:
                self._log(f"Screen power failed: {e}")
        return False

    def expand_notifications(self) -> bool:
        """Expand notification panel."""
        if self.device_id:
            try:
                import subprocess
                subprocess.run(['adb', '-s', self.device_id, 'shell', 'cmd', 'statusbar', 'expand-notifications'],
                              capture_output=True, timeout=5)
                return True
            except Exception as e:
                self._log(f"Expand notifications failed: {e}")
        return False

    def collapse_panels(self) -> bool:
        """Collapse notification/settings panels."""
        if self.device_id:
            try:
                import subprocess
                subprocess.run(['adb', '-s', self.device_id, 'shell', 'cmd', 'statusbar', 'collapse'],
                              capture_output=True, timeout=5)
                return True
            except Exception as e:
                self._log(f"Collapse panels failed: {e}")
        return False

    def expand_settings(self) -> bool:
        """Expand settings panel."""
        if self.device_id:
            try:
                import subprocess
                subprocess.run(['adb', '-s', self.device_id, 'shell', 'cmd', 'statusbar', 'expand-settings'],
                              capture_output=True, timeout=5)
                return True
            except Exception as e:
                self._log(f"Expand settings failed: {e}")
        return False

    def get_clipboard(self) -> str | None:
        """Get clipboard content."""
        # Not directly available in MYScrcpy, use adb
        if self.device_id:
            try:
                import subprocess
                result = subprocess.run(['adb', '-s', self.device_id, 'shell', 'am', 'broadcast',
                                        '-a', 'clipper.get', '-n', 'ca.zgrs.clipper/.ClipboardReceiver'],
                                       capture_output=True, timeout=5, text=True)
                return result.stdout.strip()
            except Exception:
                pass
        return None

    def set_clipboard(self, text: str, paste: bool = False) -> bool:
        """Set clipboard content."""
        if self.control is None:
            return False
        try:
            self.control.f_text_paste(text, paste=paste)
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
            "scrcpy_available": MYSCRCPY_AVAILABLE,
        }
