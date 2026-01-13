# Conditional Logic Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 5 conditional operators (if_exists, if_not_exists, if_all_exist, if_any_exist, if_screen) in the YAML test runner with full nesting support and instant evaluation.

**Architecture:** Integrate conditional logic into run-test.md as a new action type. Parse conditional steps, evaluate conditions using mobile-mcp tools (list_elements_on_screen for element checks, take_screenshot + AI vision for screen checks), and recursively execute then/else branches. No polling - instant checks only.

**Tech Stack:** Markdown command (run-test.md), mobile-mcp tools, AI vision API

---

## Task 1: Add Conditional Actions Section to run-test.md

**Files:**
- Modify: `commands/run-test.md:183-200`

**Step 1: Read current run-test.md to locate insertion point**

Current structure shows:
- Line 183-189: Verification Actions section
- Line 191-199: Flow Control section

Insert new "Conditional Actions" section between these two.

**Step 2: Add Conditional Actions section header and detection logic**

Insert after line 189 (after Verification Actions):

```markdown
### Conditional Actions

Conditionals check current state and execute branches accordingly.

**Detection:**
- Step has key starting with `if_` (if_exists, if_not_exists, if_all_exist, if_any_exist, if_screen)
- Step has `then` key (required)
- Step may have `else` key (optional)

**Evaluation Process:**

1. **Parse conditional:**
   - Extract operator: `if_exists`, `if_not_exists`, `if_all_exist`, `if_any_exist`, `if_screen`
   - Extract condition value: element text(s) or screen description
   - Extract `then` steps array (required)
   - Extract `else` steps array (optional)

2. **Evaluate condition:**

   **For element-based operators (if_exists, if_not_exists, if_all_exist, if_any_exist):**
   - **Tool:** `mcp__mobile-mcp__mobile_list_elements_on_screen` (device={DEVICE_ID})
   - Get current elements list (instant check, no retries)
   - Parse elements array
   - Check condition against elements

   **For `if_screen`:**
   - **Tool:** `mcp__mobile-mcp__mobile_take_screenshot` (device={DEVICE_ID})
   - Analyze screenshot with AI vision (same logic as `verify_screen`)
   - Check if screen matches description

3. **Execute branch:**
   - If condition evaluates to true: Execute steps in `then` array
   - If condition evaluates to false: Execute steps in `else` array (if exists)
   - Each step in branch processed recursively (may contain more conditionals)
   - Track step numbers correctly (conditional + branch steps counted)

**Condition Evaluation Logic:**

| Operator | True When | False When |
|----------|-----------|------------|
| `if_exists: "X"` | Element with text "X" found in elements list | Element not found |
| `if_not_exists: "X"` | Element with text "X" NOT in elements list | Element found |
| `if_all_exist: ["A","B"]` | ALL elements found (A AND B) | Any element missing |
| `if_any_exist: ["A","B"]` | At least ONE element found (A OR B) | No elements found |
| `if_screen: "desc"` | AI analysis returns "matches description" | AI returns "doesn't match" |

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
   - Log warning: `⚠ WARNING: {operation} failed, treating condition as false`
   - Treat condition as false
   - Execute `else` branch if present
   - Don't fail test

**Output Format:**

Condition true:
```
  [3/8] if_exists "Upgrade Dialog"
        ✓ Condition true, executing then branch (2 steps)
  [3.1/8] tap "Maybe Later"
        ✓ Tapped at (540, 800)
  [3.2/8] wait 2s
        ✓ Waited 2.0 seconds
```

Condition false with else:
```
  [4/8] if_not_exists "Premium Badge"
        ✓ Condition false, executing else branch (1 step)
  [4.1/8] verify_screen "Free tier active"
        ✓ Screen matches description
```

Condition false without else:
```
  [5/8] if_any_exist ["Login", "Sign In"]
        ℹ Condition false, skipping (no else branch)
```

**Examples:**

Simple dialog handling:
```yaml
- if_exists: "Watch Ad to Continue"
  then:
    - tap: "Watch Ad"
    - wait: 30s
  else:
    - verify_screen: "Photo generating"
