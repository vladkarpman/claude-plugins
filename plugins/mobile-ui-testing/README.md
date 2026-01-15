# Mobile UI Testing Plugin

A Claude Code plugin for writing and running YAML-based mobile UI tests with [mobile-mcp](https://github.com/anthropics/mobile-mcp).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/vladkarpman/mobile-ui-testing)](https://github.com/vladkarpman/mobile-ui-testing/releases)

## Features

- **Auto-permissions** - mobile-mcp tools auto-approved, no manual confirmation needed
- **Video-based frame capture** - Records video, extracts 7 frames per action in parallel
- **`/run-test`** - Execute YAML test files with detailed output and HTML reports
- **`/create-test`** - Scaffold new test files with proper structure
- **`/generate-test`** - Generate tests from natural language descriptions
- **`/record-test`** - Record user actions and generate YAML automatically
- **Keyboard typing detection** - Automatically detects and converts keyboard typing to `type` commands
- **Verification interview** - AI-guided checkpoint selection during recording
- **YAML Test Schema Knowledge** - Claude understands the complete test format
- **No compilation** - Just write YAML and run

## Prerequisites

Before using this plugin, ensure you have:

1. **Claude Code CLI** installed
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **mobile-mcp** configured in Claude Code
   - Follow [mobile-mcp setup guide](https://github.com/anthropics/mobile-mcp)

3. **Connected device**
   - Android: Device connected via `adb` (run `adb devices` to verify)
   - iOS: Simulator running or device connected

4. **ffmpeg** (required for video recording and frame extraction)
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu
   sudo apt install ffmpeg

   # Windows
   choco install ffmpeg
   ```

## Installation

### Option 1: Direct from GitHub (Recommended)

```bash
# Install specific version
/plugin install github:vladkarpman/mobile-ui-testing#v3.4.0

# Or install latest
/plugin install github:vladkarpman/mobile-ui-testing
```

### Option 2: Project-level

Clone into your project's plugins directory:

```bash
cd your-project
mkdir -p .claude/plugins
cd .claude/plugins
git clone https://github.com/vladkarpman/mobile-ui-testing.git
```

### Option 3: Session-only

Load for a single session:

```bash
claude --plugin-dir /path/to/mobile-ui-testing
```

## Uninstallation

### If installed via `/plugin install`:

```bash
/plugin uninstall mobile-ui-testing
```

### If installed as project-level:

```bash
rm -rf .claude/plugins/mobile-ui-testing
```

## Post-Installation Setup

### Python Dependencies (Optional)

The verification interview feature requires Python dependencies for checkpoint detection. Install them if you plan to use AI-guided verification:

```bash
pip install -r scripts/requirements.txt
```

**Required packages:**
- `Pillow>=10.0.0` - Image processing
- `imagehash>=4.3.0` - Perceptual hashing for checkpoint detection

**Note:** These are only needed for the verification interview feature during `/stop-recording`. Basic test creation and execution work without these dependencies.

## Quick Start

### 1. Create your first test

```bash
/create-test login
```

This creates `tests/login/test.yaml` with a template.

### 2. Edit the test file

```yaml
config:
  app: com.your.app.package

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: User can login
    steps:
      - tap: "Email"
      - type: "user@example.com"
      - tap: "Password"
      - type: "secret123"
      - tap: "Login"
      - wait: 2s
      - verify_screen: "Home screen after login"
```

### 3. Run the test

```bash
/run-test tests/login/
```

## Commands

### `/run-test <path> [--report]`

Execute a YAML test on a connected device.

```bash
# Folder format (recommended)
/run-test tests/login/
/run-test tests/onboarding/ --report

# File format (legacy)
/run-test tests/login.test.yaml
```

**With `--report` flag:** Generates HTML/JSON reports in `tests/reports/`.

**Output format:**
```
Running: User login flow
────────────────────────────────────────

  [1/5] wait_for "Login"
        ✓ Found in 1.2s

  [2/5] tap "Email"
        ✓ Tapped at (540, 320)

  [3/5] type "user@example.com"
        ✓ Typed 16 characters

────────────────────────────────────────
✓ PASSED  (5/5 steps in 4.2s)
```

### `/create-test <name>`

Create a new test file from a template.

```bash
/create-test login
/create-test checkout-flow
```

### `/generate-test <description>`

Generate a YAML test from a natural language description.

```bash
/generate-test "user logs in with email and password, sees home screen"
/generate-test "scroll through feed and like the first post"
```

**Example output:**
```yaml
tests:
  - name: User login flow
    steps:
      - wait_for: "Login"
      - tap: "Email"
      - type: "user@example.com"
      - tap: "Password"
      - type: "password123"
      - tap: "Login"
      - verify_screen: "Home screen"
```

### `/record-test <name>`

Start recording user actions to generate a test automatically.

```bash
/record-test login-flow
```

**How it works:**
1. Checks ffmpeg is installed
2. Starts video recording (`adb screenrecord`)
3. Captures touch events in real-time
4. You interact with your app normally

**Recorded gestures:**
- Taps (< 200ms touch)
- Long presses (≥ 500ms touch)
- Swipes (≥ 100px movement)

### `/stop-recording`

Stop recording and generate YAML from captured actions.

```bash
/stop-recording
```

**Processing steps:**
1. Stops video and touch capture
2. Extracts 7 frames per action from video in parallel (3 before, 1 exact, 3 after)
3. **Detects keyboard typing sequences** using position and timing heuristics
4. **Typing interview** - Asks what you typed in each detected sequence
5. **Verification interview** (optional) - Add checkpoints to validate app behavior
6. Generates `tests/{name}/test.yaml` with element labels and type commands

**Typing detection:**
- Automatically identifies keyboard typing (bottom 40% of screen)
- Asks you to provide the typed text for each sequence
- Replaces individual keyboard taps with `type` commands
- Supports submit action (Enter/Search)

**Output:** Test file with `type` commands for text input, not individual keyboard taps.

#### Verification Interview (Experimental)

After `/stop-recording`, Claude can guide you through adding verifications to your recorded test.

**How it works:**

1. **Checkpoint Detection** - Automatically identifies key moments:
   - Screen changes (perceptual hashing detects UI transitions)
   - Long waits (2+ seconds between taps indicate loading/transitions)
   - Navigation events (back button, new screens)

2. **AI Suggestions** - For each checkpoint, Claude analyzes the screenshot and suggests:
   - Screen state verifications: `verify_screen: "Login form visible"`
   - Element checks: `verify_contains: "Email"`
   - Wait conditions: `wait_for: "Submit"`

3. **Interactive Selection** - Choose verifications interactively:
   ```
   Checkpoint 1: After tapping "Login" (screen changed)

   Suggested verification:
   A) verify_screen: "Login form with email and password fields"
   B) verify_contains: "Email"
   C) wait_for: "Password"
   D) Custom verification (enter your own)
   E) Skip this checkpoint

   Your choice: A
   ```

4. **Enhanced Test Generation** - Creates test.yaml with:
   - Recorded actions (from touch events)
   - Your selected verifications at checkpoints
   - Proper structure and syntax

**Configuration:**
- Python dependencies (Pillow, imagehash) required for checkpoint detection - see [Post-Installation Setup](#post-installation-setup)
- Max 8 checkpoints per recording (prioritized by screen changes, long waits, and navigation events)
- AI suggestions powered by Claude Code conversation (no API key needed)

**Example output:**

```yaml
tests:
  - name: recorded-flow
    steps:
      - tap: "Login"
      - verify_screen: "Login form with email and password fields"
      - tap: "Email"
      - type: "user@example.com"
      - tap: "Password"
      - type: "password123"
      - tap: "Submit"
      - verify_screen: "Home screen after successful login"
