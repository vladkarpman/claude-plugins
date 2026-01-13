#!/usr/bin/env python3
"""
Extract frames from video at specific timestamps using ffmpeg.
Matches each touch event to the frame just BEFORE the touch.
"""

import subprocess
import json
import sys
from pathlib import Path


def extract_frame(video_path: str, timestamp_sec: float, output_path: str) -> bool:
    """Extract a single frame from video at given timestamp."""
    cmd = [
        "ffmpeg",
        "-ss", f"{timestamp_sec:.3f}",  # Seek to timestamp
        "-i", video_path,
        "-frames:v", "1",  # Extract 1 frame
        "-q:v", "2",  # High quality
        "-y",  # Overwrite
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}", file=sys.stderr)
    return result.returncode == 0


def match_touches_to_frames(
    video_path: str,
    touch_events: list,
    video_start_time: float,
    output_dir: str,
    offset_ms: int = 100  # Extract frame 100ms BEFORE touch
) -> list:
    """
    Extract frames for each touch event.

    Args:
        video_path: Path to recorded video
        touch_events: List of touch events with timestamps
        video_start_time: Unix timestamp when video recording started
        output_dir: Directory to save extracted frames
        offset_ms: How many ms before touch to extract frame

    Returns:
        List of touch events with updated screenshot paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    updated_events = []

    for event in touch_events:
        # Validate event structure
        if "index" not in event or "timestamp" not in event:
            print(f"Error: Event missing required fields: {event}", file=sys.stderr)
            continue

        touch_time = event["timestamp"]

        # Calculate position in video (seconds from video start)
        video_position = touch_time - video_start_time - (offset_ms / 1000)

        # Ensure we don't go negative
        video_position = max(0, video_position)

        # Output filename
        frame_path = output_path / f"touch_{event['index']:03d}.png"

        success = extract_frame(video_path, video_position, str(frame_path))

        if success:
            event["screenshot"] = f"recording/screenshots/touch_{event['index']:03d}.png"
            event["frame_offset_ms"] = offset_ms
            print(f"Extracted frame for touch {event['index']} at {video_position:.3f}s", file=sys.stderr)
        else:
            print(f"Failed to extract frame for touch {event['index']}", file=sys.stderr)
            event["screenshot"] = None

        updated_events.append(event)

    return updated_events


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: extract-frames.py <video> <touch_events.json> <video_start_time> <output_dir>", file=sys.stderr)
        sys.exit(1)

    # Check ffmpeg is installed
    if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
        print("Error: ffmpeg not found. Install with: brew install ffmpeg", file=sys.stderr)
        sys.exit(1)

    video_path = sys.argv[1]
    events_path = sys.argv[2]
    output_dir = sys.argv[4]

    # Validate video file exists
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"Error: Video file not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    # Validate video_start_time is a number
    try:
        video_start = float(sys.argv[3])
    except ValueError:
        print(f"Error: video_start_time must be a number, got: {sys.argv[3]}", file=sys.stderr)
        sys.exit(1)

    # Load and validate events file
    try:
        with open(events_path) as f:
            events = json.load(f)
    except FileNotFoundError:
        print(f"Error reading events file: File not found: {events_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error reading events file: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    updated = match_touches_to_frames(video_path, events, video_start, output_dir)

    # Output updated events
    print(json.dumps(updated, indent=2))
