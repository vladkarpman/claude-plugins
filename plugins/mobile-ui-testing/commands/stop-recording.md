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

### Step 8: Verification Interview (Optional)

Ask user if they want to add verifications to make this a real test.

**Tool:** `AskUserQuestion`
```
Question: "Would you like to add verifications to this test? This makes it validate app behavior, not just replay actions.

Recommended: Say yes to make this a real test
Skip: Say no to generate coordinate-based playback only"
```

**If user declines ("no", "skip", etc.):** Skip to Step 9 with no verifications.

**If user accepts ("yes", etc.):** Continue with verification interview.

#### Step 8.1: Detect Checkpoints

**Tool:** `Bash`
```bash
python3 ./scripts/analyze-checkpoints.py {TEST_FOLDER} > {TEST_FOLDER}/recording/checkpoints.json
```

**If script fails:** Show error and skip to Step 9 with no verifications.

**If successful:** Checkpoints saved to `checkpoints.json`.

#### Step 8.2: Load Checkpoints

**Tool:** `Read` file `{TEST_FOLDER}/recording/checkpoints.json`

Parse JSON array of checkpoint objects. Each checkpoint has:
- `touch_index`: Index in touch_events array
- `timestamp`: Time in seconds
- `screenshot_path`: Path to screenshot
- `score`: Importance score
- `reasons`: Why this is a good checkpoint

**Limit to 8 checkpoints:** If more than 8 detected, keep top 8 by score (highest scores first).

Store as `{CHECKPOINTS}` array. Extract the `reasons` field from each checkpoint object.

#### Step 8.3: Detect Typing Sequences

**Tool:** `Bash`
```bash
python3 ./scripts/analyze-typing.py {TEST_FOLDER}
```

This script analyzes touch patterns to detect keyboard typing sequences using:
- Y-coordinate threshold (bottom 40% of screen = keyboard region)
- Temporal clustering (< 1s between taps)
- Minimum sequence length (3+ consecutive taps)
- X-coordinate variance (confirms multiple keys, not repeated taps)

**Output:** `{TEST_FOLDER}/typing_sequences.json`

**If no sequences detected or script fails:** Continue to Step 8.5 (checkpoint interview).

**If sequences detected:** Continue to Step 8.4 (typing interview).

#### Step 8.4: Typing Interview (if sequences detected)

**Tool:** `Read` file `{TEST_FOLDER}/recording/typing_sequences.json`

Parse JSON with structure:
```json
{
  "sequences": [
    {
      "start_touch_index": 16,
      "end_touch_index": 23,
      "touch_count": 8,
      "duration_ms": 2576,
      "text": "",
      "submit": false
    }
  ],
  "total_sequences": 3
}
```

Store as `{TYPING_SEQUENCES}` array.

**For each typing sequence, execute these steps:**

**Step 8.4.1: Show sequence context**

Display to user:
```
Detected keyboard typing sequence {N} of {TOTAL}:
- Touches: {start_touch_index+1} to {end_touch_index+1} ({touch_count} taps)
- Duration: {duration_ms}ms
- Region: Bottom 40% of screen (keyboard area)
```

**Step 8.4.2: Ask what was typed**

**Tool:** `AskUserQuestion`
```
Question: "What text did you type in this sequence?

You can type the exact text or leave empty to skip this sequence."
```

**Parse user response:**
- If empty or "skip": Skip this sequence, continue to next
- Otherwise: Store text in sequence['text']

**Step 8.4.3: Ask about submit action**

**Tool:** `AskUserQuestion`
```
Question: "Did you press Enter/Search/Done after typing this text?

A) Yes, I pressed Enter/Search to submit
B) No, I just typed the text"
```

**Parse user response:**
- If "A" or "yes" or "enter" or "search" or "submit": Set sequence['submit'] = true
- If "B" or "no": Set sequence['submit'] = false

**Step 8.4.4: Confirmation**

Display to user:
```
✓ Typing sequence recorded:
  Text: "{text}"
  Submit: {submit}
```

**Repeat Steps 8.4.1-8.4.4 for each typing sequence.**

**Step 8.4.5: Save Typing Data**

**Tool:** `Write` to `{TEST_FOLDER}/recording/typing_sequences.json`

Update the sequences with user-provided text and submit values:
```json
{
  "sequences": [
    {
      "start_touch_index": 16,
      "end_touch_index": 23,
      "touch_count": 8,
      "duration_ms": 2576,
      "text": "android development",
      "submit": true
    }
  ],
  "total_sequences": 3
}
```

**If no sequences had text entered:** Write original file (all text fields empty).

#### Step 8.5: Iterate Through Checkpoints

For each checkpoint (up to 8), execute these steps:

**Step 8.5.1: Show checkpoint context**

Display to user:
```
Checkpoint {N} of {TOTAL} at {TIMESTAMP}s
Reasons: {CHECKPOINT_REASONS}
```

Where `{CHECKPOINT_REASONS}` is the checkpoint's `reasons` array joined with ", ".

**Step 8.5.2: View screenshot**

**Tool:** `Read` the screenshot file at `{CHECKPOINT.screenshot_path}`

This shows you what the screen looks like at this checkpoint.

**Step 8.5.3: Analyze screenshot and suggest verification**

Analyze the screenshot from Step 8.3.2 and suggest appropriate verifications.

**Process:**
1. Examine the screenshot to understand the screen state
2. Identify key UI elements and their purpose
3. Suggest a verification that validates important app behavior
4. Provide alternative verification options