```

Nested conditionals:
```yaml
- if_exists: "Premium Features"
  then:
    - tap: "Premium Features"
    - if_exists: "Confirm Purchase"
      then:
        - tap: "Cancel"
  else:
    - tap: "Upgrade"
```

Multiple element check:
```yaml
- if_all_exist: ["Save", "Share", "Edit"]
  then:
    - verify_screen: "Full editor mode"
  else:
    - if_any_exist: ["Upgrade", "Go Premium"]
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
```

**Step 3: Update Flow Control section**

The existing `if_present` operator at line 197 should remain for backward compatibility, but note that it's deprecated in favor of the new conditional operators.

Add note to Flow Control section:
```markdown
**Note:** The `if_present` operator is deprecated. Use `if_exists` from Conditional Actions instead for better error handling and nesting support.
```

**Step 4: Commit changes**

```bash
git add commands/run-test.md
git commit -m "feat: add conditional logic operators to test runner

Add 5 conditional operators (if_exists, if_not_exists, if_all_exist,
if_any_exist, if_screen) with full nesting support and instant evaluation.

- if_exists/if_not_exists: single element checks
- if_all_exist: AND logic for multiple elements
- if_any_exist: OR logic for multiple elements
- if_screen: AI vision-based screen matching
- Full then/else branch support with recursion
- Graceful error handling for API failures
- Consistent output formatting"
```

---

## Task 2: Create Example Test Files

**Files:**
- Create: `tests/examples/conditional-basic.test.yaml`
- Create: `tests/examples/conditional-nested.test.yaml`
- Create: `tests/examples/conditional-screen.test.yaml`

**Step 1: Create examples directory if needed**

```bash
mkdir -p tests/examples
```

**Step 2: Create conditional-basic.test.yaml**

```yaml
config:
  app: com.example.testapp

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: if_exists - Basic element check
    steps:
      - tap: "Show Dialog"
      - wait: 1s
      - if_exists: "Dialog Title"
        then:
          - tap: "OK"
        else:
          - tap: "Retry"

  - name: if_not_exists - Inverse check
    steps:
      - tap: "Start Process"
      - wait: 2s
      - if_not_exists: "Loading Spinner"
        then:
          - verify_screen: "Process complete"
        else:
          - wait: 3s

  - name: if_all_exist - Multiple elements AND
    steps:
      - tap: "Open Editor"
      - wait: 2s
      - if_all_exist: ["Save", "Share", "Edit"]
        then:
          - verify_screen: "Full editor mode"
        else:
          - verify_screen: "Limited mode"

  - name: if_any_exist - Multiple elements OR
    steps:
      - tap: "Go Home"
      - wait: 2s
      - if_any_exist: ["Login", "Sign In", "Get Started"]
        then:
          - tap: "Login"
        else:
          - verify_screen: "Already logged in"

  - name: Condition false without else branch
    steps:
      - tap: "Check Premium"
      - wait: 1s
      - if_exists: "Upgrade Button"
        then:
          - tap: "Upgrade Button"
      - verify_screen: "Status checked"
```

**Step 3: Create conditional-nested.test.yaml**

```yaml
config:
  app: com.example.testapp

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: Two-level nesting
    steps:
      - tap: "Features"
      - wait: 1s
      - if_exists: "Premium Features"
        then:
          - tap: "Premium Features"
          - if_exists: "Confirm Purchase"
            then:
              - tap: "Cancel"
            else:
              - verify_screen: "Feature activated"
        else:
          - tap: "Upgrade"

  - name: Three-level nesting
    steps:
      - tap: "Settings"
      - wait: 1s
      - if_exists: "Account"
        then:
          - tap: "Account"
          - if_exists: "Subscription"
            then:
              - tap: "Subscription"
              - if_exists: "Cancel Subscription"
                then:
                  - tap: "Keep Subscription"
                else:
                  - verify_screen: "Manage subscription"
            else:
              - tap: "Subscribe"
        else:
          - tap: "Sign In"

  - name: Nested with mixed operators
    steps:
      - tap: "Gallery"
      - wait: 2s
      - if_all_exist: ["Photos", "Albums"]
        then:
          - tap: "Photos"
          - if_any_exist: ["Select All", "Select"]
            then:
              - tap: "Select All"
            else:
              - if_not_exists: "Empty State"
                then:
                  - tap: "First Photo"
        else:
          - verify_screen: "Gallery empty"
