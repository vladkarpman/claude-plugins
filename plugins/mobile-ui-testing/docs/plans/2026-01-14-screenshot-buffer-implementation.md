# Screenshot Buffer Verification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace slow mobile-mcp verification with background ADB screenshot buffer for reliable test assertions.

**Architecture:** Background Python process captures screenshots every 150ms via ADB. Verification queries buffer for screenshots since last action, checks candidates against expected state with recency constraint.

**Tech Stack:** Python 3.8+, ADB, existing Claude Code AI vision

---

## Task 1: Screenshot Buffer Script

**Files:**
- Create: `scripts/screenshot-buffer.py`
- Create: `scripts/test-screenshot-buffer.py` (manual test)

**Step 1: Create buffer script skeleton**

```python
#!/usr/bin/env python3
"""
Background screenshot capture for test verification.

Usage:
    python3 screenshot-buffer.py --device DEVICE_ID --output /tmp/buffer --interval 150

Captures screenshots every INTERVAL ms, saves to OUTPUT directory with timestamps.
Runs until killed (SIGTERM/SIGINT).
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


class ScreenshotBuffer:
    def __init__(self, device: str, output_dir: Path, interval_ms: int = 150):
        self.device = device
        self.output_dir = output_dir
        self.interval_ms = interval_ms
        self.running = False
        self.manifest = {
            "device": device,
            "started_at": None,
            "capture_interval_ms": interval_ms,
            "screenshots": []
        }
        self.max_screenshots = 200  # Rolling buffer limit

    def setup(self):
        """Create output directory and initialize manifest."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest["started_at"] = time.time()
        self._write_manifest()

    def _write_manifest(self):
        """Write manifest.json to output directory."""
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(self.manifest, f, indent=2)

    def capture_screenshot(self) -> Optional[str]:
        """Capture screenshot via ADB, return filename or None on failure."""
        timestamp = time.time()
        filename = f"{timestamp:.3f}.png"
        device_path = "/sdcard/screen_buffer.png"
        local_path = self.output_dir / filename

        try:
            # Capture on device
            subprocess.run(
                ["adb", "-s", self.device, "shell", "screencap", "-p", device_path],
                check=True,
                capture_output=True,
                timeout=5
            )

            # Pull to local
            subprocess.run(
                ["adb", "-s", self.device, "pull", device_path, str(local_path)],
                check=True,
                capture_output=True,
                timeout=5
            )

            # Add to manifest
            self.manifest["screenshots"].append({
                "timestamp": timestamp,
                "file": filename
            })

            # Enforce rolling buffer limit
            self._cleanup_old_screenshots()

            self._write_manifest()
            return filename

        except subprocess.TimeoutExpired:
            print(f"Screenshot timeout at {timestamp}", file=sys.stderr)
            return None
        except subprocess.CalledProcessError as e:
            print(f"Screenshot failed: {e}", file=sys.stderr)
            return None

    def _cleanup_old_screenshots(self):
        """Remove oldest screenshots if over limit."""
        while len(self.manifest["screenshots"]) > self.max_screenshots:
            oldest = self.manifest["screenshots"].pop(0)
            old_path = self.output_dir / oldest["file"]
            if old_path.exists():
                old_path.unlink()

    def run(self):
        """Main capture loop."""
        self.running = True
        self.setup()

        print(f"Buffer started: {self.output_dir}", file=sys.stderr)
        print(f"Capturing every {self.interval_ms}ms", file=sys.stderr)

        while self.running:
            start = time.time()
            self.capture_screenshot()

            # Sleep for remaining interval
            elapsed_ms = (time.time() - start) * 1000
            sleep_ms = max(0, self.interval_ms - elapsed_ms)
            time.sleep(sleep_ms / 1000)

    def stop(self):
        """Stop the capture loop."""
        self.running = False
        print(f"Buffer stopped. {len(self.manifest['screenshots'])} screenshots captured.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Background screenshot capture")
    parser.add_argument("--device", required=True, help="ADB device ID")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--interval", type=int, default=150, help="Capture interval in ms")
    args = parser.parse_args()

    buffer = ScreenshotBuffer(
        device=args.device,
        output_dir=Path(args.output),
        interval_ms=args.interval
    )

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        buffer.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    buffer.run()


if __name__ == "__main__":
    main()
```

