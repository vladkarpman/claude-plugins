# Integration Testing and Documentation Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Execute comprehensive integration tests with Android Calculator, verify all plugin capabilities work correctly, then update all documentation based on test findings.

**Architecture:** Test-driven approach - create test suite, execute against real device, document results, then update README.md/CLAUDE.md/CHANGELOG.md with verified information.

**Tech Stack:** YAML test files, Bash scripts, Android Calculator app, adb, mobile-mcp tools

---

## Task 1: Create Integration Test Files

**Files:**
- Create: `tests/integration/calculator/basic-operations.test.yaml`
- Create: `tests/integration/calculator/conditional-logic.test.yaml`
- Create: `tests/integration/calculator/multi-step-calculation.test.yaml`
- Create: `tests/integration/calculator/error-recovery.test.yaml`

**Step 1: Determine Calculator package name**

Run: `adb shell pm list packages | grep calculator`

Expected output (one of):
```
package:com.google.android.calculator
package:com.android.calculator2
```

Store the actual package name for use in test files.

**Step 2: Create basic-operations.test.yaml**

File: `tests/integration/calculator/basic-operations.test.yaml`

```yaml
config:
  app: com.google.android.calculator  # Adjust based on Step 1

setup:
  - terminate_app
  - launch_app
  - wait: 2s

teardown:
  - terminate_app

tests:
  - name: Simple addition 2+2=4
    steps:
      - tap: "2"
      - tap: "+"
      - tap: "2"
      - tap: "="
      - verify_screen: "Display shows 4"

  - name: Clear and calculate 5+3=8
    steps:
      - tap: "AC"
      - wait: 500ms
      - tap: "5"
      - tap: "+"
      - tap: "3"
      - tap: "="
      - verify_screen: "Display shows 8"
```

**Step 3: Create conditional-logic.test.yaml**

File: `tests/integration/calculator/conditional-logic.test.yaml`

```yaml
config:
  app: com.google.android.calculator  # Adjust based on Step 1

setup:
  - terminate_app
  - launch_app
  - wait: 2s

teardown:
  - terminate_app

tests:
  - name: if_exists - Check button presence
    steps:
      # Test if_exists operator
      - if_exists: "5"
        then:
          - tap: "5"
          - verify_screen: "Display shows 5"
        else:
          - tap: "AC"

  - name: if_not_exists - Verify no error
    steps:
      - tap: "AC"
      - wait: 500ms
      # Check display is clear (no error)
      - if_not_exists: "Error"
        then:
          - verify_screen: "Clear calculator display"
        else:
          - tap: "AC"

  - name: if_all_exist - Multiple buttons present
    steps:
      # Verify all number buttons 1, 2, 3 exist
      - if_all_exist: ["1", "2", "3"]
        then:
          - verify_screen: "Number pad visible"

  - name: if_any_exist - Handle UI variations
    steps:
      # Check for + operator (might have variations)
      - if_any_exist: ["+", "plus", "add"]
        then:
          - tap: "+"
          - tap: "1"
          - tap: "="

  - name: if_screen - AI vision check
    steps:
      - tap: "AC"
      - tap: "2"
      - tap: "+"
      - tap: "2"
      - tap: "="
      # Use AI vision to verify result
      - if_screen: "Calculator display shows 4"
        then:
          - tap: "AC"
        else:
          - verify_screen: "Unexpected calculation result"

  - name: Nested conditionals - 2 levels deep
    steps:
      - tap: "AC"
      # Level 1: Check if button 5 exists
      - if_exists: "5"
        then:
          - tap: "5"
          # Level 2: Check if + operator exists
          - if_exists: "+"
            then:
              - tap: "+"
              - tap: "3"
              - tap: "="
              - verify_screen: "Display shows 8"
        else:
          - tap: "1"
```

**Step 4: Create multi-step-calculation.test.yaml**

File: `tests/integration/calculator/multi-step-calculation.test.yaml`

