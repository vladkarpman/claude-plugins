#!/usr/bin/env python3
"""
Analyze touch screenshots using Claude vision to identify tapped elements.
Generates YAML test steps from the analysis.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


def analyze_touch_with_vision(
    screenshot_path: Path,
    x: int,
    y: int,
    gesture: str
) -> dict:
    """
    Prepare touch data for Claude's vision analysis.

    This function collects screenshot path and touch coordinates into a
    structure that the stop-recording command uses. The actual vision
    analysis happens when Claude reads the screenshots and identifies
    UI elements at the touch coordinates using its built-in vision
    capabilities.

    Args:
        screenshot_path: Path to the screenshot captured after the touch.
        x: X coordinate of the touch in pixels.
        y: Y coordinate of the touch in pixels.
        gesture: Type of gesture (tap, long_press, swipe).

    Returns:
        Dict with touch metadata ready for vision analysis.
    """
    # Return placeholder - actual vision analysis happens in Claude
    return {
        "element_text": None,
        "element_type": "Unknown",
        "confidence": "pending_analysis",
        "screenshot_path": str(screenshot_path),
        "x": x,
        "y": y,
        "gesture": gesture
    }


def gesture_to_yaml(gesture: str, element_text: Optional[str], x: int, y: int) -> str:
    """Convert analyzed gesture to YAML action."""
    if element_text:
        target = f'"{element_text}"'
    else:
        target = f"[{x}, {y}]"

    if gesture == "tap":
        return f"- tap: {target}"
    elif gesture == "long_press":
        return f"- long_press: {target}"
    elif gesture == "swipe":
        # For swipes, we'd need direction detection
        return f"- swipe: up  # at ({x}, {y})"
    else:
        return f"- tap: {target}  # unknown gesture: {gesture}"


def analyze_recording(output_dir: str) -> List[Dict]:
    """
    Analyze all touches from a recording session.
    Returns list of analysis results ready for vision processing.
    """
    output_path = Path(output_dir)
    events_file = output_path / "recording" / "touch_events.json"
    screenshots_dir = output_path / "recording" / "screenshots"

    if not events_file.exists():
        print(f"Error: {events_file} not found", file=sys.stderr)
        return []

    with open(events_file) as f:
        events = json.load(f)

    results = []
    for i, event in enumerate(events):
        try:
            screenshot = event["screenshot"]
            x = event["x"]
            y = event["y"]
            gesture = event["gesture"]
            index = event["index"]
        except KeyError as e:
            print(f"Warning: event {i} missing required field {e}, skipping", file=sys.stderr)
            continue

        screenshot_path = screenshots_dir / screenshot
        if not screenshot_path.exists():
            print(f"Warning: {screenshot_path} not found, skipping", file=sys.stderr)
            continue

        result = analyze_touch_with_vision(
            screenshot_path,
            x,
            y,
            gesture
        )
        result["index"] = index
        result["duration_ms"] = event.get("duration_ms", 0)
        results.append(result)

    return results


def generate_yaml_steps(analyses: List[Dict]) -> str:
    """Generate YAML steps from analyzed touches."""
    lines = ["steps:"]
    for a in analyses:
        yaml_line = gesture_to_yaml(
            a["gesture"],
            a.get("element_text"),
            a["x"],
            a["y"]
        )
        confidence = a.get("confidence", "unknown")
        if confidence == "low":
            yaml_line += f"  # LOW confidence"
        lines.append(f"  {yaml_line}")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: analyze-touches.py <output-dir>", file=sys.stderr)
        print("       analyze-touches.py <output-dir> --prepare-for-vision", file=sys.stderr)
        sys.exit(1)

    output_dir = sys.argv[1]
    prepare_mode = "--prepare-for-vision" in sys.argv

    results = analyze_recording(output_dir)

    if prepare_mode:
        # Output JSON for Claude to process with vision
        print(json.dumps(results, indent=2))
    else:
        # Output YAML (without vision analysis)
        print(generate_yaml_steps(results))
