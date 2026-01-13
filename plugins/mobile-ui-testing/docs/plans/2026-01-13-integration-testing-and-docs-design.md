# Integration Testing and Documentation Update Design

**Date:** 2026-01-13
**Status:** Approved
**Approach:** Test-Driven (Testing → Documentation)

## Overview

Complete integration testing of all plugin capabilities with Android Calculator app, then update all documentation based on test findings. This ensures documentation reflects actual working behavior rather than assumptions.

## Goals

1. Verify all 5 commands work correctly with real device
2. Test new conditional operators in practice
3. Discover and document edge cases
4. Update README.md, CLAUDE.md with accurate information
5. Add verification interview feature documentation
6. Create CHANGELOG.md for version tracking

## Scope

**In Scope:**
- Full integration testing with Android Calculator
- All 5 commands: /create-test, /generate-test, /run-test, /record-test, /stop-recording
- All 5 conditional operators in real scenarios
- Documentation updates based on test findings
- Version bump recommendation

**Out of Scope:**
- iOS testing (focus on Android first)
- Performance optimization
- New feature development
- Breaking changes to existing APIs

---

## Section 1: Integration Test Architecture

### Test Structure

Location: `tests/integration/calculator/`

**Test Scenarios:**

1. **basic-operations.test.yaml**
   - Simple arithmetic: 2+2=4, 5+3=8
   - Tests: tap, type, verify_screen
   - Validates core functionality

2. **conditional-logic.test.yaml**
   - All 5 conditional operators:
     - `if_exists: "5"` - Check number button exists
     - `if_not_exists: "Error"` - Verify no error state
     - `if_all_exist: ["1", "2", "3"]` - Multiple buttons
     - `if_any_exist: ["+", "plus"]` - UI variations
     - `if_screen: "Calculator display shows 4"` - AI vision
   - Tests nested conditionals (2 levels)
   - Validates branching logic (then/else)

3. **multi-step-calculation.test.yaml**
   - Complex operations: (5+3)*2=16
   - Tests: wait_for, retry, repeat
   - Validates flow control

4. **error-recovery.test.yaml**
   - Retry mechanisms
   - Error handling
   - Graceful failures

**Command Verification Script:**

`tests/integration/run-integration-tests.sh`:

```bash
#!/bin/bash
# Integration test runner

echo "=== Mobile UI Testing Plugin - Integration Tests ==="

# Phase 1: Prerequisites
echo "Checking prerequisites..."
adb devices || exit 1
# Check Calculator installed
# Check ffmpeg installed

# Phase 2: Command tests
echo "Testing /create-test..."
# Execute and verify

echo "Testing /generate-test..."
# Execute and verify

echo "Testing /run-test..."
# Execute test files

echo "Testing /record-test + /stop-recording..."
# Manual interaction instructions

# Phase 3: Conditional operators
echo "Testing conditional operators..."
# Execute conditional-logic.test.yaml

# Phase 4: Results
echo "Generating results report..."
# Create INTEGRATION_TEST_RESULTS.md
```

**Results Documentation:**

`tests/integration/INTEGRATION_TEST_RESULTS.md`:

```markdown
# Integration Test Results

**Date:** [execution date]
**Device:** [device info]
**Calculator Package:** [package name]

## Command Testing Results

### /create-test
- [ ] Creates file successfully
- [ ] Template structure correct
- Issues: [any issues]

### /generate-test
- [ ] Generates valid YAML
- [ ] Actions mapped correctly
- Issues: [any issues]

### /run-test
- [ ] Executes test
- [ ] Shows step output
- [ ] Handles errors gracefully
- Issues: [any issues]

### /record-test + /stop-recording
- [ ] Records touch events
- [ ] Extracts frames correctly
- [ ] Identifies elements via vision
- [ ] Generates test.yaml
- Issues: [any issues]

## Conditional Operators Results

### if_exists
- [ ] Works in simple case
- [ ] Works in nested case
- [ ] Then/else branches correct
- Issues: [any issues]

### if_not_exists
- [ ] Inverse logic correct
- Issues: [any issues]

### if_all_exist
- [ ] AND logic correct
- [ ] All elements verified
- Issues: [any issues]

### if_any_exist
- [ ] OR logic correct
- [ ] First match used
- Issues: [any issues]

### if_screen
- [ ] AI vision analysis works
- [ ] Performance acceptable (~1-2s)
- [ ] Accuracy good
- Issues: [any issues]

## Performance Metrics

- Average test execution time: [X seconds]
- Element finding time: [X ms]
- AI vision time: [X seconds]
- Step overhead: [X ms]

## Issues Discovered

[List of issues, unexpected behaviors, edge cases]

## Recommendations

[Suggested fixes, improvements, documentation updates]
```

---

## Section 2: Testing Methodology & Execution Flow

### Test Execution Strategy

