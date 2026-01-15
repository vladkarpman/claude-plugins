# Preconditions + Conditional Steps Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add preconditions (reusable state setup flows) and conditional step editing to the approval UI, with operator naming migration.

**Architecture:** Three interconnected changes: (1) migrate operator names if_exists→if_present, (2) add preconditions system with /record-precondition command, (3) add conditional toggle UI to approval.html. Backward compatibility maintained by accepting old operator names.

**Tech Stack:** Markdown commands, JavaScript (approval.html), Python (generate-approval.py), YAML configuration.

---

## Task 1: Migrate Operator Names in run-test.md

**Files:**
- Modify: `commands/run-test.md:382-543` (Conditional Actions section)

**Step 1: Replace operator names in detection section**

In `commands/run-test.md`, find line ~387:
```markdown
- Step has key starting with `if_` (if_exists, if_not_exists, if_all_exist, if_any_exist, if_screen)
```

Replace with:
```markdown
- Step has key starting with `if_` (if_present, if_absent, if_all_present, if_any_present, if_screen, if_precondition)
- Legacy operators still supported: if_exists (→if_present), if_not_exists (→if_absent), if_all_exist (→if_all_present), if_any_exist (→if_any_present)
```

**Step 2: Update parse conditional section**

Find line ~394:
```markdown
   - Extract operator: `if_exists`, `if_not_exists`, `if_all_exist`, `if_any_exist`, `if_screen`
```

Replace with:
```markdown
   - Extract operator: `if_present`, `if_absent`, `if_all_present`, `if_any_present`, `if_screen`, `if_precondition`
   - Map legacy operators: if_exists→if_present, if_not_exists→if_absent, if_all_exist→if_all_present, if_any_exist→if_any_present
```

**Step 3: Update evaluate condition section**

Find line ~401:
```markdown
   **For element-based operators (if_exists, if_not_exists, if_all_exist, if_any_exist):**
```

Replace with:
```markdown
   **For element-based operators (if_present, if_absent, if_all_present, if_any_present):**
```

**Step 4: Update condition evaluation table**

Find the table at line ~420 and replace entirely:

```markdown
| Operator | True When | False When |
|----------|-----------|------------|
| `if_present: "X"` | Element with text "X" found in elements list | Element not found |
| `if_absent: "X"` | Element with text "X" NOT in elements list | Element found |
| `if_all_present: ["A","B"]` | ALL elements found (A AND B) | Any element missing |
| `if_any_present: ["A","B"]` | At least ONE element found (A OR B) | No elements found |
| `if_screen: "desc"` | AI analysis returns "matches description" | AI returns "doesn't match" |
| `if_precondition: "name"` | Precondition verify check passes (see Step 6.5) | Verify check fails |

**Legacy operator mapping (for backward compatibility):**
| Legacy | Maps To |
|--------|---------|
| `if_exists` | `if_present` |
| `if_not_exists` | `if_absent` |
| `if_all_exist` | `if_all_present` |
| `if_any_exist` | `if_any_present` |
```

**Step 5: Update all examples**

Replace all `if_exists` with `if_present`, `if_not_exists` with `if_absent`, etc. throughout the file.

Example replacement (line ~469):
```markdown
[3/8] if_present "Dialog"
      ✓ Condition true, executing then branch (2 steps)
```

**Step 6: Commit**

```bash
git add commands/run-test.md
git commit -m "refactor: migrate conditional operator names if_exists→if_present"
```

---

## Task 2: Migrate Operator Names in Documentation

**Files:**
- Modify: `skills/yaml-test-schema/references/conditionals.md`

**Step 1: Update Available Operators section**

Replace lines 5-10:
```markdown
**Available Operators:**
- ✅ `if_present` - Single element check (formerly if_exists)
- ✅ `if_absent` - Inverse element check (formerly if_not_exists)
- ✅ `if_all_present` - Multiple elements AND (formerly if_all_exist)
- ✅ `if_any_present` - Multiple elements OR (formerly if_any_exist)
- ✅ `if_screen` - AI vision-based screen matching
- 🆕 `if_precondition` - Precondition state check
```

**Step 2: Replace all operator names throughout file**

