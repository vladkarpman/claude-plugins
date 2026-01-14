# scrcpy-helper Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a scrcpy-based helper service that dramatically speeds up screenshot capture, input injection, and enables frame buffer analysis for the mobile-ui-testing plugin.

**Architecture:** Unix socket server maintaining persistent scrcpy connection, providing instant frame access and fast input injection. Integrates alongside existing mobile-mcp (which still handles element finding via uiautomator).

**Tech Stack:** Python 3.10+, py-scrcpy-client, Unix sockets, adb (for element listing)

---

## Problem Statement

Current mobile-mcp approach has speed limitations:
- Screenshot: 1-3s (adb screencap + pull)
- Touch input: 100-300ms per command
- Video recording: Requires post-processing with ffmpeg

## Solution

scrcpy-helper provides:
- Instant screenshots (~10ms, frame already in memory)
- Fast input (~50ms, direct protocol)
- Continuous frame buffer for analysis
- No video post-processing needed

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Claude Code Session                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────────────────┐  │
│  │ Plugin Hook  │────────►│  scrcpy-helper.py        │  │
│  │ SessionStart │  start  │  (background daemon)     │  │
│  └──────────────┘         │                          │  │
│                           │  • Unix socket server    │  │
│  ┌──────────────┐         │  • scrcpy client         │  │
│  │ /run-test    │◄───────►│  • Frame buffer (60fps)  │  │
│  │ /record-test │  fast   │  • Input controller      │  │
│  └──────────────┘  calls  └──────────────────────────┘  │
│                                                          │
│  ┌──────────────┐         ┌──────────────────────────┐  │
│  │ mobile-mcp   │◄───────►│  Android Device          │  │
│  │ (elements)   │         │                          │  │
│  └──────────────┘         └──────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## API Specification

**Socket:** `/tmp/scrcpy-helper.sock`

**Protocol:** Line-based commands, length-prefixed binary responses for images.

### Commands

#### Screenshots & Frames
```
screenshot                    → 4-byte length + PNG bytes
screenshot base64             → base64 string + newline
frames recent <n>             → ZIP of last N frames
frames around <ts> <b> <a>    → Frames around timestamp
frames diff <ts1> <ts2>       → "true" or "false"
frames stable [timeout_ms]    → Blocks until screen stable, returns "OK" or "TIMEOUT"
```

#### Touch & Gestures
```
tap <x> <y>                   → OK
longpress <x> <y> [duration]  → OK
swipe <x1> <y1> <x2> <y2> [steps] → OK
scroll <x> <y> <h> <v>        → OK
```

#### Text & Keys
```
type <text>                   → OK
key <keycode>                 → OK
```

Keycodes: back, home, enter, menu, volume_up, volume_down, power

#### Device Control
```
rotate                        → OK
screen on|off                 → OK
notifications expand|collapse → OK
settings                      → OK
```

#### Clipboard
```
clipboard get                 → text content
clipboard set <text>          → OK
clipboard paste <text>        → OK (set + paste)
```

#### Recording (Frame Buffer)
```
record start                  → OK
record stop                   → path to saved video
record status                 → JSON {recording: bool, frames: int, duration: float}
```

#### Connection
```
status                        → JSON {connected, device, resolution, fps}
connect [device_id]           → OK
disconnect                    → OK
```

### Response Format

| Response Type | Format |
|---------------|--------|
| Binary (screenshot) | 4 bytes (uint32 big-endian length) + bytes |
| Success | `OK\n` |
| Error | `ERROR: message\n` |
| Text data | `text content\n` |
| JSON | `{"key": "value"}\n` |

## Frame Buffer Design

```python
class FrameBuffer:
    """Circular buffer holding recent frames for analysis."""

    def __init__(self, max_frames: int = 120, max_seconds: float = 2.0):
        self.frames: deque[tuple[float, np.ndarray]] = deque(maxlen=max_frames)
        self.max_seconds = max_seconds

    def add_frame(self, frame: np.ndarray) -> None:
        """Add frame with current timestamp."""
        self.frames.append((time.time(), frame))
        self._cleanup_old()

    def get_latest(self) -> np.ndarray | None:
        """Get most recent frame."""
        return self.frames[-1][1] if self.frames else None

    def get_around(self, timestamp: float, before: int = 3, after: int = 5) -> list:
        """Get frames around a timestamp."""
        # Implementation

    def is_stable(self, threshold: float = 0.98, samples: int = 3) -> bool:
        """Check if recent frames are similar (screen stopped changing)."""
        # Compare last N frames using SSIM or perceptual hash

    def wait_stable(self, timeout: float = 5.0, threshold: float = 0.98) -> bool:
        """Block until screen is stable or timeout."""
        # Implementation
```

