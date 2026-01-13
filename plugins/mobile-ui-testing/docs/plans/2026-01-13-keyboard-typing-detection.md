# Keyboard Typing Detection for Recording Pipeline

**Date:** 2026-01-13
**Feature:** Detect keyboard typing during recording and convert to `type` commands
**Status:** Design Complete, Ready for Implementation

---

## Problem Statement

**Current Behavior:**
- Recording captures keyboard taps as individual touch coordinates
- Replaying coordinate-based taps on keyboard fails:
  - Keyboard layout varies by device/locale
  - Keys are too small for reliable coordinate taps
  - Keyboard position may differ between recording and replay

**Example from youtube-search-and-play test:**
- Touches 17-44 (28 taps) = typing "Android development"
- Generated as 28 separate `tap: [x%, y%]` commands
- These will fail when replayed

**Required Solution:**
- Detect keyboard typing sequences during recording
- Ask user what was typed during verification interview
- Generate `type: "text"` commands instead of tap coordinates

---

## Architecture Overview

### Three Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: Recording (/record-test)                          │
│ - Capture touches with enhanced metadata                    │
│ - Mark touches in keyboard regions                          │
│ - No user interaction needed                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: Detection (analyze-typing.py - NEW)               │
│ - Identify typing sequences from touch patterns             │
│ - Group consecutive keyboard taps                           │
│ - Output typing_sequences.json                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: Interview (/stop-recording)                        │
│ - Show detected typing sequences                            │
│ - Ask user: "What did you type here?"                       │
│ - Store text input in verifications.json                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: Generation (generate-test.py)                     │
│ - Replace typing sequences with type commands               │
│ - Generate: type: "user input text"                        │
│ - Insert at correct position in test steps                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Task 1: Typing Sequence Detection Script

**File:** `scripts/analyze-typing.py`

**Input:** `touch_events.json`

**Output:** `typing_sequences.json`

**Algorithm:**

```python
def detect_typing_sequences(touches):
    """
    Detect keyboard typing from touch patterns.

    Heuristics:
    1. Y-coordinate in bottom 40% of screen (keyboard region)
    2. Sequential taps with < 1s between them
    3. Minimum 3 consecutive taps to qualify
    4. X-coordinate variance suggests multiple keys
    """

    sequences = []
    current_sequence = []

    KEYBOARD_Y_THRESHOLD = 0.6  # Bottom 40% of screen
    MAX_TAP_INTERVAL = 1.0  # seconds
    MIN_SEQUENCE_LENGTH = 3  # taps

    for i, touch in enumerate(touches):
        is_keyboard_region = (touch['y'] / touch['screen_height']) > KEYBOARD_Y_THRESHOLD
        is_tap = touch['gesture_type'] == 'tap'

        if is_keyboard_region and is_tap:
            # Check time gap from previous touch
            if current_sequence:
                time_gap = touch['timestamp'] - current_sequence[-1]['timestamp']
                if time_gap > MAX_TAP_INTERVAL:
                    # Sequence break - save if long enough
                    if len(current_sequence) >= MIN_SEQUENCE_LENGTH:
                        sequences.append(create_sequence(current_sequence))
                    current_sequence = []

            current_sequence.append(touch)
        else:
            # Non-keyboard touch - end sequence
            if len(current_sequence) >= MIN_SEQUENCE_LENGTH:
                sequences.append(create_sequence(current_sequence))
            current_sequence = []

    # Handle final sequence
    if len(current_sequence) >= MIN_SEQUENCE_LENGTH:
        sequences.append(create_sequence(current_sequence))

    return sequences


def create_sequence(touches):
    """Create typing sequence metadata"""
    return {
        "start_touch_index": touches[0]['index'] - 1,  # 0-indexed
        "end_touch_index": touches[-1]['index'] - 1,
        "touch_count": len(touches),
        "start_timestamp": touches[0]['timestamp'],
        "end_timestamp": touches[-1]['timestamp'],
        "duration_ms": int((touches[-1]['timestamp'] - touches[0]['timestamp']) * 1000),
        "text": "",  # Filled in by user during interview
        "submit": False  # Whether user pressed enter/search
    }
```