Global replacements:
- `if_exists` → `if_present`
- `if_not_exists` → `if_absent`
- `if_all_exist` → `if_all_present`
- `if_any_exist` → `if_any_present`

**Step 3: Add backward compatibility note**

After the Available Operators section, add:
```markdown
**Backward Compatibility:**
Legacy operator names (`if_exists`, `if_not_exists`, `if_all_exist`, `if_any_exist`) are still supported and automatically mapped to new names.
```

**Step 4: Commit**

```bash
git add skills/yaml-test-schema/references/conditionals.md
git commit -m "docs: migrate conditional operator names in reference docs"
```

---

## Task 3: Create Preconditions Reference Documentation

**Files:**
- Create: `skills/yaml-test-schema/references/preconditions.md`

**Step 1: Create preconditions reference file**

```markdown
# Preconditions Reference

**Implementation Status:** ✅ Fully implemented

Preconditions are named, reusable flows that establish specific app states before tests run. They enable consistent test setup and conditional branching based on app state.

## What is a Precondition?

A precondition represents a known app state, such as:
- `logged_in` - User is authenticated
- `premium_user` - Premium features enabled
- `fresh_install` - App data cleared
- `onboarding_complete` - Tutorial finished

## File Location

```
tests/
├── preconditions/           # Precondition definitions
│   ├── logged_in.yaml
│   ├── premium_user.yaml
│   └── fresh_install.yaml
└── my-test/
    └── test.yaml            # References preconditions
```

## Precondition File Format

```yaml
name: premium_user
description: "App state with premium features enabled"

# Steps to reach this state
steps:
  - launch_app
  - tap: "Debug Menu"
  - tap: "Enable Premium"
  - verify_screen: "Premium badge visible"

# Runtime verification (for if_precondition checks)
verify:
  element: "Premium Badge"
  # OR for complex states:
  # screen: "Dashboard showing premium badge"
```

**Fields:**
- `name` (required): Identifier used to reference this precondition
- `description` (optional): Human-readable explanation
- `steps` (required): Actions to reach this state
- `verify` (required): How to check if state is active at runtime

## Creating Preconditions

**Command:** `/record-precondition {name}`

```
/record-precondition premium_user
→ Recording starts (video + touch capture)
→ User performs steps to reach premium state
/stop-recording
→ Generates tests/preconditions/premium_user.yaml
```

## Using Preconditions

### Single Precondition

```yaml
config:
  app: com.example.app
  precondition: logged_in
```

### Multiple Preconditions (Sequential)

```yaml
config:
  app: com.example.app
  preconditions:
    - fresh_install
    - logged_in
    - premium_user
```

Preconditions run in order, each building on previous state.

## Execution Order

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ fresh_install│ → │  logged_in   │ → │ TEST STEPS   │
└──────────────┘    └──────────────┘    └──────────────┘
```

1. All preconditions run in specified order
2. No app restart between (unless precondition does it)
3. Precondition failure stops test execution
4. Then test steps execute

## Conditional Checking

Use `if_precondition` to branch based on active precondition:

```yaml
- if_precondition: premium_user
  then:
    - tap: "Premium Features"
    - verify_screen: "Full feature list"
  else:
    - verify_screen: "Upgrade prompt"
```

The check uses the precondition's `verify` section:
- If `verify.element` specified: Check if element is present
- If `verify.screen` specified: AI vision check against description

## Best Practices

**DO:**
- Keep preconditions focused (one state per precondition)
- Use descriptive names (`logged_in_as_admin` vs `admin`)
- Include verification step in precondition to confirm state
- Use `verify.element` for fast checks, `verify.screen` for complex states

**DON'T:**
- Create overly complex preconditions (split into multiple)
- Skip the `verify` section (needed for `if_precondition`)
- Chain too many preconditions (consider separate test files)
```

**Step 2: Commit**

```bash
git add skills/yaml-test-schema/references/preconditions.md
git commit -m "docs: add preconditions reference documentation"
```

---

## Task 4: Create record-precondition Command

**Files:**
- Create: `commands/record-precondition.md`

**Step 1: Create command file**

```markdown
---
name: record-precondition
description: Start recording a reusable precondition flow
argument-hint: <precondition-name>
allowed-tools:
  - Read
  - Write
  - Glob
  - Bash
  - AskUserQuestion
  - mcp__mobile-mcp__mobile_list_available_devices
