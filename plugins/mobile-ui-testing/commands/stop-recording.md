---
name: stop-recording
description: Stop recording and generate YAML test from captured actions
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - AskUserQuestion
---

# Stop Recording - Generate YAML Test

Stop the active recording and generate a YAML test file.

## Execution Steps

Execute each step in order. Do not skip steps. Use the exact tools specified.

### Step 1: Read Recording State

**Tool:** `Read` file `.claude/recording-state.json`

**If file not found or status is not "recording":** Stop and show:
```
No active recording found.

Start a new recording with:
  /record-test <test-name>
```

**If file found:** Extract these values:
- `{TEST_NAME}` = testName
- `{TEST_FOLDER}` = testFolder
- `{APP_PACKAGE}` = appPackage
- `{DEVICE_ID}` = device
- `{VIDEO_START_TIME}` = videoStartTime
- `{VIDEO_PID}` = videoPid
- `{TOUCH_PID}` = touchPid
- `{RECORDING_TYPE}` = type (default: "test" if not present)
- `{PRECONDITION_NAME}` = preconditionName (if type is "precondition")
- `{PRECONDITION_DESCRIPTION}` = preconditionDescription (if type is "precondition")
- `{PRECONDITION_FOLDER}` = preconditionFolder (if type is "precondition")

### Step 2: Stop Screenrecord on Device (CRITICAL)

**Tool:** `Bash`
```bash
# Send SIGINT to screenrecord - this writes the moov atom and finalizes the file
adb -s {DEVICE_ID} shell pkill -2 screenrecord
```

**Why SIGINT (-2)?** Screenrecord only writes the video file index (moov atom) when it receives SIGINT. Without this, the file is corrupted and unreadable.

### Step 3: Wait for Video Script to Complete

**Tool:** `Bash`
```bash
# Wait for recording script to finish (pulls video from device)
for i in {1..30}; do
    kill -0 {VIDEO_PID} 2>/dev/null || break
    sleep 1
done
echo "Video script completed"
```

This waits up to 30 seconds for the video to be pulled from device.

### Step 4: Stop Touch Monitor

**Tool:** `Bash`
```bash
kill {TOUCH_PID} 2>/dev/null && echo "Touch monitor stopped" || echo "Already stopped"
```

### Step 5: Verify Video File

**Tool:** `Bash`
```bash
# Check video exists and is valid (has moov atom)
ls -la {TEST_FOLDER}/recording/recording.mp4
ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1:nokey=1 {TEST_FOLDER}/recording/recording.mp4
```

**If ffprobe fails with "moov atom not found":**
- Video is corrupted
- Show warning but continue with touch_events.json (will use coordinates only)

**If ffprobe succeeds:** Video is valid, continue.

### Step 6: Load Touch Events

**Tool:** `Read` file `{TEST_FOLDER}/recording/touch_events.json`

**If empty or missing:** Stop and show:
```
No touch events captured during recording.

Tips:
- Tap slowly and deliberately during recording
- Ensure the device screen was responding to touches
```

**If events found:** Store as `{TOUCH_EVENTS}` array.

### Step 7: Extract Frames from Video

**Tool:** `Bash`
```bash
python3 ./scripts/extract-frames.py {TEST_FOLDER}/recording/recording.mp4 {TEST_FOLDER}/recording/touch_events.json {VIDEO_START_TIME} {TEST_FOLDER}/recording/screenshots
```

**If video was corrupted:** Skip this step, use coordinates only.

**If successful:** Frames are saved to `{TEST_FOLDER}/recording/screenshots/touch_NNN.png`

### Step 8: Analyze Steps and Generate Approval UI

For each touch event, analyze the before and after frames to provide smart descriptions for the approval UI.

#### Step 8.1: Detect Typing Sequences

