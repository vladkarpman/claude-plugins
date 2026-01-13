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

agents/               # Specialized subagents for advanced workflows
├── test-suite-generator.md  # Generate comprehensive test suites
└── yaml-test-validator.md   # Validate test syntax and best practices
```

### Script Architecture Details

**Script dependencies:**
- `analyze-checkpoints.py` requires: Pillow, imagehash
- `monitor-touches.py` requires: adb accessible in PATH
- `extract-frames.py` requires: ffmpeg installed
- `generate-test.py` requires: JSON reading capabilities (built-in)

**Error handling:**
- All Python scripts exit with non-zero code on failure
- Bash scripts use `set -e` for immediate error propagation
- Recording state persisted to `.claude/recording-state.json` for recovery

**Key processing flow:**
```
User Action → Command (markdown) → Python/Bash Script → mobile-mcp tool → Device
           ↓
    AskUserQuestion (for interviews)
           ↓
    Write YAML test file
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

## Development & Testing

### Running Integration Tests

Comprehensive test suite using Android Calculator app:

```bash
# Run all integration tests
./tests/integration/run-integration-tests.sh

# Test specific scenarios
cd tests/integration
# Edit run-integration-tests.sh to comment out test sections you want to skip
```

**Test coverage:**
- Basic operations (tap, type, wait_for, verify_screen)
- Conditional operators (if_exists, if_not_exists, if_all_exist, if_any_exist, if_screen)
- Flow control (retry, repeat)
- Error recovery and element not found handling
- Multi-step calculations with verification

**Prerequisites:**
- Android device/emulator connected via adb
- Calculator app installed (`com.google.android.calculator`)
- mobile-mcp configured and working

### Testing Individual Scripts

```bash
# Test checkpoint detection
python3 scripts/analyze-checkpoints.py tests/example/recording/

# Test typing detection
python3 scripts/analyze-typing.py tests/example/recording/touch_events.json

# Validate YAML generation
python3 scripts/generate-test.py tests/example/recording/ tests/example/test.yaml
```

### Debugging Commands

```bash
# Check mobile-mcp connection
adb devices

# Verify ffmpeg installation
./scripts/check-ffmpeg.sh

# Monitor touch events manually (Ctrl+C to stop)
python3 scripts/monitor-touches.py

# Extract frames from recording
python3 scripts/extract-frames.py \
  tests/{name}/recording/recording.mp4 \
  tests/{name}/recording/touch_events.json \
  tests/{name}/recording/screenshots/

# Start video recording manually
./scripts/record-video.sh /sdcard/test.mp4
```

## Agent Usage Patterns

The plugin includes specialized agents for advanced workflows.

### test-suite-generator

Generates comprehensive test suites by exploring app structure.

**When to use:**
- User wants multiple test scenarios covering different features
- Need systematic test coverage for an entire app
- Creating tests for login, dashboard, settings, etc. simultaneously

**Capabilities:**
- App structure analysis via screenshots and element listing
- Navigation mapping and screen hierarchy documentation
- Feature identification (login, search, cart, settings)
- Multiple YAML test file generation with proper structure
- Edge case and error condition coverage

**Example trigger phrases:**
- "Generate comprehensive tests for my app"
- "Create test suite for login, dashboard, and settings"
- "Analyze my app and suggest test scenarios"
- "Generate tests covering all main features and edge cases"

**Process:**
1. Takes screenshots to understand current app state
2. Lists elements on screen using mobile-mcp
3. Maps navigation flows by exploring screens
4. Identifies distinct features/modules
5. Generates separate test files for each feature
6. Includes setup/teardown, verifications, and conditional logic

### yaml-test-validator

Validates YAML test files for syntax, structure, and best practices.

**When to use:**
- Before running tests (catch errors early)
- Debugging flaky tests
- Code review for test quality
- Checking for race conditions or brittle selectors

**Validation checks:**
- YAML syntax correctness (indentation, structure)
- Required fields (config.app, tests, steps)
- Action parameter validation
- Race condition detection (missing wait_for before tap)
- Brittle selector detection (coordinate-based taps without fallback)
- Best practice recommendations (prefer wait_for over wait)

**Example trigger phrases:**
- "Validate my test file"
- "Review my login test for best practices"
- "This test keeps failing randomly, can you check it?"
- "Check if my test follows best practices"

**Output includes:**
- Syntax errors with line numbers
- Missing required fields
- Timing issues (race conditions)
- Selector recommendations
- Overall quality score

## Common Development Tasks

### Adding a New Action Type

1. Document action in `skills/yaml-test-schema/references/actions.md`
2. Add example to README.md "Available Actions" table
3. Update `/run-test` command logic in `commands/run-test.md`
4. Add integration test case in `tests/integration/examples/`
5. Update CHANGELOG.md with feature addition

**Example flow:**
```markdown
# In skills/yaml-test-schema/references/actions.md
## new_action
- `new_action: "target"` - Description of what it does
- Parameters: target (string or coordinates)
- Example: `- new_action: "Button"`

# In commands/run-test.md (add handling)
- Check if step contains 'new_action' key
- Call appropriate mobile-mcp tool
- Handle success/error cases
```

