---
name: run-test
description: Execute a YAML mobile UI test file on a connected device
argument-hint: <test-path> [--no-report]
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  # screen-buffer-mcp (screenshots for verification only)
  - mcp__screen-buffer__device_screenshot
  # mobile-mcp (all device operations)
  - mcp__mobile-mcp__mobile_list_available_devices
  - mcp__mobile-mcp__mobile_get_screen_size
  - mcp__mobile-mcp__mobile_click_on_screen_at_coordinates
  - mcp__mobile-mcp__mobile_swipe_on_screen
  - mcp__mobile-mcp__mobile_type_keys
  - mcp__mobile-mcp__mobile_press_button
  - mcp__mobile-mcp__mobile_list_apps
  - mcp__mobile-mcp__mobile_launch_app
  - mcp__mobile-mcp__mobile_terminate_app
  - mcp__mobile-mcp__mobile_list_elements_on_screen
  - mcp__mobile-mcp__mobile_double_tap_on_screen
  - mcp__mobile-mcp__mobile_long_press_on_screen_at_coordinates
  - mcp__mobile-mcp__mobile_open_url
  - mcp__mobile-mcp__mobile_set_orientation
  - mcp__mobile-mcp__mobile_get_orientation
  - mcp__mobile-mcp__mobile_take_screenshot
  - mcp__mobile-mcp__mobile_save_screenshot
---

# Run Test - Execute YAML Test

Execute a YAML test file on a connected device.

## Execution Steps

### Step 1: Parse Arguments

- `{TEST_PATH}` = path argument (required)
- `{SKIP_REPORT}` = true if `--no-report` flag present (reports enabled by default)

### Step 2: Locate Test File

**If path is a folder** (e.g., `tests/login/`):
- Test file: `{TEST_PATH}/test.yaml`
- Reports: `{TEST_PATH}/reports/`

**If path is a file** (e.g., `tests/login.test.yaml`):
- Test file: `{TEST_PATH}`
- Reports: `tests/reports/`

**Tool:** `Read` the test file.

**If file not found:** Stop and show error.

### Step 3: Parse Test File

Extract from YAML:
- `{APP_PACKAGE}` = config.app
- `{SETUP_STEPS}` = setup array
- `{TEARDOWN_STEPS}` = teardown array
- `{TESTS}` = tests array
- `{PRECONDITION}` = config.precondition (single precondition name, optional)
- `{PRECONDITIONS}` = config.preconditions (array of precondition names, optional)

**Build precondition list:**
- If `{PRECONDITION}` set: `{PRECONDITION_LIST}` = [`{PRECONDITION}`]
- If `{PRECONDITIONS}` set: `{PRECONDITION_LIST}` = `{PRECONDITIONS}`
- Otherwise: `{PRECONDITION_LIST}` = [] (empty)

Initialize precondition verify storage:
- `{PRECONDITION_VERIFIES}` = {} (empty map)

### Step 4: Get Device

**Tool:** `mcp__mobile-mcp__mobile_list_available_devices`

**If 0 devices:** Stop and show:
```
No device found. Connect a device and try again.
```

**If 1 device:** Use it. Store as `{DEVICE_ID}`.

**If multiple:** Ask user to select.

### Step 5: Get Screen Size (for percentage coordinates)

**Tool:** `mcp__mobile-mcp__mobile_get_screen_size`

Store: `{SCREEN_WIDTH}`, `{SCREEN_HEIGHT}`

### Step 5.5: Load Configuration

**Tool:** `Bash` to load merged config:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/load-config.py" --test-config "{TEST_FILE}"
```

Parse JSON output. Store:
- `{CONFIG_MODEL}` = model (default: opus)
- `{GENERATE_REPORTS}` = generate_reports (default: true)

**Determine if reports should be generated:**
- `{SHOULD_GENERATE_REPORT}` = `{GENERATE_REPORTS}` AND NOT `{SKIP_REPORT}`

**If `{SHOULD_GENERATE_REPORT}`:**

Create report directory structure:
```
{REPORT_DIR} = tests/reports/{YYYY-MM-DD}_{TEST_NAME}/
{REPORT_DIR}/recording/
{REPORT_DIR}/screenshots/
```

**Tool:** `Bash` to create directories and get video start timestamp:
```bash
mkdir -p "{REPORT_DIR}/recording" "{REPORT_DIR}/screenshots"
python3 -c "import time; print(time.time())"
```

Store the timestamp output as `{VIDEO_START_TIME}` (e.g., `1768233811.7967029`).

**Start video recording in background:**

**Tool:** `Bash` with `run_in_background: true`
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/record-video.sh" "{DEVICE_ID}" "{REPORT_DIR}/recording/recording.mp4" &
echo "VIDEO_PID=$!"
```

