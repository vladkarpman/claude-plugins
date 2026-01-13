#!/usr/bin/env python3
"""Parse ADB getevent touch log, correlate with UI snapshots, and generate YAML."""
import re
import sys
import json
import os
from datetime import datetime

# Import snapshot parser from same directory
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from parse_snapshot import load_snapshots, find_nearest_snapshot, find_element_at


def parse_touch_log(log_path, screen_width=1080, screen_height=2340):
    """Parse touch log and return list of gestures."""
    with open(log_path, 'r') as f:
        content = f.read()

    # Pattern for touch events
    btn_touch_pattern = r'\[\s*(\d+\.\d+)\].*BTN_TOUCH\s+(DOWN|UP)'
    pos_x_pattern = r'\[\s*(\d+\.\d+)\].*ABS_MT_POSITION_X\s+([0-9a-f]+)'
    pos_y_pattern = r'\[\s*(\d+\.\d+)\].*ABS_MT_POSITION_Y\s+([0-9a-f]+)'

    # Find all touch down/up events
    touches = re.findall(btn_touch_pattern, content)
    pos_x = re.findall(pos_x_pattern, content)
    pos_y = re.findall(pos_y_pattern, content)

    # Group events into gestures
    gestures = []
    current_gesture = None

    # Build position lookup by timestamp
    x_by_time = {float(t): int(v, 16) for t, v in pos_x}
    y_by_time = {float(t): int(v, 16) for t, v in pos_y}

    # Get max coordinates (approximate from data)
    max_x = max(x_by_time.values()) if x_by_time else 4095
    max_y = max(y_by_time.values()) if y_by_time else 4095

    # Adjust max to be slightly higher than observed max
    max_x = max(max_x + 100, 4095)
    max_y = max(max_y + 100, 4095)

    for timestamp, state in touches:
        t = float(timestamp)
        if state == 'DOWN':
            # Find X,Y at or just after this timestamp
            start_x = None
            start_y = None
            for pos_t in sorted(x_by_time.keys()):
                if pos_t >= t:
                    start_x = x_by_time[pos_t]
                    break
            for pos_t in sorted(y_by_time.keys()):
                if pos_t >= t:
                    start_y = y_by_time[pos_t]
                    break

            current_gesture = {
                'start_time': t,
                'start_x': start_x,
                'start_y': start_y,
                'end_x': start_x,
                'end_y': start_y
            }
        elif state == 'UP' and current_gesture:
            # Find last X,Y before this timestamp
            end_x = current_gesture['start_x']
            end_y = current_gesture['start_y']
            for pos_t in sorted(x_by_time.keys(), reverse=True):
                if pos_t <= t and pos_t >= current_gesture['start_time']:
                    end_x = x_by_time[pos_t]
                    break
            for pos_t in sorted(y_by_time.keys(), reverse=True):
                if pos_t <= t and pos_t >= current_gesture['start_time']:
                    end_y = y_by_time[pos_t]
                    break

            current_gesture['end_time'] = t
            current_gesture['end_x'] = end_x
            current_gesture['end_y'] = end_y
            current_gesture['duration'] = t - current_gesture['start_time']

            # Calculate movement
            if current_gesture['start_x'] and current_gesture['end_x']:
                dx = abs(current_gesture['end_x'] - current_gesture['start_x'])
                dy = abs(current_gesture['end_y'] - current_gesture['start_y'])
                current_gesture['distance'] = (dx**2 + dy**2)**0.5
            else:
                current_gesture['distance'] = 0

            # Convert to screen coordinates
            if current_gesture['start_x']:
                current_gesture['screen_x'] = int(current_gesture['start_x'] / max_x * screen_width)
                current_gesture['screen_y'] = int(current_gesture['start_y'] / max_y * screen_height)
                current_gesture['screen_end_x'] = int(current_gesture['end_x'] / max_x * screen_width)
                current_gesture['screen_end_y'] = int(current_gesture['end_y'] / max_y * screen_height)

                # Calculate percentage coordinates (cross-device compatible)
                current_gesture['percent_x'] = round(current_gesture['screen_x'] / screen_width * 100, 1)
                current_gesture['percent_y'] = round(current_gesture['screen_y'] / screen_height * 100, 1)

            # Classify gesture
            duration_ms = current_gesture['duration'] * 1000
            distance = current_gesture['distance']

            if duration_ms < 300 and distance < 100:
                current_gesture['type'] = 'tap'
            elif distance >= 100:
                # Determine swipe direction
                if current_gesture['start_x'] and current_gesture['end_x']:
                    dx = current_gesture['end_x'] - current_gesture['start_x']
                    dy = current_gesture['end_y'] - current_gesture['start_y']
                    if abs(dx) > abs(dy):
                        current_gesture['type'] = 'swipe_right' if dx > 0 else 'swipe_left'
                    else:
                        current_gesture['type'] = 'swipe_down' if dy > 0 else 'swipe_up'
                else:
                    current_gesture['type'] = 'swipe'
            elif duration_ms >= 500:
                current_gesture['type'] = 'long_press'
            else:
                current_gesture['type'] = 'tap'

            gestures.append(current_gesture)
            current_gesture = None

    return gestures