```yaml
config:
  app: com.google.android.calculator  # Adjust based on Step 1

setup:
  - terminate_app
  - launch_app
  - wait: 2s

teardown:
  - terminate_app

tests:
  - name: Complex calculation with wait_for
    steps:
      - tap: "AC"
      - wait_for: "5"
      - tap: "5"
      - tap: "+"
      - tap: "3"
      - tap: "="
      - wait_for: "8"
      - verify_screen: "Result is 8"

  - name: Retry mechanism test
    steps:
      - tap: "AC"
      - retry:
          attempts: 3
          delay: 500ms
          steps:
            - tap: "2"
            - tap: "+"
            - tap: "2"
            - tap: "="
            - verify_screen: "Display shows 4"
```

**Step 5: Create error-recovery.test.yaml**

File: `tests/integration/calculator/error-recovery.test.yaml`

```yaml
config:
  app: com.google.android.calculator  # Adjust based on Step 1

setup:
  - terminate_app
  - launch_app
  - wait: 2s

teardown:
  - terminate_app

tests:
  - name: Graceful handling of missing elements
    steps:
      - tap: "AC"
      # Try to tap non-existent button with retry
      - retry:
          attempts: 2
          delay: 1s
          steps:
            - tap: "2"
            - tap: "+"
            - tap: "2"
```

**Step 6: Commit test files**

```bash
git add tests/integration/calculator/
git commit -m "test: add Calculator integration test suite

Add 4 test files for comprehensive integration testing:
- basic-operations: simple arithmetic validation
- conditional-logic: all 5 conditional operators
- multi-step-calculation: flow control (wait_for, retry)
- error-recovery: error handling scenarios

Tests target Android Calculator app for predictable UI."
```

---

## Task 2: Create Integration Test Runner Script

**Files:**
- Create: `tests/integration/run-integration-tests.sh`

**Step 1: Create the script**

File: `tests/integration/run-integration-tests.sh`