```

**Note:** This is an experimental feature. Manual verification editing is always supported.

## Test File Structure

```yaml
# Configuration
config:
  app: com.your.app.package    # Required: Android package or iOS bundle ID
  device: emulator-5554         # Optional: specific device

# Runs once before all tests
setup:
  - terminate_app
  - launch_app
  - wait: 3s

# Runs once after all tests
teardown:
  - terminate_app

# Test cases
tests:
  - name: Test name here
    description: Optional description
    timeout: 60s              # Optional: default 60s
    tags: [smoke, critical]   # Optional: for filtering
    steps:
      - tap: "Button"
      - type: "text"
      - verify_screen: "Expected state"
```

## Test Folder Structure (v3.3+)

New recordings create an organized folder structure:

```
tests/
└── login-flow/
    ├── test.yaml              # Test definition
    └── recording/             # Recording artifacts (for debugging)
        ├── touch_events.json      # Raw touch data with timestamps
        ├── typing_sequences.json  # Detected keyboard typing
        ├── verifications.json     # User-selected checkpoints
        ├── recording.mp4          # Video recording
        └── screenshots/           # Extracted frames from video
            ├── step_001_before_1.png  # 300ms before action
            ├── step_001_before_2.png  # 200ms before action
            ├── step_001_before_3.png  # 100ms before action
            ├── step_001_exact.png     # At action moment
            ├── step_001_after_1.png   # 100ms after action
            ├── step_001_after_2.png   # 200ms after action
            ├── step_001_after_3.png   # 300ms after action
            └── ...
```

Note: The `tests/` folder is gitignored - test artifacts are local only.

### Recording Flow

```
/record-test login-flow

> Checking ffmpeg... OK
> Starting video recording...
> Starting touch capture...
> Recording started! Interact with your app.

*you tap and interact with the app*

/stop-recording

