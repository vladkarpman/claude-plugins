---
name: record-test
description: Start recording user actions to generate a YAML test
argument-hint: <test-name>
allowed-tools:
  - Read
  - Write
  - Glob
  - Bash
  - AskUserQuestion
  # device-manager-mcp (preferred - faster)
  - mcp__device-manager__device_list
  # mobile-mcp (fallback)
  - mcp__mobile-mcp__mobile_list_available_devices
---

# Record Test - Start Recording User Actions

Start recording mode to capture user interactions and generate a YAML test file.

## Execution Steps

Execute each step in order. Do not skip steps. Use the exact tools specified.

### Step 1: Get Test Name

**If argument provided:** Use it as `{TEST_NAME}`.

**If no argument:** Use `AskUserQuestion` tool:
```
Question: "What would you like to name this test recording?"
```

Store the result as `{TEST_NAME}`.

### Step 2: Check ffmpeg

**Tool:** `Bash`
```bash
./scripts/check-ffmpeg.sh
```

**If output contains "OK":** Continue to Step 3.

**If output contains "not found":** Stop and show:
```
ffmpeg is required for recording.

Install with:
  macOS:   brew install ffmpeg
  Ubuntu:  sudo apt install ffmpeg
  Windows: choco install ffmpeg
```

### Step 3: Detect App Package

**Tool:** `Glob` with pattern `tests/*/test.yaml`

**If files found:** Use `Bash` to extract package:
```bash
grep -h "app:" tests/*/test.yaml | head -1 | sed 's/.*app: *//'
```
Store result as `{APP_PACKAGE}`.

**If no files or grep fails:** Use `AskUserQuestion`:
```
Question: "What is your app package name? (e.g., com.example.app)"
```
Store result as `{APP_PACKAGE}`.

### Step 4: Get Device

**Tool:** `mcp__device-manager__device_list` (preferred) or `mcp__mobile-mcp__mobile_list_available_devices` (fallback)

**If 0 devices:** Stop and show:
```
No device found.

Ensure your device is connected:
  Android: adb devices
  iOS: xcrun simctl list devices | grep Booted
```

**If 1 device:** Use it. Store `id` as `{DEVICE_ID}`, `name` as `{DEVICE_NAME}`.

**If multiple devices:** Use `AskUserQuestion` to let user select.

### Step 5: Create Folders

**Tool:** `Bash`
```bash
mkdir -p tests/{TEST_NAME}/recording/screenshots tests/{TEST_NAME}/baselines tests/{TEST_NAME}/reports
mkdir -p .claude
```

### Step 6: Get Video Start Timestamp

**Tool:** `Bash`
```bash
python3 -c "import time; print(time.time())"
```

Store the output number as `{VIDEO_START_TIME}` (e.g., `1768233811.7967029`).

### Step 7: Create Initial Recording State

**Tool:** `Bash` (use Bash because file doesn't exist yet)
```bash
cat > .claude/recording-state.json << 'EOF'
{
  "testName": "{TEST_NAME}",
  "testFolder": "tests/{TEST_NAME}",
  "appPackage": "{APP_PACKAGE}",
  "device": "{DEVICE_ID}",
  "startTime": "{CURRENT_ISO_TIMESTAMP}",
  "videoStartTime": {VIDEO_START_TIME},
  "status": "recording",
  "videoPid": null,
  "touchPid": null
}
EOF
```

Replace placeholders with actual values.

### Step 8: Start Video Recording

**Tool:** `Bash` with `run_in_background: true`
```bash
./scripts/record-video.sh {DEVICE_ID} tests/{TEST_NAME}/recording/recording.mp4 &
echo "VIDEO_PID=$!"
```

**Read the background task output file** to get `VIDEO_PID=XXXXX`.
Store the number as `{VIDEO_PID}`.

### Step 9: Start Touch Monitor

**Tool:** `Bash` with `run_in_background: true`
```bash
python3 ./scripts/monitor-touches.py {DEVICE_ID} tests/{TEST_NAME}/recording &
echo "TOUCH_PID=$!"
```

**Read the background task output file** to get `TOUCH_PID=XXXXX`.
Store the number as `{TOUCH_PID}`.

### Step 10: Update Recording State with PIDs

**Tool:** `Read` then `Write` on `.claude/recording-state.json`

Update the file to set:
- `"videoPid": {VIDEO_PID}`
- `"touchPid": {TOUCH_PID}`

### Step 11: Output Success Message

Output this message to the user (replace placeholders):

```
Recording started: {TEST_NAME}
══════════════════════════════════════════════════════════

Device: {DEVICE_NAME} ({DEVICE_ID})
App: {APP_PACKAGE}
Saving to: tests/{TEST_NAME}/

RECORDING ACTIVE
────────────────
Every tap, swipe, and long-press is being captured.
Screenshots will be extracted from video for analysis.

Interact with your app at normal speed.

When done, say "stop" or use /stop-recording

Note: Video recording has a 3-minute limit.

══════════════════════════════════════════════════════════
```

### Step 12: Wait for Stop Command

When user says "stop", "done", or uses `/stop-recording`:
- Invoke the `stop-recording` skill/command

## Error Handling

| Error | Action |
|-------|--------|
| ffmpeg not found | Show install instructions, stop |
| No device found | Show connection instructions, stop |
| Script file missing | Show: "Plugin not installed correctly. Re-install with: claude plugin install mobile-ui-testing" |
| Device disconnects | Stop recording, notify user |

## Notes

- Video recording has a 3-minute limit (Android screenrecord limitation)
- Touch events are captured in real-time to `touch_events.json`
- Stopping the recording properly is critical - see `/stop-recording`
