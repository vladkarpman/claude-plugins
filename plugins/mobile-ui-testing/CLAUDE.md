# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code plugin for YAML-based mobile UI testing using [mobile-mcp](https://github.com/anthropics/mobile-mcp). Enables writing declarative tests without programming, executed via mobile-mcp tools on Android/iOS devices.

## Testing the Plugin

```bash
# Load plugin for a session
claude --plugin-dir /path/to/mobile-ui-testing

# Verify plugin loaded - should see mobile-ui-testing commands
/help
```

No build/compile step - pure markdown commands.

## Python Dependencies (Optional)

The verification interview feature requires Python dependencies for checkpoint detection:

```bash
pip3 install -r scripts/requirements.txt
```

Required packages:
- `Pillow` - Image processing for checkpoint detection
- `imagehash` - Perceptual hashing for screen change detection

**Note:** These are only needed for the verification interview feature during `/stop-recording`. Basic test creation and execution work without these dependencies.

## Architecture

```
commands/           # Slash command implementations (markdown with YAML frontmatter)
├── run-test.md     # /run-test - Execute YAML tests
├── record-test.md  # /record-test - Start touch capture
├── stop-recording.md # /stop-recording - Generate YAML from recording
├── generate-test.md  # /generate-test - NL to YAML
├── create-test.md    # /create-test - Scaffold from template
└── lib/
    └── touch-parser.md  # Touch event parsing reference

skills/yaml-test-schema/  # Skill that teaches Claude the YAML format
├── SKILL.md              # Main skill definition
└── references/           # Detailed action/assertion docs

hooks/
├── hooks.json        # Auto-approves mobile-mcp tools (no manual confirmation)
└── session-start.sh  # Runs on plugin load

scripts/
├── analyze-checkpoints.py   # Detect verification checkpoints
├── analyze-typing.py        # Detect keyboard typing sequences
├── generate-test.py         # YAML generation with verifications and typing
├── check-ffmpeg.sh          # Verifies ffmpeg is installed
├── record-video.sh          # adb screenrecord wrapper with error handling
├── monitor-touches.py       # Captures touch events via adb getevent
├── extract-frames.py        # Extracts frames from video at touch timestamps
├── parse-touches.py         # Parses raw touch events into gestures (legacy)
└── record-touches.sh        # Touch capture script (legacy)

templates/            # Example YAML templates (reference only, not used by commands)
tests/                # Generated test files (gitignored)
```

## Command Frontmatter Pattern

Commands use YAML frontmatter with `allowed-tools` to declare permissions:

```yaml
---
name: command-name
description: What it does
argument-hint: <required> [optional]
allowed-tools:
  - Read
  - Write
  - mcp__mobile-mcp__mobile_tap
  # ... explicit tool list
---
```

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

    → Typing Detection (automatic):
        - Analyze touch patterns for keyboard typing sequences
        - Heuristics: bottom 40% of screen, < 1s between taps, 3+ consecutive taps
        - Store typing_sequences.json with detected sequences

    → Typing Interview (if sequences detected):
        - For each detected typing sequence:
            • Show context (touch range, duration)
            • Ask: "What text did you type here?"
            • Ask: "Did you press Enter/Search?"
        - Update typing_sequences.json with user input

    → Verification Interview (optional):
        - Detect checkpoints (screen changes, long waits, navigation)
        - For each checkpoint:
            • Show screenshot in conversation
            • Claude analyzes UI and suggests verifications
            • User chooses: suggestion, alternative, skip, or custom
        - Store verifications.json with selected verifications

    → Generate YAML test file:
        - Replace keyboard tap sequences with `type` commands
        - If verifications exist: Insert at checkpoints
        - If no verifications: Coordinate playback (legacy)
```

**Recording state stored in `.claude/recording-state.json`.**

**Key insight:** Extracting frames 100ms before each touch ensures vision sees
what the user actually tapped, not the changed UI after the tap.

## Conditional Logic (New in v3.2.0)

Conditionals enable runtime branching without separate test files.

**5 Operators:**
- `if_exists` - Single element check
- `if_not_exists` - Inverse element check
- `if_all_exist` - Multiple elements (AND logic)
- `if_any_exist` - Multiple elements (OR logic)
- `if_screen` - AI vision-based screen matching

**Key Features:**
- Full nesting support (unlimited depth)
- Instant evaluation (no retries - use wait_for before conditionals)
- Then/else branching
- Decimal step numbering (3.1, 3.2 for branch steps)

**Integration:**
- Documented in `commands/run-test.md`
- Examples in `tests/integration/examples/`
- Reference docs in `skills/yaml-test-schema/references/conditionals.md`

**Design:** See `docs/plans/2026-01-13-conditional-logic-implementation.md`

## Test Folder Structure (v3.3+)

```
tests/{name}/
├── test.yaml           # Test definition
└── recording/          # Recording artifacts (for debugging)
    ├── touch_events.json   # Raw touch events with timestamps
    ├── typing_sequences.json # Detected keyboard typing
    ├── verifications.json  # User-selected checkpoints
    ├── checkpoints.json    # AI-detected verification points
    ├── recording.mp4       # Video recording
    └── screenshots/        # Extracted frames from video
        ├── touch_001.png   # Frame 100ms before touch 1
        ├── touch_002.png   # Frame 100ms before touch 2
        └── ...
```

Note: `tests/` folder is gitignored - test artifacts are local only.

**Version History:**
- v3.3+: Recording artifacts in recording/ subfolder
- v2.0-3.2: All artifacts at top level alongside test.yaml
- v1.0: `tests/{name}.test.yaml` (single file)

## YAML Test Format

```yaml
config:
  app: com.package.name   # Required

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: Test name
    steps:
      - tap: "Button"      # Element text preferred
      - tap: [100, 200]    # Coordinates as fallback
      - type: "text"
      - wait_for: "Element"  # Polling wait (preferred over fixed wait)
      - verify_screen: "Description of expected state"
```

## Verification Interview

AI-guided verification insertion after recording.

**Pipeline:**
```
Recording → Checkpoint Detection → Claude Analysis → User Interview → Enhanced Test
```

**How It Works:**
1. `/stop-recording` detects verification checkpoints using perceptual hashing
2. For each checkpoint, Claude:
   - Views the screenshot directly in conversation
   - Analyzes UI state and identifies key elements
   - Suggests appropriate verifications with alternatives
3. User chooses which verifications to add (or skips checkpoint)
4. Selected verifications inserted into generated YAML test

**Components:**
- `scripts/analyze-checkpoints.py` - Detects verification points using perceptual hashing
- `commands/stop-recording.md` - Orchestrates interview workflow with Claude

**Checkpoint Detection:**
- Screen changes: Perceptual hashing (imagehash library)
- Long waits: 2+ seconds between touches
- Navigation: Back button, screen transitions
- Max 8 checkpoints per recording (top-scored)

**Requirements:**
- Python dependencies: `Pillow`, `imagehash` (optional, only for checkpoint detection)
- No API keys needed - uses Claude Code's conversation flow

**Design:** See `docs/plans/2026-01-13-verification-interview-design.md`

## Key Conventions

- **Element targeting**: Prefer text labels over coordinates
- **Waits**: Use `wait_for` (polling) over `wait` (fixed duration) when possible
- **Actions**: lowercase snake_case (`tap`, `wait_for`, `verify_screen`)
- **Verification**: `verify_screen` uses AI vision to validate screen state
- **Error handling**: Include available elements list when element not found
