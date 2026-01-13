#!/usr/bin/env python3
"""Parse dumpsys activity top output and extract view hierarchy with bounds."""
import re
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ViewElement:
    """Represents a UI element with bounds."""
    class_name: str
    bounds: tuple  # (left, top, right, bottom)
    view_id: Optional[str] = None
    text: Optional[str] = None
    content_desc: Optional[str] = None

    @property
    def center(self) -> tuple:
        """Return center point of the element."""
        left, top, right, bottom = self.bounds
        return ((left + right) // 2, (top + bottom) // 2)

    @property
    def width(self) -> int:
        return self.bounds[2] - self.bounds[0]

    @property
    def height(self) -> int:
        return self.bounds[3] - self.bounds[1]

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point (x, y) is within this element's bounds."""
        left, top, right, bottom = self.bounds
        return left <= x <= right and top <= y <= bottom

    def get_identifier(self) -> Optional[str]:
        """Get the best identifier for this element."""
        if self.text:
            return self.text
        if self.content_desc:
            return self.content_desc
        if self.view_id:
            # Extract just the ID name from app:id/xxx
            if '/' in self.view_id:
                return self.view_id.split('/')[-1]
            return self.view_id
        return None


def parse_snapshot(content: str) -> list[ViewElement]:
    """Parse dumpsys activity top output and extract view elements.

    Example line formats:
      android.widget.Button{bb712e GFED..C.. ......ID 0,1831-570,1963 #7f0a014c app:id/clear_all}
      android.widget.TextView{61ef565 V.ED..... ........ 224,911-855,977}
      IconViewImpl{6e6248b VFED..C.. ......ID 0,0-249,285 #7f0a02ed app:id/icon} - Discord, ...
    """
    elements = []

    # Pattern to match view lines with bounds
    # Format: ClassName{hash FLAGS FLAGS left,top-right,bottom [#id app:id/name]}
    view_pattern = re.compile(
        r'([a-zA-Z0-9_.]+)\{[^}]+\s+(\d+),(\d+)-(\d+),(\d+)(?:\s+#[0-9a-f]+\s+([^\s}]+))?'
    )

    # Pattern to extract text after "} - TEXT," for IconView style
    text_after_pattern = re.compile(r'\}\s+-\s+([^,]+),')

    for line in content.split('\n'):
        match = view_pattern.search(line)
        if not match:
            continue

        class_name = match.group(1)
        left = int(match.group(2))
        top = int(match.group(3))
        right = int(match.group(4))
        bottom = int(match.group(5))
        view_id = match.group(6) if match.lastindex >= 6 else None

        # Skip zero-size elements
        if left == right or top == bottom:
            continue

        # Skip very large elements (likely containers)
        if (right - left) > 1000 and (bottom - top) > 2000:
            continue

        # Try to extract text
        text = None
        text_match = text_after_pattern.search(line)
        if text_match:
            text = text_match.group(1).strip()

        element = ViewElement(
            class_name=class_name,
            bounds=(left, top, right, bottom),
            view_id=view_id,
            text=text
        )
        elements.append(element)

    return elements


def find_element_at(elements: list[ViewElement], x: int, y: int) -> Optional[ViewElement]:
    """Find the smallest element containing the given point.

    Returns the most specific (smallest) element at that location,
    preferring clickable elements.
    """
    matches = [e for e in elements if e.contains_point(x, y)]

    if not matches:
        return None

    # Sort by area (smallest first) to get most specific element
    matches.sort(key=lambda e: e.width * e.height)

    # Prefer elements with identifiers
    for elem in matches:
        if elem.get_identifier():
            return elem

    # Return smallest element
    return matches[0]


def load_snapshots(snapshots_dir: str) -> dict[int, list[ViewElement]]:
    """Load all snapshots from directory, keyed by timestamp."""
    snapshots = {}

    if not os.path.isdir(snapshots_dir):
        return snapshots

    for filename in os.listdir(snapshots_dir):
        if not filename.endswith('.txt'):
            continue

        try:
            timestamp = int(filename.replace('.txt', ''))
        except ValueError:
            continue

        filepath = os.path.join(snapshots_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()

        elements = parse_snapshot(content)
        if elements:
            snapshots[timestamp] = elements

    return snapshots


def find_nearest_snapshot(snapshots: dict[int, list[ViewElement]],
                          touch_timestamp_ms: int,
                          max_diff_ms: int = 200) -> Optional[tuple[int, list[ViewElement]]]:
    """Find the snapshot taken closest to (and preferably before) the touch.

    Returns (timestamp, elements) or None if no snapshot within max_diff_ms.
    """
    if not snapshots:
        return None

    timestamps = sorted(snapshots.keys())

    # Find snapshots before the touch
    before = [t for t in timestamps if t <= touch_timestamp_ms]
    after = [t for t in timestamps if t > touch_timestamp_ms]

    # Prefer the snapshot just before the touch
    if before:
        nearest = before[-1]
        if touch_timestamp_ms - nearest <= max_diff_ms:
            return (nearest, snapshots[nearest])

    # Fall back to snapshot just after
    if after:
        nearest = after[0]
        if nearest - touch_timestamp_ms <= max_diff_ms:
            return (nearest, snapshots[nearest])

    return None


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: parse_snapshot.py <snapshot-file-or-dir> [x] [y]")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isdir(path):
        # Load all snapshots
        snapshots = load_snapshots(path)
        print(f"Loaded {len(snapshots)} snapshots")

        for ts, elements in sorted(snapshots.items())[:3]:
            print(f"\nSnapshot {ts}:")
            for elem in elements[:5]:
                print(f"  {elem.class_name} {elem.bounds} - {elem.get_identifier()}")
    else:
        # Parse single file
        with open(path, 'r') as f:
            content = f.read()

        elements = parse_snapshot(content)
        print(f"Found {len(elements)} elements:\n")

        for elem in elements:
            ident = elem.get_identifier() or "(no identifier)"
            print(f"  {elem.bounds} {elem.class_name}: {ident}")

        # If coordinates provided, find element at that point
        if len(sys.argv) >= 4:
            x, y = int(sys.argv[2]), int(sys.argv[3])
            elem = find_element_at(elements, x, y)
            if elem:
                print(f"\nElement at ({x}, {y}): {elem.get_identifier()} ({elem.class_name})")
            else:
                print(f"\nNo element found at ({x}, {y})")
