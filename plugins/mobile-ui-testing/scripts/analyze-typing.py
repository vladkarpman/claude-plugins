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
    events_file = test_folder / "recording" / "touch_events.json"

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
    output_file = test_folder / "recording" / "typing_sequences.json"
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