**Step 2: Test manually**

```bash
# Start buffer (in background)
python3 scripts/screenshot-buffer.py --device RFCW318P7NV --output /tmp/test-buffer --interval 150 &

# Wait 3 seconds
sleep 3

# Check manifest
cat /tmp/test-buffer/manifest.json

# Kill buffer
kill %1

# Verify screenshots exist
ls -la /tmp/test-buffer/*.png | head -5
```

Expected: ~20 screenshots captured, manifest.json with entries

**Step 3: Commit**

```bash
git add scripts/screenshot-buffer.py
git commit -m "feat: add background screenshot buffer script

Captures screenshots via ADB at configurable interval.
Rolling buffer of 200 screenshots max (~30 seconds).
Writes manifest.json with timestamps for verification lookup."
```

---

## Task 2: Verify From Buffer Script

**Files:**
- Create: `scripts/verify-from-buffer.py`

**Step 1: Create verification script**

```python
#!/usr/bin/env python3
"""
Query screenshot buffer for verification candidates.

Usage:
    python3 verify-from-buffer.py --buffer /tmp/buffer --since TIMESTAMP [--recency 500]

Returns JSON with candidate screenshots for AI verification.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any


def load_manifest(buffer_dir: Path) -> Dict[str, Any]:
    """Load manifest.json from buffer directory."""
    manifest_path = buffer_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path) as f:
        return json.load(f)


def get_screenshots_since(manifest: Dict[str, Any], since_timestamp: float) -> List[Dict[str, Any]]:
    """Get all screenshots captured after the given timestamp."""
    return [
        s for s in manifest["screenshots"]
        if s["timestamp"] >= since_timestamp
    ]


def filter_candidates(
    screenshots: List[Dict[str, Any]],
    recency_threshold_ms: float = 500
) -> List[Dict[str, Any]]:
    """
    Filter to verification candidates:
    - Within recency threshold of now, OR
    - Most recent screenshot
    """
    if not screenshots:
        return []

    now = time.time()
    most_recent = screenshots[-1]

    candidates = []
    for s in screenshots:
        age_ms = (now - s["timestamp"]) * 1000
        is_recent = age_ms <= recency_threshold_ms
        is_most_recent = s == most_recent

        if is_recent or is_most_recent:
            candidates.append({
                **s,
                "age_ms": age_ms,
                "is_most_recent": is_most_recent
            })

    return candidates


def main():
    parser = argparse.ArgumentParser(description="Query buffer for verification")
    parser.add_argument("--buffer", required=True, help="Buffer directory")
    parser.add_argument("--since", required=True, type=float, help="Action timestamp")
    parser.add_argument("--recency", type=int, default=500, help="Recency threshold in ms")
    args = parser.parse_args()

    buffer_dir = Path(args.buffer)

    try:
        manifest = load_manifest(buffer_dir)
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e), "candidates": []}))
        sys.exit(1)

    # Get screenshots since action
    screenshots = get_screenshots_since(manifest, args.since)

    # Filter to candidates
    candidates = filter_candidates(screenshots, args.recency)

    # Build full paths
    for c in candidates:
        c["path"] = str(buffer_dir / c["file"])

    result = {
        "buffer_dir": str(buffer_dir),
        "since": args.since,
        "total_since_action": len(screenshots),
        "candidates": candidates,
        "recommended": candidates[-1]["path"] if candidates else None
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

**Step 2: Test with existing buffer**

```bash
# Create test buffer with a few screenshots
mkdir -p /tmp/test-verify
NOW=$(python3 -c "import time; print(time.time())")