**Tool:** `Bash`
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/analyze-typing.py" {TEST_FOLDER}
```

This script analyzes touch patterns to detect keyboard typing sequences using:
- Y-coordinate threshold (bottom 40% of screen = keyboard region)
- Temporal clustering (< 1s between taps)
- Minimum sequence length (3+ consecutive taps)
- X-coordinate variance (confirms multiple keys, not repeated taps)

**Output:** `{TEST_FOLDER}/recording/typing_sequences.json`

**If script fails:** Continue without typing detection (user can add type commands manually in UI).

#### Step 8.2: Get Screenshot List

**Tool:** `Glob` pattern `{TEST_FOLDER}/recording/screenshots/step_*_before_*.png`

Store the list of screenshot files. Extract step numbers from filenames.

**Count unique steps:** Each step has multiple before/after frames. Count unique step numbers.

#### Step 8.3: Analyze Steps (Before/After Diff)

For each unique step number, analyze the before and after frames to provide smart descriptions.

**For each step {N} (formatted as 3-digit: 001, 002, etc.):**

**Step 8.3.1: View before frame**

**Tool:** `Read` file `{TEST_FOLDER}/recording/screenshots/step_{N}_before_3.png`

This shows the screen state 300ms before the tap (frame index 3 = closest to tap).

**Step 8.3.2: View after frame**

**Tool:** `Read` file `{TEST_FOLDER}/recording/screenshots/step_{N}_after_3.png`

This shows the screen state 300ms after the tap.

**Step 8.3.3: Analyze and describe**

Analyze both frames and create a description object:
- `before`: Brief description of the screen state before the tap (1 sentence)
- `action`: What element was tapped (identify button, text, area)
- `after`: What changed after the tap (1 sentence)
- `suggestedVerification`: Propose a verify_screen based on the change (null if no meaningful verification)

**Store analysis** in memory for approval generation.

**Example analysis for one step:**
```json
{
  "before": "Calculator app with empty display",
  "action": "Tapped '5' button on number pad",
  "after": "Display now shows '5'",
  "suggestedVerification": "Display shows the number 5"
}
```

**Guidelines for analysis:**
- Keep descriptions concise (under 100 characters each)
- Focus on user-visible changes
- Suggested verification should describe expected state, not the action
- Set suggestedVerification to null for transitional taps (navigation, scrolling)

**Repeat Step 8.3.1-8.3.3 for each step.**

#### Step 8.4: Build Analysis Data

Create the analysis data structure combining all step analyses:

```json
{
  "step_001": {
    "analysis": {
      "before": "Calculator app with empty display",
      "action": "Tapped '5' button on number pad",
      "after": "Display now shows '5'"
    },
    "suggestedVerification": "Display shows the number 5"
  },
  "step_002": {
    "analysis": {
      "before": "Display shows '5'",
      "action": "Tapped '+' operator button",
      "after": "Display shows '5 +'"
    },
    "suggestedVerification": null
  }
}
```

**Tool:** `Write` to `{TEST_FOLDER}/recording/analysis.json`

Write the complete analysis data as JSON.

#### Step 8.4.5: Branch by Recording Type

**If `{RECORDING_TYPE}` is "precondition":**
- Go to Step 8.7 (Generate Precondition YAML)

**Otherwise:**
- Continue to Step 8.5 (Generate Approval UI)

#### Step 8.5: Generate Approval UI

**Tool:** `Bash`
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generate-approval.py" \
    "{TEST_FOLDER}/recording" \
    --test-name "{TEST_NAME}" \
    --app-package "{APP_PACKAGE}" \
    --output "{TEST_FOLDER}/approval.html"
```

**If script fails:** Show error and provide fallback instructions for manual YAML creation.

#### Step 8.6: Open Approval UI

**Tool:** `Bash`
```bash
open "{TEST_FOLDER}/approval.html"
```

**Note:** On Linux, use `xdg-open` instead of `open`.

#### Step 8.7: Generate Precondition YAML (for precondition recordings only)

**This step only runs if `{RECORDING_TYPE}` is "precondition".**

**Tool:** `AskUserQuestion`
```
Question: "How should the runtime verify this precondition is active?"
Options:
- Check for element (fast)
- Check screen state (AI vision)
```

**If "Check for element":**

**Tool:** `AskUserQuestion`
```
Question: "What element text indicates this state is active?"
```
Store response as `{VERIFY_ELEMENT}`.

**If "Check screen state":**

**Tool:** `AskUserQuestion`
```
Question: "Describe the screen when this state is active"
```
Store response as `{VERIFY_SCREEN}`.

**Generate precondition YAML:**

Build `{GENERATED_STEPS}` from touch events and typing sequences:
- For each touch event, check the analysis data
- If analysis identifies the tapped element: `- tap: "element text"`
- Otherwise use coordinates: `- tap: [x, y]`
- For detected typing sequences: `- type: "text"`
- For long pauses (> 2s): `- wait: Xs`

**Tool:** `Write` to `{PRECONDITION_FOLDER}/precondition.yaml`

