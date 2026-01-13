# Verification Interview Design

**Date:** 2026-01-13
**Status:** Approved
**Author:** Design session with user

## Overview

Transform the recording workflow from generating simple playback tests into creating real UI tests with assertions. Add a guided verification interview after recording that helps users add meaningful checkpoints and verifications to their tests.

## Problem Statement

Current recording workflow captures user actions but produces "blind playback tests" that don't verify anything actually works. Tests tap coordinates without checking if:
- Screens loaded successfully
- Photos generated correctly
- Errors appeared
- App state changed as expected

This makes tests unreliable - they can "pass" even when the app is broken.

## Goals

1. **Make tests meaningful** - Add verifications that check expected behavior
2. **Don't interrupt recording flow** - Keep natural interaction during recording
3. **Guide the user** - Suggest smart verifications based on AI analysis
4. **Support different states** - Handle premium/free users, logged in/out, etc.
5. **Enable autonomous tests** - Auto-setup required preconditions

## Design

### Architecture: Two-Phase Recording Workflow

#### Phase 1: Natural Recording (Unchanged)
- User starts `/record-test <name>`
- Interacts with app naturally without interruptions
- Video + touch events + screenshots are captured
- User says "stop" to end recording

#### Phase 2: Guided Verification Interview (New)
After recording completes, offer interactive verification:

```
Recording Analysis Complete
══════════════════════════════════════════════════════════
Touch events captured: 97
Video duration: 180s

Would you like to add verifications to make this a real test? (y/n)
```

**If "no":** Generate test.yaml with coordinate taps (current behavior)

**If "yes":** Enter verification interview mode:
1. Detect checkpoints (screen/state changes)
2. Review screenshots at critical moments
3. Add verifications based on user input
4. Generate complete test with assertions

### Checkpoint Detection

Identify 5-10 "critical moments" from all touch events where verification makes sense.

#### Detection Heuristics (Priority Order)

**1. Screen Changes (PRIMARY)**
Compare consecutive screenshots for visual differences:
- Screen title changes
- Major layout shifts
- Different dominant colors/content
- Element hierarchy changes

**2. State Changes Within Screen**
Detect UI state changes without full screen transition:
- Loading spinner appears/disappears
- Content populates (empty → filled)
- Buttons enable/disable
- Modal/dialog appears

**3. Long Waits (Supporting Signal)**
5+ seconds between touches suggests:
- App processing (photo generation, network request)
- User reviewing new content
- Animation/transition completing

**4. Navigation Events (Supporting Signal)**
- Back button taps (top-left: x < 15%, y < 10%)
- Bottom nav taps (y > 85%)
- Predict screen changes

**5. Action Buttons (Supporting Signal)**
Screenshot analysis for action words:
- "Generate", "Save", "Submit", "Apply", "Done"
- Likely triggers state changes

#### Combined Strategy

```
For each touch event:
  1. Did screen change after this? → PRIMARY CHECKPOINT
  2. Did UI state change? → CHECKPOINT
  3. Long wait before next touch? → CANDIDATE
  4. Navigation event? → CANDIDATE
  5. Action button tap? → CANDIDATE

Prioritize where signals align:
  - Tap "Generate" + long wait + screen changed = HIGH
  - Navigation + screen changed = HIGH
  - Long wait alone = LOW
```

#### Example

For 97-touch recording, detect ~6 checkpoints:
- Touch 23: Tap in gallery → Screen shows "Looks" page
- Touch 34: After 10s wait → Photo generation completed
- Touch 38: Top-right tap → Returned to home
- Touch 40: Long press → Edit mode activated
- Touch 62: Back button → Previous screen
- Touch 66: Upper tap → Custom create screen

### Verification Interview UX

#### Multi-Choice Guided Flow

For each checkpoint, show screenshot and offer options:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📸 Checkpoint 1 of 6: After selecting style from gallery
   Touch 23 at 53.6s

[Shows screenshot touch_024.png]

I can see: "Looks" screen with generated photo results

What should we verify here?
  A) Photo generation started successfully (recommended)
  B) Specific style was applied
  C) Nothing - just browsing
  D) Custom verification...

Type A, B, C, D, or describe what to verify:
```

#### Option Design

- **Option A**: AI-recommended verification (screenshot analysis)
- **Option B**: Alternative common verification
- **Option C**: Skip checkpoint (no verification)
- **Option D**: Custom - user describes in natural language

#### AI-Suggested Verifications

Based on screenshot analysis:

**Loading/progress visible:**
```
A) Wait for loading to complete (recommended)
B) Verify progress indicator visible
```

**New content appeared:**
```
A) Verify content loaded successfully (recommended)
B) Verify specific elements present
```

**Edit/action screen:**
```
A) Verify edit controls available (recommended)
B) Verify photo displayed
```

#### Custom Input Handling

When user provides custom description:

```
User: "Check that Viking photo has Save button enabled"