# Create fake manifest
cat > /tmp/test-verify/manifest.json << EOF
{
  "device": "test",
  "started_at": $NOW,
  "capture_interval_ms": 150,
  "screenshots": [
    {"timestamp": $NOW, "file": "a.png"},
    {"timestamp": $(python3 -c "print($NOW + 0.15)"), "file": "b.png"},
    {"timestamp": $(python3 -c "print($NOW + 0.30)"), "file": "c.png"}
  ]
}
EOF

# Query buffer
python3 scripts/verify-from-buffer.py --buffer /tmp/test-verify --since $NOW
```

Expected: JSON with 3 candidates, recommended = c.png

**Step 3: Commit**

```bash
git add scripts/verify-from-buffer.py
git commit -m "feat: add buffer verification query script

Filters screenshots since last action with recency constraint.
Returns candidates for AI vision analysis."
```

---

## Task 3: Config Loading

**Files:**
- Create: `scripts/load-config.py`

**Step 1: Create config loader**

```python
#!/usr/bin/env python3
"""
Load plugin configuration with priority: test > project > defaults.

Usage:
    python3 load-config.py [--project-config PATH] [--test-config PATH]

Outputs merged config as JSON.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


DEFAULTS = {
    "model": "opus",
    "buffer_interval_ms": 150,
    "buffer_max_screenshots": 200,
    "verification_recency_ms": 500
}


def load_yaml_file(path: Path) -> Dict[str, Any]:
    """Load YAML file, return empty dict if not found."""
    if not path.exists():
        return {}

    if not HAS_YAML:
        print(f"Warning: PyYAML not installed, skipping {path}", file=sys.stderr)
        return {}

    with open(path) as f:
        data = yaml.safe_load(f)
        return data if data else {}


def load_project_config(project_config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load project-level config from .claude/mobile-ui-testing.yaml"""
    if project_config_path:
        return load_yaml_file(project_config_path)

    # Default location
    default_path = Path(".claude/mobile-ui-testing.yaml")
    return load_yaml_file(default_path)


def extract_test_config(test_yaml: Dict[str, Any]) -> Dict[str, Any]:
    """Extract config section from test YAML."""
    config = test_yaml.get("config", {})
    # Only return keys that are configuration, not test-specific like 'app'
    return {
        k: v for k, v in config.items()
        if k in ["model", "buffer_interval_ms", "verification_recency_ms"]
    }