If verification is by element:
```yaml
name: {PRECONDITION_NAME}
description: "{PRECONDITION_DESCRIPTION}"

steps:
{GENERATED_STEPS}

verify:
  element: "{VERIFY_ELEMENT}"
```

If verification is by screen:
```yaml
name: {PRECONDITION_NAME}
description: "{PRECONDITION_DESCRIPTION}"

steps:
{GENERATED_STEPS}

verify:
  screen: "{VERIFY_SCREEN}"
```

**Copy precondition to standard location:**

**Tool:** `Bash`
```bash
mkdir -p tests/preconditions && cp "{PRECONDITION_FOLDER}/precondition.yaml" "tests/preconditions/{PRECONDITION_NAME}.yaml"
```

#### Step 8.8: Output Precondition Results (for precondition recordings only)

**This step only runs if `{RECORDING_TYPE}` is "precondition".**

Count steps from generated YAML as `{STEP_COUNT}`.

Output to user:

```
Precondition Created: {PRECONDITION_NAME}
══════════════════════════════════════════════════════════

Description: {PRECONDITION_DESCRIPTION}
Steps recorded: {STEP_COUNT}
Saved to: tests/preconditions/{PRECONDITION_NAME}.yaml

Usage in test files:
─────────────────────
config:
  app: com.example.app
  precondition: {PRECONDITION_NAME}

Conditional check:
──────────────────
- if_precondition: {PRECONDITION_NAME}
  then:
    - tap: "Premium Feature"

══════════════════════════════════════════════════════════
```

**Update recording state and skip to end:**

**Tool:** `Write` to `.claude/recording-state.json`

```json
{
  "status": "completed",
  "type": "precondition",
  "preconditionName": "{PRECONDITION_NAME}",
  "preconditionFile": "tests/preconditions/{PRECONDITION_NAME}.yaml"
}
```

**Stop here for precondition recordings** - do not continue to Step 9 or 10.

### Step 9: Update Recording State

**Tool:** `Write` to `.claude/recording-state.json`

```json
{
  "status": "approval_pending",
  "testName": "{TEST_NAME}",
  "testFolder": "{TEST_FOLDER}",
  "approvalFile": "{TEST_FOLDER}/approval.html"
}
```

### Step 10: Output Results

Output to user:

```
Recording Analysis Complete
══════════════════════════════════════════════════════════

Touch events captured: {EVENT_COUNT}
Video duration: {DURATION}s
Steps analyzed: {STEP_COUNT}

Approval UI opened in browser: {TEST_FOLDER}/approval.html

Review your recorded test:
  1. Check each step's before/after frames
  2. Accept or skip suggested verifications
  3. Edit tap targets or add wait times if needed
  4. Add new steps using video scrubber
  5. Click "Export YAML" when done

The YAML file will be downloaded to your Downloads folder.
Move it to: {TEST_FOLDER}/test.yaml

Then run with: /run-test {TEST_FOLDER}/

══════════════════════════════════════════════════════════
```

**Where:**
- `{EVENT_COUNT}`: Number of touch events from touch_events.json
- `{DURATION}`: Video duration in seconds (from ffprobe or touch event timestamps)
- `{STEP_COUNT}`: Number of unique steps analyzed

## Error Handling

| Error | Action |
|-------|--------|
| No recording state | Show "No active recording" message |
| Video corrupted | Warn, continue with coordinates only |
| No touch events | Show tips for better recording |
| Frame extraction fails | Continue with coordinates only |
| Typing detection fails | Continue without typing sequences |
| Step analysis fails | Use empty analysis, user can edit in UI |
| Approval UI generation fails | Show error, provide manual YAML template |
| Browser open fails | Show file path for manual opening |

## Output Files

After completion:
```
{TEST_FOLDER}/
├── approval.html         ← Approval UI (open in browser)
├── test.yaml             ← Generated after export from approval UI
└── recording/            ← Recording artifacts
    ├── touch_events.json     ← Raw touch data with timestamps
    ├── typing_sequences.json ← Detected keyboard typing
    ├── analysis.json         ← AI step analysis
    ├── recording.mp4         ← Video file
    └── screenshots/          ← Extracted frames
        ├── step_001_before_1.png
        ├── step_001_before_2.png
        ├── step_001_before_3.png
        ├── step_001_after_1.png
        ├── step_001_after_2.png
        ├── step_001_after_3.png
        └── ...
```

**Note:** The `test.yaml` file is created when user clicks "Export YAML" in the approval UI. The exported file downloads to the browser's download folder and should be moved to the test folder.