> Stopping capture...
> Extracting frames from video...
> Analyzing 12 touch events with vision...
> Generated tests/login-flow/test.yaml
```

**Key feature:** Frames are extracted from video for each action:
- 3 frames BEFORE (300ms, 200ms, 100ms before action)
- 1 exact frame (at action moment)
- 3 frames AFTER (100ms, 200ms, 300ms after action)

This enables accurate element identification and shows the UI response to each action.

### Running Folder-Format Tests

```bash
/run-test tests/login-flow/
/run-test tests/login-flow/ --report
```

## Available Actions

### Tap Actions

| Action | Example | Description |
|--------|---------|-------------|
| `tap` | `- tap: "Button"` | Tap element by text |
| `tap` | `- tap: [100, 200]` | Tap at pixel coordinates |
| `tap` | `- tap: ["50%", "75%"]` | Tap at percentage (cross-device) |
| `double_tap` | `- double_tap: "Element"` | Double tap |
| `long_press` | `- long_press: "Element"` | Long press (500ms default) |

### Input Actions

| Action | Example | Description |
|--------|---------|-------------|
| `type` | `- type: "Hello"` | Type into focused field |
| `swipe` | `- swipe: up` | Swipe direction (up/down/left/right) |
| `press` | `- press: back` | Press button (back, home, enter, volume_up/down) |
| `wait` | `- wait: 2s` | Wait for duration |

### App Control

| Action | Example | Description |
|--------|---------|-------------|
| `launch_app` | `- launch_app` | Launch configured app |
| `terminate_app` | `- terminate_app` | Stop configured app |
| `install_app` | `- install_app: "/path/to/app.apk"` | Install app |
| `uninstall_app` | `- uninstall_app: "com.app"` | Uninstall app |
| `open_url` | `- open_url: "https://..."` | Open URL in browser |

### Screen Actions

| Action | Example | Description |
|--------|---------|-------------|
| `set_orientation` | `- set_orientation: landscape` | Change orientation |
| `get_orientation` | `- get_orientation` | Get current orientation |
| `get_screen_size` | `- get_screen_size` | Get screen dimensions |
| `list_elements` | `- list_elements` | List all elements (debugging) |
| `screenshot` | `- screenshot: "name"` | Take screenshot |

### Verification

| Action | Example | Description |
|--------|---------|-------------|
| `verify_screen` | `- verify_screen: "Home with tabs"` | AI verifies screen state |
| `verify_contains` | `- verify_contains: "Welcome"` | Check element exists |
| `verify_no_element` | `- verify_no_element: "Error"` | Check element absent |

### Flow Control

| Action | Example | Description |
|--------|---------|-------------|
| `wait_for` | `- wait_for: "Continue"` | Wait until element appears (10s timeout) |
| `if_present` | `- if_present: "Button"` | Execute then/else based on element presence |
| `if_absent` | `- if_absent: "Error"` | Execute if element not present |
| `if_all_present` | `- if_all_present: ["A", "B"]` | Execute if ALL elements present (AND) |
| `if_any_present` | `- if_any_present: ["A", "B"]` | Execute if ANY element present (OR) |
| `if_screen` | `- if_screen: "Login page"` | Execute based on AI vision screen match |
| `if_precondition` | `- if_precondition: "logged_in"` | Execute based on precondition state |
| `retry` | `- retry: {attempts: 3, steps: [...]}` | Retry steps on failure |
| `repeat` | `- repeat: {times: 5, steps: [...]}` | Repeat steps N times |

**Backward compatibility:** Old operator names (`if_exists`, `if_not_exists`, `if_all_exist`, `if_any_exist`) are still supported but deprecated. Use the new names for clarity.

**Note:** All conditional operators (`if_*`) require `then` and optional `else` blocks. See [Conditional Logic](#conditional-logic) section for complete syntax.

## Conditional Logic

Execute steps conditionally based on runtime state. All conditionals support full nesting and then/else branches.

### Basic Conditional

```yaml
- if_present: "Skip Tutorial"
  then:
    - tap: "Skip Tutorial"
  else:
    - verify_screen: "Tutorial required"
```

### Multiple Elements (AND Logic)

```yaml
# Check if ALL buttons are present
- if_all_present: ["Save", "Share", "Edit"]
  then:
    - verify_screen: "Full editor mode active"
  else:
    - verify_screen: "Limited editing mode"
```

### Multiple Elements (OR Logic)

```yaml
# Check if ANY login button variant exists
- if_any_present: ["Login", "Sign In", "Get Started"]
  then:
    - tap: "Login"
  else:
    - verify_screen: "Already logged in"
```

### AI Vision Check

```yaml
# Use AI to verify screen state
- if_screen: "Empty gallery with no photos"
  then:
    - tap: "Import Photos"
    - wait: 5s
  else:
    - tap: "Select Photo"
