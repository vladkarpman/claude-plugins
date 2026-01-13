# Verification Interview Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform recording workflow from blind coordinate playback into real UI tests with AI-guided verification interview and preconditions.

**Architecture:** Two-phase recording (natural interaction + guided verification interview). AI analyzes screenshots to detect checkpoints, suggests verifications, and helps add preconditions. Users choose from multi-choice options or provide custom verifications. Final YAML includes assertions, conditional logic, and smart auto-setup preconditions.

**Tech Stack:** Python 3 (checkpoint analysis, AI suggestions, YAML generation), Claude API (vision for screenshot analysis), mobile-mcp (device interaction), existing scripts (touch monitoring, frame extraction)

---

## Task 1: Create Checkpoint Detection Script

**Files:**
- Create: `scripts/analyze-checkpoints.py`
- Test: Manual validation with existing recording data

**Step 1: Write checkpoint detection structure**

Create basic structure for analyzing touch events and screenshots:

```python
#!/usr/bin/env python3
"""
Analyze recorded touch events and screenshots to detect verification checkpoints.

Checkpoints are moments where verification makes sense:
- Screen transitions
- UI state changes
- Long waits (processing/loading)
- Navigation events
- Action button taps
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from PIL import Image
import imagehash


@dataclass
class Checkpoint:
    """Represents a verification checkpoint"""
    touch_index: int
    timestamp: float
    screenshot_path: str
    score: float
    reasons: List[str]
    screen_description: str = ""


def load_touch_events(events_file: Path) -> List[Dict[str, Any]]:
    """Load touch events from JSON file"""
    with open(events_file) as f:
        return json.load(f)


def detect_screen_changes(screenshots_dir: Path, touch_events: List[Dict[str, Any]]) -> List[int]:
    """
    Detect screen changes by comparing consecutive screenshots using perceptual hashing.

    Returns list of touch indices where screen changed after the action.
    """
    changes = []
    screenshots = sorted(screenshots_dir.glob("touch_*.png"))

    if len(screenshots) < 2:
        return changes

    prev_hash = None
    for i, screenshot in enumerate(screenshots):
        current_hash = imagehash.average_hash(Image.open(screenshot))

        if prev_hash is not None:
            # Hamming distance > 10 indicates significant visual change
            if current_hash - prev_hash > 10:
                changes.append(i)

        prev_hash = current_hash

    return changes


def detect_long_waits(touch_events: List[Dict[str, Any]], threshold_seconds: float = 5.0) -> List[int]:
    """
    Detect long waits between touches (processing/loading).

    Returns list of touch indices where wait occurred after the action.
    """
    waits = []

    for i in range(len(touch_events) - 1):
        current_time = touch_events[i]["timestamp"]
        next_time = touch_events[i + 1]["timestamp"]
        wait_duration = next_time - current_time

        if wait_duration >= threshold_seconds:
            waits.append(i)

    return waits


def detect_navigation_events(touch_events: List[Dict[str, Any]], screen_width: int, screen_height: int) -> List[int]:
    """
    Detect navigation taps (back button, bottom nav).

    Returns list of touch indices that look like navigation.
    """
    navigation = []

    for i, event in enumerate(touch_events):
        if event["gesture_type"] != "tap":
            continue

        x_percent = (event["x"] / screen_width) * 100
        y_percent = (event["y"] / screen_height) * 100

        # Back button: top-left corner
        if x_percent < 15 and y_percent < 10:
            navigation.append(i)

        # Bottom nav: bottom of screen
        elif y_percent > 85:
            navigation.append(i)

    return navigation


def score_checkpoints(
    touch_events: List[Dict[str, Any]],
    screen_changes: List[int],
    long_waits: List[int],
    navigation: List[int],
    screenshots_dir: Path
) -> List[Checkpoint]:
    """
    Score and rank potential checkpoints based on signal combination.

    Priority:
    1. Screen change (PRIMARY) - 50 points
    2. Long wait (supporting) - 20 points
    3. Navigation event (supporting) - 15 points

    Higher scores = better checkpoint candidates.
    """
    checkpoints = []

    for i in range(len(touch_events)):
        score = 0
        reasons = []

        # Primary signal: screen changed
        if i in screen_changes:
            score += 50
            reasons.append("screen_changed")

        # Supporting: long wait after action
        if i in long_waits:
            score += 20
            reasons.append("long_wait")

        # Supporting: navigation event
        if i in navigation:
            score += 15
            reasons.append("navigation")

        # Only create checkpoint if we have some signal
        if score > 0:
            screenshot_path = screenshots_dir / f"touch_{i+1:03d}.png"

            checkpoint = Checkpoint(
                touch_index=i,
                timestamp=touch_events[i]["timestamp"],
                screenshot_path=str(screenshot_path) if screenshot_path.exists() else "",
                score=score,
                reasons=reasons
            )
            checkpoints.append(checkpoint)

    # Sort by score (highest first)
    checkpoints.sort(key=lambda c: c.score, reverse=True)

    return checkpoints


def select_top_checkpoints(checkpoints: List[Checkpoint], max_count: int = 8) -> List[Checkpoint]:
    """
    Select top N checkpoints, filtering out those too close together.

    Avoid checkpoints within 3 touches of each other.
    """
    selected = []

    for checkpoint in checkpoints:
        # Check if too close to already selected
        too_close = any(
            abs(checkpoint.touch_index - s.touch_index) < 3
            for s in selected
        )

        if not too_close:
            selected.append(checkpoint)

        if len(selected) >= max_count:
            break

    # Sort by touch order for presentation
    selected.sort(key=lambda c: c.touch_index)

    return selected


def main():
    if len(sys.argv) != 2:
        print("Usage: analyze-checkpoints.py <test_folder>")
        print("Example: analyze-checkpoints.py tests/my-test")
        sys.exit(1)

    test_folder = Path(sys.argv[1])

    # Load data
    events_file = test_folder / "touch_events.json"
    screenshots_dir = test_folder / "screenshots"

    if not events_file.exists():
        print(f"Error: {events_file} not found")
        sys.exit(1)

    if not screenshots_dir.exists():
        print(f"Error: {screenshots_dir} not found")
        sys.exit(1)

    touch_events = load_touch_events(events_file)

    # Assume standard screen dimensions (can be extracted from device in future)
    screen_width = 1080
    screen_height = 2400

    # Detect signals
    print("Detecting verification checkpoints...", file=sys.stderr)
    screen_changes = detect_screen_changes(screenshots_dir, touch_events)
    long_waits = detect_long_waits(touch_events)
    navigation = detect_navigation_events(touch_events, screen_width, screen_height)

    # Score and select
    all_checkpoints = score_checkpoints(touch_events, screen_changes, long_waits, navigation, screenshots_dir)
    selected = select_top_checkpoints(all_checkpoints, max_count=8)

    print(f"Found {len(selected)} checkpoints from {len(touch_events)} touches", file=sys.stderr)

    # Output as JSON
    output = {
        "checkpoints": [asdict(c) for c in selected],
        "total_touches": len(touch_events),
        "total_duration": touch_events[-1]["timestamp"] if touch_events else 0
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
```