```

**Step 4: Create conditional-screen.test.yaml**

```yaml
config:
  app: com.example.testapp

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: if_screen - AI vision check
    steps:
      - tap: "Open Gallery"
      - wait: 2s
      - if_screen: "Empty gallery with no photos"
        then:
          - tap: "Import Photos"
          - wait: 5s
        else:
          - tap: "Select Photo"
      - verify_screen: "Photo selected or imported"

  - name: if_screen with nested element checks
    steps:
      - tap: "Profile"
      - wait: 2s
      - if_screen: "User profile with avatar visible"
        then:
          - if_exists: "Edit Profile"
            then:
              - tap: "Edit Profile"
          else:
            - verify_screen: "View-only profile"
        else:
          - tap: "Sign In"

  - name: Combined element and screen checks
    steps:
      - tap: "Create"
      - wait: 1s
      - if_exists: "Premium Badge"
        then:
          - if_screen: "Advanced editor tools visible"
            then:
              - verify_screen: "Full premium features available"
            else:
              - tap: "Unlock Advanced Tools"
        else:
          - if_screen: "Basic editor interface"
            then:
              - verify_screen: "Free tier features"
```

**Step 5: Commit example test files**

```bash
git add tests/examples/
git commit -m "docs: add example tests for conditional operators

Add three example test files demonstrating conditional logic:
- conditional-basic.test.yaml: all 5 operators with simple examples
- conditional-nested.test.yaml: 2-3 level nesting demonstrations
- conditional-screen.test.yaml: if_screen with AI vision checks

These serve as both documentation and integration test references."
```

---

## Task 3: Update conditionals.md Documentation

**Files:**
- Modify: `skills/yaml-test-schema/references/conditionals.md`

**Step 1: Read current conditionals.md**

Check current content to understand what needs updating.

**Step 2: Add implementation status at top**

Add after the title:

```markdown
**Implementation Status:** ✅ Fully implemented (Phase 1)

**Available Operators:**
- ✅ `if_exists` - Single element check
- ✅ `if_not_exists` - Inverse element check
- ✅ `if_all_exist` - Multiple elements (AND logic)
- ✅ `if_any_exist` - Multiple elements (OR logic)
- ✅ `if_screen` - AI vision-based screen matching

**Future Operators (Phase 2):**
- 🔄 `if_element_enabled` - Element state check (requires mobile-mcp support)
- 🔄 `if_orientation` - Device orientation check
- 🔄 `if_network` - Network connectivity check
```

**Step 3: Remove if_present references**

Search for `if_present` and either:
- Remove the section entirely
- Add deprecation note: "**Deprecated:** Use `if_exists` instead. The `if_present` operator is maintained for backward compatibility only."

**Step 4: Remove if_element_enabled implementation details**

Change `if_element_enabled` section to:

```markdown
### if_element_enabled (Not Yet Implemented)

**Status:** Deferred to Phase 2 (requires mobile-mcp support)

**Reason:** The mobile-mcp `list_elements_on_screen` tool doesn't expose element enabled/disabled state. This operator will be added when the underlying tool supports it.

**Workaround:** Use `if_exists` combined with `verify_screen` for clickability checks:
```yaml
- if_exists: "Submit Button"
  then:
    - verify_screen: "Submit button is enabled and clickable"
    - tap: "Submit Button"
```
```

**Step 5: Add execution behavior notes**

Add new section:

```markdown
## Execution Behavior

### Instant Evaluation

Conditionals perform instant checks without retries or polling:

```yaml
# ✓ GOOD: Wait first, then check
- wait_for: "Home"
- if_exists: "Upgrade Dialog"
  then:
    - tap: "Maybe Later"

# ✗ BAD: Relying on conditional to wait
- if_exists: "Upgrade Dialog"  # May execute before element appears
  then:
    - tap: "Maybe Later"
```

