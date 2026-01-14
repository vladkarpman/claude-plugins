"""Command handlers for scrcpy-helper server."""

from __future__ import annotations

import base64
import io
import json
import struct
import time
import zipfile
from typing import TYPE_CHECKING, Callable, Dict, Tuple

import numpy as np

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

if TYPE_CHECKING:
    from .server import ScrcpyHelperServer


def frame_to_png(frame: np.ndarray) -> bytes:
    """Convert numpy frame to PNG bytes."""
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow not installed")

    # scrcpy gives BGR, PIL wants RGB
    if len(frame.shape) == 3 and frame.shape[2] == 3:
        rgb = frame[:, :, ::-1]
    else:
        rgb = frame

    img = Image.fromarray(rgb)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def register_screenshot_commands(server: "ScrcpyHelperServer") -> None:
    """Register screenshot and frame buffer commands."""

    def cmd_screenshot(args: list[str]) -> str | bytes:
        """Take a screenshot. Returns PNG bytes or base64 string."""
        if not server.scrcpy.connected:
            return "ERROR: not connected"

        frame, timestamp = server.scrcpy.get_frame()
        if frame is None:
            return "ERROR: no frame available"

        try:
            png_data = frame_to_png(frame)
        except Exception as e:
            return f"ERROR: {e}"

        # Check if base64 output requested
        if args and args[0].lower() == "base64":
            return base64.b64encode(png_data).decode("ascii")

        # Return raw PNG with length prefix
        # Mark this as binary response
        return ("BINARY", png_data)

    def cmd_frames_recent(args: list[str]) -> str | bytes:
        """Get recent frames as ZIP. Usage: frames recent <n>"""
        if not args:
            return "ERROR: usage: frames recent <n>"

        try:
            n = int(args[0])
        except ValueError:
            return "ERROR: n must be integer"

        frames = server.scrcpy.frame_buffer.get_recent(n)
        if not frames:
            return "ERROR: no frames in buffer"

        # Create ZIP with frames
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, (ts, frame) in enumerate(frames):
                    png_data = frame_to_png(frame)
                    zf.writestr(f"frame_{i:03d}_{ts:.3f}.png", png_data)

            return ("BINARY", zip_buffer.getvalue())
        except Exception as e:
            return f"ERROR: {e}"

    def cmd_frames_around(args: list[str]) -> str | bytes:
        """Get frames around timestamp. Usage: frames around <ts> <before> <after>"""
        if len(args) < 3:
            return "ERROR: usage: frames around <timestamp> <before> <after>"

        try:
            ts = float(args[0])
            before = int(args[1])
            after = int(args[2])
        except ValueError:
            return "ERROR: invalid arguments"

        frames = server.scrcpy.frame_buffer.get_around(ts, before, after)
        if not frames:
            return "ERROR: no frames found"

        # Create ZIP with frames
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, (frame_ts, frame) in enumerate(frames):
                    png_data = frame_to_png(frame)
                    zf.writestr(f"frame_{i:03d}_{frame_ts:.3f}.png", png_data)

            return ("BINARY", zip_buffer.getvalue())
        except Exception as e:
            return f"ERROR: {e}"

    def cmd_frames_diff(args: list[str]) -> str:
        """Check if screen changed between timestamps. Usage: frames diff <ts1> <ts2>"""
        if len(args) < 2:
            return "ERROR: usage: frames diff <ts1> <ts2>"

        try:
            ts1 = float(args[0])
            ts2 = float(args[1])
        except ValueError:
            return "ERROR: timestamps must be floats"

        changed = server.scrcpy.frame_buffer.get_timestamps_diff(ts1, ts2)
        return "true" if changed else "false"

    def cmd_frames_stable(args: list[str]) -> str:
        """Wait for screen to stabilize. Usage: frames stable [timeout_ms]"""
        timeout = 5.0
        if args:
            try:
                timeout = float(args[0]) / 1000.0
            except ValueError:
                pass

        if server.scrcpy.frame_buffer.wait_stable(timeout=timeout):
            return "OK"
        else:
            return "TIMEOUT"

    def cmd_frames_info(args: list[str]) -> str:
        """Get frame buffer info."""
        fb = server.scrcpy.frame_buffer
        info = {
            "count": fb.get_frame_count(),
            "duration": round(fb.get_duration(), 3),
            "fps": round(fb.get_fps(), 1),
            "stable": fb.is_stable(),
        }
        return json.dumps(info)

    # Register all commands
    server.register_command("screenshot", cmd_screenshot)

    # Frames subcommands - we'll parse the subcommand in a wrapper
    def cmd_frames(args: list[str]) -> str | bytes:
        if not args:
            return "ERROR: usage: frames <recent|around|diff|stable|info> [args...]"

        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "recent":
            return cmd_frames_recent(subargs)
        elif subcmd == "around":
            return cmd_frames_around(subargs)
        elif subcmd == "diff":
            return cmd_frames_diff(subargs)
        elif subcmd == "stable":
            return cmd_frames_stable(subargs)
        elif subcmd == "info":
            return cmd_frames_info(subargs)
        else:
            return f"ERROR: unknown frames subcommand '{subcmd}'"

    server.register_command("frames", cmd_frames)