### Adding a New Conditional Operator

1. Document in `skills/yaml-test-schema/references/conditionals.md`
2. Update `/run-test` conditional evaluation logic in `commands/run-test.md`
3. Add test case to `tests/integration/examples/conditional-{name}.test.yaml`
4. Update README.md conditionals section
5. Add to CHANGELOG.md

**Key considerations:**
- Instant evaluation (no retries)
- Support nesting
- Handle then/else branches
- Decimal step numbering (3.1, 3.2)

### Modifying Recording Pipeline

Key files to modify:
- `commands/record-test.md` - Initiates recording (video + touch capture)
- `commands/stop-recording.md` - Processes recording and generates YAML
- `scripts/monitor-touches.py` - Touch event capture via adb getevent
- `scripts/analyze-typing.py` - Detects keyboard typing sequences
- `scripts/analyze-checkpoints.py` - Detects verification points
- `scripts/generate-test.py` - Final YAML generation with type commands

**Test changes with:**
```bash
# Record a test manually
/record-test dev-test
# Interact with app
/stop-recording
# Verify generated YAML structure
cat tests/dev-test/test.yaml
```

**Pipeline stages:**
1. Recording: Video + touch events captured simultaneously
2. Frame extraction: ffmpeg extracts frames 100ms before each touch
3. Typing detection: Analyze touch patterns for keyboard input
4. Typing interview: Ask user for typed text
5. Checkpoint detection: Identify verification points (optional)
6. Verification interview: AI-guided checkpoint selection (optional)
7. YAML generation: Combine actions, type commands, verifications

### Adding a New Command

1. Create `commands/{name}.md` with YAML frontmatter
2. Define `allowed-tools` list for required permissions
3. Implement command logic using markdown with tool calls
4. Test command loads: `/help` should show it
5. Add to README.md if user-facing

**Frontmatter template:**
```yaml
---
name: command-name
description: Brief description
argument-hint: <required> [optional]
allowed-tools:
  - Read
  - Write
  - Bash
  - mcp__mobile-mcp__mobile_tap
---
```

## Design Documentation

Implementation details and architectural decisions documented in `docs/plans/`:

- **conditional-logic-implementation.md** - Conditional operators design (if_exists, if_screen, etc.)
- **verification-interview-design.md** - AI-guided verification workflow and checkpoint detection
- **keyboard-typing-detection.md** - Typing detection heuristics and interview flow
- **recording-reorganization.md** - Test folder structure evolution (v1.0 → v3.3+)
- **integration-testing-and-docs-design.md** - Testing strategy and integration test suite

**When to reference:**
- Modifying core features (conditionals, recording, verification)
- Understanding design rationale and trade-offs
- Extending existing functionality
- Debugging complex pipeline issues

## Troubleshooting Plugin Development

### Command Not Loading

```bash
# Verify frontmatter syntax
head -20 commands/{command-name}.md

# Check for YAML errors in frontmatter
# Ensure "---" delimiters are present
# Verify allowed-tools list is properly formatted as YAML array

# Test if plugin loads
claude --plugin-dir .
/help  # Should show your command
```

### Agent Not Triggering

```bash
# Check agent description matches usage pattern
cat agents/{agent-name}.md | head -50

# Verify agent frontmatter includes name and description
# Agent descriptions should include trigger examples

# Check if agent appears in Task tool
# Agents auto-discovered from agents/ directory
```

### Python Script Errors

```bash
# Install dependencies
pip3 install -r scripts/requirements.txt

# Test script in isolation
python3 scripts/{script-name}.py --help

# Check Python version (requires 3.8+)
python3 --version

# Debug with verbose output
python3 -v scripts/{script-name}.py

# Check for missing imports
python3 -c "import PIL; import imagehash"
```

### Recording State Corruption

```bash
# View current recording state
cat .claude/recording-state.json

# Reset recording state (if corrupted)
rm -f .claude/recording-state.json

# Manually clean up test artifacts
rm -rf tests/{name}/recording/

# Check for orphaned adb processes
ps aux | grep adb
ps aux | grep screenrecord
```

### Mobile-MCP Connection Issues

```bash
# Verify adb connection
adb devices
# Should show: <device-id>  device

# Restart adb server
adb kill-server && adb start-server

# Check device screen is on
adb shell dumpsys power | grep "Display Power"

# Test element listing manually
adb shell uiautomator dump /sdcard/window_dump.xml
adb pull /sdcard/window_dump.xml
```

### Integration Test Failures

```bash
# Run single test file
cd tests/integration
# Edit run-integration-tests.sh, comment out other tests
./run-integration-tests.sh

# Check test results
cat INTEGRATION_TEST_RESULTS.md

# Verify Calculator app installed
adb shell pm list packages | grep calculator

# Reset Calculator app state
adb shell pm clear com.google.android.calculator
```