```

### Nested Conditionals

```yaml
# Conditionals can be nested
- if_present: "Premium Badge"
  then:
    - if_screen: "Advanced tools visible"
      then:
        - verify_screen: "Premium features active"
      else:
        - tap: "Unlock Tools"
  else:
    - tap: "Upgrade to Premium"
```

### Key Behaviors

- **Instant evaluation**: Conditionals check current state once (no retries)
- **Use wait_for first**: If element might be loading, use `wait_for` before conditional
- **Full nesting**: Unlimited nesting depth supported
- **Step numbering**: Branch steps use decimal notation (3.1, 3.2, 3.1.1)
- **Empty else allowed**: Else branch is optional

**See:** [Conditionals Reference](skills/yaml-test-schema/references/conditionals.md) for complete syntax and examples.

## Templates

### Basic Navigation Test

```yaml
config:
  app: com.example.app

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: Navigate to Settings
    steps:
      - wait_for: "Home"
      - tap: "Settings"
      - wait: 2s
      - verify_screen: "Settings screen displayed"
      - screenshot: settings_screen
```

### Form Input Test

```yaml
config:
  app: com.example.app

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: Submit contact form
    steps:
      - wait_for: "Contact"
      - tap: "Contact"
      - wait: 1s

      - tap: "Name"
      - type: "John Doe"

      - tap: "Email"
      - type: "john@example.com"

      - tap: "Message"
      - type: "Hello, this is a test message."

      - tap: "Submit"
      - wait_for: "Thank you"
      - verify_screen: "Success confirmation displayed"
```

### Onboarding Flow Test

```yaml
config:
  app: com.example.app

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: Complete onboarding
    timeout: 120s
    steps:
      # Page 1
      - wait_for: "Welcome"
      - screenshot: onboarding_page_1
      - tap: "Next"
      - wait: 1s

      # Page 2
      - wait_for: "Features"
      - screenshot: onboarding_page_2
      - tap: "Next"
      - wait: 1s

      # Page 3
      - wait_for: "Get Started"
      - screenshot: onboarding_page_3
      - tap: "Get Started"
      - wait: 2s

      - verify_screen: "Home screen after onboarding"
```

### Handling Optional Elements

```yaml
tests:
  - name: Login with optional popup handling
    steps:
      - wait_for: "Login"

      # Handle optional notification permission popup
      - if_present: "Allow Notifications"
        then:
          - tap: "Not Now"
        else:
          - verify_screen: "No permission prompt"

      # Handle optional rate app dialog
      - if_present: "Rate our app"
        then:
          - tap: "Later"
        else:
          - verify_screen: "No rating dialog"

      - tap: "Email"
      - type: "user@example.com"
      - tap: "Password"
      - type: "password123"
      - tap: "Login"

      - wait_for: "Home"
      - verify_screen: "Logged in successfully"
```

### Retry Flaky Operations

```yaml
tests:
  - name: Upload with retry
    steps:
      - tap: "Upload"

      - retry:
          attempts: 3
          delay: 2s
          steps:
            - tap: "Select File"
            - wait: 1s
            - tap: "photo.jpg"
            - tap: "Upload"
            - wait_for: "Upload complete"

      - verify_screen: "File uploaded successfully"
```

## Asking for Help

The plugin's skill activates when you ask questions about mobile testing:

```
How do I write a mobile UI test?
What YAML actions are available?
How do I verify a screen state?
How do I handle optional popups?
What's the best way to test login flows?
```

## Documentation

- [Actions Reference](skills/yaml-test-schema/references/actions.md) - All available actions
- [Assertions Reference](skills/yaml-test-schema/references/assertions.md) - Verification actions
- [Flow Control Reference](skills/yaml-test-schema/references/flow-control.md) - wait_for, retry, repeat
- [Conditionals Reference](skills/yaml-test-schema/references/conditionals.md) - if_present, if_absent, if_all_present, if_any_present, if_screen, if_precondition

## Troubleshooting

### "No device found"

Ensure your device is connected:
```bash
# Android
adb devices

# iOS Simulator
xcrun simctl list devices | grep Booted
```

### "Element not found"

- Add `wait_for` before interacting with elements
- Check element text matches exactly (case-sensitive)
- Use `screenshot` to debug what's on screen

### "Test timeout"

- Increase timeout in test: `timeout: 120s`
- Add `wait` actions for slow operations
- Use `wait_for` instead of fixed `wait` durations

### "Video file corrupted" during recording

If you see "moov atom not found" errors:
- Ensure you use `/stop-recording` to stop (not Ctrl+C)
- The plugin sends SIGINT to screenrecord to finalize the video properly
- Check ffmpeg is installed: `ffmpeg -version`

## Contributing

Contributions welcome! Please open an issue or submit a PR.

## License

MIT