def correlate_with_snapshots(gestures, snapshots, recording_start_time_ms):
    """Correlate gestures with UI snapshots to find elements.

    Args:
        gestures: List of gesture dicts with screen_x, screen_y
        snapshots: Dict of timestamp -> list of ViewElements
        recording_start_time_ms: Unix timestamp (ms) when recording started
    """
    for gesture in gestures:
        if 'screen_x' not in gesture:
            continue

        # Convert gesture timestamp to Unix ms
        # gesture['start_time'] is seconds since boot, we need to map to wall clock
        # This is tricky - we'll estimate based on snapshot timestamps
        gesture_time_relative = gesture['start_time']

        # Find the snapshot whose timestamp is closest to when this gesture occurred
        # Since we don't have exact mapping, use proximity to first/last snapshot
        if not snapshots:
            gesture['element'] = None
            gesture['confidence'] = 'low'
            continue

        snapshot_times = sorted(snapshots.keys())
        first_snapshot_time = snapshot_times[0]
        last_snapshot_time = snapshot_times[-1]

        # Estimate gesture wall-clock time based on position in gesture sequence
        # (This is a heuristic - assumes gestures span the recording duration)
        gestures_with_coords = [g for g in gestures if 'screen_x' in g]
        if len(gestures_with_coords) > 1:
            first_gesture_time = gestures_with_coords[0]['start_time']
            last_gesture_time = gestures_with_coords[-1]['start_time']
            gesture_range = last_gesture_time - first_gesture_time

            if gesture_range > 0:
                # Map gesture time to snapshot time range
                progress = (gesture_time_relative - first_gesture_time) / gesture_range
                estimated_wall_time = first_snapshot_time + progress * (last_snapshot_time - first_snapshot_time)
            else:
                estimated_wall_time = first_snapshot_time
        else:
            estimated_wall_time = first_snapshot_time

        # Find nearest snapshot
        result = find_nearest_snapshot(snapshots, int(estimated_wall_time), max_diff_ms=500)

        if result:
            snapshot_time, elements = result
            x, y = gesture['screen_x'], gesture['screen_y']
            element = find_element_at(elements, x, y)

            if element:
                gesture['element'] = {
                    'identifier': element.get_identifier(),
                    'class': element.class_name,
                    'bounds': element.bounds,
                    'view_id': element.view_id
                }
                gesture['confidence'] = 'high' if element.get_identifier() else 'medium'
            else:
                gesture['element'] = None
                gesture['confidence'] = 'low'
        else:
            gesture['element'] = None
            gesture['confidence'] = 'low'

    return gestures