def register_input_commands(server: "ScrcpyHelperServer") -> None:
    """Register input injection commands."""

    def cmd_tap(args: list[str]) -> str:
        """Tap at coordinates. Usage: tap <x> <y>"""
        if len(args) < 2:
            return "ERROR: usage: tap <x> <y>"

        try:
            x = int(args[0])
            y = int(args[1])
        except ValueError:
            return "ERROR: coordinates must be integers"

        if not server.scrcpy.connected:
            return "ERROR: not connected"

        if server.scrcpy.tap(x, y):
            return "OK"
        else:
            return "ERROR: tap failed"

    def cmd_longpress(args: list[str]) -> str:
        """Long press at coordinates. Usage: longpress <x> <y> [duration_ms]"""
        if len(args) < 2:
            return "ERROR: usage: longpress <x> <y> [duration_ms]"

        try:
            x = int(args[0])
            y = int(args[1])
            duration = int(args[2]) if len(args) > 2 else 500
        except ValueError:
            return "ERROR: invalid arguments"

        if not server.scrcpy.connected:
            return "ERROR: not connected"

        if server.scrcpy.long_press(x, y, duration):
            return "OK"
        else:
            return "ERROR: long press failed"

    def cmd_swipe(args: list[str]) -> str:
        """Swipe between coordinates. Usage: swipe <x1> <y1> <x2> <y2> [steps]"""
        if len(args) < 4:
            return "ERROR: usage: swipe <x1> <y1> <x2> <y2> [steps]"

        try:
            x1 = int(args[0])
            y1 = int(args[1])
            x2 = int(args[2])
            y2 = int(args[3])
            steps = int(args[4]) if len(args) > 4 else 20
        except ValueError:
            return "ERROR: invalid arguments"

        if not server.scrcpy.connected:
            return "ERROR: not connected"

        if server.scrcpy.swipe(x1, y1, x2, y2, steps):
            return "OK"
        else:
            return "ERROR: swipe failed"

    def cmd_scroll(args: list[str]) -> str:
        """Scroll at position. Usage: scroll <x> <y> <h> <v>"""
        if len(args) < 4:
            return "ERROR: usage: scroll <x> <y> <horizontal> <vertical>"

        try:
            x = int(args[0])
            y = int(args[1])
            h = int(args[2])
            v = int(args[3])
        except ValueError:
            return "ERROR: invalid arguments"

        if not server.scrcpy.connected:
            return "ERROR: not connected"

        if server.scrcpy.scroll(x, y, h, v):
            return "OK"
        else:
            return "ERROR: scroll failed"

    def cmd_type(args: list[str]) -> str:
        """Type text. Usage: type <text>"""
        if not args:
            return "ERROR: usage: type <text>"

        text = " ".join(args)

        if not server.scrcpy.connected:
            return "ERROR: not connected"

        if server.scrcpy.type_text(text):
            return "OK"
        else:
            return "ERROR: type failed"

    def cmd_key(args: list[str]) -> str:
        """Send keycode. Usage: key <keycode>"""
        if not args:
            return "ERROR: usage: key <keycode>"

        # Map common key names to Android keycodes
        key_map = {
            "back": 4,
            "home": 3,
            "menu": 82,
            "enter": 66,
            "search": 84,
            "delete": 67,
            "backspace": 67,
            "volume_up": 24,
            "volume_down": 25,
            "power": 26,
            "camera": 27,
            "tab": 61,
            "space": 62,
            "escape": 111,
            "dpad_up": 19,
            "dpad_down": 20,
            "dpad_left": 21,
            "dpad_right": 22,
            "dpad_center": 23,
        }

        key_name = args[0].lower()
        if key_name in key_map:
            keycode = key_map[key_name]
        else:
            try:
                keycode = int(key_name)
            except ValueError:
                return f"ERROR: unknown key '{key_name}'"

        if not server.scrcpy.connected:
            return "ERROR: not connected"

        if server.scrcpy.key(keycode):
            return "OK"
        else:
            return "ERROR: key failed"

    # Register all input commands
    server.register_command("tap", cmd_tap)
    server.register_command("longpress", cmd_longpress)
    server.register_command("swipe", cmd_swipe)
    server.register_command("scroll", cmd_scroll)
    server.register_command("type", cmd_type)
    server.register_command("key", cmd_key)