**Phase 1: Environment Setup (5 minutes)**

Prerequisites checklist:
```bash
# 1. Device connected
adb devices

# 2. Calculator app present
adb shell pm list packages | grep calculator

# Expected packages:
# - com.google.android.calculator
# - com.android.calculator2

# 3. ffmpeg installed
ffmpeg -version

# 4. Launch Calculator to baseline state
adb shell am start -n com.google.android.calculator/.Calculator
```

**Phase 2: Command Testing (15 minutes)**

**Test 1 - /create-test:**
```bash
/create-test calculator-basic
```

**Expected output:**
```
Creating test: calculator-basic
Created tests/calculator-basic/test.yaml
```

**Verification:**
- File exists at correct path
- Contains template with config, setup, teardown, tests
- YAML syntax valid

**Test 2 - /generate-test:**
```bash
/generate-test "tap 2, tap plus, tap 2, tap equals, verify result is 4"
```

**Expected output:**
```yaml
tests:
  - name: Calculator operation
    steps:
      - tap: "2"
      - tap: "+"
      - tap: "2"
      - tap: "="
      - verify_screen: "Display shows 4"
```

**Verification:**
- Valid YAML generated
- Actions mapped to Calculator elements
- Logical flow correct

**Test 3 - /run-test:**
```bash
/run-test tests/integration/calculator/basic-operations.test.yaml
```

**Expected output:**
```
Running: Basic arithmetic
────────────────────────────────────────

  [1/6] launch_app
        ✓ Launched com.google.android.calculator

  [2/6] tap "2"
        ✓ Tapped at (540, 800)

  [3/6] tap "+"
        ✓ Tapped at (700, 900)

  [4/6] tap "2"
        ✓ Tapped at (540, 800)

  [5/6] tap "="
        ✓ Tapped at (700, 1100)

  [6/6] verify_screen "Display shows 4"
        ✓ Screen matches description

────────────────────────────────────────
✓ PASSED  (6/6 steps in 3.2s)
```

**Verification:**
- All steps execute
- Correct tap coordinates
- AI vision verification succeeds
- Output formatting correct

**Test 4 - /record-test + /stop-recording:**

```bash
/record-test calculator-manual
```

**Expected output:**
```
> Checking ffmpeg... OK
> Creating tests/calculator-manual/
> Starting video recording...
> Starting touch capture...
> Recording started! Interact with your app.
```

**Manual interaction:** Perform 5+3=8 on Calculator

```bash
/stop-recording
```

**Expected output:**
```
> Stopping capture...
> Pulled recording.mp4 (2.3 MB)
> Extracting frames from video...
> Extracted 4 frames (100ms before each touch)
> Analyzing touch events with vision...
> Touch 1: Identified as "5"
> Touch 2: Identified as "+"
> Touch 3: Identified as "3"
> Touch 4: Identified as "="
> Generated tests/calculator-manual/test.yaml
```

**Verification:**
- Video recorded successfully
- Touch events captured with timestamps
- Frames extracted correctly
- Elements identified as text (not coordinates)
- test.yaml generated with proper syntax

**Phase 3: Conditional Operators (10 minutes)**

Execute `tests/integration/calculator/conditional-logic.test.yaml`:

```yaml
config:
  app: com.google.android.calculator

setup:
  - terminate_app
  - launch_app
  - wait: 2s

tests:
  - name: if_exists - Simple check
    steps:
      - if_exists: "5"
        then:
          - tap: "5"
          - verify_screen: "Display shows 5"
        else:
          - tap: "AC"

  - name: if_not_exists - Inverse check
    steps:
      - tap: "AC"
      - if_not_exists: "Error"
        then:
          - verify_screen: "Clear display"
        else:
          - tap: "AC"

  - name: if_all_exist - Multiple elements
    steps:
      - if_all_exist: ["1", "2", "3"]
        then:
          - verify_screen: "All number buttons present"

  - name: if_any_exist - UI variations
    steps:
      - if_any_exist: ["+", "plus", "add"]
        then:
          - tap: "+"

  - name: if_screen - AI vision
    steps:
      - tap: "2"
      - tap: "+"
      - tap: "2"
      - tap: "="
      - if_screen: "Display shows 4"
        then:
          - tap: "AC"
        else:
          - verify_screen: "Calculation error"

  - name: Nested conditionals
    steps:
      - if_exists: "5"
        then:
          - tap: "5"
          - if_exists: "+"
            then:
              - tap: "+"
              - tap: "3"
              - tap: "="

teardown:
  - terminate_app
```

**Expected behavior:**
- Step numbering: [3/8], [3.1/8], [3.2/8], [4/8]
- Instant evaluation (no retries)
- Correct branch selection (then vs else)
- Nested conditionals execute properly

