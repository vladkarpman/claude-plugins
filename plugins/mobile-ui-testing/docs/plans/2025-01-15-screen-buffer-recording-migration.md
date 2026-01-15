# Screen Buffer Recording Migration

**Date:** 2025-01-15
**Status:** Approved

## Summary

Migrate video recording and screenshots from adb-based tools to screen-buffer-mcp. This removes the 3-minute recording limit and unifies visual capture through a single MCP server.

## Motivation

- `adb screenrecord` has a hard 3-minute limit
- Current architecture requires bash wrapper script and file pulling from device
- screen-buffer-mcp already provides recording capabilities via scrcpy

## Architecture Change

### Before

```
Recording:
  record-test.md → Bash (record-video.sh) → adb screenrecord → /sdcard/recording.mp4
                                          → adb pull → tests/{name}/recording/recording.mp4

Screenshots:
  run-test.md → mobile-mcp → mobile_take_screenshot
```

### After

```
Recording:
  record-test.md → screen-buffer-mcp → device_start_recording(output_path)
  stop-recording.md → screen-buffer-mcp → device_stop_recording()

Screenshots:
  run-test.md → screen-buffer-mcp → device_screenshot
```

### Comparison

| Aspect | Current (adb) | New (screen-buffer-mcp) |
|--------|---------------|-------------------------|
| Recording limit | 3 minutes | None |
| File location | Device → pull to host | Direct to host |
| Process management | Background bash + PID tracking | MCP tool call |
| Stop mechanism | `pkill -2 screenrecord` on device | `device_stop_recording()` |
| Dependencies | adb shell access | scrcpy (via screen-buffer-mcp) |

## Implementation

### 1. commands/record-test.md

**Remove:** Steps 8-9 background bash processes for video recording.

**Replace with:**

```markdown
### Step 8: Start Video Recording

**Tool:** `mcp__screen-buffer__device_start_recording`
```json
{
  "output_path": "tests/{TEST_NAME}/recording/recording.mp4"
}
```
```

**Update recording state:** Remove `videoPid` field (no longer managing background process):

```json
{
  "testName": "{TEST_NAME}",
  "testFolder": "tests/{TEST_NAME}",
  "appPackage": "{APP_PACKAGE}",
  "device": "{DEVICE_ID}",
  "startTime": "{CURRENT_ISO_TIMESTAMP}",
  "videoStartTime": {VIDEO_START_TIME},
  "status": "recording",
  "touchPid": null
}
```

**Update success message:** Remove "Note: Video recording has a 3-minute limit."

**Update allowed-tools:** Add `mcp__screen-buffer__device_start_recording`

### 2. commands/stop-recording.md

**Remove:** Bash commands for stopping screenrecord and pulling files:
```bash
adb -s {DEVICE} shell pkill -2 screenrecord
adb -s {DEVICE} pull /sdcard/recording.mp4 ...
```

**Replace with:**

```markdown
### Step X: Stop Video Recording

**Tool:** `mcp__screen-buffer__device_stop_recording`
```json
{}
```
```

Response includes duration, file size, output path. No file pulling needed.

**Update allowed-tools:** Add `mcp__screen-buffer__device_stop_recording`

### 3. commands/run-test.md

**For verify_screen and if_screen actions:**

Replace:
```yaml
- mcp__mobile-mcp__mobile_take_screenshot
```

With:
```yaml
- mcp__screen-buffer__device_screenshot
```

Tool call changes from:
```json
{ "device": "{DEVICE_ID}" }
```

To:
```json
{ "device": "{DEVICE_ID}" }
```

Both return base64-encoded PNG - downstream processing unchanged.

### 4. File Deletions

- `scripts/record-video.sh` - Delete (was adb screenrecord wrapper)

### 5. CLAUDE.md Documentation

Update:
- Dependencies section: Remove adb screenrecord references, keep ffmpeg
- MCP Server Architecture: Update screen-buffer-mcp to show recording + screenshots
- Recording Pipeline: Update flow diagram, remove 3-minute limit references
- Remove all "3-minute limit" mentions

## What Stays Unchanged

- Touch monitor (`monitor-touches.py`) - still uses adb getevent
- Frame extraction (`extract-frames.py` + ffmpeg) - same video file location
- mobile-mcp for device interactions (tap, swipe, type, element listing)
- All downstream processing (typing detection, verification interview, YAML generation)

## Testing

1. Run `/record-test test-migration`
2. Interact with app for 4+ minutes (exceeds old limit)
3. Run `/stop-recording`
4. Verify video file exists and is playable
5. Verify frame extraction works
6. Run `/run-test` with verify_screen action
7. Verify screenshot-based verification works