**Output Format (`typing_sequences.json`):**

```json
{
  "sequences": [
    {
      "start_touch_index": 16,
      "end_touch_index": 43,
      "touch_count": 28,
      "start_timestamp": 1768327743.737889,
      "end_timestamp": 1768327754.373908,
      "duration_ms": 10636,
      "text": "",
      "submit": false
    }
  ],
  "total_sequences": 1
}
```

---

### Task 2: Update stop-recording.md Command

**File:** `commands/stop-recording.md`

**Changes:**

**Step 8.4 (NEW): Detect Typing Sequences**

Add after checkpoint detection, before verification interview:

```markdown
**Step 8.4: Detect typing sequences**

Run typing detection script:

```bash
python3 scripts/analyze-typing.py ${TEST_FOLDER}
```

This creates `${TEST_FOLDER}/typing_sequences.json`.

If no sequences detected, skip to Step 8.5.
```

**Step 8.5 (UPDATED): Typing Interview**

Add before checkpoint verification interview:

```markdown
**Step 8.5: Typing interview (if sequences detected)**

If `typing_sequences.json` contains sequences, ask user for each:

**For each typing sequence:**

1. Show context:
   ```
   Detected keyboard typing:
   - Touches: 17-44 (28 taps)
   - Duration: 10.6 seconds
   - Timestamp: 01:42:23 - 01:42:34
   ```

2. Ask: **"What text did you type here?"**

3. Store user input in sequence['text']

4. Ask: **"Did you press Enter/Search after typing? (y/n)"**

5. Store answer in sequence['submit'] (true/false)

6. Update typing_sequences.json with user input

**Example interaction:**

```
Detected keyboard typing (touches 17-44):
What did you type? Android development
Did you press Enter/Search after? y

✓ Saved: "Android development" with submit
```

Save updated typing_sequences.json.
```

**Step 8.6 (RENUMBERED): Verification Interview**

Continue with existing checkpoint verification interview (now step 8.6).

---

### Task 3: Update generate-test.py Script

**File:** `scripts/generate-test.py`

**Changes:**

**Load typing sequences:**

```python
def load_typing_sequences(test_folder: Path) -> List[Dict]:
    """Load typing sequences if available"""
    typing_file = test_folder / "typing_sequences.json"
    if not typing_file.exists():
        return []

    with open(typing_file) as f:
        data = json.load(f)
    return data.get('sequences', [])
```

**Filter touches that are part of typing:**

```python
def is_touch_in_typing_sequence(touch_index: int, sequences: List[Dict]) -> Optional[Dict]:
    """Check if touch is part of a typing sequence"""
    for seq in sequences:
        if seq['start_touch_index'] <= touch_index <= seq['end_touch_index']:
            return seq
    return None
```

**Generate YAML with type commands:**

```python
def generate_yaml(touches, verifications, typing_sequences):
    """Generate YAML test with typing support"""

    # Track which typing sequences we've already added
    added_sequences = set()

    for i, touch in enumerate(touches):
        # Check if this touch is part of a typing sequence
        typing_seq = is_touch_in_typing_sequence(i, typing_sequences)

        if typing_seq:
            seq_id = typing_seq['start_touch_index']

            # Only add type command at start of sequence
            if i == typing_seq['start_touch_index'] and seq_id not in added_sequences:
                # Generate type command
                if typing_seq['submit']:
                    yaml_lines.append(f"      - type: {{text: \"{typing_seq['text']}\", submit: true}}")
                else:
                    yaml_lines.append(f"      - type: \"{typing_seq['text']}\"")

                added_sequences.add(seq_id)

            # Skip individual keyboard taps (they're part of the type command)
            continue

        # Regular touch (not part of typing) - add as tap/swipe
        x_pct = round((touch['x'] / touch['screen_width']) * 100, 1)
        y_pct = round((touch['y'] / touch['screen_height']) * 100, 1)

        if touch['gesture_type'] == 'tap':
            yaml_lines.append(f"      - tap: [{x_pct}%, {y_pct}%]")
        elif touch['gesture_type'] == 'long_press':
            yaml_lines.append(f"      - long_press: [{x_pct}%, {y_pct}%]")
        # ... etc

        # Add verification if exists at this index
        if i in verification_map:
            # ... existing verification logic
```

