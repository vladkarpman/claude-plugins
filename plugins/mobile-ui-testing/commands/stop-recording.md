---
name: stop-recording
description: Stop recording and generate YAML test from captured actions
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Task
  - AskUserQuestion
  - mcp__screen-buffer__device_stop_recording
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
- `{TOUCH_PID}` = touchPid
- `{RECORDING_TYPE}` = type (default: "test" if not present)
- `{PRECONDITION_NAME}` = preconditionName (if type is "precondition")
- `{PRECONDITION_DESCRIPTION}` = preconditionDescription (if type is "precondition")
- `{PRECONDITION_FOLDER}` = preconditionFolder (if type is "precondition")

**Set common folder variable:**
- If `{RECORDING_TYPE}` is "precondition": Set `{TEST_FOLDER}` = `{PRECONDITION_FOLDER}`
- Otherwise: `{TEST_FOLDER}` is already set from testFolder

This ensures subsequent steps can use `{TEST_FOLDER}` consistently regardless of recording type.

### Step 2: Stop Video Recording

**Tool:** `mcp__screen-buffer__device_stop_recording`
```json
{}
```

This stops the recording and finalizes the video file.
The response includes duration and file size.
Video is saved directly to: `{TEST_FOLDER}/recording/recording.mp4`

### Step 3: Stop Touch Monitor

**Tool:** `Bash`
```bash
kill {TOUCH_PID} 2>/dev/null && echo "Touch monitor stopped" || echo "Already stopped"
```

### Step 4: Verify Video File

**Tool:** `Bash`
```bash
# Check video exists and is valid
ls -la {TEST_FOLDER}/recording/recording.mp4
ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1:nokey=1 {TEST_FOLDER}/recording/recording.mp4
```

**If ffprobe fails:** Video may be corrupted. Show warning but continue with touch_events.json.

**If ffprobe succeeds:** Video is valid, continue.

### Step 5: Load Touch Events

**Tool:** `Read` file `{TEST_FOLDER}/recording/touch_events.json`

**If empty or missing:** Stop and show:
```
No touch events captured during recording.

Tips:
- Tap slowly and deliberately during recording
- Ensure the device screen was responding to touches
```

**If events found:** Store as `{TOUCH_EVENTS}` array.

### Step 6: Extract Frames from Video

**Tool:** `Bash`
```bash
python3 ./scripts/extract-frames.py {TEST_FOLDER}/recording/recording.mp4 {TEST_FOLDER}/recording/touch_events.json {VIDEO_START_TIME} {TEST_FOLDER}/recording/screenshots
```

**If video was corrupted:** Skip this step, use coordinates only.

**If successful:** Frames are saved to `{TEST_FOLDER}/recording/screenshots/`:
- `step_NNN_before_1.png` to `step_NNN_before_3.png` (300ms, 200ms, 100ms before action)
- `step_NNN_exact.png` (at action moment)
- `step_NNN_after_1.png` to `step_NNN_after_3.png` (100ms, 200ms, 300ms after action)

### Step 7: Analyze Steps and Generate Approval UI

For each touch event, analyze the before and after frames to provide smart descriptions for the approval UI.

#### Step 7.1: Detect Typing Sequences

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

#### Step 7.2: Get Screenshot List

**Tool:** `Glob` pattern `{TEST_FOLDER}/recording/screenshots/step_*_before_*.png`

Store the list of screenshot files. Extract step numbers from filenames.

**Count unique steps:** Each step has multiple before/after frames. Count unique step numbers.

#### Step 7.3: Analyze Steps in Parallel (5 Agents)

Analyze steps using parallel agents for faster processing.

**Step 7.3.1: Calculate step batches**

Total steps: `{STEP_COUNT}` (from unique step numbers in Step 7.2)

Split steps into 5 batches (or fewer if less than 5 steps):
- Batch 1: steps 1 to ceil(N/5)
- Batch 2: steps ceil(N/5)+1 to ceil(2N/5)
- etc.

**Example:** 29 steps → batches of [1-6], [7-12], [13-18], [19-24], [25-29]

**Step 7.3.2: Dispatch parallel agents**

**Tool:** `Task` with subagent_type="step-analyzer" (dispatch ALL agents in ONE message)

Launch up to 5 agents in parallel. Each agent receives:
```
Analyze recording steps for test.

test_folder: {TEST_FOLDER}
step_numbers: [{BATCH_START}..{BATCH_END}]
output_file: {TEST_FOLDER}/recording/analysis_batch_{N}.json
```

**CRITICAL:** Send all Task tool calls in a single message to enable parallel execution.

**Step 7.3.3: Collect and merge results**

After all agents complete, read each batch file and merge:

**Tool:** `Read` each `{TEST_FOLDER}/recording/analysis_batch_{N}.json`

Merge all batch results into a single analysis object.

**Example merged analysis:**
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

#### Step 7.4: Build Analysis Data

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

#### Step 7.4.5: Branch by Recording Type

**If `{RECORDING_TYPE}` is "precondition":**
- Go to Step 7.7 (Generate Precondition YAML)

**Otherwise:**
- Continue to Step 7.5 (Generate Approval UI)

#### Step 7.5: Generate Approval UI

**Tool:** `Bash`
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generate-approval.py" \
    "{TEST_FOLDER}/recording" \
    --test-name "{TEST_NAME}" \
    --app-package "{APP_PACKAGE}" \
    --output "{TEST_FOLDER}/approval.html"
```

**If script fails:** Show error and provide fallback instructions for manual YAML creation.

#### Step 7.6: Open Approval UI

**Tool:** `Bash`
```bash
open "{TEST_FOLDER}/approval.html"
```

**Note:** On Linux, use `xdg-open` instead of `open`.

#### Step 7.7: Generate Precondition YAML (for precondition recordings only)

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

#### Step 7.8: Output Precondition Results (for precondition recordings only)

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

**Stop here for precondition recordings** - do not continue to Step 8 or 9.

### Step 8: Update Recording State

**Tool:** `Write` to `.claude/recording-state.json`

```json
{
  "status": "approval_pending",
  "testName": "{TEST_NAME}",
  "testFolder": "{TEST_FOLDER}",
  "approvalFile": "{TEST_FOLDER}/approval.html"
}
```

### Step 9: Output Results

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