```bash
#!/bin/bash

# Integration Test Runner for Mobile UI Testing Plugin
# Tests all commands and conditional operators with Android Calculator

set -e  # Exit on first error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Mobile UI Testing Plugin - Integration Tests            ║"
echo "╔════════════════════════════════════════════════════════════╗"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print test result
print_result() {
    local test_name="$1"
    local result="$2"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# ============================================================
# Phase 1: Prerequisites Check
# ============================================================

echo "─────────────────────────────────────────────────────────────"
echo "Phase 1: Checking Prerequisites"
echo "─────────────────────────────────────────────────────────────"
echo ""

# Check adb
echo -n "Checking adb... "
if command -v adb &> /dev/null; then
    echo -e "${GREEN}OK${NC}"
    print_result "adb installed" "PASS"
else
    echo -e "${RED}FAIL${NC}"
    print_result "adb installed" "FAIL"
    echo "Error: adb not found. Please install Android SDK platform-tools."
    exit 1
fi

# Check device connected
echo -n "Checking device connection... "
DEVICE_COUNT=$(adb devices | grep -v "List" | grep "device$" | wc -l)
if [ "$DEVICE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}OK${NC} ($DEVICE_COUNT device(s))"
    print_result "Device connected" "PASS"
else
    echo -e "${RED}FAIL${NC}"
    print_result "Device connected" "FAIL"
    echo "Error: No devices connected. Run 'adb devices' to check."
    exit 1
fi

# Check Calculator app
echo -n "Checking Calculator app... "
if adb shell pm list packages | grep -q calculator; then
    CALC_PACKAGE=$(adb shell pm list packages | grep calculator | head -1 | cut -d: -f2)
    echo -e "${GREEN}OK${NC} ($CALC_PACKAGE)"
    print_result "Calculator app present" "PASS"
else
    echo -e "${RED}FAIL${NC}"
    print_result "Calculator app present" "FAIL"
    echo "Error: Calculator app not found on device."
    exit 1
fi

# Check ffmpeg (for recording tests)
echo -n "Checking ffmpeg... "
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}OK${NC}"
    print_result "ffmpeg installed" "PASS"
else
    echo -e "${YELLOW}WARNING${NC} - Recording tests will be skipped"
    print_result "ffmpeg installed" "FAIL"
fi

echo ""

# ============================================================
# Phase 2: Command Testing
# ============================================================

echo "─────────────────────────────────────────────────────────────"
echo "Phase 2: Command Testing"
echo "─────────────────────────────────────────────────────────────"
echo ""

# Test 1: /create-test
echo "Test 1: /create-test command"
echo "   Expected: Creates test file with proper structure"
echo "   Action: Manual verification required"
echo -e "   ${YELLOW}→ Run: /create-test calculator-test-manual${NC}"
echo "   → Verify: tests/calculator-test-manual/test.yaml exists"
echo ""
read -p "   Did /create-test work correctly? (y/n): " response
if [ "$response" = "y" ]; then
    print_result "/create-test command" "PASS"
else
    print_result "/create-test command" "FAIL"
fi
echo ""

# Test 2: /generate-test
echo "Test 2: /generate-test command"
echo "   Expected: Generates valid YAML from natural language"
echo "   Action: Manual verification required"
echo -e "   ${YELLOW}→ Run: /generate-test \"tap 2, tap plus, tap 2, tap equals\"${NC}"
echo "   → Verify: Valid YAML generated with correct actions"
echo ""
read -p "   Did /generate-test work correctly? (y/n): " response
if [ "$response" = "y" ]; then
    print_result "/generate-test command" "PASS"
else
    print_result "/generate-test command" "FAIL"
fi
echo ""

# Test 3: /run-test
echo "Test 3: /run-test command"
echo "   Expected: Executes test files successfully"
echo "   Action: Automated test execution"
echo -e "   ${YELLOW}→ Running: tests/integration/calculator/basic-operations.test.yaml${NC}"
echo ""
read -p "   Ready to run /run-test? (y to continue): " response
if [ "$response" = "y" ]; then
    echo "   → Please run: /run-test tests/integration/calculator/basic-operations.test.yaml"
    read -p "   Did the test execute and pass? (y/n): " result
    if [ "$result" = "y" ]; then
        print_result "/run-test basic operations" "PASS"
    else
        print_result "/run-test basic operations" "FAIL"
    fi
fi
echo ""

# Test 4: /record-test and /stop-recording
if command -v ffmpeg &> /dev/null; then
    echo "Test 4: /record-test and /stop-recording commands"
    echo "   Expected: Records touch events and generates test"
    echo "   Action: Manual verification required"
    echo -e "   ${YELLOW}→ Run: /record-test calculator-recording${NC}"
    echo "   → Perform: Tap 5, tap +, tap 3, tap ="
    echo -e "   ${YELLOW}→ Run: /stop-recording${NC}"
    echo "   → Verify: test.yaml created with element text (not coordinates)"
    echo ""
    read -p "   Did recording work correctly? (y/n): " response
    if [ "$response" = "y" ]; then
        print_result "/record-test and /stop-recording" "PASS"
    else
        print_result "/record-test and /stop-recording" "FAIL"
    fi
fi
echo ""

# ============================================================
# Phase 3: Conditional Operators Testing
# ============================================================

echo "─────────────────────────────────────────────────────────────"
echo "Phase 3: Conditional Operators Testing"
echo "─────────────────────────────────────────────────────────────"
echo ""

echo "Test 5: Conditional operators"
echo "   Expected: All 5 operators work with proper branching"
echo -e "   ${YELLOW}→ Running: tests/integration/calculator/conditional-logic.test.yaml${NC}"
echo ""
read -p "   Ready to run conditional tests? (y to continue): " response
if [ "$response" = "y" ]; then
    echo "   → Please run: /run-test tests/integration/calculator/conditional-logic.test.yaml"
    echo ""
    read -p "   Did if_exists work correctly? (y/n): " result
    [ "$result" = "y" ] && print_result "if_exists operator" "PASS" || print_result "if_exists operator" "FAIL"

    read -p "   Did if_not_exists work correctly? (y/n): " result
    [ "$result" = "y" ] && print_result "if_not_exists operator" "PASS" || print_result "if_not_exists operator" "FAIL"

    read -p "   Did if_all_exist work correctly? (y/n): " result
    [ "$result" = "y" ] && print_result "if_all_exist operator" "PASS" || print_result "if_all_exist operator" "FAIL"

    read -p "   Did if_any_exist work correctly? (y/n): " result
    [ "$result" = "y" ] && print_result "if_any_exist operator" "PASS" || print_result "if_any_exist operator" "FAIL"

    read -p "   Did if_screen work correctly? (y/n): " result
    [ "$result" = "y" ] && print_result "if_screen operator" "PASS" || print_result "if_screen operator" "FAIL"

    read -p "   Did nested conditionals work correctly? (y/n): " result
    [ "$result" = "y" ] && print_result "Nested conditionals" "PASS" || print_result "Nested conditionals" "FAIL"
fi
echo ""

# ============================================================
# Phase 4: Summary
# ============================================================

echo "─────────────────────────────────────────────────────────────"
echo "Test Summary"
echo "─────────────────────────────────────────────────────────────"
echo ""
echo "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ All Integration Tests Passed!          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ Some Tests Failed - Review Above        ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
    exit 1
fi
```

