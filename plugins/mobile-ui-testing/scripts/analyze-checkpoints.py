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

# Tunable thresholds
SCREEN_CHANGE_THRESHOLD = 10  # Hamming distance for perceptual hash (higher = more different)
LONG_WAIT_THRESHOLD = 5.0  # seconds


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
        data = json.load(f)

    # Validate structure
    if not isinstance(data, list):
        raise ValueError("touch_events.json must contain a list of events")

    for i, event in enumerate(data):
        required_fields = ["timestamp", "gesture_type", "x", "y"]
        for field in required_fields:
            if field not in event:
                raise ValueError(f"Event {i} missing required field: {field}")

    return data


def detect_screen_changes(screenshots_dir: Path, touch_events: List[Dict[str, Any]], Image, imagehash) -> List[int]:
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
        try:
            current_hash = imagehash.average_hash(Image.open(screenshot))
        except Exception as e:
            print(f"Warning: Failed to process {screenshot}: {e}", file=sys.stderr)
            continue

        if prev_hash is not None:
            # Hamming distance > threshold indicates significant visual change
            if current_hash - prev_hash > SCREEN_CHANGE_THRESHOLD:
                changes.append(i)

        prev_hash = current_hash

    return changes


def detect_long_waits(touch_events: List[Dict[str, Any]], threshold_seconds: float = LONG_WAIT_THRESHOLD) -> List[int]:
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


def parse_arguments():
    """Parse command-line arguments"""
    if len(sys.argv) < 2:
        print("Usage: analyze-checkpoints.py <test_folder> [--width WIDTH] [--height HEIGHT]", file=sys.stderr)
        print("Example: analyze-checkpoints.py tests/my-test --width 1080 --height 2400", file=sys.stderr)
        sys.exit(1)

    test_folder = Path(sys.argv[1])
    screen_width = 1080  # default
    screen_height = 2400  # default

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--width" and i + 1 < len(sys.argv):
            try:
                screen_width = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                print(f"Error: Invalid width value: {sys.argv[i + 1]}", file=sys.stderr)
                sys.exit(1)
        elif sys.argv[i] == "--height" and i + 1 < len(sys.argv):
            try:
                screen_height = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                print(f"Error: Invalid height value: {sys.argv[i + 1]}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: Unknown argument: {sys.argv[i]}", file=sys.stderr)
            sys.exit(1)

    return test_folder, screen_width, screen_height


def main():
    # Validate dependencies first
    try:
        from PIL import Image
        import imagehash
    except ImportError as e:
        print(f"Error: Required Python package not found: {e}", file=sys.stderr)
        print("Install with: pip install pillow imagehash", file=sys.stderr)
        sys.exit(1)

    # Parse arguments
    test_folder, screen_width, screen_height = parse_arguments()

    # Load data
    events_file = test_folder / "recording" / "touch_events.json"
    screenshots_dir = test_folder / "recording" / "screenshots"

    if not events_file.exists():
        print(f"Error: {events_file} not found", file=sys.stderr)
        sys.exit(1)

    if not screenshots_dir.exists():
        print(f"Error: {screenshots_dir} not found", file=sys.stderr)
        sys.exit(1)

    touch_events = load_touch_events(events_file)

    # Detect signals
    print("Detecting verification checkpoints...", file=sys.stderr)
    screen_changes = detect_screen_changes(screenshots_dir, touch_events, Image, imagehash)
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