Claude: Got it! I'll add:
  1. verify_screen: "Generated Viking style photo displayed"
  2. verify_element:
       text: "Save"
       enabled: true

Does this capture what you want? (y/n/edit)
```

#### Sequential vs Batch

**Sequential (recommended):**
- One checkpoint at a time
- Focused, not overwhelming
- User can say "approve all remaining with defaults" to speed up

### Test Assembly

#### YAML Structure with Verifications

```yaml
tests:
  - name: regular-flow (recorded)
    description: Complete flow with verifications
    steps:
      # Actions before checkpoint 1
      - tap: ["69%", "48%"]
      - tap: ["73%", "51%"]
      # ... (touches 1-22)

      # Checkpoint 1: Style selected
      - tap: ["58%", "48%"]
      - wait_for: "Looks"
      - verify_screen: "Photo generation started"

      # Actions before checkpoint 2
      - tap: ["26%", "64%"]
      # ... (touches 24-29)

      # Checkpoint 2: Generation complete
      - wait: 10s
      - tap: ["90%", "61%"]
      - wait_for: "Edit Photo"
      - verify_element:
          text: "Save"
          enabled: true
```

#### Insertion Rules

1. **After action that triggered change**
   ```yaml
   - tap: "Generate"
   - wait_for: "Generating your photo"
   ```

2. **After waits (async operations)**
   ```yaml
   - wait: 10s
   - verify_screen: "Photo generated"
   ```

3. **Before next action (sanity check)**
   ```yaml
   - verify_element: "Edit Photo"
   - tap: "Edit Photo"
   ```

#### Verification Types by Context

**"Photo generation started"** →
```yaml
- wait_for: "Generating your photo"
- verify_screen: "Progress indicator visible"
```

**"Photo saved"** →
```yaml
- wait_for: "Saved"
- verify_no_element: "Save"
```

**"Edit controls available"** →
```yaml
- verify_contains: ["Enhance", "Beautify", "Low-light fix"]
- verify_element:
    text: "Before"
    visible: true
```

**"Returned to home"** →
```yaml
- wait_for: "PhotoBoost"
- verify_element: "Home"
- verify_screen: "Navigation tabs visible"
```

### Preconditions

#### Smart Preconditions with Auto-Setup

Instead of just checking and skipping, **try to achieve required state**.

#### Format

```yaml
preconditions:
  # Simple (auto-setup enabled)
  - user_state: premium

  # Explicit with custom setup
  - require: user_logged_in
    value: true
    setup:
      - tap: "Login"
      - type: "{{test_accounts.premium.email}}"
      - type: "{{test_accounts.premium.password}}"
      - tap: "Sign In"
      - wait_for: "Home"
    on_failure: skip
```

#### Built-in Smart Preconditions

**User Authentication:**
```yaml
- user_logged_in: true

# Auto-setup:
# 1. Check if logged in
# 2. If not → Find "Login" button
# 3. Use credentials from config
# 4. Verify login succeeded
```

**User State:**
```yaml
- user_state: premium

# Auto-setup:
# 1. Check current state
# 2. If free → Navigate to settings
# 3. Enable test premium mode
# 4. Verify premium active
```

**Gallery Content:**
```yaml
- min_photos: 5

# Auto-setup:
# 1. Check gallery count
# 2. If < 5 → Import test photos
# 3. Verify imported
```

**Onboarding:**
```yaml
- onboarding_completed: true

# Auto-setup:
# 1. Check if onboarding active
# 2. If yes → Tap through all screens
# 3. Verify home reached
```

#### Config-Level Credentials

```yaml
config:
  app: tap.photo.boost.restoration

  test_accounts:
    premium:
      email: "premium@test.com"
      password: "test123"
    free:
      email: "free@test.com"
      password: "test123"

  test_data:
    photos: "tests/fixtures/sample-photos/"
```

#### Execution Flow

```
Starting test: premium-unlimited-generation

Checking preconditions...

1. user_logged_in: true
   ✗ Not met
   → Running setup actions...
   → Logging in with test account
   ✓ Setup succeeded

2. user_state: premium
   ✗ Not met (current: free)
   → Running setup actions...
   → Enabling premium test mode
   ✓ Setup succeeded