Read the background task output file to get `VIDEO_PID=XXXXX`.
Store the number as `{VIDEO_PID}`.

Initialize step timestamp tracking:
```
{STEP_TIMESTAMPS} = []  # Array to track when each action was performed
```

Initialize report data:
```
{REPORT_DATA} = {
  test_file: "{TEST_FILE}",
  device: { id, name, platform, version, type },
  started_at: ISO timestamp,
  status: "running",
  summary: { total: 0, passed: 0, failed: 0, duration_seconds: 0 },
  tests: []
}
```

### Step 5.7: Execute Preconditions

**If `{PRECONDITION_LIST}` is not empty:**

For each `{PRECONDITION_NAME}` in `{PRECONDITION_LIST}`:

1. **Load precondition file:**
   **Tool:** `Read` file `tests/preconditions/{PRECONDITION_NAME}.yaml`

   **If not found:**
   - **Tool:** `Glob` pattern `tests/preconditions/*.yaml` to list available preconditions
   - FAIL with:
   ```
   ✗ Precondition not found: {PRECONDITION_NAME}

   Available preconditions:
   {list of .yaml files in tests/preconditions/}
   ```

2. **Parse precondition:**
   - Extract `steps` array from precondition YAML
   - Extract `verify` section (for later if_precondition checks)
   - Store verify config: `{PRECONDITION_VERIFIES}[{PRECONDITION_NAME}] = verify`

3. **Execute precondition steps:**
   Output:
   ```
   Precondition: {PRECONDITION_NAME}
   ────────────────────────────────────────
   ```

   For each step in precondition.steps:
   - Execute action (same logic as test steps in Action Mapping)
   - Output: `  [precondition] {action} ✓`
   - On failure: FAIL test with precondition error:
     ```
     ✗ Precondition failed: {PRECONDITION_NAME}
       Step: {action}
       Error: {error details}
     ```

4. **Verify precondition state:**
   Using the `verify` section from precondition file:
   - If `verify.element`: **Tool:** `mcp__mobile-mcp__mobile_list_elements_on_screen`, check element exists
   - If `verify.screen`: Take screenshot via `mcp__screen-buffer__device_screenshot`, AI vision check

   **If verification fails:**
   ```
   ✗ Precondition verification failed: {PRECONDITION_NAME}
   Expected: {verify.element or verify.screen}
   ```

   **If verification passes:**
   ```
   ✓ Precondition active: {PRECONDITION_NAME}
   ```

**Continue to Step 6 (Execute Setup).**

### Step 6: Execute Setup

For each step in `{SETUP_STEPS}`:
1. Execute action (see Action Mapping below)
2. Output: `  [setup] {action} ✓`

### Step 7: Execute Each Test

For each test in `{TESTS}`:

1. **Initialize test tracking:**
   ```
   {CURRENT_TEST} = {
     name: test.name,
     description: test.description,
     status: "running",
     steps_completed: 0,
     steps_total: count(test.steps),
     duration_seconds: 0,
     steps: [],
     failure: null
   }
   {TEST_START_TIME} = current time
   {STEP_COUNTER} = 0
   ```

2. Output header:
   ```
   Running: {test.name}
   ────────────────────────────────────────
   ```

