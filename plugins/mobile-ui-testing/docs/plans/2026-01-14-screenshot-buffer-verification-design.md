# Screenshot Buffer Verification Design

**Date:** 2026-01-14
**Status:** Approved
**Problem:** Test verification via mobile-mcp is slow, causing missed transient states and inaccurate assertions

## Problem Statement

Current `verify_screen` uses mobile-mcp's `take_screenshot` which has 1-2s latency. This causes:
- False negatives: Screen matched but mobile-mcp was too slow to capture it
- Missed transient states: Toasts, brief confirmations disappear before capture

**Goal:** Reliable verification with <10% flakiness rate

## Solution: Background Screenshot Buffer

Continuously capture screenshots via ADB in background during test execution. Verify against buffer instead of point-in-time mobile-mcp calls.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Test Execution                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ run-test.md  │───▶│ Screenshot   │───▶│ Verification │  │
│  │ (orchestrator)│    │ Buffer       │    │ Engine       │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   ▲                    │          │
│         │                   │                    │          │
│         ▼                   │                    ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Action       │    │ ADB Screen   │    │ AI Vision    │  │
│  │ Executor     │    │ Capture      │    │ (Claude)     │  │
│  │ (mobile-mcp) │    │ (background) │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Screenshot Buffer (`scripts/screenshot-buffer.py`)

Background process that captures screenshots continuously.

**Capture mechanism:**
```bash
adb shell screencap -p /sdcard/screen.png
adb pull /sdcard/screen.png {buffer_dir}/{timestamp}.png
```

**Configuration:**
- Capture interval: 150ms (~6-7 fps)
- Buffer size: 200 screenshots max (~30 seconds)
- Rolling window: Older screenshots auto-deleted

**Buffer structure:**
```
/tmp/mobile-ui-testing-buffer-{test_id}/
├── manifest.json          # Metadata + index
├── 1736821234.150.png     # timestamp in filename
├── 1736821234.300.png
└── ...
```

**manifest.json:**
```json
{
  "test_id": "youtube-search-001",
  "device": "RFCW318P7NV",
  "started_at": 1736821234.0,
  "capture_interval_ms": 150,
  "screenshots": [
    {"timestamp": 1736821234.150, "file": "1736821234.150.png"},
    {"timestamp": 1736821234.300, "file": "1736821234.300.png"}
  ]
}
```

### 2. Verification Engine (`scripts/verify-from-buffer.py`)

Sequence validation with recency constraint.

**Algorithm:**
1. Load all screenshots since last action timestamp
2. Filter to candidates: within 500ms of now OR most recent
3. Check each candidate against expected state
4. Pass if ANY candidate matches

**Logic:**
```python
def verify_screen(
    buffer_dir: Path,
    expected_state: str,
    action_timestamp: float,
    recency_threshold_ms: float = 500
) -> VerifyResult:

    # 1. Load screenshots since last action
    screenshots = get_screenshots_since(buffer_dir, action_timestamp)

    # 2. Filter to recent candidates
    now = time.time()
    most_recent = screenshots[-1]
    candidates = [
        s for s in screenshots
        if (now - s.timestamp) * 1000 <= recency_threshold_ms
        or s == most_recent
    ]

    # 3. Return candidates for AI analysis
    return candidates
```

**Why this works:**
- Captures transient states (toasts, animations)
- Adapts to variable timing (fast vs slow devices)
- Recency constraint ensures we verify "current-ish" state

### 3. Integration with run-test.md

**Modified execution flow:**
```
start buffer → setup → actions → verify (from buffer) → teardown → stop buffer
```

**Before setup:**
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/screenshot-buffer.py" \
  --device {DEVICE_ID} \
  --output /tmp/mobile-ui-testing-buffer-{TEST_ID} \
  --interval 150 &
```

**After each action:**
```
{LAST_ACTION_TIMESTAMP} = current time
```

**verify_screen (updated):**
1. Query buffer for candidate screenshots since last action
2. Read best candidate image
3. AI analysis: check if image matches expected state
4. Pass/fail based on AI decision

**After teardown:**
- Kill buffer process
- On failure: preserve buffer for debugging
- On pass: clean up buffer directory

## Error Handling

| Scenario | Handling |
|----------|----------|
| Buffer fails to start | Fall back to mobile-mcp screenshot |
| Buffer crashes mid-test | Detect via PID, fall back for remaining verifications |
| ADB disconnects | Buffer exits, test continues with fallback |
| Disk full | Buffer auto-cleans old screenshots |
| No screenshots since action | Use most recent screenshot available |
| All candidates fail AI check | Report failure with checked screenshots |

**Fallback mechanism:**
```python
def verify_with_fallback(expected_state, buffer_dir, action_ts):
    if buffer_available(buffer_dir):
        result = verify_from_buffer(buffer_dir, expected_state, action_ts)
        if result.checked_count > 0:
            return result

    # Fallback: traditional mobile-mcp screenshot
    screenshot = mobile_mcp_take_screenshot()
    return verify_single_screenshot(screenshot, expected_state)
```

## Debugging Support

On test failure, output includes:
```
✗ FAILED: verify_screen "Login success message"

  Checked 4 screenshots (1736821234.150 → 1736821234.600)
  None matched expected state.

  Screenshots preserved: /tmp/mobile-ui-testing-buffer-abc123/
  Debug: View screenshots to see actual screen states
```

## Performance

- Buffer process: ~2% CPU
- Disk I/O: ~3-4 MB/s
- No impact on test action execution (parallel process)
- Total buffer size: ~100MB max

## Model Configuration

**Default:** All agents use Opus
**Override:** Users can configure at project or test level

### Project-level config (`.claude/mobile-ui-testing.yaml`)

```yaml
# Plugin settings
model: opus  # Default model for all agents (opus, sonnet, haiku)
```

### Test-level override

```yaml
config:
  app: com.example.app
  model: sonnet  # Override for this specific test
```

**Priority:** Test config > Project config > Default (opus)

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/screenshot-buffer.py` | Create | Background capture process |
| `scripts/verify-from-buffer.py` | Create | Sequence validation logic |
| `commands/run-test.md` | Modify | Integrate buffer lifecycle and verification |
| `commands/lib/load-config.md` | Create | Load and merge config from project + test |

## Backward Compatibility

- Existing test YAML syntax unchanged
- No changes needed to user's test files
- Falls back gracefully if buffer unavailable

## Future Enhancements (Not in Scope)

- Video recording for failure debugging (separate feature)
- Configurable capture interval per test
- Remote buffer for CI environments