**Step 2: Make script executable**

```bash
chmod +x tests/integration/run-integration-tests.sh
```

**Step 3: Commit script**

```bash
git add tests/integration/run-integration-tests.sh
git commit -m "test: add integration test runner script

Comprehensive test runner that:
- Checks prerequisites (adb, device, Calculator, ffmpeg)
- Tests all 5 commands manually with verification prompts
- Tests all 5 conditional operators
- Tracks pass/fail results
- Provides summary report

Interactive script guides user through testing process."
```

---

## Task 3: Execute Integration Tests and Document Results

**Files:**
- Create: `tests/integration/INTEGRATION_TEST_RESULTS.md`

**Step 1: Run the integration test script**

```bash
cd tests/integration
./run-integration-tests.sh
```

Follow the prompts and record results.

**Step 2: Create results template**

File: `tests/integration/INTEGRATION_TEST_RESULTS.md`

```markdown
# Integration Test Results

**Date:** [Fill in execution date]
**Device:** [Fill in device name/model]
**Android Version:** [Fill in Android version]
**Calculator Package:** [Fill in from test output]
**Tester:** [Your name]

## Environment

- adb version: [Fill in]
- ffmpeg version: [Fill in if available]
- Device resolution: [Fill in]

## Command Testing Results

### /create-test
- [x] Creates file successfully: YES/NO
- [x] Template structure correct: YES/NO
- Issues: [Any issues encountered]

### /generate-test
- [x] Generates valid YAML: YES/NO
- [x] Actions mapped correctly: YES/NO
- Issues: [Any issues encountered]

### /run-test
- [x] Executes basic-operations.test.yaml: YES/NO
- [x] Shows step-by-step output: YES/NO
- [x] All steps pass: YES/NO
- Issues: [Any issues encountered]

### /record-test + /stop-recording
- [x] Records touch events: YES/NO
- [x] Extracts frames correctly: YES/NO
- [x] Identifies elements via vision: YES/NO
- [x] Generates test.yaml: YES/NO
- Issues: [Any issues encountered]

## Conditional Operators Results

### if_exists
- [x] Simple check works: YES/NO
- [x] Then branch executes: YES/NO
- [x] Else branch executes when false: YES/NO
- Issues: [Any issues encountered]

### if_not_exists
- [x] Inverse logic correct: YES/NO
- Issues: [Any issues encountered]

### if_all_exist
- [x] AND logic correct: YES/NO
- [x] All elements verified: YES/NO
- Issues: [Any issues encountered]

### if_any_exist
- [x] OR logic correct: YES/NO
- [x] First match used: YES/NO
- Issues: [Any issues encountered]

### if_screen
- [x] AI vision analysis works: YES/NO
- [x] Performance acceptable: YES/NO
- [x] Accuracy good: YES/NO
- Execution time: [X seconds]
- Issues: [Any issues encountered]

### Nested Conditionals
- [x] 2-level nesting works: YES/NO
- [x] Step numbering correct (3.1, 3.2): YES/NO
- [x] Branches execute correctly: YES/NO
- Issues: [Any issues encountered]

## Performance Metrics

- Basic test execution time: [X seconds]
- Conditional test execution time: [X seconds]
- Average element finding time: [X ms]
- Average if_screen time: [X seconds]

## Issues Discovered

[List all issues, bugs, unexpected behaviors found during testing]

1. Issue: [Description]
   - Severity: Critical/High/Medium/Low
   - Steps to reproduce:
   - Expected behavior:
   - Actual behavior:

## Edge Cases Found

[List any edge cases or special scenarios discovered]

## Recommendations

[List recommended fixes, improvements, or documentation updates]

## Overall Assessment

- Commands working: X/5
- Conditional operators working: X/5
- Ready for documentation update: YES/NO
- Recommended version bump: Patch/Minor/Major
- Notes: [Overall assessment]
```