---

# Record Precondition - Start Recording State Setup Flow

Start recording mode to capture a reusable precondition flow that establishes a specific app state.

## Execution Steps

Execute each step in order. Do not skip steps. Use the exact tools specified.

### Step 1: Get Precondition Name

**If argument provided:** Use it as `{PRECONDITION_NAME}`.

**If no argument:** Use `AskUserQuestion` tool:
```
Question: "What would you like to name this precondition? (e.g., logged_in, premium_user)"
```

Store the result as `{PRECONDITION_NAME}`.

**Validate name:** Must be lowercase with underscores only (a-z, 0-9, _).

### Step 2: Get Precondition Description

Use `AskUserQuestion`:
```
Question: "Brief description of this precondition (e.g., 'User logged in with test account')"
```

Store as `{PRECONDITION_DESCRIPTION}`.

### Step 3: Check ffmpeg

**Tool:** `Bash`
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/check-ffmpeg.sh"
```

**If output contains "OK":** Continue.
**If output contains "not found":** Stop and show install instructions.

### Step 4: Detect App Package

**Tool:** `Glob` with pattern `tests/*/test.yaml`

**If files found:** Use `Bash` to extract package:
```bash
grep -h "app:" tests/*/test.yaml | head -1 | sed 's/.*app: *//'
```
Store result as `{APP_PACKAGE}`.

**If no files or grep fails:** Use `AskUserQuestion` for app package.

### Step 5: Get Device

**Tool:** `mcp__mobile-mcp__mobile_list_available_devices`

**If 0 devices:** Stop and show connection instructions.
**If 1 device:** Use it. Store `id` as `{DEVICE_ID}`, `name` as `{DEVICE_NAME}`.
**If multiple:** Use `AskUserQuestion` to let user select.

### Step 6: Create Folders

**Tool:** `Bash`
```bash
mkdir -p tests/preconditions/{PRECONDITION_NAME}/recording/screenshots
mkdir -p .claude
```

### Step 7: Get Video Start Timestamp

**Tool:** `Bash`
```bash
python3 -c "import time; print(time.time())"
```

Store output as `{VIDEO_START_TIME}`.

### Step 8: Create Recording State

**Tool:** `Bash`
```bash
cat > .claude/recording-state.json << 'EOF'
{
  "type": "precondition",
  "preconditionName": "{PRECONDITION_NAME}",
  "preconditionDescription": "{PRECONDITION_DESCRIPTION}",
  "preconditionFolder": "tests/preconditions/{PRECONDITION_NAME}",
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

### Step 9: Start Video Recording

**Tool:** `Bash` with `run_in_background: true`
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/record-video.sh" {DEVICE_ID} tests/preconditions/{PRECONDITION_NAME}/recording/recording.mp4 &
echo "VIDEO_PID=$!"
```

Store the VIDEO_PID.

### Step 10: Start Touch Monitor

**Tool:** `Bash` with `run_in_background: true`
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/monitor-touches.py" {DEVICE_ID} tests/preconditions/{PRECONDITION_NAME}/recording &
echo "TOUCH_PID=$!"
```

Store the TOUCH_PID.

### Step 11: Update Recording State with PIDs

**Tool:** `Read` then `Write` on `.claude/recording-state.json`

Update the file with videoPid and touchPid.

### Step 12: Output Success Message

```
Recording Precondition: {PRECONDITION_NAME}
══════════════════════════════════════════════════════════

Description: {PRECONDITION_DESCRIPTION}
Device: {DEVICE_NAME} ({DEVICE_ID})
App: {APP_PACKAGE}
Saving to: tests/preconditions/{PRECONDITION_NAME}/

RECORDING ACTIVE
────────────────
Every tap, swipe, and long-press is being captured.
Perform the steps to reach your desired app state.

When done, say "stop" or use /stop-recording

Note: Video recording has a 3-minute limit.

══════════════════════════════════════════════════════════
```

### Step 13: Wait for Stop Command

When user says "stop", "done", or uses `/stop-recording`:
- Invoke the `stop-recording` command
```

**Step 2: Commit**

```bash
git add commands/record-precondition.md
git commit -m "feat: add /record-precondition command"
```

---

## Task 5: Update stop-recording.md for Preconditions

**Files:**
- Modify: `commands/stop-recording.md`

**Step 1: Update Step 1 to detect recording type**

After extracting values from recording state, add:
```markdown
- `{RECORDING_TYPE}` = type (default: "test" if not present)
- `{PRECONDITION_NAME}` = preconditionName (if type is "precondition")
- `{PRECONDITION_DESCRIPTION}` = preconditionDescription (if type is "precondition")
- `{PRECONDITION_FOLDER}` = preconditionFolder (if type is "precondition")
```

**Step 2: Add branching after Step 8.4**

After Step 8.4 (Build Analysis Data), add:

```markdown
#### Step 8.4.5: Branch by Recording Type

**If `{RECORDING_TYPE}` is "precondition":**
- Go to Step 8.7 (Generate Precondition YAML)

**Otherwise:**
- Continue to Step 8.5 (Generate Approval UI)
```

**Step 3: Add Step 8.7 for precondition generation**

After Step 8.6, add new section:

```markdown
#### Step 8.7: Generate Precondition YAML (for precondition recordings only)

**Tool:** `AskUserQuestion`
```
Question: "How should the runtime verify this precondition is active?"
Options:
- Check for element (fast)
- Check screen state (AI vision)
```

**If element check:**
```
Question: "What element text indicates this state is active?"
```
Store as `{VERIFY_ELEMENT}`.

**If screen check:**
```
Question: "Describe the screen when this state is active"
```
Store as `{VERIFY_SCREEN}`.

**Generate precondition YAML:**

**Tool:** `Write` to `{PRECONDITION_FOLDER}/precondition.yaml`

```yaml
name: {PRECONDITION_NAME}
description: "{PRECONDITION_DESCRIPTION}"

steps:
{GENERATED_STEPS}

verify:
  element: "{VERIFY_ELEMENT}"  # or screen: "{VERIFY_SCREEN}"
```

Where `{GENERATED_STEPS}` is built from touch events:
- For each touch event, generate `- tap: "element"` or `- tap: [x, y]`
- Include detected typing as `- type: "text"`

**Copy precondition to standard location:**

**Tool:** `Bash`
```bash
cp "{PRECONDITION_FOLDER}/precondition.yaml" "tests/preconditions/{PRECONDITION_NAME}.yaml"
```

**Skip Step 8.5 and 8.6** (no approval UI for preconditions - simpler flow).

#### Step 8.8: Output Precondition Results (for precondition recordings only)

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

**Update recording state and exit** (skip remaining steps).
```

**Step 4: Commit**

```bash
git add commands/stop-recording.md
git commit -m "feat: update stop-recording to handle precondition recordings"
```

---

## Task 6: Add Precondition Execution to run-test.md

**Files:**
- Modify: `commands/run-test.md`

**Step 1: Update Step 3 to parse preconditions**

After parsing `{TESTS}`, add:
```markdown
- `{PRECONDITION}` = config.precondition (single precondition name, optional)
- `{PRECONDITIONS}` = config.preconditions (array of precondition names, optional)

**Build precondition list:**
- If `{PRECONDITION}` set: `{PRECONDITION_LIST}` = [`{PRECONDITION}`]
- If `{PRECONDITIONS}` set: `{PRECONDITION_LIST}` = `{PRECONDITIONS}`
- Otherwise: `{PRECONDITION_LIST}` = [] (empty)
```

**Step 2: Add Step 5.7 for precondition execution**

After Step 5.5 (Load Configuration), before Step 6 (Execute Setup), add:

```markdown
### Step 5.7: Execute Preconditions

**If `{PRECONDITION_LIST}` is not empty:**

For each `{PRECONDITION_NAME}` in `{PRECONDITION_LIST}`:

1. **Load precondition file:**
   **Tool:** `Read` file `tests/preconditions/{PRECONDITION_NAME}.yaml`

   **If not found:** FAIL with:
   ```
   ✗ Precondition not found: {PRECONDITION_NAME}

   Available preconditions:
   {list files in tests/preconditions/}
   ```

2. **Parse precondition:**
   - Extract `steps` array
   - Extract `verify` section (for later if_precondition checks)
   - Store verify config: `{PRECONDITION_VERIFIES}[{PRECONDITION_NAME}] = verify`

3. **Execute precondition steps:**
   Output:
   ```
   Precondition: {PRECONDITION_NAME}
   ────────────────────────────────────────
   ```

   For each step in precondition.steps:
   - Execute action (same logic as test steps)
   - Output: `  [precondition] {action} ✓`
   - On failure: FAIL test with precondition error

4. **Verify precondition state:**
   Using the `verify` section:
   - If `verify.element`: Check element exists via `list_elements`
   - If `verify.screen`: AI vision check

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
```

**Step 3: Add if_precondition evaluation**

In the Conditional Actions section, after the `if_screen` evaluation, add:

```markdown
   **For `if_precondition`:**
   - Look up verify config: `{PRECONDITION_VERIFIES}[condition_value]`
   - If `verify.element`: Check element exists via `list_elements`
   - If `verify.screen`: AI vision check
   - Condition is true if verify check passes

   **If precondition not in `{PRECONDITION_VERIFIES}`:**
   - Precondition was not executed for this test
   - Treat condition as false
   - Log warning: `⚠ Precondition '{name}' not loaded, treating as false`
```

**Step 4: Commit**

```bash
git add commands/run-test.md
git commit -m "feat: add precondition execution and if_precondition operator"
```

---

## Task 7: Add Conditional UI to approval.html

**Files:**
- Modify: `templates/approval.html`

**Step 1: Add CSS for conditional UI**

After `.suggestion-actions button` styles (around line 378), add:

```css
/* Conditional Section */
.step-conditional {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 12px;
}

.conditional-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.conditional-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--accent-color);
    display: flex;
    align-items: center;
    gap: 6px;
}