3. min_photos: 3
   ✓ Already met

All preconditions met. Running test...
```

**If setup fails:**
```
1. user_state: premium
   ✗ Not met
   → Running setup actions...
   ✗ Setup failed

Test SKIPPED: Could not achieve required state
```

#### Fallback Strategies

```yaml
- user_state: premium
  on_failure: skip    # Don't run if can't achieve

- network: connected
  on_failure: fail    # Critical, fail the test

- device_storage: 100MB
  on_failure: warn    # Log warning, continue
```

### Conditional Logic (If/Else)

Handle runtime variations within tests.

#### Syntax

```yaml
steps:
  - tap: "Generate"

  # Simple if/else
  - if_exists: "Upgrade to Premium"
    then:
      - tap: "Maybe Later"
    else:
      - tap: "Continue"

  # Multiple conditions
  - if_all_exist: ["Save", "Share", "Edit"]
    then:
      - verify_screen: "Full editing options"
    else:
      - verify_screen: "Limited mode"

  # Check absence
  - if_not_exists: "Loading"
    then:
      - verify_screen: "Content loaded"
    else:
      - wait: 5s

  # Nested
  - if_exists: "Premium Feature"
    then:
      - tap: "Premium Feature"
      - if_exists: "Confirm Purchase"
        then:
          - tap: "Cancel"
```

#### Conditional Operators

```yaml
- if_exists: "Element"           # Present
- if_not_exists: "Element"       # Absent
- if_all_exist: ["A", "B"]       # All present (AND)
- if_any_exist: ["A", "B"]       # Any present (OR)
- if_screen: "Description"       # Screen matches
- if_element_enabled: "Submit"   # Element clickable
```

#### Use Cases

**Optional dialogs:**
```yaml
- if_exists: "Allow Camera"
  then:
    - tap: "Allow"
```

**State-based branching:**
```yaml
- if_exists: "Upgrade to Premium"
  then:
    # Free user path
    - tap: "Watch Ad"
    - wait: 30s
  else:
    # Premium user path
    - verify_screen: "Generating"
```

**Error handling:**
```yaml
- if_exists: "Error"
  then:
    - tap: "Retry"
    - wait: 5s
```

### When to Use What

#### Separate Tests vs Conditionals vs Preconditions

**Use separate tests for:**
- Fundamentally different flows (premium features vs free limitations)
- Different user roles (admin, user, guest)
- Different onboarding paths
- Major A/B test variants

**Use conditionals for:**
- Optional system dialogs (permissions, notifications)
- Dismissible tips
- Minor UI variations
- Flaky elements

**Use preconditions for:**
- Setting up required state
- Ensuring test prerequisites
- Managing test accounts
- Preparing test data

## Implementation

### Components

**1. New Script: `analyze-checkpoints.py`**
```python
# Input: touch_events.json, screenshots/
# Output: checkpoints.json

- Load touch events
- Compare consecutive screenshots
- Detect long waits, navigation patterns
- Score checkpoints
- Return top 6-8 with metadata
```

**2. New Script: `suggest-verification.py`**
```python
# Input: screenshot path
# Output: suggested verification text

- Use Claude API with vision
- Analyze screenshot
- Identify key elements, states
- Suggest verification type
```

**3. New Script: `generate-test.py`**
```python
# Extract YAML generation logic
# Accept verifications parameter
# Insert verifications at checkpoints
# Add section comments
```

**4. Update: `stop-recording` command**

Add Step 8.5 (between frame extraction and YAML generation):

```markdown
### Step 8.5: Verification Interview (Optional)

Ask: "Add verifications? (y/n)"

If yes:
  1. Run analyze-checkpoints.py
  2. For each checkpoint:
     - Show screenshot
     - Run suggest-verification.py
     - Offer multi-choice (AskUserQuestion)
     - Collect response
  3. Store verifications
  4. Ask about preconditions
  5. Pass to Step 9

If no: Continue to Step 9 (current behavior)
```

### File Structure

```
commands/
  stop-recording.md          # Add Step 8.5

scripts/
  analyze-checkpoints.py     # NEW: Checkpoint detection
  suggest-verification.py    # NEW: AI suggestions
  generate-test.py           # NEW: YAML generation

skills/yaml-test-schema/
  references/
    assertions.md            # Exists, no changes
    conditionals.md          # NEW: If/else docs
    preconditions.md         # NEW: Precondition docs
```

### Data Flow

```
User: /stop-recording
  ↓
Load recording data
  ↓
Extract frames
  ↓
Ask: "Add verifications?"
  ↓ [yes]
