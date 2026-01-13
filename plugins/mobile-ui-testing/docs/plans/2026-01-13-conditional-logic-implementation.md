# Conditional Logic Implementation Design

**Date:** 2026-01-13
**Status:** Approved
**Phase:** Phase 1 - Conditional Operators Only

## Overview

Implement conditional logic in the YAML test runner to handle runtime variations (optional dialogs, permission prompts, UI state differences) without requiring separate test files.

## Goals

1. Support 5 conditional operators in test execution
2. Enable nested conditionals for complex flows
3. Instant evaluation (no polling) for responsive tests
4. Seamless integration with existing test runner
5. Clear error handling and debugging output

## Scope

**In Scope (Phase 1):**
- 5 conditional operators: `if_exists`, `if_not_exists`, `if_all_exist`, `if_any_exist`, `if_screen`
- Full nesting support (`then`/`else` branches can contain any steps)
- Integration with existing `run-test.md` command
- Error handling and edge cases

**Out of Scope (Future Phases):**
- `if_element_enabled` operator (mobile-mcp doesn't expose element state)
- Smart preconditions with auto-setup
- `if_present` legacy operator (removed for simplicity)
- State-based conditionals (orientation, network, app state)
- Comparison-based conditionals (element counts, text matching)

---

## Architecture Overview

### Core Components

1. **Conditional Step Parser** - Detects conditional syntax in YAML steps
2. **Element Checker** - Instant element presence checks using `mobile_list_elements_on_screen`
3. **Branch Executor** - Executes `then` or `else` branches based on condition result
4. **Nested Processor** - Recursively handles nested conditionals in branches

### Integration Point

Conditionals integrate into the existing "Action Mapping" section of `run-test.md` (around line 200). They're treated as a special action type alongside `tap`, `swipe`, `verify_screen`, etc.

### Execution Flow

```
Parse step → Is conditional?
                 ↓
           Yes → Evaluate condition
                 ↓
           True or False?
                 ↓
        Execute then/else branch
        (steps may contain more conditionals - recurse)
```

---

## Conditional Syntax

### General Structure

All conditionals follow this pattern:

```yaml
steps:
  - if_[operator]: [value]
    then:
      - [steps to execute if true]
    else:  # Optional
      - [steps to execute if false]
```

### Operator Specifications

#### 1. `if_exists` - Single Element Check

```yaml
- if_exists: "Login Button"
  then:
    - tap: "Login Button"
  else:
    - tap: "Sign Up"
```

**Behavior:**
- Checks if element with text "Login Button" exists on current screen
- Case-insensitive text matching
- Instant check (no retries) using `mobile_list_elements_on_screen`
- True if element found, false otherwise

#### 2. `if_not_exists` - Inverse Check

```yaml
- if_not_exists: "Loading Spinner"
  then:
    - verify_screen: "Content loaded"
  else:
    - wait: 2s
```

**Behavior:**
- Checks if element does NOT exist on current screen
- True if element NOT found, false if found
- Useful for waiting for loading states to disappear

#### 3. `if_all_exist` - Multiple Elements (AND)

```yaml
- if_all_exist: ["Save", "Share", "Edit"]
  then:
    - verify_screen: "Full editor mode"
  else:
    - verify_screen: "Limited mode"
```

**Behavior:**
- Checks if ALL specified elements exist
- Array of element text strings
- True only if every element found
- If any element missing → false

#### 4. `if_any_exist` - Multiple Elements (OR)

```yaml
- if_any_exist: ["Login", "Sign In", "Get Started"]
  then:
    - tap: "Login"
```

**Behavior:**
- Checks if at least ONE element exists
- Array of element text strings
- True if any element found
- Useful for UI variations

#### 5. `if_screen` - AI Vision Check

```yaml
- if_screen: "Login page with email field visible"
  then:
    - type: "user@example.com"
  else:
    - tap: "Show Login"
```

**Behavior:**
- Takes screenshot using `mobile_take_screenshot`
- Calls AI vision API with description (same as `verify_screen`)
- Returns true if screen semantically matches description
- False if doesn't match
- Slower than element checks (~1-2s for API call)

---

## Implementation in run-test.md

### Location

Add new section after "Verification Actions" (around line 200):

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
```

---

## Error Handling

### Error Scenarios

#### 1. Malformed Conditional Syntax

**Scenario:**
```yaml
- if_exists: "Button"
  # Missing required 'then' key
```

**Handling:**
- Fail test immediately
- Error message: `✗ FAILED: Conditional missing required 'then' key at step 5`
- Don't continue test execution

#### 2. Empty Branch

**Scenario:**
```yaml
- if_exists: "Dialog"
  then: []  # Empty array
```

**Handling:**
- Valid - treat as no-op
- Skip to next step
- No error

#### 3. AI Vision Failure (if_screen)

**Scenario:**
```yaml
- if_screen: "Login page"
  then: [...]
```

**Handling:**
- If API call fails (network error, auth error, etc.):
  - Log warning: `⚠ WARNING: if_screen failed (API error), treating as false`
  - Treat condition as `false`
  - Execute `else` branch if present
  - Continue test (don't fail)

#### 4. Nested Conditional Failure

**Scenario:**
```yaml
- if_exists: "Menu"
  then:
    - tap: "Settings"
    - if_exists: "NonExistent"
      then:
        - tap: "Save"
```

**Handling:**
- Inner conditional evaluates to false
- No `else` branch → skip inner `then` steps
- Continue with next step in outer branch
- Only fail if an action step fails (like tapping missing element)

#### 5. Element List Retrieval Failure

**Scenario:**
```yaml
- if_all_exist: ["A", "B", "C"]
```

**Handling:**
- If `mobile_list_elements_on_screen` fails:
  - Log error: `⚠ WARNING: Failed to get elements, treating condition as false`
  - Treat condition as `false`
  - Execute `else` branch or skip
  - Don't fail test

---

## Output Format

### Success Cases

**Condition true:**
```
  [3/8] if_exists "Upgrade Dialog"
        ✓ Condition true, executing then branch (2 steps)
  [3.1/8] tap "Maybe Later"
        ✓ Tapped at (540, 800)
  [3.2/8] wait 2s
        ✓ Waited 2.0 seconds
```

**Condition false with else:**
```
  [4/8] if_not_exists "Premium Badge"
        ✓ Condition false, executing else branch (1 step)
  [4.1/8] verify_screen "Free tier active"
        ✓ Screen matches description
```

**Condition false without else:**
```
  [5/8] if_any_exist ["Login", "Sign In"]
        ℹ Condition false, skipping (no else branch)
```

### Failure Cases

**Malformed syntax:**
```
  [6/8] if_exists "Button"
        ✗ FAILED: Conditional missing required 'then' key
```

**API error (non-fatal):**
```
  [7/8] if_screen "Home page"
        ⚠ WARNING: if_screen failed (API error), treating as false
        ℹ Condition false, skipping (no else branch)
```

---

## Execution Examples

### Example 1: Simple Optional Dialog

```yaml
tests:
  - name: Generate photo with ad handling
    steps:
      - tap: "Generate Photo"
      - wait: 2s
      - if_exists: "Watch Ad to Continue"
        then:
          - tap: "Watch Ad"
          - wait: 30s
          - tap: "Continue"
        else:
          - verify_screen: "Photo generating"
      - wait_for: "Photo Ready"
```

**Execution flow:**
1. Tap "Generate Photo" → ✓
2. Wait 2s → ✓
3. Check elements for "Watch Ad to Continue"
   - **Found** (free user):
     - Execute `then`: Tap ad, wait, continue
   - **Not found** (premium user):
     - Execute `else`: Verify generating screen
4. Wait for "Photo Ready" → ✓

### Example 2: Nested Conditionals

```yaml
steps:
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
```

**Execution flow:**
1. Check "Premium Features" exists
   - **Found** (premium user):
     - Tap "Premium Features"
     - Check "Confirm Purchase" exists
       - **Found**: Tap "Cancel"
       - **Not found**: Verify feature activated
   - **Not found** (free user):
     - Execute `else`: Tap "Upgrade"

### Example 3: Multiple Element Check

```yaml
steps:
  - wait_for: "Home"
  - if_all_exist: ["Save", "Share", "Edit"]
    then:
      - verify_screen: "Full editing mode active"
    else:
      - if_any_exist: ["Upgrade", "Go Premium"]
        then:
          - tap: "Maybe Later"
```

**Execution flow:**
1. Wait for "Home" element → ✓
2. Check if ALL of ["Save", "Share", "Edit"] exist
   - **All found** (premium):
     - Verify full editing mode
   - **Any missing** (free):
     - Check if ANY of ["Upgrade", "Go Premium"] exist
       - **Found**: Tap "Maybe Later"
       - **Not found**: Skip (no nested else)

### Example 4: Screen-Based Conditional

```yaml
steps:
  - tap: "Open Gallery"
  - wait: 2s
  - if_screen: "Empty gallery with no photos"
    then:
      - tap: "Import Photos"
      - wait: 5s
    else:
      - tap: "Select Photo"
  - verify_screen: "Photo selected"
```

**Execution flow:**
1. Tap "Open Gallery" → ✓
2. Wait 2s → ✓
3. Take screenshot, call AI vision
   - **AI returns**: "matches empty gallery description"
     - Execute `then`: Import photos flow
   - **AI returns**: "doesn't match, photos present"
     - Execute `else`: Select photo flow
4. Verify photo selected → ✓

---

## Testing Strategy

### Unit Tests

Create mock test files covering:

1. **Basic conditionals:**
   - `if_exists` with true/false cases
   - `if_not_exists` with true/false cases

2. **Multiple element checks:**
   - `if_all_exist` with all found, some missing
   - `if_any_exist` with one found, none found

3. **Nested conditionals:**
   - 2 levels deep
   - 3 levels deep (edge case)

4. **Error cases:**
   - Missing `then` key
   - Empty branches
   - Invalid syntax

### Integration Tests

Test with real mobile-mcp:

1. Permission dialog handling
2. Login screen variations
3. Premium vs free user flows
4. Onboarding skip logic

---

## Implementation Tasks

### Task 1: Update run-test.md with Conditional Logic

**Files:**
- Modify: `commands/run-test.md`

**Changes:**
1. Add "Conditional Actions" section after "Verification Actions"
2. Document all 5 operators with syntax and behavior
3. Add conditional detection logic to step processing
4. Implement evaluation logic for each operator
5. Add branch execution with recursion support
6. Update error handling section
7. Update output format examples

### Task 2: Create Test Files

**Files:**
- Create: `tests/examples/conditional-basic.test.yaml`
- Create: `tests/examples/conditional-nested.test.yaml`
- Create: `tests/examples/conditional-screen.test.yaml`

**Content:**
- Example tests demonstrating each operator
- Reference examples for documentation
- Runnable tests for validation

### Task 3: Update Documentation

**Files:**
- Modify: `skills/yaml-test-schema/references/conditionals.md`

**Changes:**
- Add note: "Implementation status: ✅ Fully implemented"
- Remove `if_present` references
- Remove `if_element_enabled` references (not implemented)
- Add execution behavior notes
- Link to example test files

### Task 4: Integration Testing

**Process:**
1. Run example test files with real device
2. Verify all operators work correctly
3. Test nested conditionals
4. Verify error handling
5. Check output formatting

---

## Success Criteria

1. ✅ All 5 operators work correctly with instant evaluation
2. ✅ Nested conditionals execute properly (3+ levels deep)
3. ✅ Error cases handled gracefully (don't crash tests)
4. ✅ Clear output shows condition results and branch execution
5. ✅ Integration with existing actions seamless (tap, verify, etc.)
6. ✅ Example test files run successfully
7. ✅ Documentation updated and accurate

---

## Future Enhancements (Phase 2+)

### Additional Operators

**State-based:**
- `if_orientation: landscape` - Check device orientation
- `if_network: connected` - Network connectivity check

**Comparison-based:**
- `if_element_count: {element: "Item", greater_than: 5}` - Element counting
- `if_text_contains: {element: "Status", text: "Success"}` - Text matching

**Element state:**
- `if_element_enabled: "Submit"` - Clickable state check (requires mobile-mcp support)

### Smart Preconditions

See `docs/plans/2026-01-13-verification-interview-design.md` for full precondition design:
- Built-in preconditions: `user_logged_in`, `user_state`, `min_photos`, etc.
- Auto-setup logic
- Credential management
- Failure handling strategies

---

## Appendix: Design Decisions

### Why instant checks instead of polling?

**Decision:** Conditionals check current state instantly, no retries.

**Rationale:**
- Conditionals are about current state, not waiting for change
- If waiting needed, use `wait_for` before conditional
- Keeps tests fast and responsive
- Clear semantics: "if this exists right now"

**Example pattern:**
```yaml
- wait_for: "Home"              # Wait for state
- if_exists: "Upgrade Dialog"   # Check current state
  then:
    - tap: "Maybe Later"
```

### Why support nesting?

**Decision:** Full nesting support for conditionals.

**Rationale:**
- Minimal implementation cost (recursion handles it naturally)
- Important for complex flows (premium checks, dialog chains)
- Documentation already shows nested examples
- Users expect it based on other programming languages

### Why no `if_element_enabled`?

**Decision:** Defer `if_element_enabled` to future phase.

**Rationale:**
- mobile-mcp `list_elements_on_screen` doesn't expose enabled state
- Would require AI vision fallback (slow, expensive)
- Can use `if_exists` + `verify_screen` as workaround
- Add when mobile-mcp supports element properties

### Why remove `if_present`?

**Decision:** Don't support legacy `if_present` operator.

**Rationale:**
- Simplifies implementation (one less operator)
- `if_exists` is clearer and more consistent
- No existing tests depend on it (documentation only)
- Migration is trivial (rename `if_present` to `if_exists`)