def merge_configs(
    defaults: Dict[str, Any],
    project: Dict[str, Any],
    test: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge configs with priority: test > project > defaults."""
    result = defaults.copy()
    result.update(project)
    result.update(test)
    return result


def main():
    parser = argparse.ArgumentParser(description="Load merged configuration")
    parser.add_argument("--project-config", help="Project config path")
    parser.add_argument("--test-config", help="Test YAML path (extracts config section)")
    args = parser.parse_args()

    # Load project config
    project_path = Path(args.project_config) if args.project_config else None
    project_config = load_project_config(project_path)

    # Load test config
    test_config = {}
    if args.test_config:
        test_path = Path(args.test_config)
        if test_path.exists():
            test_yaml = load_yaml_file(test_path)
            test_config = extract_test_config(test_yaml)

    # Merge
    merged = merge_configs(DEFAULTS, project_config, test_config)

    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
```

**Step 2: Test config loading**

```bash
# Test with defaults only
python3 scripts/load-config.py

# Create project config
mkdir -p .claude
cat > .claude/mobile-ui-testing.yaml << 'EOF'
model: sonnet
buffer_interval_ms: 200
EOF

# Test with project config
python3 scripts/load-config.py

# Clean up test config
rm .claude/mobile-ui-testing.yaml
```

Expected: First outputs defaults (opus), second outputs merged (sonnet, 200ms)

**Step 3: Commit**

```bash
git add scripts/load-config.py
git commit -m "feat: add config loader with priority merging

Priority: test config > project config > defaults
Defaults: opus model, 150ms interval, 500ms recency"
```

---

## Task 4: Update run-test.md - Buffer Lifecycle

**Files:**
- Modify: `commands/run-test.md`

**Step 1: Add buffer start after Step 5 (Get Screen Size)**

Add this section after "### Step 5: Get Screen Size":

```markdown
### Step 5.5: Load Configuration

**Tool:** `Bash` to load merged config:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/load-config.py" --test-config "{TEST_FILE}"
```

Parse JSON output. Store:
- `{CONFIG_MODEL}` = model (default: opus)
- `{BUFFER_INTERVAL}` = buffer_interval_ms (default: 150)
- `{VERIFICATION_RECENCY}` = verification_recency_ms (default: 500)

### Step 5.6: Start Screenshot Buffer

**Tool:** `Bash` to start buffer in background:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/screenshot-buffer.py" \
  --device "{DEVICE_ID}" \
  --output "/tmp/mobile-ui-testing-buffer-$(date +%s)" \
  --interval {BUFFER_INTERVAL} &
echo $!
```

Store:
- `{BUFFER_PID}` = process ID from output
- `{BUFFER_DIR}` = the output path used
- `{LAST_ACTION_TIMESTAMP}` = current time (initialize)
```

**Step 2: Add action timestamp tracking**

In the "### Step 7: Execute Each Test" section, after each action execution, add:

```markdown
After executing any action (tap, swipe, type, press, etc.):
- Update `{LAST_ACTION_TIMESTAMP}` = current time
```

**Step 3: Add buffer stop after Step 8 (Execute Teardown)**

Add after teardown section:

```markdown
### Step 8.5: Stop Screenshot Buffer

**Tool:** `Bash` to stop buffer:
```bash
kill {BUFFER_PID} 2>/dev/null || true
```

**On test failure:** Keep `{BUFFER_DIR}` for debugging, report path in failure output.
**On test pass:** Clean up:
```bash
rm -rf {BUFFER_DIR}
```
```

**Step 4: Commit**

```bash
git add commands/run-test.md
git commit -m "feat: integrate buffer lifecycle into run-test

- Load config before setup
- Start buffer after screen size detection
- Track action timestamps
- Stop buffer after teardown
- Preserve buffer on failure for debugging"
```

---

## Task 5: Update run-test.md - Buffer-Based Verification

**Files:**
- Modify: `commands/run-test.md`

**Step 1: Update verify_screen action**

Replace the existing `verify_screen` entry in "### Verification Actions" table:

```markdown
### Verification Actions

| YAML | Execution |
|------|-----------|
| `verify_screen: "X"` | Query buffer → AI analysis → pass if matches description |
| `verify_contains: "X"` | List elements → pass if element with text X exists |
| `verify_no_element: "X"` | List elements → pass if element with text X NOT found |

#### verify_screen with Buffer

1. **Tool:** `Bash` - Query buffer for candidates:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/verify-from-buffer.py" \
     --buffer "{BUFFER_DIR}" \
     --since {LAST_ACTION_TIMESTAMP} \
     --recency {VERIFICATION_RECENCY}
   ```

2. Parse JSON output. Get `recommended` screenshot path.

3. **If no candidates (buffer unavailable):** Fall back to mobile-mcp:
   - **Tool:** `mcp__mobile-mcp__mobile_take_screenshot`
   - Use that screenshot for analysis

4. **Tool:** `Read` the recommended screenshot image

5. **AI Analysis:** Examine the image and determine if it matches the expected state description.
   - If matches: PASS
   - If doesn't match: Check other candidates from buffer
   - If none match: FAIL

6. **On failure:** Include in error output:
   ```
   Checked {total_since_action} screenshots from buffer
   Screenshots preserved: {BUFFER_DIR}
   ```
```

**Step 2: Commit**

```bash
git add commands/run-test.md
git commit -m "feat: use buffer for verify_screen assertions

Query buffer for screenshots since last action.
AI analyzes candidates with recency constraint.
Falls back to mobile-mcp if buffer unavailable."
```

---

## Task 6: Create Config Template

**Files:**
- Create: `templates/mobile-ui-testing.yaml`

**Step 1: Create template**

```yaml
# Mobile UI Testing Plugin Configuration
# Copy to .claude/mobile-ui-testing.yaml in your project

# Model for AI-powered operations (opus, sonnet, haiku)
# Default: opus
model: opus

# Screenshot buffer capture interval in milliseconds
# Lower = more screenshots, higher disk usage
# Default: 150
buffer_interval_ms: 150

# Maximum screenshots in rolling buffer
# Default: 200 (~30 seconds at 150ms)
buffer_max_screenshots: 200

# Verification recency threshold in milliseconds
# Screenshots must be within this time OR be most recent
# Default: 500
verification_recency_ms: 500
```

**Step 2: Commit**

```bash
git add templates/mobile-ui-testing.yaml
git commit -m "docs: add config template with all options documented"
```

---

## Task 7: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add configuration section**

Add after "## Key Conventions" section:

```markdown
## Configuration

### Project Config (`.claude/mobile-ui-testing.yaml`)

```yaml
model: opus              # AI model: opus, sonnet, haiku
buffer_interval_ms: 150  # Screenshot capture interval
verification_recency_ms: 500  # Recency constraint for verification
```

See `templates/mobile-ui-testing.yaml` for all options.

### Test Config Override

Override settings per-test in YAML:

```yaml
config:
  app: com.example.app
  model: sonnet  # Override for this test only
```

Priority: Test config > Project config > Defaults
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: document configuration options in CLAUDE.md"
```

---

## Task 8: Integration Test

**Files:**
- Create: `tests/integration/examples/buffer-verification.test.yaml`

**Step 1: Create test file**

```yaml
# Buffer verification integration test
# Tests that verify_screen uses buffer correctly

config:
  app: com.google.android.calculator

setup:
  - terminate_app
  - launch_app
  - wait: 2s

teardown:
  - terminate_app

tests:
  - name: Buffer Verification Test
    description: Verify screen states are captured and verified via buffer
    timeout: 60s
    steps:
      # Initial state
      - verify_screen: "Calculator app showing number pad"

      # Perform calculation
      - tap: "5"
      - tap: "+"
      - tap: "3"
      - tap: "="

      # Verify result - this should use buffer
      - verify_screen: "Calculator showing result 8"

      # Clear and verify
      - tap: "AC"
      - verify_screen: "Calculator cleared, showing 0 or empty display"
```

**Step 2: Run integration test**

```bash
# Run the test
/run-test tests/integration/examples/buffer-verification.test.yaml
```

Expected: All steps pass, buffer used for verify_screen

**Step 3: Commit**

```bash
git add tests/integration/examples/buffer-verification.test.yaml
git commit -m "test: add buffer verification integration test"
```

---

## Task 9: Final Verification

**Step 1: Run full test suite**

```bash
./tests/integration/run-integration-tests.sh
```

**Step 2: Verify all tests pass**

Expected: All existing tests still pass + new buffer test passes

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: complete buffer verification implementation"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Screenshot buffer script | `scripts/screenshot-buffer.py` |
| 2 | Verification query script | `scripts/verify-from-buffer.py` |
| 3 | Config loader | `scripts/load-config.py` |
| 4 | Buffer lifecycle in run-test | `commands/run-test.md` |
| 5 | Buffer-based verify_screen | `commands/run-test.md` |
| 6 | Config template | `templates/mobile-ui-testing.yaml` |
| 7 | Documentation | `CLAUDE.md` |
| 8 | Integration test | `tests/integration/examples/buffer-verification.test.yaml` |
| 9 | Final verification | Run all tests |