**Verification checklist:**
- [ ] All 5 operators execute without errors
- [ ] Then/else branching correct
- [ ] Step numbering uses decimal notation
- [ ] Instant evaluation confirmed
- [ ] Nested conditionals work (2 levels)
- [ ] AI vision for if_screen succeeds
- [ ] Performance acceptable (<50ms for element checks, ~1-2s for if_screen)

**Phase 4: Issue Discovery & Documentation (10 minutes)**

Document in `INTEGRATION_TEST_RESULTS.md`:
- Command test results (pass/fail)
- Conditional operator results
- Performance metrics
- Issues discovered
- Edge cases found
- Unexpected behaviors
- Recommendations for fixes

### Success Criteria

- ✅ All 5 commands execute without crashes
- ✅ At least 80% of test steps pass
- ✅ New conditional operators function in real scenarios
- ✅ Clear documentation of what works vs. what needs fixes
- ✅ Results documented for reference

---

## Section 3: Documentation Update Strategy

### Documentation Updates (Based on Test Findings)

After integration tests complete, update documentation in this order:

**1. README.md Updates**

**A. Flow Control Section (lines 358-365)**

Current:
```markdown
| Action | Example | Description |
|--------|---------|-------------|
| `wait_for` | `- wait_for: "Continue"` | Wait until element appears |
| `if_present` | `- if_present: "Skip"` | Conditional execution |
| `retry` | `- retry: {attempts: 3, steps: [...]}` | Retry on failure |
| `repeat` | `- repeat: {times: 5, steps: [...]}` | Repeat steps |
```

Update to:
```markdown
| Action | Example | Description |
|--------|---------|-------------|
| `wait_for` | `- wait_for: "Continue"` | Wait until element appears |
| `if_exists` | `- if_exists: "Button"` | Execute if element exists |
| `if_not_exists` | `- if_not_exists: "Error"` | Execute if element absent |
| `if_all_exist` | `- if_all_exist: ["A", "B"]` | Execute if all elements exist (AND) |
| `if_any_exist` | `- if_any_exist: ["A", "B"]` | Execute if any element exists (OR) |
| `if_screen` | `- if_screen: "Login visible"` | Execute if screen matches description |
| `retry` | `- retry: {attempts: 3, steps: [...]}` | Retry on failure |
| `repeat` | `- repeat: {times: 5, steps: [...]}` | Repeat steps |
```

Add note:
```markdown
**Note:** The `if_present` operator is deprecated. Use `if_exists` instead for better error handling and nesting support.
```

**B. Handling Optional Elements Template (lines 467-495)**

Update from:
```yaml
- if_present: "Allow Notifications"
  then:
    - tap: "Not Now"
    - wait: 500ms
```

To:
```yaml
- if_exists: "Allow Notifications"
  then:
    - tap: "Not Now"
  else:
    - verify_screen: "No permission prompt"
```

**C. Add Conditional Logic Section**

Add after "Available Actions" section:

```markdown
### Conditional Logic

Execute steps conditionally based on runtime state:

```yaml
# Simple conditional
- if_exists: "Skip"
  then:
    - tap: "Skip"
  else:
    - verify_screen: "Required content"

# Multiple elements (AND logic)
- if_all_exist: ["Save", "Share", "Edit"]
  then:
    - verify_screen: "Full editor mode"

# Multiple elements (OR logic)
- if_any_exist: ["Login", "Sign In", "Get Started"]
  then:
    - tap: "Login"

# AI vision check
- if_screen: "Empty gallery with no photos"
  then:
    - tap: "Import Photos"
  else:
    - tap: "Select Photo"

# Nested conditionals
- if_exists: "Premium Badge"
  then:
    - if_screen: "Advanced tools visible"
      then:
        - verify_screen: "Premium features active"
```

**Key behaviors:**
- Instant evaluation (no retries)
- Full nesting support
- Decimal step numbering (3.1, 3.2)
- Empty else branches allowed

See [Conditionals Reference](skills/yaml-test-schema/references/conditionals.md) for details.
```

**D. Add Verification Interview Section**

Add after `/stop-recording` section (around line 233):

```markdown
#### Verification Interview

After recording stops, Claude guides you through adding verifications:

**What it does:**
1. **Detects checkpoints** - Identifies key moments using:
   - Screen changes (perceptual hashing)
   - Long waits (2+ seconds between taps)
   - Navigation events (back button, new screens)

2. **Suggests verifications** - AI analyzes screenshots and suggests:
   - Screen state verifications
   - Element presence checks
   - Expected outcomes

3. **Interactive interview** - You choose which verifications to add:
   ```
   Checkpoint 1: After tapping "Login" (screen changed)

   Suggested verification:
   A) verify_screen: "Login form with email and password fields"
   B) verify_contains: "Email"
   C) wait_for: "Password"
   D) Custom verification
   E) Skip this checkpoint

   Your choice: A
   ```

4. **Generates enhanced test** - Creates test.yaml with:
   - Recorded actions (from touch events)
   - Your selected verifications at checkpoints
   - Proper test structure

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

**Configuration:**
- Max 8 checkpoints per recording (top scores)
- Checkpoint detection configurable in scripts/analyze-checkpoints.py
- AI suggestions require ANTHROPIC_API_KEY environment variable
```

