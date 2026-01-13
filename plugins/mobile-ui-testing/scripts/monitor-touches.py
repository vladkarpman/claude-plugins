#!/usr/bin/env python3
"""
Real-time touch monitor that detects touch UP events and triggers callbacks.
Reads from adb getevent output and parses touch coordinates.
"""

import subprocess
import re
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class TouchEvent:
    timestamp: float  # seconds since epoch
    x: int  # raw coordinate
    y: int  # raw coordinate
    gesture: str  # "tap", "swipe", "long_press"
    duration_ms: int

class TouchMonitor:
    def __init__(self, device_id: str, output_dir: str):
        self.device_id = device_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Touch state
        self.touch_down_time: Optional[float] = None
        self.touch_down_x: Optional[int] = None
        self.touch_down_y: Optional[int] = None
        self.current_x: Optional[int] = None
        self.current_y: Optional[int] = None

        # Coordinate bounds (from device)
        self.max_x = 1080  # default, will be updated
        self.max_y = 2340  # default, will be updated

        # Screen size
        self.screen_width = 1080
        self.screen_height = 2340

        # Events log
        self.events: list[dict] = []
        self.event_count = 0

    def _get_device_info(self):
        """Get screen size and coordinate bounds from device."""
        # Get screen size
        result = subprocess.run(
            ["adb", "-s", self.device_id, "shell", "wm", "size"],
            capture_output=True, text=True
        )
        match = re.search(r"(\d+)x(\d+)", result.stdout)
        if match:
            self.screen_width = int(match.group(1))
            self.screen_height = int(match.group(2))

        # Get touch coordinate bounds
        result = subprocess.run(
            ["adb", "-s", self.device_id, "shell", "getevent", "-lp"],
            capture_output=True, text=True
        )
        # Parse ABS_MT_POSITION_X max
        for line in result.stdout.split("\n"):
            if "ABS_MT_POSITION_X" in line:
                match = re.search(r"max (\d+)", line)
                if match:
                    self.max_x = int(match.group(1))
            if "ABS_MT_POSITION_Y" in line:
                match = re.search(r"max (\d+)", line)
                if match:
                    self.max_y = int(match.group(1))

        print(f"Screen: {self.screen_width}x{self.screen_height}", file=sys.stderr)
        print(f"Touch bounds: {self.max_x}x{self.max_y}", file=sys.stderr)

    def _raw_to_screen(self, raw_x: int, raw_y: int) -> tuple[int, int]:
        """Convert raw touch coordinates to screen pixels."""
        screen_x = int((raw_x / self.max_x) * self.screen_width)
        screen_y = int((raw_y / self.max_y) * self.screen_height)
        return screen_x, screen_y

    def _classify_gesture(self, duration_ms: int, distance_px: float) -> str:
        """Classify touch gesture based on duration and movement in screen pixels."""
        if distance_px >= 100:
            return "swipe"
        elif duration_ms >= 500:
            return "long_press"
        elif duration_ms < 200 and distance_px < 50:
            return "tap"
        else:
            # Ambiguous: 200-499ms with < 100px, or < 500ms with 50-99px
            # Default to tap for simplicity
            return "tap"

    def _on_touch_up(self):
        """Called when touch UP is detected."""
        if self.touch_down_time is None:
            return

        now = time.time()
        duration_ms = int((now - self.touch_down_time) * 1000)

        # Convert to screen coordinates
        screen_x, screen_y = self._raw_to_screen(
            self.current_x or self.touch_down_x or 0,
            self.current_y or self.touch_down_y or 0
        )
        start_screen_x, start_screen_y = self._raw_to_screen(
            self.touch_down_x or 0,
            self.touch_down_y or 0
        )

        # Calculate movement distance in screen pixels
        dx = screen_x - start_screen_x
        dy = screen_y - start_screen_y
        distance_px = (dx**2 + dy**2) ** 0.5

        gesture = self._classify_gesture(duration_ms, distance_px)

        self.event_count += 1
        event = {
            "index": self.event_count,
            "timestamp": now,
            "x": screen_x,
            "y": screen_y,
            "gesture": gesture,
            "duration_ms": duration_ms,
            "screenshot": f"touch_{self.event_count:03d}.png",
            "screen_width": self.screen_width,
            "screen_height": self.screen_height
        }
        self.events.append(event)

        # Save events incrementally (survives kill -9)
        summary_path = self.output_dir / "touch_events.json"
        with open(summary_path, "w") as f:
            json.dump(self.events, f, indent=2)

        # Output event as JSON line (for real-time processing)
        print(json.dumps(event), flush=True)

        # Reset state
        self.touch_down_time = None
        self.touch_down_x = None
        self.touch_down_y = None

    def _process_line(self, line: str):
        """Process a single getevent output line."""
        # Format: [timestamp] /dev/input/eventX: TYPE CODE VALUE
        # Example: [    1234.567890] /dev/input/event9: EV_ABS ABS_MT_POSITION_X 00000abc

        match = re.match(r"\[\s*([\d.]+)\]\s+\S+:\s+(\w+)\s+(\w+)\s+(\w+)", line)
        if not match:
            return

        timestamp_str, ev_type, code, value_hex = match.groups()

        if ev_type == "EV_ABS":
            value = int(value_hex, 16)
            if code == "ABS_MT_POSITION_X":
                self.current_x = value
                if self.touch_down_x is None:
                    self.touch_down_x = value
            elif code == "ABS_MT_POSITION_Y":
                self.current_y = value
                if self.touch_down_y is None:
                    self.touch_down_y = value

        elif ev_type == "EV_KEY":
            if code == "BTN_TOUCH":
                # With -l flag, values are "DOWN"/"UP" not hex codes
                if value_hex in ("00000001", "DOWN"):
                    self.touch_down_time = time.time()
                elif value_hex in ("00000000", "UP"):
                    self._on_touch_up()

    def start(self):
        """Start monitoring touch events."""
        self._get_device_info()

        print(f"Starting touch monitor for {self.device_id}...", file=sys.stderr)
        print("Touch events will be output as JSON lines.", file=sys.stderr)

        # Start getevent
        proc = subprocess.Popen(
            ["adb", "-s", self.device_id, "shell", "getevent", "-lt"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            for line in proc.stdout:
                self._process_line(line.strip())
        except KeyboardInterrupt:
            pass
        finally:
            proc.terminate()

            # Save events summary
            summary_path = self.output_dir / "touch_events.json"
            with open(summary_path, "w") as f:
                json.dump(self.events, f, indent=2)
            print(f"\nSaved {len(self.events)} events to {summary_path}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: monitor-touches.py <device-id> <output-dir>", file=sys.stderr)
        sys.exit(1)

    device_id = sys.argv[1]
    output_dir = sys.argv[2]

    monitor = TouchMonitor(device_id, output_dir)
    monitor.start()