analyze-checkpoints.py → [6 checkpoints]
  ↓
For each checkpoint:
  suggest-verification.py → suggestion
  AskUserQuestion → user choice
  Store verification
  ↓
Ask: "Add preconditions?"
  AskUserQuestion → user choices
  Store preconditions
  ↓
generate-test.py
  → test.yaml with verifications + preconditions
```

### Graceful Degradation

**If components fail:**
- `analyze-checkpoints.py` fails → Use long-wait detection only
- `suggest-verification.py` fails → Offer generic options
- User skips all → Generate without verifications

This preserves existing workflow.

## Benefits

### For Test Quality
- **Real assertions** instead of blind playback
- **Catches regressions** when behavior changes
- **Self-documenting** - verifications explain expected behavior
- **Reliable** - fails when app actually breaks

### For Developer Experience
- **Guided process** - AI suggests what to verify
- **No interruption** - Record naturally, add verifications after
- **Flexible** - Quick defaults or detailed custom verifications
- **Autonomous** - Tests set up their own preconditions

### For CI/CD
- **Parallelizable** - Each test manages its own state
- **Fresh installs** - Auto-setup handles new environments
- **Clear failures** - Know difference between setup vs test failure
- **Multiple states** - Test premium and free flows easily

## Success Metrics

1. **Tests have assertions** - % of generated tests with verifications
2. **Tests catch bugs** - % of tests that fail when app breaks
3. **Setup success** - % of preconditions auto-setup successfully
4. **User adoption** - % of users who choose verification interview

## Future Enhancements

### Phase 1 (MVP)
- Basic checkpoint detection (screen changes, long waits)
- Simple verification interview
- Manual verification descriptions
- No preconditions yet

### Phase 2
- AI-suggested verifications
- Smart preconditions with auto-setup
- Conditional logic (if/else)

### Phase 3
- Visual regression testing (screenshot comparison)
- Performance assertions (loading time checks)
- Network mocking support
- Test data management

## Open Questions

1. **Checkpoint detection accuracy** - Need to validate visual diff thresholds
2. **AI suggestion quality** - How often are AI suggestions useful?
3. **Setup reliability** - How often do precondition auto-setups succeed?
4. **Interview length** - Is 6-8 checkpoints too many? Should we batch?

## Appendix: Examples

### Complete Test Example

```yaml
config:
  app: tap.photo.boost.restoration

  test_accounts:
    premium:
      email: "premium@test.com"
      password: "test123"

  test_data:
    photos: "tests/fixtures/sample-photos/"

preconditions:
  - require: user_logged_in
    value: true
    setup:
      - tap: "Login"
      - type: "{{test_accounts.premium.email}}"
      - type: "{{test_accounts.premium.password}}"
      - tap: "Sign In"
      - wait_for: "Home"
    on_failure: skip

  - require: user_state
    value: premium
    setup:
      - tap: "Menu"
      - tap: "Settings"
      - tap: "Enable Premium Test Mode"
      - wait_for: "Premium Active"
    on_failure: skip

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: Generate and edit Viking photo
    description: |
      Test complete photo generation and editing flow.
      Works for premium users with conditional handling.

    steps:
      # Navigate to creation
      - tap: "Create New"
      - wait_for: "Style Selection"
      - verify_screen: "Style gallery visible"

      # Select Viking style
      - tap: "Viking"
      - tap: "Generate"

      # Handle optional limit (for free users)
      - if_exists: "Free Tier Limit"
        then:
          - tap: "Watch Ad"
          - wait: 30s
          - tap: "Continue"

      # Verify generation started
      - wait_for: "Generating your photo"
      - verify_screen: "Progress indicator visible"

      # Wait for completion
      - wait_for: "Edit Photo"
      - verify_element:
          text: "Save"
          enabled: true
      - verify_screen: "Generated Viking photo displayed"

      # Open editor
      - tap: "Edit Photo"
      - wait_for: "Before"
      - verify_contains: ["Enhance", "Beautify", "Low-light fix"]

      # Apply enhancement
      - tap: "Enhance"
      - wait: 2s
      - verify_screen: "Enhancement effect applied"

      # Save photo
      - tap: "Save"

      # Handle watermark notice (free users)
      - if_exists: "Watermark Notice"
        then:
          - tap: "OK"

      # Verify saved
      - wait_for: "Saved"
      - verify_screen: "Photo saved to gallery"
```

This test demonstrates:
- Smart preconditions (auto-login, premium setup)
- Verification at checkpoints
- Conditional logic for state variations
- Clear, maintainable structure