---

### Task 4: Update run-test.md Command

**File:** `commands/run-test.md`

**Changes:**

Already supports `type` action! Just verify it works with adb:

```python
# In run-test execution logic
elif action_type == 'type':
    if isinstance(action_value, str):
        text = action_value
        submit = False
    else:
        text = action_value.get('text', '')
        submit = action_value.get('submit', False)

    # Type using adb input
    await mobile_type_keys(device, text, submit)
```

**No changes needed** - already implemented!

---

### Task 5: Create analyze-typing.py Script

**File:** `scripts/analyze-typing.py`

**Implementation:**

```python
#!/usr/bin/env python3
"""
Analyze touch events to detect keyboard typing sequences.

Usage: analyze-typing.py <test_folder>

Outputs: typing_sequences.json in test folder
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


# Configuration thresholds
KEYBOARD_Y_THRESHOLD = 0.6  # Bottom 40% of screen (keyboard region)
MAX_TAP_INTERVAL = 1.0  # Maximum seconds between taps in a sequence
MIN_SEQUENCE_LENGTH = 3  # Minimum taps to qualify as typing
MIN_X_VARIANCE = 50  # Minimum X-coordinate variance to confirm multiple keys


def load_touch_events(test_folder: Path) -> List[Dict[str, Any]]:
    """Load touch events from JSON file"""
    events_file = test_folder / "touch_events.json"

    if not events_file.exists():
        print(f"Error: {events_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(events_file) as f:
        events = json.load(f)

    if not isinstance(events, list):
        print("Error: touch_events.json must contain a list", file=sys.stderr)
        sys.exit(1)

    return events


def calculate_x_variance(touches: List[Dict]) -> float:
    """Calculate X-coordinate variance to confirm multiple keys"""
    if len(touches) < 2:
        return 0

    x_coords = [t['x'] for t in touches]
    mean_x = sum(x_coords) / len(x_coords)
    variance = sum((x - mean_x) ** 2 for x in x_coords) / len(x_coords)
    return variance ** 0.5  # Standard deviation


def detect_typing_sequences(touches: List[Dict]) -> List[Dict]:
    """
    Detect keyboard typing sequences from touch patterns.

    Returns list of typing sequence metadata.
    """
    sequences = []
    current_sequence = []

    for i, touch in enumerate(touches):
        # Calculate normalized Y position (0.0 = top, 1.0 = bottom)
        y_normalized = touch['y'] / touch['screen_height']

        # Check if touch is in keyboard region
        is_keyboard_region = y_normalized > KEYBOARD_Y_THRESHOLD
        is_tap = touch.get('gesture_type', touch.get('gesture')) == 'tap'

        if is_keyboard_region and is_tap:
            # Check time gap from previous touch in sequence
            if current_sequence:
                time_gap = touch['timestamp'] - current_sequence[-1]['timestamp']

                if time_gap > MAX_TAP_INTERVAL:
                    # Time gap too large - end current sequence
                    if len(current_sequence) >= MIN_SEQUENCE_LENGTH:
                        # Verify X-coordinate variance (multiple keys)
                        if calculate_x_variance(current_sequence) >= MIN_X_VARIANCE:
                            sequences.append(create_sequence(current_sequence))

                    current_sequence = []

            # Add touch to current sequence
            current_sequence.append(touch)
        else:
            # Non-keyboard touch - end sequence
            if len(current_sequence) >= MIN_SEQUENCE_LENGTH:
                if calculate_x_variance(current_sequence) >= MIN_X_VARIANCE:
                    sequences.append(create_sequence(current_sequence))

            current_sequence = []

    # Handle final sequence
    if len(current_sequence) >= MIN_SEQUENCE_LENGTH:
        if calculate_x_variance(current_sequence) >= MIN_X_VARIANCE:
            sequences.append(create_sequence(current_sequence))

    return sequences


def create_sequence(touches: List[Dict]) -> Dict:
    """Create typing sequence metadata from touch list"""
    return {
        "start_touch_index": touches[0]['index'] - 1,  # Convert to 0-indexed
        "end_touch_index": touches[-1]['index'] - 1,
        "touch_count": len(touches),
        "start_timestamp": touches[0]['timestamp'],
        "end_timestamp": touches[-1]['timestamp'],
        "duration_ms": int((touches[-1]['timestamp'] - touches[0]['timestamp']) * 1000),
        "text": "",  # Filled by user during interview
        "submit": False  # Whether user pressed enter/search
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: analyze-typing.py <test_folder>", file=sys.stderr)
        sys.exit(1)

    test_folder = Path(sys.argv[1])

    if not test_folder.exists():
        print(f"Error: Test folder not found: {test_folder}", file=sys.stderr)
        sys.exit(1)

    # Load touch events
    print("Analyzing touch patterns for keyboard typing...", file=sys.stderr)
    touches = load_touch_events(test_folder)

    # Detect typing sequences
    sequences = detect_typing_sequences(touches)

    # Create output
    output = {
        "sequences": sequences,
        "total_sequences": len(sequences)
    }

    # Save to file
    output_file = test_folder / "typing_sequences.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    # Print summary
    print(f"Found {len(sequences)} typing sequence(s)", file=sys.stderr)
    for i, seq in enumerate(sequences, 1):
        print(f"  Sequence {i}: touches {seq['start_touch_index']+1}-{seq['end_touch_index']+1} ({seq['touch_count']} taps, {seq['duration_ms']}ms)", file=sys.stderr)

    # Output JSON to stdout for piping
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
```