**Create suggestion with this structure:**
- `screen_description`: Brief description of what's visible (1-2 sentences)
- `suggested_verification`: Primary recommended verification (verify_screen format)
- `alternatives`: Array of 2-3 alternative verifications

**Examples of good verifications:**
- `verify_screen: "Login form with email and password fields visible"`
- `verify_screen: "Shopping cart shows 3 items with correct total"`
- `verify_screen: "Success message displayed after submission"`
- `verify_contains: "Welcome back, John"`

**Avoid:**
- Verifying transitional states (loading screens, animations)
- Overly specific text that might change
- Coordinate-based assertions

**Step 8.5.4: Ask user to choose**

**Tool:** `AskUserQuestion`
```
Question: "Checkpoint {N} of {TOTAL} at {TIMESTAMP}s

Screen: {screen_description}

What should we verify here?

A) {suggested_verification} (recommended)
B) {alternatives[0]}
C) Skip this checkpoint
D) I'll describe a custom verification

You can type the letter (A/B/C/D) or describe what you want to verify in your own words."
```

**Parse user response:**
- If "A" or contains suggested verification text: Use suggested_verification
- If "B" or contains first alternative text: Use alternatives[0]
- If "C" or "skip": Skip this checkpoint
- If "D" or "custom" or other text: Treat as custom description

**Step 8.5.5: Handle custom verification**

**If user chose custom (option D):**

**Tool:** `AskUserQuestion`
```
Question: "Describe what you want to verify at this checkpoint:"
```

Store custom description as verification text.

**Tool:** `AskUserQuestion` for confirmation:
```
Question: "I'll add this verification: '{USER_CUSTOM_TEXT}'

Is this correct?

A) Yes, use this verification
B) No, let me revise it"
```

**If user chooses B (revise):** Return to "Describe what you want to verify" question (Step 8.5.5 start).

**If user chooses A (yes):** Continue to store verification (Step 8.5.6).

**Step 8.5.6: Store verification**

Add to `{VERIFICATIONS}` array:
```json
{
  "touch_index": CHECKPOINT.touch_index,
  "type": "screen",
  "description": "CHOSEN_VERIFICATION_TEXT"
}
```

**Repeat Steps 8.5.1-8.5.6 for each checkpoint.**

#### Step 8.6: Save Verifications

**Tool:** `Write` to `{TEST_FOLDER}/recording/verifications.json`

Write the `{VERIFICATIONS}` array as JSON:
```json
[
  {
    "touch_index": 5,
    "type": "screen",
    "description": "Photo generation started"
  },
  {
    "touch_index": 12,
    "type": "screen",
    "description": "Edit controls available"
  }
]
```

**If no verifications selected:** Write empty array `[]`.

### Step 9: Generate YAML Test

**Tool:** `Bash`
```bash
python3 ./scripts/generate-test.py {TEST_FOLDER} {APP_PACKAGE} {TEST_NAME}
```

This script:
- Loads touch_events.json
- Loads verifications.json (if exists)
- Loads typing_sequences.json (if exists)
- Converts touches to YAML actions with percentage coordinates
- Replaces keyboard tap sequences with `type` commands
- Inserts verification steps at checkpoints
- Writes to `{TEST_FOLDER}/test.yaml`

**Output format:**
```yaml
# {TEST_NAME} (Recorded)
# Recorded on: {TODAY_DATE}
# Total actions: {EVENT_COUNT}

config:
  app: {APP_PACKAGE}

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: {TEST_NAME}
    description: Recorded test with verifications
    steps:
      - tap: ["50%", "80%"]
      - tap: ["30%", "40%"]
      - verify_screen: "Photo generation started"  # Inserted verification
      - tap: ["60%", "70%"]
```

**If script fails:** Show error message with script output.

### Step 10: Cleanup Recording State

**Tool:** `Bash`
```bash
rm -f .claude/recording-state.json
```

### Step 11: Output Results

Output to user:

```
Recording Analysis Complete
══════════════════════════════════════════════════════════

Touch events captured: {EVENT_COUNT}
Video duration: {DURATION}s
Verifications added: {VERIFICATION_COUNT}

Generated: {TEST_FOLDER}/test.yaml

Next steps:
  1. Review the generated test
  2. Run with: /run-test {TEST_FOLDER}/
  3. Refine verifications or actions as needed

══════════════════════════════════════════════════════════
```

**Where {VERIFICATION_COUNT}:** Count from verifications.json array (or 0 if file doesn't exist).

## Error Handling

| Error | Action |
|-------|--------|
| No recording state | Show "No active recording" message |
| Video corrupted | Warn, continue with coordinates only |
| No touch events | Show tips for better recording |
| Frame extraction fails | Continue with coordinates only |
| Checkpoint detection fails | Skip verification interview, generate coordinate-based test |
| AI suggestion fails | Use fallback suggestion, continue interview |

## Output Files

After completion:
```
{TEST_FOLDER}/
├── test.yaml             ← Generated test (run with /run-test)
└── recording/            ← Recording artifacts (for debugging)
    ├── touch_events.json     ← Raw touch data
    ├── typing_sequences.json ← Detected typing + user input
    ├── verifications.json    ← User-selected verifications
    ├── checkpoints.json      ← Detected verification points
    ├── recording.mp4         ← Video file
    └── screenshots/          ← Extracted frames
        ├── touch_001.png
        ├── touch_002.png
        └── ...
```