def generate_yaml(gestures, app_package, screen_width, screen_height):
    """Generate YAML test content from gestures."""
    lines = [
        f"# Test recorded on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"# Gestures: {len(gestures)}",
        "",
        "config:",
        f"  app: {app_package}",
        f"  recorded_resolution: [{screen_width}, {screen_height}]",
        "",
        "setup:",
        "  - terminate_app",
        "  - launch_app",
        "  - wait: 3s",
        "",
        "teardown:",
        "  - terminate_app",
        "",
        "tests:",
        "  - name: recorded-test",
        "    description: Auto-generated from touch recording",
        "    steps:",
    ]

    for i, g in enumerate(gestures):
        gtype = g['type']
        confidence = g.get('confidence', 'low')
        element = g.get('element')

        if gtype.startswith('swipe_'):
            direction = gtype.replace('swipe_', '')
            lines.append(f"      - swipe: {direction}")
        elif gtype == 'tap':
            if element and element.get('identifier'):
                # Use element text (cross-device compatible)
                identifier = element['identifier']
                # Escape quotes in identifier
                if '"' in identifier or '\n' in identifier:
                    identifier = identifier.replace('\n', ' ').strip()
                lines.append(f'      - tap: "{identifier}"')
            else:
                # Use percentage coordinates (cross-device compatible fallback)
                px = g.get('percent_x', 50)
                py = g.get('percent_y', 50)
                comment = ""
                if element and element.get('view_id'):
                    comment = f"  # {element['view_id']}"
                lines.append(f"      - tap: [\"{px}%\", \"{py}%\"]{comment}")
        elif gtype == 'long_press':
            if element and element.get('identifier'):
                identifier = element['identifier']
                lines.append(f'      - long_press: "{identifier}"')
            else:
                px = g.get('percent_x', 50)
                py = g.get('percent_y', 50)
                lines.append(f"      - long_press: [\"{px}%\", \"{py}%\"]")

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: parse-touches.py <test-folder>")
        print("       parse-touches.py <touch_log.txt>")
        sys.exit(1)

    path = sys.argv[1]

    # Determine if path is a folder or file
    if os.path.isdir(path):
        test_folder = path
        touch_log = os.path.join(path, 'touch_log.txt')
        snapshots_dir = os.path.join(path, 'snapshots')
    else:
        touch_log = path
        test_folder = os.path.dirname(path)
        snapshots_dir = os.path.join(test_folder, 'snapshots')

    if not os.path.exists(touch_log):
        print(f"ERROR: Touch log not found: {touch_log}")
        sys.exit(1)

    # Load screen size if available
    screen_size_file = os.path.join(test_folder, 'screen_size.txt')
    if os.path.exists(screen_size_file):
        with open(screen_size_file) as f:
            size_str = f.read().strip()
            if 'x' in size_str:
                screen_width, screen_height = map(int, size_str.split('x'))
            else:
                screen_width, screen_height = 1080, 2340
    else:
        screen_width, screen_height = 1080, 2340

    print(f"Screen size: {screen_width}x{screen_height}")

    # Parse touch log
    print(f"Parsing touch log: {touch_log}")
    gestures = parse_touch_log(touch_log, screen_width, screen_height)
    print(f"Found {len(gestures)} gestures")

    # Load and correlate with snapshots
    if os.path.isdir(snapshots_dir):
        print(f"Loading snapshots from: {snapshots_dir}")
        snapshots = load_snapshots(snapshots_dir)
        print(f"Loaded {len(snapshots)} snapshots")

        if snapshots:
            first_snapshot_time = min(snapshots.keys())
            gestures = correlate_with_snapshots(gestures, snapshots, first_snapshot_time)

            # Count confidence levels
            high = sum(1 for g in gestures if g.get('confidence') == 'high')
            medium = sum(1 for g in gestures if g.get('confidence') == 'medium')
            low = sum(1 for g in gestures if g.get('confidence') == 'low')
            print(f"Element correlation: {high} high, {medium} medium, {low} low confidence")
    else:
        print("No snapshots directory found - using percentage coordinates")

    # Print summary
    print(f"\nGestures:")
    for i, g in enumerate(gestures, 1):
        gtype = g['type']
        element = g.get('element')
        confidence = g.get('confidence', 'low')

        if 'screen_x' in g:
            if element and element.get('identifier'):
                elem_str = f'"{element["identifier"]}"'
            else:
                elem_str = f"[{g.get('percent_x', '?')}%, {g.get('percent_y', '?')}%]"

            conf_marker = {'high': '✓', 'medium': '~', 'low': '?'}.get(confidence, '?')
            print(f"  {i:2}. {gtype:12} {elem_str:30} {conf_marker}")
        else:
            print(f"  {i:2}. {gtype:12} (coords unknown)")

    # Save gestures JSON
    output_json = os.path.join(test_folder, 'gestures.json')
    with open(output_json, 'w') as f:
        # Convert element objects to serializable format
        serializable = []
        for g in gestures:
            sg = dict(g)
            if sg.get('element'):
                sg['element'] = dict(sg['element'])
            serializable.append(sg)
        json.dump(serializable, f, indent=2)
    print(f"\nSaved gestures: {output_json}")

    # Generate YAML
    # Try to detect app package
    app_package = "com.example.app"  # Default
    config_file = os.path.join(test_folder, 'config.json')
    if os.path.exists(config_file):
        with open(config_file) as f:
            config = json.load(f)
            app_package = config.get('app', app_package)

    yaml_content = generate_yaml(gestures, app_package, screen_width, screen_height)
    yaml_file = os.path.join(test_folder, 'test.yaml')
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)
    print(f"Saved test: {yaml_file}")


if __name__ == '__main__':
    main()