def register_device_commands(server: "ScrcpyHelperServer") -> None:
    """Register device control commands."""

    def cmd_rotate(args: list[str]) -> str:
        """Rotate device."""
        if not server.scrcpy.connected:
            return "ERROR: not connected"

        if server.scrcpy.rotate():
            return "OK"
        else:
            return "ERROR: rotate failed"

    def cmd_screen(args: list[str]) -> str:
        """Control screen power. Usage: screen <on|off>"""
        if not args:
            return "ERROR: usage: screen <on|off>"

        if not server.scrcpy.connected:
            return "ERROR: not connected"

        mode = args[0].lower()
        if mode == "on":
            if server.scrcpy.set_screen_power(True):
                return "OK"
        elif mode == "off":
            if server.scrcpy.set_screen_power(False):
                return "OK"
        else:
            return "ERROR: use 'on' or 'off'"

        return "ERROR: screen control failed"

    def cmd_notifications(args: list[str]) -> str:
        """Control notifications panel. Usage: notifications <expand|collapse>"""
        if not args:
            return "ERROR: usage: notifications <expand|collapse>"

        if not server.scrcpy.connected:
            return "ERROR: not connected"

        mode = args[0].lower()
        if mode == "expand":
            if server.scrcpy.expand_notifications():
                return "OK"
        elif mode == "collapse":
            if server.scrcpy.collapse_panels():
                return "OK"
        else:
            return "ERROR: use 'expand' or 'collapse'"

        return "ERROR: notifications control failed"

    def cmd_settings(args: list[str]) -> str:
        """Expand settings panel."""
        if not server.scrcpy.connected:
            return "ERROR: not connected"

        if server.scrcpy.expand_settings():
            return "OK"
        else:
            return "ERROR: settings failed"

    def cmd_clipboard(args: list[str]) -> str:
        """Clipboard operations. Usage: clipboard <get|set|paste> [text]"""
        if not args:
            return "ERROR: usage: clipboard <get|set|paste> [text]"

        if not server.scrcpy.connected:
            return "ERROR: not connected"

        cmd = args[0].lower()
        if cmd == "get":
            result = server.scrcpy.get_clipboard()
            if result is not None:
                return result
            else:
                return "ERROR: clipboard get failed"
        elif cmd == "set":
            if len(args) < 2:
                return "ERROR: usage: clipboard set <text>"
            text = " ".join(args[1:])
            if server.scrcpy.set_clipboard(text, paste=False):
                return "OK"
            else:
                return "ERROR: clipboard set failed"
        elif cmd == "paste":
            if len(args) < 2:
                return "ERROR: usage: clipboard paste <text>"
            text = " ".join(args[1:])
            if server.scrcpy.set_clipboard(text, paste=True):
                return "OK"
            else:
                return "ERROR: clipboard paste failed"
        else:
            return f"ERROR: unknown clipboard command '{cmd}'"

    # Register all device commands
    server.register_command("rotate", cmd_rotate)
    server.register_command("screen", cmd_screen)
    server.register_command("notifications", cmd_notifications)
    server.register_command("settings", cmd_settings)
    server.register_command("clipboard", cmd_clipboard)


def register_video_commands(server: "ScrcpyHelperServer") -> None:
    """Register video recording commands."""

    def cmd_record(args: list[str]) -> str:
        """Video recording control. Usage: record <start|stop|status> [filename]"""
        if not args:
            return "ERROR: usage: record <start|stop|status> [filename]"

        subcmd = args[0].lower()

        if subcmd == "start":
            if not server.scrcpy.connected:
                return "ERROR: not connected"

            if server.scrcpy.video_recorder.start():
                return "OK"
            else:
                return "ERROR: already recording"

        elif subcmd == "stop":
            filename = args[1] if len(args) > 1 else None
            result = server.scrcpy.video_recorder.stop(filename)
            if result:
                return result
            else:
                return "ERROR: no recording or save failed"

        elif subcmd == "status":
            status = server.scrcpy.video_recorder.get_status()
            return json.dumps(status)

        else:
            return f"ERROR: unknown record command '{subcmd}'"

    server.register_command("record", cmd_record)


def register_all_commands(server: "ScrcpyHelperServer") -> None:
    """Register all command handlers."""
    register_screenshot_commands(server)
    register_input_commands(server)
    register_device_commands(server)
    register_video_commands(server)