**Step 2: Test with existing recording**

Run: `python3 scripts/analyze-checkpoints.py tests/example-test`
Expected: JSON output with 6-8 checkpoints with scores and reasons

**Step 3: Commit**

```bash
git add scripts/analyze-checkpoints.py
git commit -m "feat: add checkpoint detection for verification interview"
```

---

## Task 2: Create AI Verification Suggestion Script

**Files:**
- Create: `scripts/suggest-verification.py`
- Test: Manual validation with sample screenshots

**Step 1: Write AI suggestion script**

Create script that uses Claude API to analyze screenshots and suggest verifications:

```python
#!/usr/bin/env python3
"""
Use Claude API with vision to analyze screenshot and suggest verification.

Outputs structured verification suggestion with options.
"""

import json
import sys
import base64
from pathlib import Path
from anthropic import Anthropic


def encode_image(image_path: Path) -> str:
    """Encode image as base64 for API"""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def analyze_screenshot(client: Anthropic, image_path: Path) -> dict:
    """
    Analyze screenshot and suggest verification.

    Returns dict with:
    - screen_description: What's visible
    - suggested_verification: Recommended check
    - alternatives: Other possible checks
    """

    image_data = encode_image(image_path)

    prompt = """Analyze this mobile app screenshot and suggest what to verify in a UI test.

Focus on:
1. What screen/state is shown?
2. What just happened or is happening? (loading, content appeared, etc.)
3. What's the most important thing to verify here?

Provide response as JSON:
{
  "screen_description": "Brief description of what's visible (1 sentence)",
  "suggested_verification": "Recommended verification (e.g., 'Photo generation started', 'Edit controls available')",
  "alternatives": [
    "Alternative verification option 1",
    "Alternative verification option 2"
  ]
}

Focus on meaningful state changes, not just element presence."""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    # Extract JSON from response
    content = response.content[0].text

    # Find JSON in response (may be wrapped in markdown)
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()
    else:
        json_str = content.strip()

    return json.loads(json_str)


def main():
    if len(sys.argv) != 2:
        print("Usage: suggest-verification.py <screenshot_path>")
        print("Example: suggest-verification.py tests/my-test/screenshots/touch_023.png")
        sys.exit(1)

    screenshot_path = Path(sys.argv[1])

    if not screenshot_path.exists():
        print(f"Error: {screenshot_path} not found")
        sys.exit(1)

    # Initialize API client
    client = Anthropic()

    print(f"Analyzing {screenshot_path.name}...", file=sys.stderr)

    try:
        result = analyze_screenshot(client, screenshot_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error analyzing screenshot: {e}", file=sys.stderr)
        # Fallback: provide generic suggestion
        fallback = {
            "screen_description": "Unable to analyze screenshot",
            "suggested_verification": "Verify screen loaded successfully",
            "alternatives": [
                "Verify expected elements present",
                "Skip verification"
            ]
        }
        print(json.dumps(fallback, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Test with sample screenshot**

Run: `python3 scripts/suggest-verification.py tests/example-test/screenshots/touch_001.png`
Expected: JSON with screen description and verification suggestions

**Step 3: Commit**

```bash
git add scripts/suggest-verification.py
git commit -m "feat: add AI-powered verification suggestion"
```

---

## Task 3: Extract YAML Generation Logic

**Files:**
- Create: `scripts/generate-test.py`
- Modify: `commands/stop-recording.md` (extract inline YAML generation to script)
- Test: Compare output with current stop-recording behavior

**Step 1: Write test YAML generation script**

Create standalone script that generates YAML with optional verifications:

```python
#!/usr/bin/env python3
"""
Generate test.yaml from touch events with optional verifications.

Supports:
- Basic coordinate-based playback
- Verification insertion at checkpoints
- Preconditions
- Conditional logic
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Verification:
    """Represents a verification to insert at a checkpoint"""
    touch_index: int
    verification_type: str  # "screen", "element", "wait_for"
    description: str
    details: Optional[Dict[str, Any]] = None


def load_touch_events(events_file: Path) -> List[Dict[str, Any]]:
    """Load touch events from JSON"""
    with open(events_file) as f:
        return json.load(f)


def load_verifications(verifications_file: Path) -> List[Verification]:
    """Load user-selected verifications"""
    if not verifications_file.exists():
        return []

    with open(verifications_file) as f:
        data = json.load(f)

    verifications = []
    for v in data.get("verifications", []):
        verifications.append(Verification(
            touch_index=v["touch_index"],
            verification_type=v["type"],
            description=v["description"],
            details=v.get("details")
        ))

    return verifications


def format_touch_action(event: Dict[str, Any], screen_width: int, screen_height: int) -> str:
    """Format touch event as YAML action"""
    gesture_type = event.get("gesture_type", "tap")

    # Convert to percentage coordinates
    x_percent = f"{(event['x'] / screen_width) * 100:.1f}%"
    y_percent = f"{(event['y'] / screen_height) * 100:.1f}%"

    if gesture_type == "tap":
        return f'      - tap: [{x_percent}, {y_percent}]'
    elif gesture_type == "long_press":
        duration = event.get("duration", 1.0)
        return f'      - long_press: [{x_percent}, {y_percent}, {duration}s]'
    elif gesture_type == "swipe":
        direction = event.get("direction", "up")
        return f'      - swipe: {direction}'
    else:
        return f'      - tap: [{x_percent}, {y_percent}]  # {gesture_type}'


def format_verification(verification: Verification) -> List[str]:
    """Format verification as YAML lines"""
    lines = []

    if verification.verification_type == "wait_for":
        lines.append(f'      - wait_for: "{verification.description}"')

    elif verification.verification_type == "screen":
        lines.append(f'      - verify_screen: "{verification.description}"')

    elif verification.verification_type == "element":
        lines.append(f'      - verify_element:')
        if verification.details:
            for key, value in verification.details.items():
                if isinstance(value, str):
                    lines.append(f'          {key}: "{value}"')
                else:
                    lines.append(f'          {key}: {value}')

    elif verification.verification_type == "custom":
        # User provided custom YAML
        for line in verification.description.split('\n'):
            lines.append(f'      {line}')

    return lines


def generate_yaml(
    app_package: str,
    touch_events: List[Dict[str, Any]],
    verifications: List[Verification],
    screen_width: int = 1080,
    screen_height: int = 2400,
    test_name: str = "recorded-flow"
) -> str:
    """Generate complete test.yaml with verifications"""

    # Sort verifications by touch index
    verifications.sort(key=lambda v: v.touch_index)
    verification_map = {v.touch_index: v for v in verifications}

    lines = []

    # Header
    lines.append("config:")
    lines.append(f"  app: {app_package}")
    lines.append("")
    lines.append("setup:")
    lines.append("  - terminate_app")
    lines.append("  - launch_app")
    lines.append("  - wait: 3s")
    lines.append("")
    lines.append("teardown:")
    lines.append("  - terminate_app")
    lines.append("")
    lines.append("tests:")
    lines.append(f"  - name: {test_name}")
    lines.append("    steps:")

    # Process touch events
    for i, event in enumerate(touch_events):
        # Add touch action
        action = format_touch_action(event, screen_width, screen_height)
        lines.append(action)

        # Add verification if exists for this touch
        if i in verification_map:
            verification = verification_map[i]
            lines.append("")
            lines.append(f"      # Checkpoint {i+1}: {verification.description}")
            verification_lines = format_verification(verification)
            lines.extend(verification_lines)
            lines.append("")

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: generate-test.py <test_folder> <app_package> [test_name]")
        print("Example: generate-test.py tests/my-test com.example.app my-test")
        sys.exit(1)

    test_folder = Path(sys.argv[1])
    app_package = sys.argv[2]
    test_name = sys.argv[3] if len(sys.argv) > 3 else "recorded-flow"

    # Load data
    events_file = test_folder / "touch_events.json"
    verifications_file = test_folder / "verifications.json"

    if not events_file.exists():
        print(f"Error: {events_file} not found")
        sys.exit(1)

    touch_events = load_touch_events(events_file)
    verifications = load_verifications(verifications_file)

    print(f"Generating test.yaml with {len(verifications)} verifications...", file=sys.stderr)

    # Generate YAML
    yaml_content = generate_yaml(
        app_package=app_package,
        touch_events=touch_events,
        verifications=verifications,
        test_name=test_name
    )

    # Write to file
    output_file = test_folder / "test.yaml"
    with open(output_file, 'w') as f:
        f.write(yaml_content)

    print(f"Generated {output_file}", file=sys.stderr)
    print(yaml_content)


if __name__ == "__main__":
    main()
```

**Step 2: Test YAML generation**

Run: `python3 scripts/generate-test.py tests/example-test com.example.app`
Expected: test.yaml file created with touch actions

**Step 3: Commit**

```bash
git add scripts/generate-test.py
git commit -m "feat: extract YAML generation into standalone script"
```

---

## Task 4: Add Verification Interview to stop-recording Command

**Files:**
- Modify: `commands/stop-recording.md`
- Test: Run through verification interview flow

**Step 1: Read current stop-recording command**

```bash
# Read to understand current structure
```

**Step 2: Add Step 8.5 for verification interview**

Insert between frame extraction and YAML generation:

```markdown
### Step 8.5: Verification Interview (Optional)

Ask user if they want to add verifications to make this a real test.

If user declines, skip to Step 9 with empty verifications.

If user accepts:

1. **Run checkpoint detection:**
   ```bash
   python3 scripts/analyze-checkpoints.py "$test_folder" > "$test_folder/checkpoints.json"
   ```

2. **Load checkpoints and iterate:**
   - Parse checkpoints.json
   - For each checkpoint (up to 8):
     - Display checkpoint info (number, timestamp, touch index)
     - Show screenshot using Read tool
     - Run AI suggestion: `python3 scripts/suggest-verification.py "$screenshot_path"`
     - Parse AI suggestion JSON
     - Use AskUserQuestion with multi-choice:
       - Option A: AI suggested verification (recommended)
       - Option B: Alternative verification
       - Option C: Skip this checkpoint
       - Option D: Custom verification (user describes)
     - If user provides custom description, confirm interpretation
     - Store selected verification in verifications list

3. **Save verifications:**
   ```bash
   echo "$verifications_json" > "$test_folder/verifications.json"
   ```

4. **Ask about preconditions (future phase):**
   - For MVP, skip this
   - Add placeholder: "Preconditions support coming in Phase 2"

5. **Continue to Step 9 with verifications**
```

**Step 3: Update Step 9 to use generate-test.py**

Replace inline YAML generation with script call:

```markdown
### Step 9: Generate test.yaml

Use the new generation script:

```bash
python3 scripts/generate-test.py "$test_folder" "$app_package" "$test_name"
```

This script:
- Loads touch events
- Loads verifications (if any)
- Generates test.yaml with verifications inserted at checkpoints
```

**Step 4: Test the flow**

Run: `/stop-recording` after an active recording
Expected: Verification interview runs, shows checkpoints, generates test.yaml

**Step 5: Commit**

```bash
git add commands/stop-recording.md
git commit -m "feat: add verification interview to stop-recording workflow"
```

---

## Task 5: Add Conditional Logic Documentation

**Files:**
- Create: `skills/yaml-test-schema/references/conditionals.md`
- Test: Reference docs are readable and complete

**Step 1: Write conditional logic reference**

Create comprehensive documentation for if/else syntax:

```markdown
# Conditional Logic Reference

Enable tests to handle runtime variations (optional dialogs, state differences, flaky elements).

## Syntax

### Basic If/Else

```yaml
steps:
  - tap: "Generate"

  # Handle optional upgrade prompt
  - if_exists: "Upgrade to Premium"
    then:
      - tap: "Maybe Later"
    else:
      - tap: "Continue"
```

### Multiple Conditions

```yaml
# All must exist (AND)
- if_all_exist: ["Save", "Share", "Edit"]
  then:
    - verify_screen: "Full editing options"
  else:
    - verify_screen: "Limited mode"

# Any can exist (OR)
- if_any_exist: ["Login", "Sign In", "Get Started"]
  then:
    - tap: "Login"
```

### Check Absence

```yaml
# Element not present
- if_not_exists: "Loading"
  then:
    - verify_screen: "Content loaded"
  else:
    - wait: 5s
```

### Nested Conditionals

```yaml
- if_exists: "Premium Feature"
  then:
    - tap: "Premium Feature"
    - if_exists: "Confirm Purchase"
      then:
        - tap: "Cancel"
      else:
        - verify_screen: "Feature activated"
```

## Conditional Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `if_exists` | Element present | `if_exists: "Button"` |
| `if_not_exists` | Element absent | `if_not_exists: "Error"` |
| `if_all_exist` | All present (AND) | `if_all_exist: ["A", "B"]` |
| `if_any_exist` | Any present (OR) | `if_any_exist: ["X", "Y"]` |
| `if_screen` | Screen matches description | `if_screen: "Login page"` |
| `if_element_enabled` | Element clickable | `if_element_enabled: "Submit"` |

## Use Cases

### Optional System Dialogs

```yaml
# Camera permission
- if_exists: "Allow Camera"
  then:
    - tap: "Allow"

# Notification request
- if_exists: "Enable Notifications"
  then:
    - tap: "Not Now"
```

### State-Based Branching

```yaml
# Free vs premium user paths
- tap: "Generate Photo"

- if_exists: "Watch Ad to Continue"
  then:
    # Free user: watch ad
    - tap: "Watch Ad"
    - wait: 30s
    - tap: "Continue"
  else:
    # Premium user: direct access
    - verify_screen: "Generating"
```

### Error Handling

```yaml
# Retry on error
- if_exists: "Network Error"
  then:
    - tap: "Retry"
    - wait: 3s
  else:
    - verify_screen: "Content loaded"
```

### Onboarding Screens

```yaml
# Skip if already completed
- if_exists: "Welcome"
  then:
    - tap: "Next"
    - tap: "Next"
    - tap: "Get Started"
  else:
    - verify_screen: "Home"
```

## Best Practices

### Do: Use for Optional Elements

```yaml
# Good: Handle optional prompt
- if_exists: "Rate This App"
  then:
    - tap: "Maybe Later"
```

### Do: Branch on User State

```yaml
# Good: Different paths for different states
- if_exists: "Premium Badge"
  then:
    - verify_screen: "Premium features visible"
  else:
    - verify_screen: "Free tier limitations"
```

### Don't: Use for Core Flow

```yaml
# Bad: Core elements should always be present
- if_exists: "Submit Button"
  then:
    - tap: "Submit"
  else:
    - tap: [50%, 80%]  # Fragile fallback
```

Instead, use `verify_element` to ensure it exists:

```yaml
# Good: Fail if core element missing
- verify_element: "Submit Button"
- tap: "Submit"
```

### Don't: Overcomplicate

```yaml
# Bad: Too many nested conditions
- if_exists: "A"
  then:
    - if_exists: "B"
      then:
        - if_exists: "C"
          then:
            - tap: "D"
```

Instead, use multiple simple conditions:

```yaml
# Good: Clear sequential checks
- if_exists: "A"
  then:
    - tap: "A"

- if_exists: "B"
  then:
    - tap: "B"
```

## When to Use Conditionals vs Separate Tests

### Use Conditionals For:
- Optional system dialogs
- Dismissible tips/onboarding
- Minor UI variations
- Flaky elements

### Use Separate Tests For:
- Fundamentally different flows (premium vs free features)
- Different user roles (admin vs user)
- Major A/B test variants
- Different feature paths

## Implementation Notes

Conditionals are evaluated at runtime by checking element presence on current screen. Element lookup uses same logic as `verify_element` and `tap`.

Timeout: 5 seconds (configurable in future)

If condition evaluation fails (timeout), treats as `false` and executes `else` branch if present.
```

**Step 2: Commit**

```bash
git add skills/yaml-test-schema/references/conditionals.md
git commit -m "docs: add conditional logic reference for YAML tests"
```

---

## Task 6: Add Preconditions Documentation

**Files:**
- Create: `skills/yaml-test-schema/references/preconditions.md`
- Test: Reference docs are complete

**Step 1: Write preconditions reference**

Create documentation for smart preconditions with auto-setup:

```markdown
# Preconditions Reference

Define required state before test execution with automatic setup attempts.

## Philosophy

Tests should be **autonomous** - able to set up their own prerequisites rather than relying on manual preparation or external scripts.

**Traditional approach (fragile):**
```yaml
# Assumes: User already logged in, premium account, 5+ photos
tests:
  - name: Edit photo
    steps:
      - tap: "Gallery"
      # Breaks if prerequisites not met
```

**Precondition approach (autonomous):**
```yaml
preconditions:
  - user_logged_in: true
  - user_state: premium
  - min_photos: 5

tests:
  - name: Edit photo
    steps:
      - tap: "Gallery"
      # Runs reliably - preconditions auto-setup
```

## Basic Syntax

### Simple Preconditions

```yaml
preconditions:
  # Login required
  - user_logged_in: true

  # Premium account
  - user_state: premium

  # Minimum photos
  - min_photos: 5

  # Onboarding completed
  - onboarding_completed: true
```

### Explicit Preconditions with Custom Setup

```yaml
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
```

## Built-in Smart Preconditions

### User Authentication

```yaml
- user_logged_in: true

# Auto-setup:
# 1. Check if user logged in (look for logout/account buttons)
# 2. If not → Find "Login" button
# 3. Use credentials from config.test_accounts
# 4. Fill email, password, submit
# 5. Verify login succeeded (wait for home screen)
```

### User State (Premium/Free)

```yaml
- user_state: premium

# Auto-setup:
# 1. Check current state (look for premium badge/indicators)
# 2. If free → Navigate to settings
# 3. Find test/debug mode toggle
# 4. Enable premium test mode
# 5. Verify premium active
```

### Gallery Content

```yaml
- min_photos: 5

# Auto-setup:
# 1. Check gallery photo count
# 2. If insufficient → Import test photos
# 3. Use photos from config.test_data.photos
# 4. Verify imported successfully
```

### Onboarding

```yaml
- onboarding_completed: true

# Auto-setup:
# 1. Check if onboarding active
# 2. If yes → Detect onboarding pattern
# 3. Tap through all screens (Next, Skip, etc.)
# 4. Verify home screen reached
```

### Network State

```yaml
- network: connected

# Auto-setup:
# 1. Check network connectivity
# 2. If disconnected → Enable wifi/data
# 3. Verify connection established
```

### Device Storage

```yaml
- device_storage: 100MB

# Auto-setup:
# 1. Check available storage
# 2. If insufficient → Clear cache/temp files
# 3. Verify space available
```

## Configuration

### Test Accounts

```yaml
config:
  app: com.example.app

  test_accounts:
    premium:
      email: "premium@test.example.com"
      password: "test123secure"

    free:
      email: "free@test.example.com"
      password: "test123secure"

    admin:
      email: "admin@test.example.com"
      password: "admin123secure"
```

### Test Data

```yaml
config:
  test_data:
    photos: "tests/fixtures/sample-photos/"
    videos: "tests/fixtures/sample-videos/"
    documents: "tests/fixtures/documents/"
```

### Environment Variables

```yaml
config:
  env:
    API_URL: "{{env.TEST_API_URL}}"
    DEBUG_MODE: true
```

## Failure Handling

### on_failure Options

```yaml
# Skip test if setup fails (default)
- user_logged_in: true
  on_failure: skip

# Fail test if setup fails (critical)
- network: connected
  on_failure: fail

# Warn but continue (non-critical)
- device_storage: 100MB
  on_failure: warn
```

### Failure Example

```
Starting test: premium-feature-test

Checking preconditions...

1. user_logged_in: true
   ✗ Not met
   → Running setup actions...
   → Looking for Login button...
   ✗ Setup failed: Login button not found

Test SKIPPED: Could not achieve required state (user_logged_in)
```

## Execution Flow

```
┌─────────────────────────────┐
│ Start Test Execution        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Check Preconditions         │
│ (one by one, in order)      │
└──────────┬──────────────────┘
           │
           ▼
     ┌─────────┐
     │ Met?    │
     └────┬────┘
          │
    ┌─────┴─────┐
    │           │
    NO         YES
    │           │
    ▼           ▼
┌────────┐  ┌────────┐
│ Run    │  │ Skip   │
│ Setup  │  │ Setup  │
└────┬───┘  └────┬───┘
     │           │
     ▼           │
┌──────────┐     │
│ Success? │     │
└────┬─────┘     │
     │           │
 ┌───┴───┐       │
 │       │       │
YES     NO       │
 │       │       │
 │       ▼       │
 │   ┌─────────┐│
 │   │on_failure│
 │   └────┬────┘│
 │        │     │
 │    ┌───┴──┐  │
 │    │      │  │
 │   skip  fail │
 │    │      │  │
 │    ▼      ▼  │
 │  ┌──────────┐│
 │  │Exit Test ││
 │  └──────────┘│
 │              │
 └──────┬───────┘
        │
        ▼
┌─────────────────────────────┐
│ All preconditions met       │
│ Run test steps...           │
└─────────────────────────────┘
```

## Advanced Examples

### Multiple Account Types

```yaml
config:
  test_accounts:
    premium:
      email: "premium@test.example.com"
      password: "test123"
    free:
      email: "free@test.example.com"
      password: "test123"

tests:
  # Test 1: Premium flow
  - name: premium-unlimited-generation
    preconditions:
      - user_logged_in: true
        account: premium
      - user_state: premium
    steps:
      - tap: "Generate"
      # No ads, no limits

  # Test 2: Free flow
  - name: free-with-ads
    preconditions:
      - user_logged_in: true
        account: free
      - user_state: free
    steps:
      - tap: "Generate"
      - if_exists: "Watch Ad"
        then:
          - tap: "Watch Ad"
```

### Conditional Preconditions

```yaml
preconditions:
  # Only require premium for premium tests
  - require: user_state
    value: premium
    when:
      test_tag: premium_feature
    on_failure: skip
```

### Data Preparation

```yaml
preconditions:
  # Ensure clean slate
  - gallery_empty: true
    setup:
      - tap: "Settings"
      - tap: "Clear Gallery"
      - tap: "Confirm"
      - wait_for: "Gallery Empty"

  # Import specific photos
  - photos_imported: ["portrait.jpg", "landscape.jpg"]
    from: "tests/fixtures/"
```

## Best Practices

### Do: Use for State Management

```yaml
# Good: Test sets up what it needs
preconditions:
  - user_state: premium
  - onboarding_completed: true
```

### Do: Fail Fast on Critical Requirements

```yaml
# Good: Network required for test to be meaningful
preconditions:
  - network: connected
    on_failure: fail
```

### Don't: Over-specify

```yaml
# Bad: Too specific, brittle
preconditions:
  - exact_photo_count: 7
  - screen_brightness: 50%
  - battery_level: 80%
```

```yaml
# Good: Specify minimum requirements
preconditions:
  - min_photos: 5
```

### Don't: Duplicate Setup

```yaml
# Bad: Manual setup AND precondition
preconditions:
  - user_logged_in: true

setup:
  - tap: "Login"  # Redundant!
  - type: "email"
  - tap: "Submit"
```

```yaml
# Good: Let precondition handle it
preconditions:
  - user_logged_in: true

setup:
  - terminate_app
  - launch_app
```

## Implementation Status

**Phase 1 (MVP):** Not yet implemented - Manual test.yaml creation only

**Phase 2 (Planned):**
- Built-in smart preconditions
- Auto-setup with credential support
- Failure handling strategies

**Phase 3 (Future):**
- Custom precondition plugins
- Data provisioning helpers
- Network mocking support
```

**Step 2: Commit**

```bash
git add skills/yaml-test-schema/references/preconditions.md
git commit -m "docs: add preconditions reference with auto-setup design"
```

---

## Task 7: Update YAML Test Schema Skill

**Files:**
- Modify: `skills/yaml-test-schema/SKILL.md`
- Test: Verify skill references new documentation

**Step 1: Read current skill**

```bash
# Read to understand structure
```

**Step 2: Add references to new documentation**

Update the skill to reference conditionals and preconditions:

```markdown
## Advanced Features

### Conditional Logic

Handle runtime variations within tests (optional dialogs, state differences).

See: `references/conditionals.md` for complete syntax and examples.

Basic example:
```yaml
- if_exists: "Upgrade Prompt"
  then:
    - tap: "Maybe Later"
  else:
    - tap: "Continue"
```

### Preconditions (Phase 2)

Define required state with automatic setup.

See: `references/preconditions.md` for design and examples.

Basic example:
```yaml
preconditions:
  - user_logged_in: true
  - user_state: premium
```

**Status:** Documentation complete, implementation planned for Phase 2.
```

**Step 3: Commit**

```bash
git add skills/yaml-test-schema/SKILL.md
git commit -m "docs: update skill with conditional and precondition references"
```

---

## Task 8: Add Python Dependencies

**Files:**
- Create: `scripts/requirements.txt`
- Test: Install dependencies and verify scripts run

**Step 1: Write requirements file**

```txt
anthropic>=0.39.0
Pillow>=10.0.0
imagehash>=4.3.0
```

**Step 2: Test installation**

Run: `pip3 install -r scripts/requirements.txt`
Expected: All packages install successfully

**Step 3: Update CLAUDE.md with dependency info**

Add section about Python dependencies:

```markdown
## Python Dependencies

Scripts require Python 3.8+ and dependencies:

```bash
pip3 install -r scripts/requirements.txt
```

Required packages:
- `anthropic` - Claude API client for AI suggestions
- `Pillow` - Image processing for checkpoint detection
- `imagehash` - Perceptual hashing for screen change detection
```

**Step 4: Commit**

```bash
git add scripts/requirements.txt CLAUDE.md
git commit -m "chore: add Python dependencies for verification interview"
```

---

## Task 9: Add Integration Tests

**Files:**
- Create: `tests/integration/test_verification_interview.sh`
- Test: Run integration test end-to-end

**Step 1: Write integration test script**

```bash
#!/bin/bash
# Integration test for verification interview workflow

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Verification Interview Integration Test ==="

# Test 1: Checkpoint detection
echo ""
echo "Test 1: Checkpoint Detection"
echo "----------------------------"

# Create mock test data
TEST_DIR="$PROJECT_ROOT/tests/mock-recording"
mkdir -p "$TEST_DIR/screenshots"

# Mock touch events
cat > "$TEST_DIR/touch_events.json" << 'EOF'
[
  {"timestamp": 0.0, "x": 500, "y": 1000, "gesture_type": "tap"},
  {"timestamp": 2.5, "x": 600, "y": 800, "gesture_type": "tap"},
  {"timestamp": 15.0, "x": 100, "y": 100, "gesture_type": "tap"},
  {"timestamp": 16.0, "x": 500, "y": 2200, "gesture_type": "tap"}
]
EOF

# Create mock screenshots (would be real in actual recording)
# For test, just create empty images
for i in {1..4}; do
    touch "$TEST_DIR/screenshots/touch_$(printf "%03d" $i).png"
done

echo "✓ Mock test data created"

# Run checkpoint detection
if python3 "$PROJECT_ROOT/scripts/analyze-checkpoints.py" "$TEST_DIR" > "$TEST_DIR/checkpoints.json" 2>/dev/null; then
    echo "✓ Checkpoint detection executed"

    # Verify output format
    if jq -e '.checkpoints | length > 0' "$TEST_DIR/checkpoints.json" > /dev/null 2>&1; then
        echo "✓ Checkpoints detected"
    else
        echo "✗ No checkpoints in output"
        exit 1
    fi
else
    echo "✗ Checkpoint detection failed"
    exit 1
fi

# Test 2: YAML generation
echo ""
echo "Test 2: YAML Generation"
echo "-----------------------"

# Create mock verifications
cat > "$TEST_DIR/verifications.json" << 'EOF'
{
  "verifications": [
    {
      "touch_index": 2,
      "type": "screen",
      "description": "Back button worked"
    }
  ]
}
EOF

# Generate YAML
if python3 "$PROJECT_ROOT/scripts/generate-test.py" "$TEST_DIR" "com.test.app" "mock-test" > /dev/null 2>&1; then
    echo "✓ YAML generation executed"

    # Verify YAML created
    if [ -f "$TEST_DIR/test.yaml" ]; then
        echo "✓ test.yaml created"

        # Verify verification inserted
        if grep -q "verify_screen" "$TEST_DIR/test.yaml"; then
            echo "✓ Verification inserted"
        else
            echo "✗ Verification not found in YAML"
            exit 1
        fi
    else
        echo "✗ test.yaml not created"
        exit 1
    fi
else
    echo "✗ YAML generation failed"
    exit 1
fi

# Cleanup
rm -rf "$TEST_DIR"

echo ""
echo "=== All Tests Passed ==="
```

**Step 2: Make executable and test**

Run: `chmod +x tests/integration/test_verification_interview.sh && tests/integration/test_verification_interview.sh`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/integration/test_verification_interview.sh
git commit -m "test: add integration test for verification interview"
```

---

## Task 10: Update Plugin Documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md` (if exists)
- Test: Documentation is accurate and complete

**Step 1: Update CLAUDE.md architecture section**

Add verification interview to architecture:

```markdown
## Recording Pipeline (Screenrecord-based)

**Requires:** ffmpeg installed (`brew install ffmpeg`)

```
/record-test {name}
    → Check ffmpeg availability
    → Create tests/{name}/ folder structure
    → Start video recording (adb screenrecord) in background
    → Start touch monitor (adb getevent) in background
    → User interacts with app naturally
    → Touch events saved to touch_events.json with timestamps

/stop-recording
    → Stop video and touch capture processes
    → Pull video from device (recording.mp4)
    → Extract frames from video using ffmpeg:
        - For each touch event, extract frame 100ms BEFORE touch
        - This shows UI state at moment of tap decision

    → [NEW] Verification Interview (optional):
        - Analyze checkpoints (screen changes, long waits, navigation)
        - For each checkpoint:
            • Show screenshot to user
            • AI suggests verification
            • User chooses: AI suggestion, alternative, skip, or custom
        - Store verifications.json

    → Generate YAML test file:
        - If verifications exist: Insert at checkpoints
        - If no verifications: Coordinate playback (legacy)
```

**Recording state stored in `.claude/recording-state.json`.**

**Key insight:** Extracting frames 100ms before each touch ensures vision sees
what the user actually tapped, not the changed UI after the tap.

## Verification Interview

Transform recordings into real tests with meaningful assertions.

### Checkpoint Detection

Automatically identifies 6-8 critical moments for verification:
- **Screen changes** (primary signal) - Visual diff using perceptual hashing
- **Long waits** (5+ seconds) - Indicates processing/loading
- **Navigation events** - Back button, bottom nav taps
- **Combined scoring** - Multiple signals = higher priority

### AI-Guided Verification

For each checkpoint:
1. **Screenshot analysis** - Claude vision identifies what's happening
2. **Suggested verifications** - AI recommends what to check
3. **Multi-choice options** - User picks: suggestion, alternative, skip, custom
4. **Verification insertion** - Added to YAML at checkpoint location

### Example Verification Interview

```
Recording Analysis Complete
══════════════════════════════════════════════════════════
Touch events captured: 97
Video duration: 180s

Would you like to add verifications to make this a real test? (y/n)
> y

Detecting checkpoints... Found 6 checkpoints

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📸 Checkpoint 1 of 6: After selecting style
   Touch 23 at 53.6s

[Shows screenshot]

I can see: "Looks" screen with style selection confirmed

What should we verify here?
  A) Photo generation started successfully (recommended)
  B) Specific style was applied
  C) Skip - just browsing
  D) Custom verification...

> A

✓ Added: verify_screen: "Photo generation started"

[Continues for remaining checkpoints...]
```

### Output

Generated `test.yaml` includes:
- Touch actions (coordinate-based)
- Verifications at checkpoints (element/screen checks)
- Section comments for readability
- Standard setup/teardown
```

**Step 2: Add new scripts to architecture section**

```markdown
scripts/
├── analyze-checkpoints.py   # NEW: Detect verification checkpoints
├── suggest-verification.py  # NEW: AI-powered verification suggestions
├── generate-test.py         # NEW: YAML generation with verifications
├── check-ffmpeg.sh         # Verifies ffmpeg is installed
├── record-video.sh         # adb screenrecord wrapper
├── monitor-touches.py      # Captures touch events via adb getevent
└── extract-frames.py       # Extracts frames from video at touch timestamps
```

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update documentation with verification interview features"
```

---

## Summary

This plan implements **Phase 1 (MVP)** of the Verification Interview feature:

**Completed Components:**
1. ✅ Checkpoint detection (screen changes, waits, navigation)
2. ✅ AI-powered verification suggestions
3. ✅ Standalone YAML generation script
4. ✅ Interactive verification interview in stop-recording
5. ✅ Conditional logic documentation
6. ✅ Preconditions documentation (design for Phase 2)
7. ✅ Integration tests
8. ✅ Updated documentation

**Phase 2 Features (Future):**
- Smart preconditions with auto-setup
- Conditional logic implementation in test runner
- Enhanced checkpoint detection (OCR for button text)
- Batch verification approval ("approve all with defaults")

**Success Criteria:**
- Users can add verifications after recording
- AI suggests meaningful checkpoints
- Generated tests include assertions
- Documentation complete for conditionals and preconditions

**Testing Plan:**
1. Run integration test: `tests/integration/test_verification_interview.sh`
2. Manual test: Record real app flow and complete verification interview
3. Verify generated YAML has verifications at appropriate checkpoints
4. Validate documentation is clear and complete