## Integration Points

### 1. Recording Pipeline

**Before:**
```
adb getevent → adb screenrecord → stop → pull video → ffmpeg → frames
```

**After:**
```
adb getevent → scrcpy frame buffer → get_around(touch_time) → instant frames
```

### 2. Test Runner

**Before (each step):**
```python
mobile_mcp.tap(x, y)           # 300ms
mobile_mcp.take_screenshot()    # 2000ms
```

**After:**
```python
scrcpy_helper.tap(x, y)        # 50ms
scrcpy_helper.screenshot()      # 10ms
```

### 3. Assertions

**New capabilities:**
```yaml
- wait_for_stable: 5s          # Wait until screen stops changing
- verify_clipboard: "text"     # Check clipboard contents
- verify_orientation: landscape
```

### 4. Reports

**Before:**
```
20 steps × 2s screenshot = 40s for captures
```

**After:**
```
20 steps × 10ms = 0.2s for captures
+ Optional: Full video of test run
```

## Configuration

In `.claude/mobile-ui-testing.yaml`:

```yaml
# scrcpy-helper settings
scrcpy:
  enabled: true                 # Use scrcpy-helper (default: true if available)
  socket: /tmp/scrcpy-helper.sock
  frame_buffer_size: 120        # Max frames to keep (~2s at 60fps)
  frame_buffer_seconds: 2.0     # Max age of frames
  max_fps: 60                   # Limit frame rate
  save_video: false             # Save test runs as video
  video_output: tests/videos/   # Video output directory
```

## File Structure

```
scripts/
├── scrcpy-helper/
│   ├── __init__.py
│   ├── server.py           # Unix socket server
│   ├── client.py           # scrcpy connection management
│   ├── frame_buffer.py     # Frame storage and analysis
│   ├── commands.py         # Command handlers
│   └── video.py            # Video recording/saving
├── scrcpy-helper.py        # Entry point (starts server)
└── scrcpy-client.sh        # Bash helper for sending commands
```

## Dependencies

New Python dependencies:
```
scrcpy-client>=0.4.0          # or py-scrcpy-client
numpy                          # Frame handling
Pillow                         # Image encoding
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Device disconnected | Auto-reconnect, queue commands |
| Socket already exists | Remove stale socket, restart |
| scrcpy connection fails | Fall back to mobile-mcp |
| Command timeout | Return ERROR with reason |

## Graceful Degradation

If scrcpy-helper is unavailable:
1. Plugin detects missing socket
2. Falls back to mobile-mcp for all operations
3. Logs warning about slower performance

## Implementation Tasks

### Task 1: Core Server Infrastructure
- Unix socket server with command parsing
- Connection lifecycle management
- Basic status and connect commands

### Task 2: scrcpy Client Integration
- py-scrcpy-client connection
- Frame event handling
- Auto-reconnect on disconnect

### Task 3: Frame Buffer
- Circular buffer implementation
- Timestamp-based frame retrieval
- Stability detection (SSIM-based)

### Task 4: Screenshot Commands
- screenshot (raw PNG)
- screenshot base64
- frames recent/around/diff/stable

### Task 5: Input Commands
- tap, longpress, swipe, scroll
- type, key
- Coordinate handling

### Task 6: Device Control Commands
- rotate, screen on/off
- notifications, settings
- clipboard get/set/paste

### Task 7: Video Recording
- Frame buffer to video conversion
- record start/stop commands
- Configuration options

### Task 8: Plugin Integration
- Session start hook (launch helper)
- Session end hook (stop helper)
- Bash client wrapper script

### Task 9: Fallback Mechanism
- Detect helper availability
- Graceful fallback to mobile-mcp
- Logging and warnings

### Task 10: Update Commands
- Update /run-test for scrcpy integration
- Update /record-test for frame buffer
- Add new YAML actions (wait_for_stable, clipboard, rotation)

## Success Criteria

- [ ] Screenshot capture < 50ms (vs current 2000ms)
- [ ] Tap execution < 100ms (vs current 300ms)
- [ ] 20-step test runs 4x faster
- [ ] Recording generates frames without ffmpeg
- [ ] Graceful fallback when scrcpy unavailable
- [ ] Frame stability detection works reliably
