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


@dataclass
class TypingSequence:
    """Represents a detected keyboard typing sequence"""
    start_touch_index: int
    end_touch_index: int
    touch_count: int
    duration_ms: int
    text: str
    submit: bool


def load_touch_events(events_file: Path) -> List[Dict[str, Any]]:
    """Load touch events from JSON"""
    try:
        with open(events_file) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {events_file}: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading {events_file}: {e}", file=sys.stderr)
        sys.exit(1)


def load_verifications(verifications_file: Path) -> List[Verification]:
    """Load user-selected verifications"""
    if not verifications_file.exists():
        return []

    try:
        with open(verifications_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {verifications_file}: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading {verifications_file}: {e}", file=sys.stderr)
        sys.exit(1)

    verifications = []
    # Handle both bare array and wrapped object structures
    verification_list = data if isinstance(data, list) else data.get("verifications", [])
    for v in verification_list:
        verifications.append(Verification(
            touch_index=v["touch_index"],
            verification_type=v["type"],
            description=v["description"],
            details=v.get("details")
        ))

    return verifications


def load_typing_sequences(typing_file: Path) -> List[TypingSequence]:
    """Load detected typing sequences with user input"""
    if not typing_file.exists():
        return []

    try:
        with open(typing_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {typing_file}: {e}", file=sys.stderr)
        return []
    except IOError as e:
        print(f"Error reading {typing_file}: {e}", file=sys.stderr)
        return []

    sequences = []
    sequence_list = data.get("sequences", [])
    for seq in sequence_list:
        # Skip sequences without text (user skipped them)
        if not seq.get("text"):
            continue

        sequences.append(TypingSequence(
            start_touch_index=seq["start_touch_index"],
            end_touch_index=seq["end_touch_index"],
            touch_count=seq["touch_count"],
            duration_ms=seq["duration_ms"],
            text=seq["text"],
            submit=seq.get("submit", False)
        ))

    return sequences


def is_touch_in_typing_sequence(touch_index: int, sequences: List[TypingSequence]) -> Optional[TypingSequence]:
    """Check if a touch is part of a typing sequence"""
    for seq in sequences:
        if seq.start_touch_index <= touch_index <= seq.end_touch_index:
            return seq
    return None


def format_typing_action(sequence: TypingSequence) -> str:
    """Format typing sequence as YAML action"""
    if sequence.submit:
        return f'      - type: {{text: "{sequence.text}", submit: true}}'
    else:
        return f'      - type: "{sequence.text}"'


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
    typing_sequences: List[TypingSequence],
    screen_width: int = 1080,
    screen_height: int = 2400,
    test_name: str = "recorded-flow"
) -> str:
    """Generate complete test.yaml with verifications and typing sequences"""

    # Sort verifications by touch index
    verifications.sort(key=lambda v: v.touch_index)
    verification_map = {v.touch_index: v for v in verifications}

    # Track which typing sequences have been added
    added_sequences = set()

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
        # Check if this touch is part of a typing sequence
        typing_seq = is_touch_in_typing_sequence(i, typing_sequences)

        if typing_seq:
            # Generate unique ID for this sequence
            seq_id = (typing_seq.start_touch_index, typing_seq.end_touch_index)

            if i == typing_seq.start_touch_index and seq_id not in added_sequences:
                # First touch of sequence - add type command
                action = format_typing_action(typing_seq)
                lines.append(action)
                added_sequences.add(seq_id)

                # Add comment about replaced touches
                touch_range = f"{typing_seq.start_touch_index+1}-{typing_seq.end_touch_index+1}"
                lines.append(f"      # Replaced touches {touch_range} ({typing_seq.touch_count} keyboard taps)")
                lines.append("")
            # else: Skip individual keyboard taps within sequence
            continue

        # Add normal touch action
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
    events_file = test_folder / "recording" / "touch_events.json"
    verifications_file = test_folder / "recording" / "verifications.json"
    typing_file = test_folder / "recording" / "typing_sequences.json"

    if not events_file.exists():
        print(f"Error: {events_file} not found")
        sys.exit(1)

    touch_events = load_touch_events(events_file)
    verifications = load_verifications(verifications_file)
    typing_sequences = load_typing_sequences(typing_file)

    print(f"Generating test.yaml with {len(verifications)} verifications and {len(typing_sequences)} typing sequences...", file=sys.stderr)

    # Generate YAML
    yaml_content = generate_yaml(
        app_package=app_package,
        touch_events=touch_events,
        verifications=verifications,
        typing_sequences=typing_sequences,
        test_name=test_name
    )

    # Write to file
    output_file = test_folder / "test.yaml"
    try:
        with open(output_file, 'w') as f:
            f.write(yaml_content)
    except IOError as e:
        print(f"Error writing {output_file}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Generated {output_file}", file=sys.stderr)
    print(yaml_content)


if __name__ == "__main__":
    main()