**2. CLAUDE.md Updates**

Add to architecture section:

```markdown
## Conditional Logic

Conditionals enable runtime branching without separate test files:

- **5 operators**: if_exists, if_not_exists, if_all_exist, if_any_exist, if_screen
- **Full nesting**: Unlimited depth, recursive execution
- **Instant evaluation**: No retries/polling (use wait_for before conditionals)
- **Integration**: Documented in commands/run-test.md

## Verification Interview

AI-guided verification insertion after recording:

**Pipeline:**
```
Recording → Checkpoint Detection → AI Suggestions → User Interview → Enhanced Test
```

**Scripts:**
- `scripts/analyze-checkpoints.py` - Detects verification points
- `scripts/suggest-verification.py` - AI-powered suggestions
- `commands/stop-recording.md` - Orchestrates interview flow

**Design:** See `docs/plans/2026-01-13-verification-interview-design.md`
```

**3. Create CHANGELOG.md**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 5 conditional operators for runtime branching:
  - `if_exists` - Single element check
  - `if_not_exists` - Inverse element check
  - `if_all_exist` - Multiple elements (AND logic)
  - `if_any_exist` - Multiple elements (OR logic)
  - `if_screen` - AI vision-based screen matching
- Full nesting support for conditionals (unlimited depth)
- Verification interview feature in /stop-recording:
  - Automatic checkpoint detection (screen changes, waits, navigation)
  - AI-powered verification suggestions
  - Interactive verification selection
  - Enhanced test generation with verifications
- Comprehensive integration tests with Android Calculator
- Example test files demonstrating all conditional operators
- Complete reference documentation for conditionals

### Changed
- Deprecated `if_present` in favor of `if_exists` (better error handling, nesting support)
- Updated all documentation examples to use new conditional syntax
- Improved /stop-recording workflow with verification interview

### Fixed
- [Any issues discovered during integration testing]

## [3.1.0] - [Previous Release Date]

[Previous changes...]
```

**4. Version Bump Decision**

Based on test results, recommend version:

**Patch (3.1.1):** If only bug fixes discovered
- No new features
- Only fixes to existing functionality

**Minor (3.2.0):** If features work as designed (likely)
- New conditional operators
- Verification interview feature
- Backwards compatible (if_present deprecated but functional)

**Major (4.0.0):** If breaking changes needed
- if_present removed entirely
- API changes required
- Incompatible with previous versions

Recommendation: **3.2.0** (minor version bump)
- Significant new features (conditionals, verification interview)
- Backwards compatible (if_present deprecated but works)
- No breaking API changes

**5. Update plugin.json (if exists)**

```json
{
  "name": "mobile-ui-testing",
  "version": "3.2.0",
  "description": "YAML-based mobile UI testing with conditional logic and AI-powered verification",
  "features": [
    "5 conditional operators with full nesting",
    "Verification interview for recorded tests",
    "Auto-approved mobile-mcp tools",
    "AI vision for screen verification"
  ]
}
```

---

## Implementation Tasks

### Task 1: Create Integration Test Suite
- Create tests/integration/calculator/ directory
- Write 4 test YAML files
- Create run-integration-tests.sh script
- Create INTEGRATION_TEST_RESULTS.md template

### Task 2: Execute Integration Tests
- Run all command tests
- Execute conditional operator tests
- Document results
- Capture screenshots/logs of issues

### Task 3: Update README.md
- Update Flow Control section
- Add Conditional Logic section
- Add Verification Interview section
- Update templates with new syntax
- Add deprecation notes

### Task 4: Update CLAUDE.md
- Add conditional logic architecture
- Document verification interview pipeline
- Update recording flow

### Task 5: Create CHANGELOG.md
- Document all changes
- Recommend version bump
- List discovered issues

### Task 6: Version Bump & Finalization
- Update version in plugin.json
- Tag release if applicable
- Commit all documentation updates

---

## Success Criteria

1. ✅ All 5 commands tested with real device
2. ✅ All conditional operators verified working
3. ✅ Integration test results documented
4. ✅ README.md updated with accurate information
5. ✅ CLAUDE.md reflects current architecture
6. ✅ CHANGELOG.md created with version history
7. ✅ Issues discovered and documented
8. ✅ Version bump recommended

---

## Notes

- Test-driven approach ensures documentation accuracy
- Android Calculator provides predictable test target
- Integration tests serve as regression suite
- Documentation updates based on real behavior, not assumptions
- Version bump reflects significant feature additions