---

## Testing Plan

### Test 1: Detection Accuracy

**Input:** youtube-search-and-play touch_events.json (56 touches)

**Expected Output:**
```json
{
  "sequences": [
    {
      "start_touch_index": 16,
      "end_touch_index": 43,
      "touch_count": 28,
      "duration_ms": 10636,
      "text": "",
      "submit": false
    }
  ],
  "total_sequences": 1
}
```

**Validation:**
- Correctly identifies touches 17-44 as typing
- Single sequence (not fragmented)
- Reasonable duration

### Test 2: Interview Flow

**User performs:**
1. /record-test youtube-search
2. [Interact with YouTube, type in search box]
3. /stop-recording

**Expected:**
- Script detects typing sequence
- Asks: "What did you type?"
- User enters: "Android development"
- Asks: "Did you press Enter/Search?"
- User answers: "y"
- Generates: `type: {text: "Android development", submit: true}`

### Test 3: YAML Generation

**Input:**
- 56 touches
- 1 typing sequence (touches 17-44, text: "Android development", submit: true)
- 3 verifications

**Expected Output:**
```yaml
tests:
  - name: youtube-search
    steps:
      - tap: [64.9%, 37.5%]  # Touch 1
      # ... touches 2-16
      - type: {text: "Android development", submit: true}  # Touches 17-44 replaced
      # ... touches 45-56
      - verify_screen: "Search results loaded"
```

**Validation:**
- Typing sequence replaces 28 individual taps
- Only appears once (not duplicated)
- Correct position in sequence

### Test 4: Test Execution

**Run:** `/run-test tests/youtube-search/`

**Expected:**
- Type command executes via adb input
- Text appears in YouTube search box
- Submit presses enter/search
- Test continues normally

---

## Edge Cases

### Edge Case 1: Multiple Typing Sequences

**Scenario:** User types, navigates, types again

**Example:**
- Sequence 1: Touches 10-25 (search query)
- Sequence 2: Touches 40-50 (video comment)

**Handling:**
- Detect both sequences
- Interview asks for text for each
- Generate two `type` commands at correct positions

### Edge Case 2: Short Sequences (< 3 taps)

**Scenario:** User taps 1-2 keyboard keys

**Handling:**
- Not detected as typing (below MIN_SEQUENCE_LENGTH)
- Treated as regular taps
- Acceptable: 1-2 keys probably not text input

### Edge Case 3: No Keyboard Typing

**Scenario:** Test has no typing (only taps/swipes)