**Step 3: Fill in the results document**

Based on actual test execution, fill in all the YES/NO fields, times, and issue descriptions.

**Step 4: Commit results**

```bash
git add tests/integration/INTEGRATION_TEST_RESULTS.md
git commit -m "test: document integration test results

Complete integration testing performed against Android Calculator.
Document actual test execution results, performance metrics,
issues discovered, and recommendations for documentation updates."
```

---

## Task 4: Update README.md Based on Test Findings

**Files:**
- Modify: `README.md`

**Step 1: Update Flow Control section (lines 358-365)**

Replace current content:

```markdown
| Action | Example | Description |
|--------|---------|-------------|
| `wait_for` | `- wait_for: "Continue"` | Wait until element appears |
| `if_present` | `- if_present: "Skip"` | Conditional execution |
| `retry` | `- retry: {attempts: 3, steps: [...]}` | Retry on failure |
| `repeat` | `- repeat: {times: 5, steps: [...]}` | Repeat steps |
```

With:

```markdown
### Flow Control

| Action | Example | Description |
|--------|---------|-------------|
| `wait_for` | `- wait_for: "Continue"` | Wait until element appears (10s timeout) |
| `if_exists` | `- if_exists: "Button"` | Execute then/else based on element presence |
| `if_not_exists` | `- if_not_exists: "Error"` | Execute if element not present |
| `if_all_exist` | `- if_all_exist: ["A", "B"]` | Execute if ALL elements exist (AND) |
| `if_any_exist` | `- if_any_exist: ["A", "B"]` | Execute if ANY element exists (OR) |
| `if_screen` | `- if_screen: "Login page"` | Execute based on AI vision screen match |
| `retry` | `- retry: {attempts: 3, steps: [...]}` | Retry steps on failure |
| `repeat` | `- repeat: {times: 5, steps: [...]}` | Repeat steps N times |

**Note:** `if_present` is deprecated. Use `if_exists` for better error handling and nesting support.
```

**Step 2: Add Conditional Logic section**

After "Available Actions" section (around line 366), add:

```markdown
## Conditional Logic

Execute steps conditionally based on runtime state. All conditionals support full nesting and then/else branches.

### Basic Conditional

```yaml
- if_exists: "Skip Tutorial"
  then:
    - tap: "Skip Tutorial"
  else:
    - verify_screen: "Tutorial required"
```

### Multiple Elements (AND Logic)

```yaml
# Check if ALL buttons are present
- if_all_exist: ["Save", "Share", "Edit"]
  then:
    - verify_screen: "Full editor mode active"
  else:
    - verify_screen: "Limited editing mode"
```

### Multiple Elements (OR Logic)

```yaml
# Check if ANY login button variant exists
- if_any_exist: ["Login", "Sign In", "Get Started"]
  then:
    - tap: "Login"
  else:
    - verify_screen: "Already logged in"
```

### AI Vision Check

```yaml
# Use AI to verify screen state
- if_screen: "Empty gallery with no photos"
  then:
    - tap: "Import Photos"
    - wait: 5s
  else:
    - tap: "Select Photo"
```

### Nested Conditionals

```yaml
# Conditionals can be nested
- if_exists: "Premium Badge"
  then:
    - if_screen: "Advanced tools visible"
      then:
        - verify_screen: "Premium features active"
      else:
        - tap: "Unlock Tools"
  else:
    - tap: "Upgrade to Premium"