3. For each step in test.steps:
   - `{STEP_COUNTER}` += 1
   - Output: `  [{STEP_COUNTER}/{total}] {action}`

   **Track step timestamp (if reporting enabled):**

   Get current timestamp before executing action:
   ```
   {STEP_TIMESTAMP} = current Unix timestamp (e.g., time.time() in Python)
   ```

   - **Execute action** (tap, swipe, type, etc.)
   - Store result: `{STEP_RESULT}` = success message or error
   - Store tap/swipe coordinates: `{ACTION_X}`, `{ACTION_Y}` (if applicable)
   - `{STEP_STATUS}` = "passed" or "failed"

   **Record step data (frames will be extracted from video later):**
   ```
   {STEP_TIMESTAMPS}.push({
     index: {STEP_COUNTER},
     timestamp: {STEP_TIMESTAMP},
     gesture: "{action type: tap, swipe, etc.}",
     x: {ACTION_X},
     y: {ACTION_Y}
   })

   {CURRENT_TEST}.steps.push({
     number: {STEP_COUNTER},
     action: "{action description}",
     status: "{STEP_STATUS}",
     result: "{STEP_RESULT}",
     timestamp: {STEP_TIMESTAMP},
     // Frames will be populated after video extraction
     frames_before: [],
     frames_after: [],
     // Tap/swipe coordinates for overlay indicator
     action_x: {ACTION_X},  // null if not tap/swipe
     action_y: {ACTION_Y}   // null if not tap/swipe
   })
   ```

   - Output result: `✓` or `✗ FAILED: {reason}`
   - On failure:
     - Record failure details in `{CURRENT_TEST}.failure`
     - Stop this test (don't continue steps)


4. **Finalize test:**
   ```
   {CURRENT_TEST}.status = "passed" or "failed"
   {CURRENT_TEST}.steps_completed = {STEP_COUNTER}
   {CURRENT_TEST}.duration_seconds = (current time - {TEST_START_TIME})
   {REPORT_DATA}.tests.push({CURRENT_TEST})
   ```

5. Output result:
   ```
   ────────────────────────────────────────
   ✓ PASSED  ({passed}/{total} steps in {duration}s)
   ```
   or
   ```
   ✗ FAILED  ({passed}/{total} steps, failed at step {N})
   ```

### Step 8: Execute Teardown

For each step in `{TEARDOWN_STEPS}`:
- Execute action
- Output: `  [teardown] {action} ✓`

**Always run teardown**, even if tests failed.

### Step 9: Show Summary

```
═══════════════════════════════════════
           TEST RESULTS
═══════════════════════════════════════

  ✓ Test name 1                    2.4s
  ✗ Test name 2                    5.1s
    └─ Failed: Element "X" not found

───────────────────────────────────────
  Total:    {count}
  Passed:   {passed}
  Failed:   {failed}
  Duration: {total}s
═══════════════════════════════════════
```

### Step 10: Generate Report (default, skip with --no-report)

**If `{SHOULD_GENERATE_REPORT}` is true:**

1. **Stop video recording:**

   **Tool:** `Bash`
   ```bash
   # Send SIGINT to screenrecord - this writes the moov atom and finalizes the file
   adb -s "{DEVICE_ID}" shell pkill -2 screenrecord
   ```

   **Wait for video script to complete:**
   ```bash
   # Wait for recording script to finish (pulls video from device)
   for i in {1..30}; do
       kill -0 {VIDEO_PID} 2>/dev/null || break
       sleep 1
   done
   echo "Video script completed"
   ```

2. **Write step timestamps for frame extraction:**

   **Tool:** `Write` to `{REPORT_DIR}/recording/step_timestamps.json`
   Content: `{STEP_TIMESTAMPS}` as JSON array

3. **Extract frames from video:**

   **Tool:** `Bash`
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/extract-frames.py" \
     "{REPORT_DIR}/recording/recording.mp4" \
     "{REPORT_DIR}/recording/step_timestamps.json" \
     "{VIDEO_START_TIME}" \
     "{REPORT_DIR}/screenshots"
   ```

   This extracts 7 frames per step in parallel:
   - `step_NNN_before_1.png` to `step_NNN_before_3.png` (300ms, 200ms, 100ms before action)
   - `step_NNN_exact.png` (at action moment)
   - `step_NNN_after_1.png` to `step_NNN_after_3.png` (100ms, 200ms, 300ms after action)

4. **Update report data with frame paths:**

   For each test in `{REPORT_DATA}.tests`:
     For each step in test.steps:
       ```
       step_num = step.number formatted as 3 digits (e.g., "001")
       step.frames_before = [
         "screenshots/step_{step_num}_before_1.png",
         "screenshots/step_{step_num}_before_2.png",
         "screenshots/step_{step_num}_before_3.png"
       ]
       step.frame_exact = "screenshots/step_{step_num}_exact.png"
       step.frames_after = [
         "screenshots/step_{step_num}_after_1.png",
         "screenshots/step_{step_num}_after_2.png",
         "screenshots/step_{step_num}_after_3.png"
       ]
       ```

5. **Finalize report data:**
   ```
   {REPORT_DATA}.ended_at = ISO timestamp
   {REPORT_DATA}.status = "completed"
   {REPORT_DATA}.summary = {
     total: count({REPORT_DATA}.tests),
     passed: count tests with status="passed",
     failed: count tests with status="failed",
     duration_seconds: (ended_at - started_at) in seconds
   }
   ```

6. **Write JSON report:**
   **Tool:** `Write` to `{REPORT_DIR}/report.json`
   Content: `{REPORT_DATA}` as JSON

7. **Generate HTML report:**
   **Tool:** `Bash`
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generate-report.py" "{REPORT_DIR}/report.json"
   ```

8. **Output report location:**
   ```
   📊 Report: {REPORT_DIR}/report.html
   ```

9. **Open report in browser (optional):**
   ```bash
   open "{REPORT_DIR}/report.html"
   ```

## Action Mapping

**Tool Architecture:**

- **Video recording:** Screen is recorded during entire test execution, frames extracted afterwards in parallel
- **screen-buffer-mcp:** Used only for verification actions (verify_screen, if_screen) that need immediate visual analysis
- **mobile-mcp:** All device interaction operations

**Video-Based Frame Extraction:**
- No screenshots taken during test execution (no runtime overhead)
- Video recording runs continuously in background
- After all steps complete, frames extracted in parallel using ffmpeg
- 7 frames per step: 3 before, 1 exact, 3 after (100ms intervals)

**Screen-Buffer Tools (verification only):**
- `mcp__screen-buffer__device_screenshot` - Used only for verify_screen and if_screen

**Mobile-MCP Tools:**
- `mcp__mobile-mcp__mobile_click_on_screen_at_coordinates` - Tap
- `mcp__mobile-mcp__mobile_swipe_on_screen` - Swipe
- `mcp__mobile-mcp__mobile_type_keys` - Text input
- `mcp__mobile-mcp__mobile_press_button` - Key events (BACK, HOME, ENTER)
- `mcp__mobile-mcp__mobile_list_elements_on_screen` - UI element discovery
- `mcp__mobile-mcp__mobile_launch_app` / `mobile_terminate_app` - App lifecycle
- `mcp__mobile-mcp__mobile_set_orientation` - Screen orientation

### Tap Actions

| YAML | Tool | Parameters |
|------|------|------------|
| `tap: "Button"` | Find element via `mcp__mobile-mcp__mobile_list_elements_on_screen`, then `mcp__mobile-mcp__mobile_click_on_screen_at_coordinates` | x, y of element center |
| `tap: [100, 200]` | `mcp__mobile-mcp__mobile_click_on_screen_at_coordinates` | x=100, y=200 |
| `tap: ["50%", "80%"]` | Calculate pixels, then `mcp__mobile-mcp__mobile_click_on_screen_at_coordinates` | x=width×0.5, y=height×0.8 |

### Finding Elements

When action uses element text (e.g., `tap: "Login"`):

1. **Tool:** `mcp__mobile-mcp__mobile_list_elements_on_screen`
2. Search for element with matching text (case-insensitive)
3. **If found:** Use element's center coordinates
4. **If not found:** Retry up to 3 times with 500ms delay
5. **After 3 failures:** FAIL and show available elements

### Other Actions

| YAML | Tool |
|------|------|
| `double_tap: "X"` | Find element → `mcp__mobile-mcp__mobile_double_tap_on_screen` |
| `long_press: "X"` | Find element → `mcp__mobile-mcp__mobile_long_press_on_screen_at_coordinates` |
| `type: "text"` | `mcp__mobile-mcp__mobile_type_keys` with text |
| `type: {text: "X", submit: true}` | `mcp__mobile-mcp__mobile_type_keys` then `mcp__mobile-mcp__mobile_press_button` button="ENTER" |
| `swipe: up` | `mcp__mobile-mcp__mobile_swipe_on_screen` direction="up" |
| `swipe: {direction: up, distance: 500}` | `mcp__mobile-mcp__mobile_swipe_on_screen` with distance |
| `press: back` | `mcp__mobile-mcp__mobile_press_button` button="BACK" |
| `press: home` | `mcp__mobile-mcp__mobile_press_button` button="HOME" |
| `press: enter` | `mcp__mobile-mcp__mobile_press_button` button="ENTER" |
| `wait: 2s` | Pause for 2 seconds (no tool call needed) |
| `launch_app` | `mcp__mobile-mcp__mobile_launch_app` with config.app |
| `terminate_app` | `mcp__mobile-mcp__mobile_terminate_app` with config.app |
| `clear_app_data` | `Bash`: `adb -s {DEVICE_ID} shell pm clear {package}` with config.app |
| `clear_app_data: "pkg"` | `Bash`: `adb -s {DEVICE_ID} shell pm clear pkg` |
| `revoke_permissions` | `Bash`: `adb -s {DEVICE_ID} shell pm reset-permissions -p {package}` with config.app |
| `revoke_permissions: "pkg"` | `Bash`: `adb -s {DEVICE_ID} shell pm reset-permissions -p pkg` |
| `screenshot: "name"` | `mcp__screen-buffer__device_screenshot` (save base64 to path) |
| `set_orientation: landscape` | `mcp__mobile-mcp__mobile_set_orientation` |
| `open_url: "https://..."` | `mcp__mobile-mcp__mobile_open_url` |

### Verification Actions

| YAML | Execution |
|------|-----------|
| `verify_screen: "X"` | Take screenshot → AI analysis → pass if matches description |
| `verify_contains: "X"` | List elements → pass if element with text X exists |
| `verify_no_element: "X"` | List elements → pass if element with text X NOT found |

#### verify_screen Implementation

1. **Tool:** `mcp__screen-buffer__device_screenshot` (fast, ~50ms)

2. **AI Analysis:** Examine the screenshot and determine if it matches the expected state description.
   - If matches: PASS
   - If doesn't match: FAIL with description of what was actually seen

### Conditional Actions

Conditionals check current state and execute branches accordingly.

**Detection:**
- Step has key starting with `if_` (if_present, if_absent, if_all_present, if_any_present, if_screen, if_precondition)
- Legacy operators still supported: if_exists (→if_present), if_not_exists (→if_absent), if_all_exist (→if_all_present), if_any_exist (→if_any_present)
- Step has `then` key (required)
- Step may have `else` key (optional)

**Evaluation Process:**

1. **Parse conditional:**
   - Extract operator: `if_present`, `if_absent`, `if_all_present`, `if_any_present`, `if_screen`, `if_precondition`
   - Map legacy operators: if_exists→if_present, if_not_exists→if_absent, if_all_exist→if_all_present, if_any_exist→if_any_present
   - Extract condition value: element text(s) or screen description
   - Extract `then` steps array (required)
   - Extract `else` steps array (optional)

2. **Evaluate condition:**

   **For element-based operators (if_present, if_absent, if_all_present, if_any_present):**
   - **Tool:** `mcp__mobile-mcp__mobile_list_elements_on_screen` (device={DEVICE_ID})
   - Get current elements list (instant check, no retries - *Rationale: Conditionals check current state at a point in time, unlike element actions which wait for UI to stabilize. If element might be loading, use `wait_for` before the conditional*)
   - Parse elements array
   - Check condition against elements

   **For `if_screen`:**
   - **Tool:** `mcp__screen-buffer__device_screenshot`
   - Analyze screenshot with AI vision (same logic as `verify_screen`)
   - Check if screen matches description

   **For `if_precondition`:**
   - Look up verify config: `{PRECONDITION_VERIFIES}[condition_value]`
   - If precondition not in `{PRECONDITION_VERIFIES}`:
     - Precondition was not executed for this test
     - Treat condition as false
     - Log warning: `⚠ Precondition '{condition_value}' not loaded, treating as false`
   - If verify config exists:
     - If `verify.element`: **Tool:** `mcp__mobile-mcp__mobile_list_elements_on_screen`, check element exists
     - If `verify.screen`: **Tool:** `mcp__screen-buffer__device_screenshot`, AI vision check
   - Condition is true if verify check passes

3. **Execute branch:**
   - If condition evaluates to true: Execute steps in `then` array
   - If condition evaluates to false: Execute steps in `else` array (if exists)
   - Each step in branch processed recursively (may contain more conditionals)
   - Track step numbers correctly (conditional + branch steps counted)

**Condition Evaluation Logic:**

| Operator | True When | False When |
|----------|-----------|------------|
| `if_present: "X"` | Element with text "X" found in elements list | Element not found |
| `if_absent: "X"` | Element with text "X" NOT in elements list | Element found |
| `if_all_present: ["A","B"]` | ALL elements found (A AND B) | Any element missing |
| `if_any_present: ["A","B"]` | At least ONE element found (A OR B) | No elements found |
| `if_screen: "desc"` | AI analysis returns "matches description" | AI returns "doesn't match" |
| `if_precondition: "name"` | Precondition verify check passes (see Step 5.7) | Verify check fails or precondition not loaded |

**Legacy operator mapping (for backward compatibility):**
| Legacy | Maps To |
|--------|---------|
| `if_exists` | `if_present` |
| `if_not_exists` | `if_absent` |
| `if_all_exist` | `if_all_present` |
| `if_any_exist` | `if_any_present` |

**Element Matching:**
- Case-insensitive text matching
- Partial match allowed (element text contains search text)
- Consistent with existing element finding logic

**Error Handling:**

1. **Missing `then` key:**
   - Fail test immediately
   - Error: `✗ FAILED: Conditional missing required 'then' key at step {N}`

2. **Empty branches:**
   - Valid - treat as no-op, skip to next step

3. **API failures (if_screen or element list retrieval):**
   - Treat condition as false
   - Execute `else` branch if present
   - Don't fail test

**Error Message Templates:**
- Missing then: `✗ FAILED: Conditional missing required 'then' key at step {N}`
- Element list failure: `⚠ WARNING: Failed to get elements for {operator}, treating condition as false`
- if_screen API failure: `⚠ WARNING: if_screen failed (AI vision API error), treating condition as false`

**Important Notes:**
- `then` and `else` must be arrays, even for single steps
- Unlimited nesting supported

**Output Format:**

**Step Numbering:**
- Conditional itself counts as 1 step: [3/8]
- Substeps use dot notation: [3.1/8], [3.2/8]
- Total count (8) doesn't change when executing branches
- Nested conditionals use additional dots: [3.1.1/8], [3.1.2/8]
- Next step after conditional continues sequence: [4/8]

**Example showing step progression:**
```
[1/8] tap "Start"
[2/8] wait 2s
[3/8] if_present "Dialog"
      ✓ Condition true, executing then branch (2 steps)
[3.1/8] tap "OK"
[3.2/8] verify_screen "Dialog closed"
[4/8] tap "Next"  ← Note: continues from 4, not 6
```

Condition true:
```
  [3/8] if_present "Upgrade Dialog"
        ✓ Condition true, executing then branch (2 steps)
  [3.1/8] tap "Maybe Later"
        ✓ Tapped at (540, 800)
  [3.2/8] wait 2s
        ✓ Waited 2.0 seconds
```

Condition false with else:
```
  [4/8] if_absent "Premium Badge"
        ✓ Condition false, executing else branch (1 step)
  [4.1/8] verify_screen "Free tier active"
        ✓ Screen matches description
```

Condition false without else:
```
  [5/8] if_any_present ["Login", "Sign In"]
        ℹ Condition false, skipping (no else branch)
```

**Examples:**

Simple dialog handling:
```yaml
- if_present: "Watch Ad to Continue"
  then:
    - tap: "Watch Ad"
    - wait_for: "Continue"
  else:
    - verify_screen: "Photo generating"
```

Nested conditionals:
```yaml
- if_present: "Premium Features"
  then:
    - tap: "Premium Features"
    - if_present: "Confirm Purchase"
      then:
        - tap: "Cancel"
  else:
    - tap: "Upgrade"
```

Multiple element check:
```yaml
- if_all_present: ["Save", "Share", "Edit"]
  then:
    - verify_screen: "Full editor mode"
  else:
    - if_any_present: ["Upgrade", "Go Premium"]
      then:
        - tap: "Maybe Later"
```

Screen-based check:
```yaml
- if_screen: "Empty gallery with no photos"
  then:
    - tap: "Import Photos"
  else:
    - tap: "Select Photo"
```

### Flow Control

| YAML | Execution |
|------|-----------|
| `wait_for: "X"` | Poll `list_elements` until element found (10s timeout) |
| `wait_for: {element: "X", timeout: 30s}` | Poll with custom timeout |
| `if_present: "X"` | Check element, execute `then` steps if found (see Conditional Actions) |
| `retry: {attempts: 3, steps: [...]}` | Retry steps on failure |
| `repeat: {times: 5, steps: [...]}` | Execute steps N times |

## Error Handling

On step failure:
1. List all elements on screen
2. Show error with:
   - What was expected
   - What was found
   - Suggestion if similar element exists
3. Mark test as failed
4. Continue to next test (don't abort suite)
5. Always run teardown
6. Frames from video recording will capture the failure state

## Output Format

### Success
```
  [3/8] tap "Login"
        ✓ Tapped at (540, 800)
```

### Failure
```
  [4/8] tap "Submit"
        ✗ FAILED: Element not found

        Elements on screen:
        - "Send" at (540, 800)
        - "Cancel" at (540, 900)

        Hint: Did you mean "Send"?

        See report for failure frames: tests/reports/2026-01-15_login/
```