**Handling:**
- analyze-typing.py returns empty sequences
- No interview prompts
- Test generation works as before

### Edge Case 4: User Forgets What They Typed

**Scenario:** User can't remember typed text

**Options:**
1. Allow empty text: `type: ""`
2. Skip sequence: treat as regular taps
3. Show screenshot from typing start

**Recommendation:** Show screenshot + allow empty text

### Edge Case 5: Non-English Keyboard

**Scenario:** User types in Russian/Chinese/etc.

**Handling:**
- Detection works (based on position, not content)
- User enters text in their language
- adb input handles unicode correctly

---

## Implementation Checklist

### Phase 1: Core Detection
- [ ] Create `scripts/analyze-typing.py`
- [ ] Implement sequence detection algorithm
- [ ] Add X-coordinate variance check
- [ ] Test with youtube-search-and-play data
- [ ] Validate output format

### Phase 2: Interview Integration
- [ ] Update `commands/stop-recording.md`
- [ ] Add Step 8.4: Detect typing sequences
- [ ] Add Step 8.5: Typing interview
- [ ] Renumber existing verification interview
- [ ] Test interview flow

### Phase 3: YAML Generation
- [ ] Update `scripts/generate-test.py`
- [ ] Add load_typing_sequences()
- [ ] Add is_touch_in_typing_sequence()
- [ ] Modify generate_yaml() to replace sequences
- [ ] Test YAML output

### Phase 4: End-to-End Testing
- [ ] Record new test with typing
- [ ] Verify detection works
- [ ] Complete typing interview
- [ ] Validate generated YAML
- [ ] Run test and confirm typing executes

### Phase 5: Documentation
- [ ] Update README.md with typing feature
- [ ] Update CLAUDE.md architecture section
- [ ] Add typing examples to templates/
- [ ] Document in yaml-test-schema skill

---

## Success Criteria

✅ **Detection:**
- Correctly identifies 90%+ of keyboard typing sequences
- False positive rate < 10%
- Works with various keyboard layouts/sizes

✅ **Interview:**
- Clear prompts for user
- Supports multiple sequences
- Shows helpful context (timestamp, touch count)

✅ **Generation:**
- Replaces touch sequences with type commands
- Maintains correct action order
- Generates valid YAML syntax

✅ **Execution:**
- Type commands work via adb input
- Text appears correctly in apps
- Submit option works (presses enter)

---

## Future Enhancements

### Enhancement 1: OCR-Based Text Extraction

Instead of asking user, use OCR on keyboard screenshots to detect what was typed.

**Pros:** Fully automated, no user input needed
**Cons:** OCR accuracy, complex implementation

### Enhancement 2: Keyboard Detection

Detect when keyboard appears/disappears using perceptual hashing.

**Use Case:** Auto-detect text input fields

### Enhancement 3: Autocomplete Handling

Detect when user selects autocomplete suggestion vs typing full text.

**Challenge:** How to represent in YAML

---

## Files to Create/Modify

### New Files:
1. `scripts/analyze-typing.py` (NEW)
2. `tests/youtube-search-and-play/typing_sequences.json` (generated)

### Modified Files:
1. `commands/stop-recording.md` (add steps 8.4-8.5)
2. `scripts/generate-test.py` (add typing support)
3. `README.md` (document typing feature)
4. `CLAUDE.md` (update architecture)

### Unchanged Files:
- `commands/run-test.md` (already supports type action)
- `scripts/monitor-touches.py` (no changes needed)
- `scripts/extract-frames.py` (no changes needed)

---

## Timeline Estimate

- **Phase 1 (Detection):** 30 minutes
- **Phase 2 (Interview):** 20 minutes
- **Phase 3 (Generation):** 30 minutes
- **Phase 4 (Testing):** 20 minutes
- **Phase 5 (Documentation):** 15 minutes

**Total:** ~2 hours

---

## Next Steps

1. Create `scripts/analyze-typing.py`
2. Test with youtube-search-and-play data
3. Update stop-recording.md
4. Update generate-test.py
5. End-to-end test with new recording
6. Document feature
7. Commit changes

---

**Ready to implement!** 🚀