.conditional-toggle {
    width: 20px;
    height: 20px;
    cursor: pointer;
    accent-color: var(--accent-color);
}

.conditional-config {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.conditional-field {
    display: flex;
    align-items: center;
    gap: 6px;
}

.conditional-field label {
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.conditional-field select,
.conditional-field input {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 4px 8px;
    color: var(--text-primary);
    font-size: 0.8rem;
}

.conditional-field select {
    min-width: 140px;
}

.conditional-field input {
    min-width: 180px;
}

.conditional-badge {
    background: var(--accent-color);
    color: white;
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 3px;
    margin-left: 8px;
}
```

**Step 2: Update testData to include availablePreconditions**

In the script section (around line 527), update:
```javascript
const testData = {{testDataJSON}};
let steps = [...testData.steps];
let activeStepId = null;
let stepIdCounter = 0;
const availablePreconditions = testData.availablePreconditions || [];
```

**Step 3: Add conditional rendering function**

After the `renderStepEditor` function, add:

```javascript
function renderConditional(step) {
    const isConditional = step.conditional && step.conditional.enabled;
    const condType = step.conditional?.type || 'if_present';
    const condValue = step.conditional?.value || step.target?.text || '';

    return `
        <div class="step-conditional">
            <div class="conditional-header">
                <span class="conditional-label">
                    ⚡ CONDITIONAL
                </span>
                <input type="checkbox" class="conditional-toggle"
                       ${isConditional ? 'checked' : ''}
                       onchange="toggleConditional('${step.id}', this.checked); event.stopPropagation();">
            </div>
            ${isConditional ? `
                <div class="conditional-config">
                    <div class="conditional-field">
                        <label>Type:</label>
                        <select onchange="updateConditionalType('${step.id}', this.value); event.stopPropagation();">
                            <option value="if_present" ${condType === 'if_present' ? 'selected' : ''}>if_present</option>
                            <option value="if_absent" ${condType === 'if_absent' ? 'selected' : ''}>if_absent</option>
                            <option value="if_precondition" ${condType === 'if_precondition' ? 'selected' : ''}>if_precondition</option>
                            <option value="if_screen" ${condType === 'if_screen' ? 'selected' : ''}>if_screen</option>
                        </select>
                    </div>
                    <div class="conditional-field">
                        <label>${condType === 'if_precondition' ? 'Precondition:' : 'Check for:'}</label>
                        ${condType === 'if_precondition' ? `
                            <select onchange="updateConditionalValue('${step.id}', this.value); event.stopPropagation();">
                                <option value="">Select...</option>
                                ${availablePreconditions.map(p =>
                                    `<option value="${escapeHtml(p)}" ${condValue === p ? 'selected' : ''}>${escapeHtml(p)}</option>`
                                ).join('')}
                            </select>
                        ` : `
                            <input type="text" value="${escapeHtml(condValue)}"
                                   onchange="updateConditionalValue('${step.id}', this.value); event.stopPropagation();"
                                   placeholder="${condType === 'if_screen' ? 'Screen description...' : 'Element text...'}">
                        `}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}
```

**Step 4: Add conditional to step card rendering**

In `renderStepCard` function, after the frames section and before analysis, add:
```javascript
${renderConditional(step)}
```

Find this line:
```javascript
${step.frames ? renderFrames(step) : ''}

${step.analysis ? renderAnalysis(step.analysis) : ''}
```

Change to:
```javascript
${step.frames ? renderFrames(step) : ''}

${renderConditional(step)}

${step.analysis ? renderAnalysis(step.analysis) : ''}
```

**Step 5: Add conditional toggle badge to step header**

In `renderStepCard`, update the step-action span:
```javascript
<span class="step-action ${actionClass}">${step.action}: ${getStepTargetDisplay(step)}${step.conditional?.enabled ? '<span class="conditional-badge">if</span>' : ''}</span>
```

**Step 6: Add conditional management functions**

After the `updateStepDuration` function, add:

```javascript
// Conditional Management
function toggleConditional(stepId, enabled) {
    const step = steps.find(s => s.id === stepId);
    if (step) {
        if (!step.conditional) {
            step.conditional = {
                enabled: false,
                type: 'if_present',
                value: step.target?.text || ''
            };
        }
        step.conditional.enabled = enabled;
        renderSteps();
    }
}

function updateConditionalType(stepId, type) {
    const step = steps.find(s => s.id === stepId);
    if (step && step.conditional) {
        step.conditional.type = type;
        // Reset value when switching to precondition (different input type)
        if (type === 'if_precondition') {
            step.conditional.value = '';
        }
        renderSteps();
    }
}

function updateConditionalValue(stepId, value) {
    const step = steps.find(s => s.id === stepId);
    if (step && step.conditional) {
        step.conditional.value = value;
    }
}
```

**Step 7: Update stepToYAML for conditionals**

Replace the `stepToYAML` function:

```javascript
function stepToYAML(step, indent = '      ') {
    let yaml = '';

    // Check if step is conditional
    if (step.conditional?.enabled && step.conditional.value) {
        yaml = `${indent}- ${step.conditional.type}: "${escapeYamlString(step.conditional.value)}"\n`;
        yaml += `${indent}  then:\n`;
        yaml += stepToYAMLInner(step, indent + '    ');
        return yaml;
    }

    return stepToYAMLInner(step, indent);
}

function stepToYAMLInner(step, indent) {
    let yaml = '';

    if (step.action === 'tap') {
        const target = step.target?.text || `[${step.target?.x}, ${step.target?.y}]`;
        yaml = `${indent}- tap: "${escapeYamlString(target)}"\n`;
        if (step.waitAfter > 0) {
            yaml += `${indent}- wait: ${step.waitAfter}ms\n`;
        }
    } else if (step.action === 'verify_screen') {
        yaml = `${indent}- verify_screen: "${escapeYamlString(step.description || '')}"\n`;
    } else if (step.action === 'wait_for') {
        yaml = `${indent}- wait_for: "${escapeYamlString(step.target?.text || '')}"\n`;
    } else if (step.action === 'wait') {
        yaml = `${indent}- wait: ${step.duration}ms\n`;
    }

    return yaml;
}

function escapeYamlString(str) {
    if (!str) return '';
    return String(str).replace(/"/g, '\\"');
}
```

**Step 8: Commit**

```bash
git add templates/approval.html
git commit -m "feat: add conditional toggle UI to approval template"
```

---

## Task 8: Update generate-approval.py for Preconditions

**Files:**
- Modify: `scripts/generate-approval.py`

**Step 1: Add function to find available preconditions**

After the imports, add:

```python
def find_available_preconditions(base_path: Path) -> list:
    """Find all available precondition names."""
    preconditions_dir = base_path.parent.parent / "preconditions"
    if not preconditions_dir.exists():
        return []

    preconditions = []
    for f in preconditions_dir.glob("*.yaml"):
        preconditions.append(f.stem)
    return sorted(preconditions)
```

**Step 2: Update build_test_data to include preconditions**

Find where `test_data` dict is built and add:
```python
"availablePreconditions": find_available_preconditions(recording_dir),
```

**Step 3: Commit**

```bash
git add scripts/generate-approval.py
git commit -m "feat: include available preconditions in approval data"
```

---

## Task 9: Update CLAUDE.md Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add Preconditions section**

After the "Conditional Logic" section, add:

```markdown
## Preconditions (New in v3.5+)

Preconditions are reusable flows that establish specific app states before tests run.

**Creating preconditions:**
```bash
/record-precondition premium_user
→ Record steps to reach premium state
/stop-recording
→ Generates tests/preconditions/premium_user.yaml
```

**File location:** `tests/preconditions/{name}.yaml`

**File format:**
```yaml
name: premium_user
description: "Premium features enabled"

steps:
  - launch_app
  - tap: "Debug Menu"
  - tap: "Enable Premium"

verify:
  element: "Premium Badge"
```

**Using in tests:**
```yaml
config:
  app: com.example.app
  precondition: premium_user
  # OR multiple:
  preconditions:
    - logged_in
    - premium_user
```

**Conditional check:**
```yaml
- if_precondition: premium_user
  then:
    - tap: "Premium Feature"
  else:
    - verify_screen: "Upgrade prompt"
```
```

**Step 2: Update operator names in Conditional Logic section**

Replace references to old operator names:
- `if_exists` → `if_present`
- `if_not_exists` → `if_absent`
- etc.

Add note about backward compatibility.

**Step 3: Update Approval UI section**

Add:
```markdown
**Conditional editing:**
- Toggle "Conditional" on any step
- Select condition type (if_present, if_absent, if_precondition, if_screen)
- Set condition value
- Export generates proper if/then YAML structure
```

**Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add preconditions and update conditional operators in CLAUDE.md"
```

---

## Task 10: Integration Testing

**Files:**
- Create: `tests/integration/examples/precondition-example.test.yaml`

**Step 1: Create example precondition file**

**Tool:** `Write` to `tests/preconditions/calculator_cleared.yaml`

```yaml
name: calculator_cleared
description: "Calculator app with cleared display"

steps:
  - launch_app
  - tap: "AC"

verify:
  element: "0"
```

**Step 2: Create example test using precondition**

**Tool:** `Write` to `tests/integration/examples/precondition-example.test.yaml`

```yaml
config:
  app: com.google.android.calculator
  precondition: calculator_cleared

tests:
  - name: Precondition Test
    steps:
      - verify_screen: "Calculator with 0 displayed"
      - tap: "5"
      - if_precondition: calculator_cleared
        then:
          - verify_screen: "Display shows 5"
```

**Step 3: Test the flow manually**

1. Run `/run-test tests/integration/examples/precondition-example.test.yaml`
2. Verify precondition executes first
3. Verify if_precondition conditional works

**Step 4: Commit**

```bash
git add tests/preconditions/calculator_cleared.yaml
git add tests/integration/examples/precondition-example.test.yaml
git commit -m "test: add precondition integration test example"
```

---

## Success Criteria

1. ✅ Operator names migrated: if_present, if_absent, if_all_present, if_any_present
2. ✅ Old operator names work (backward compatibility)
3. ✅ `/record-precondition` creates precondition recordings
4. ✅ `/stop-recording` handles precondition recordings
5. ✅ Preconditions stored in `tests/preconditions/`
6. ✅ Tests can reference preconditions in config
7. ✅ Preconditions execute before test steps
8. ✅ `if_precondition` operator works at runtime
9. ✅ Approval UI shows conditional toggle per step
10. ✅ Conditional config (type, value) editable in UI
11. ✅ Export generates proper conditional YAML
12. ✅ Documentation updated