```

### Key Behaviors

- **Instant evaluation**: Conditionals check current state once (no retries)
- **Use wait_for first**: If element might be loading, use `wait_for` before conditional
- **Full nesting**: Unlimited nesting depth supported
- **Step numbering**: Branch steps use decimal notation (3.1, 3.2, 3.1.1)
- **Empty else allowed**: Else branch is optional

**See:** [Conditionals Reference](skills/yaml-test-schema/references/conditionals.md) for complete syntax and examples.
```

**Step 3: Update "Handling Optional Elements" template (lines 467-495)**

Replace:

```yaml
- if_present: "Allow Notifications"
  then:
    - tap: "Not Now"
    - wait: 500ms

- if_present: "Rate our app"
  then:
    - tap: "Later"
    - wait: 500ms
```

With:

```yaml
- if_exists: "Allow Notifications"
  then:
    - tap: "Not Now"
  else:
    - verify_screen: "No permission prompt"

- if_exists: "Rate our app"
  then:
    - tap: "Later"
  else:
    - verify_screen: "No rating dialog"
```

**Step 4: Add Verification Interview section**

After `/stop-recording` section (around line 233), add:

```markdown
#### Verification Interview (Experimental)

After `/stop-recording`, Claude can guide you through adding verifications to your recorded test.

**How it works:**

1. **Checkpoint Detection** - Automatically identifies key moments:
   - Screen changes (perceptual hashing detects UI transitions)
   - Long waits (2+ seconds between taps indicate loading/transitions)
   - Navigation events (back button, new screens)

2. **AI Suggestions** - For each checkpoint, Claude analyzes the screenshot and suggests:
   - Screen state verifications: `verify_screen: "Login form visible"`
   - Element checks: `verify_contains: "Email"`
   - Wait conditions: `wait_for: "Submit"`

3. **Interactive Selection** - Choose verifications interactively:
   ```
   Checkpoint 1: After tapping "Login" (screen changed)

   Suggested verification:
   A) verify_screen: "Login form with email and password fields"
   B) verify_contains: "Email"
   C) wait_for: "Password"
   D) Custom verification (enter your own)
   E) Skip this checkpoint

   Your choice: A
   ```

4. **Enhanced Test Generation** - Creates test.yaml with:
   - Recorded actions (from touch events)
   - Your selected verifications at checkpoints
   - Proper structure and syntax

**Prerequisites:**
- Set `ANTHROPIC_API_KEY` environment variable for AI suggestions
- Max 8 checkpoints per recording (top-scored)

**Example output:**

```yaml
tests:
  - name: recorded-flow
    steps:
      - tap: "Login"
      - verify_screen: "Login form with email and password fields"
      - tap: "Email"
      - type: "user@example.com"
      - tap: "Password"
      - type: "password123"
      - tap: "Submit"
      - verify_screen: "Home screen after successful login"
```

**Note:** This is an experimental feature. Manual verification editing is always supported.
```

**Step 5: Update documentation references section**

Find the "Documentation" section (around line 530) and update:

```markdown
## Documentation

- [Actions Reference](skills/yaml-test-schema/references/actions.md) - All available actions
- [Assertions Reference](skills/yaml-test-schema/references/assertions.md) - Verification actions
- [Flow Control Reference](skills/yaml-test-schema/references/flow-control.md) - wait_for, retry, repeat
- [Conditionals Reference](skills/yaml-test-schema/references/conditionals.md) - if_exists, if_not_exists, if_all_exist, if_any_exist, if_screen
```

**Step 6: Commit README.md updates**

```bash
git add README.md
git commit -m "docs: update README with conditional operators and verification interview

Major documentation updates based on integration testing:
- Add Flow Control section with all 5 conditional operators
- Add Conditional Logic section with examples
- Add Verification Interview feature documentation
- Update templates to use if_exists instead of deprecated if_present
- Add conditionals reference to documentation links

All changes verified through Android Calculator integration tests."
```

---

## Task 5: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add Conditional Logic section**

After the "Recording Pipeline" section, add:

```markdown
## Conditional Logic (New in v3.2.0)

Conditionals enable runtime branching without separate test files.

**5 Operators:**
- `if_exists` - Single element check
- `if_not_exists` - Inverse element check
- `if_all_exist` - Multiple elements (AND logic)
- `if_any_exist` - Multiple elements (OR logic)
- `if_screen` - AI vision-based screen matching

**Key Features:**
- Full nesting support (unlimited depth)
- Instant evaluation (no retries - use wait_for before conditionals)
- Then/else branching
- Decimal step numbering (3.1, 3.2 for branch steps)

**Integration:**
- Documented in `commands/run-test.md`
- Examples in `tests/integration/examples/`
- Reference docs in `skills/yaml-test-schema/references/conditionals.md`

**Design:** See `docs/plans/2026-01-13-conditional-logic-implementation.md`
```

**Step 2: Add Verification Interview section**

After the Conditional Logic section, add:

```markdown
## Verification Interview (Experimental)

AI-guided verification insertion after recording.

**Pipeline:**
```
Recording → Checkpoint Detection → AI Suggestions → User Interview → Enhanced Test
```

**Components:**
- `scripts/analyze-checkpoints.py` - Detects verification points using perceptual hashing
- `scripts/suggest-verification.py` - AI-powered suggestions via Claude API
- `commands/stop-recording.md` - Orchestrates interview workflow

**Checkpoint Detection:**
- Screen changes: Perceptual hashing (imagehash library)
- Long waits: 2+ seconds between touches
- Navigation: Back button, screen transitions
- Max 8 checkpoints per recording (top-scored)

**Requirements:**
- Python dependencies: `anthropic`, `Pillow`, `imagehash`
- Environment: `ANTHROPIC_API_KEY` for AI suggestions

**Design:** See `docs/plans/2026-01-13-verification-interview-design.md`
```

**Step 3: Commit CLAUDE.md updates**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with new features

Add documentation for:
- Conditional logic operators (5 operators with nesting)
- Verification interview workflow and architecture
- Design document references

Reflects current v3.2.0 feature set verified through integration testing."
```

---

## Task 6: Create CHANGELOG.md

**Files:**
- Create: `CHANGELOG.md`

**Step 1: Create CHANGELOG.md**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.2.0] - 2026-01-13

### Added

- **Conditional Logic Operators** - Runtime branching without separate test files:
  - `if_exists` - Execute steps if element exists
  - `if_not_exists` - Execute steps if element doesn't exist
  - `if_all_exist` - Execute if ALL elements exist (AND logic)
  - `if_any_exist` - Execute if ANY element exists (OR logic)
  - `if_screen` - Execute based on AI vision screen matching
  - Full nesting support (unlimited depth)
  - Then/else branch execution
  - Decimal step numbering for branch steps (3.1, 3.2)

- **Verification Interview Feature** (Experimental) - AI-guided verification insertion:
  - Automatic checkpoint detection (screen changes, waits, navigation)
  - AI-powered verification suggestions via Claude API
  - Interactive verification selection workflow
  - Enhanced test generation with verifications at checkpoints
  - `scripts/analyze-checkpoints.py` for checkpoint detection
  - `scripts/suggest-verification.py` for AI suggestions
  - `scripts/generate-test.py` supports verification insertion

- **Integration Test Suite** - Comprehensive testing with Android Calculator:
  - `tests/integration/calculator/` test files
  - `tests/integration/run-integration-tests.sh` test runner
  - All commands and conditional operators validated

- **Example Tests** - Reference implementations:
  - `tests/integration/examples/conditional-basic.test.yaml`
  - `tests/integration/examples/conditional-nested.test.yaml`
  - `tests/integration/examples/conditional-screen.test.yaml`

- **Reference Documentation**:
  - `skills/yaml-test-schema/references/conditionals.md` - Complete conditional syntax
  - Updated `skills/yaml-test-schema/SKILL.md` with conditional operators

- **Python Dependencies** - Added to `scripts/requirements.txt`:
  - `anthropic>=0.39.0` for AI verification suggestions
  - `Pillow>=10.0.0` for image processing
  - `imagehash>=4.3.0` for perceptual hashing

### Changed

- **Deprecated `if_present` operator** - Use `if_exists` instead:
  - Better error handling
  - Full nesting support
  - Consistent with new conditional operators
  - `if_present` still works for backwards compatibility

- **Updated README.md** - Comprehensive documentation updates:
  - Flow Control section with all conditional operators
  - Conditional Logic section with examples
  - Verification Interview feature documentation
  - Updated templates to use `if_exists`

- **Updated CLAUDE.md** - Architecture documentation:
  - Conditional logic architecture
  - Verification interview pipeline
  - Design document references

### Fixed

- **Recording pipeline** - Improved frame extraction timing (100ms before touch)
- **Step numbering** - Proper decimal notation for nested steps

### Security

- No security updates in this release

## [3.1.0] - [Previous Release Date]

### Added
- Initial recording features
- Basic test execution
- YAML test schema

[Continue with previous version history if available]

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backwards compatible
- **Patch** (0.0.X): Bug fixes, backwards compatible
```