If you need to wait for an element before checking conditions, use `wait_for` explicitly.

### Nesting Support

Conditionals support unlimited nesting depth:

```yaml
- if_exists: "A"
  then:
    - if_exists: "B"
      then:
        - if_exists: "C"
          then:
            - tap: "Deep nested action"
```

**Best practice:** Keep nesting to 2-3 levels maximum for readability.

### Error Handling

- **Malformed syntax** (missing `then` key): Test fails immediately
- **API failures** (element list retrieval, screenshot): Condition treated as false, test continues
- **Empty branches**: Valid no-op, continues to next step
- **Nested failures**: Inner conditional failures don't affect outer conditionals

### Step Numbering

Branch steps use decimal notation:

```
[3/8] if_exists "Dialog"
      ✓ Condition true, executing then branch (2 steps)
[3.1/8] tap "OK"
        ✓ Tapped at (540, 800)
[3.2/8] wait 1s
        ✓ Waited 1.0 seconds
[4/8] verify_screen "Dialog closed"
```
```

**Step 6: Add links to example files**

Add section at the end:

```markdown
## Example Test Files

See working examples in:
- `tests/examples/conditional-basic.test.yaml` - All 5 operators with simple examples
- `tests/examples/conditional-nested.test.yaml` - 2-3 level nesting demonstrations
- `tests/examples/conditional-screen.test.yaml` - AI vision-based conditionals

Run examples:
```bash
/run-test tests/examples/conditional-basic.test.yaml
/run-test tests/examples/conditional-nested.test.yaml
/run-test tests/examples/conditional-screen.test.yaml
```
```

**Step 7: Commit documentation updates**

```bash
git add skills/yaml-test-schema/references/conditionals.md
git commit -m "docs: update conditionals.md with implementation status

Mark Phase 1 operators as fully implemented:
- Add implementation status badges
- Remove if_present (deprecated)
- Mark if_element_enabled as Phase 2
- Add execution behavior section
- Add links to example test files
- Document instant evaluation, nesting, error handling"
```

---

## Task 4: Update YAML Test Schema Skill

**Files:**
- Modify: `skills/yaml-test-schema/SKILL.md`

**Step 1: Read current SKILL.md**

Check if conditionals are already mentioned and where to add details.

**Step 2: Add conditionals to action list**

Find the section listing available actions and add:

```markdown
### Conditional Actions

Execute steps conditionally based on runtime state:

- `if_exists: "Element"` - Check if single element exists
- `if_not_exists: "Element"` - Check if element does NOT exist
- `if_all_exist: ["A", "B"]` - Check if ALL elements exist (AND)
- `if_any_exist: ["A", "B"]` - Check if ANY element exists (OR)
- `if_screen: "description"` - Check screen state with AI vision

All conditionals support `then` and `else` branches with full nesting.

**Details:** See `references/conditionals.md`
```

**Step 3: Add conditional examples to skill**

If there's an examples section, add:

```yaml
# Handle optional dialog
- if_exists: "Upgrade Dialog"
  then:
    - tap: "Maybe Later"
  else:
    - verify_screen: "No dialog shown"

# Check premium features
- if_all_exist: ["Save", "Share", "Edit"]
  then:
    - verify_screen: "Premium mode active"
  else:
    - tap: "Upgrade"

# Handle UI variations
- if_any_exist: ["Login", "Sign In", "Get Started"]
  then:
    - tap: "Login"
```

**Step 4: Commit skill updates**

```bash
git add skills/yaml-test-schema/SKILL.md
git commit -m "docs: add conditional operators to YAML test schema skill