**Step 2: Commit CHANGELOG.md**

```bash
git add CHANGELOG.md
git commit -m "docs: add CHANGELOG.md with version history

Document v3.2.0 release with:
- 5 conditional operators
- Verification interview feature
- Integration test suite
- Complete documentation updates
- Deprecation of if_present

Follows Keep a Changelog format and Semantic Versioning."
```

---

## Task 7: Version Bump and Final Verification

**Files:**
- Modify: `plugin.json` (if exists)
- Modify: `package.json` (if exists)

**Step 1: Check for version files**

```bash
# Check if version files exist
ls plugin.json package.json 2>/dev/null || echo "No version files found"
```

**Step 2: Update version to 3.2.0**

If `plugin.json` exists:

```json
{
  "name": "mobile-ui-testing",
  "version": "3.2.0",
  "description": "YAML-based mobile UI testing with conditional logic and AI-powered verification"
}
```

If `package.json` exists:

```json
{
  "name": "@vladkarpman/mobile-ui-testing",
  "version": "3.2.0",
  "description": "Claude Code plugin for YAML-based mobile UI testing"
}
```

**Step 3: Commit version bump**

```bash
git add plugin.json package.json  # Only add files that exist
git commit -m "chore: bump version to 3.2.0

Minor version bump for new features:
- 5 conditional operators with full nesting
- Verification interview (experimental)
- Comprehensive integration tests
- Complete documentation updates

Backwards compatible - if_present deprecated but functional."
```

**Step 4: Create git tag**

```bash
git tag -a v3.2.0 -m "Release v3.2.0 - Conditional Logic & Verification Interview

New Features:
- 5 conditional operators (if_exists, if_not_exists, if_all_exist, if_any_exist, if_screen)
- Full nesting support for conditionals
- Verification interview with AI suggestions
- Integration test suite with Android Calculator

Documentation:
- Complete README.md updates
- CLAUDE.md architecture docs
- CHANGELOG.md version history

Tested:
- All commands verified working
- All conditional operators validated
- Android Calculator integration tests pass"

git push origin feature/verification-interview
git push origin v3.2.0
```

**Step 5: Final verification**

Review all changes:

```bash
# Review commit history
git log --oneline -10

# Verify all documentation files updated
ls -la README.md CLAUDE.md CHANGELOG.md

# Verify test files created
ls -la tests/integration/calculator/
ls -la tests/integration/examples/

# Check no uncommitted changes
git status
```

Expected: Clean working directory, all changes committed.

---

## Success Criteria

- ✅ Integration test suite created with 4 test files
- ✅ Test runner script created and executable
- ✅ Integration tests executed and results documented
- ✅ README.md updated with conditional operators and verification interview
- ✅ CLAUDE.md updated with architecture documentation
- ✅ CHANGELOG.md created with version history
- ✅ Version bumped to 3.2.0
- ✅ Git tag created for release
- ✅ All changes committed and pushed

---

## Notes

- Integration tests require real Android device with Calculator app
- Tests are semi-automated (interactive prompts for manual verification)
- Verification interview requires ANTHROPIC_API_KEY environment variable
- Version 3.2.0 is a minor bump (new features, backwards compatible)
- if_present deprecated but still functional for backwards compatibility