Update skill documentation to include 5 new conditional operators
with examples and reference to detailed conditionals.md documentation."
```

---

## Task 5: Integration Testing

**Files:**
- No file changes, testing only

**Step 1: Check device connectivity**

```bash
claude --plugin-dir . "/list-devices"
```

Expected: At least one device listed

**Step 2: Run basic conditionals test**

```bash
claude --plugin-dir . "/run-test tests/examples/conditional-basic.test.yaml"
```

**Expected output:**
- All 5 test cases execute
- Conditionals show "✓ Condition true/false"
- Branch steps show decimal notation (3.1, 3.2)
- No errors or crashes

**Step 3: Run nested conditionals test**

```bash
claude --plugin-dir . "/run-test tests/examples/conditional-nested.test.yaml"
```

**Expected output:**
- 2-level and 3-level nesting executes correctly
- Step numbers track properly through nesting
- Mixed operators work together

**Step 4: Run screen-based conditionals test**

```bash
claude --plugin-dir . "/run-test tests/examples/conditional-screen.test.yaml"
```

**Expected output:**
- `if_screen` takes screenshots
- AI vision analysis completes
- Screen checks return true/false appropriately
- Combined element + screen checks work

**Step 5: Test error handling**

Create temporary test file with malformed conditional:

```yaml
config:
  app: com.example.testapp

setup:
  - terminate_app
  - launch_app
  - wait: 2s

tests:
  - name: Missing then key
    steps:
      - if_exists: "Button"
        # Missing 'then' key
        else:
          - tap: "Other"
```

Run and verify:
- Test fails immediately with clear error message
- Error shows: "✗ FAILED: Conditional missing required 'then' key"

**Step 6: Document test results**

Create `tests/examples/TEST_RESULTS.md`:

```markdown
# Conditional Logic Test Results

## Date: [Current Date]
## Device: [Device Name/ID]

### conditional-basic.test.yaml

- ✅ if_exists: Detected element correctly, executed then branch
- ✅ if_not_exists: Inverse logic worked correctly
- ✅ if_all_exist: AND logic verified all elements
- ✅ if_any_exist: OR logic found at least one element
- ✅ Missing else branch: Skipped gracefully without errors

### conditional-nested.test.yaml

- ✅ Two-level nesting: Inner conditionals executed correctly
- ✅ Three-level nesting: Deep nesting worked, step numbers correct
- ✅ Mixed operators: Different operators nested together successfully

### conditional-screen.test.yaml

- ✅ if_screen: AI vision analysis completed, returned appropriate result
- ✅ Nested with elements: Combined checks worked correctly
- ✅ Performance: if_screen ~1-2s per check as expected

### Error Handling

- ✅ Missing then key: Failed immediately with clear error
- ✅ Empty branches: Treated as no-op, continued execution
- ✅ API failures: Gracefully handled, treated as false

## Summary

All conditional operators working as designed. Integration complete.
```

**Step 7: Commit test results**

```bash
git add tests/examples/TEST_RESULTS.md
git commit -m "test: document conditional logic integration test results

All operators verified working:
- Basic conditionals (5 operators)
- Nested conditionals (2-3 levels)
- Screen-based conditionals
- Error handling

Integration testing complete and successful."
```

---

## Success Criteria Checklist

After completing all tasks, verify:

- [ ] ✅ All 5 operators implemented in run-test.md
- [ ] ✅ Nested conditionals work (tested 3 levels deep)
- [ ] ✅ Instant evaluation (no retries) confirmed
- [ ] ✅ Error handling graceful (missing then, API failures)
- [ ] ✅ Output formatting clear and consistent
- [ ] ✅ Example test files created and runnable
- [ ] ✅ Documentation updated (conditionals.md, SKILL.md)
- [ ] ✅ Integration tests pass on real device

---

## Notes for Implementation

**YAGNI Principles:**
- Don't add operators beyond the 5 specified
- Don't add polling/retry logic to conditionals
- Don't optimize step numbering beyond simple decimal notation
- Don't add comparison operators (Phase 2)

**DRY Principles:**
- Reuse existing element finding logic
- Reuse existing AI vision logic from verify_screen
- Don't duplicate error handling code

**Testing Focus:**
- Test each operator independently first
- Then test nesting combinations
- Verify error cases explicitly
- Keep example tests simple and focused

**Common Pitfalls:**
- Forgetting to handle missing `then` key (must fail test)
- Not treating API failures gracefully (must continue test)
- Incorrect step numbering in nested branches
- Case-sensitive element matching (must be case-insensitive)
