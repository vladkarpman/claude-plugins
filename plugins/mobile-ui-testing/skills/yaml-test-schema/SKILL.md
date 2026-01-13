# YAML Mobile Test Schema

This skill should be used when the user wants to "write mobile UI tests", "create YAML tests", "run mobile tests", "test my app", "automate mobile app", asks about "YAML test syntax", "test actions", "verify_screen", "tap", "swipe", "wait_for", "if_exists", "retry", "mobile-mcp testing", or any mobile UI testing related queries. It provides complete knowledge of the YAML-based mobile testing format used with mobile-mcp.

## Overview

YAML mobile tests are declarative test files that Claude Code interprets and executes via mobile-mcp tools. No compilation required - just write YAML and run.

**Key benefits:**
- Human-readable test definitions
- No programming required
- AI-powered screen verification
- Works with Android and iOS

## Test File Structure

```yaml
config:
  app: com.your.app.package    # Required: Android package or iOS bundle ID
  device: emulator-5554         # Optional: auto-detect if omitted

setup:                          # Optional: runs once before all tests
  - terminate_app
  - launch_app
  - wait: 3s

teardown:                       # Optional: runs once after all tests
  - terminate_app

tests:
  - name: Test name             # Required
    description: What it tests  # Optional
    timeout: 60s                # Optional: default 60s
    tags: [smoke, critical]     # Optional: for filtering
    steps:
      - tap: "Button"
      - verify_screen: "Expected state"
```

## Quick Action Reference

### Basic Actions
| Action | Example | Description |
|--------|---------|-------------|
| Tap element | `- tap: "Continue"` | Find and tap by text |
| Tap coordinates | `- tap: [100, 200]` | Tap at x, y position |
| Double tap | `- double_tap: "Item"` | Double tap element |
| Long press | `- long_press: "Item"` | Long press (500ms) |
| Type text | `- type: "hello"` | Type into focused field |
| Type + submit | `- type: {text: "query", submit: true}` | Type and press enter |
| Swipe | `- swipe: up` | Swipe direction |
| Swipe with distance | `- swipe: {direction: up, distance: 800}` | Custom swipe |
| Press button | `- press: back` | Press back/home button |
| Wait | `- wait: 2s` | Fixed delay |

### App Control
| Action | Example | Description |
|--------|---------|-------------|
| Launch app | `- launch_app` | Start configured app |
| Launch specific | `- launch_app: "com.other.app"` | Start specific app |
| Stop app | `- terminate_app` | Stop configured app |
| Set orientation | `- set_orientation: landscape` | Change orientation |
| Open URL | `- open_url: "https://..."` | Open in browser |
| Screenshot | `- screenshot: "name"` | Capture screenshot |

### Verification
| Action | Example | Description |
|--------|---------|-------------|
| Verify screen | `- verify_screen: "Home with tabs"` | AI verifies screen matches |
| Check element | `- verify_contains: "Welcome"` | Element exists |
| Check elements | `- verify_contains: ["A", "B"]` | Multiple elements exist |
| Check absence | `- verify_no_element: "Error"` | Element not present |

### Flow Control
| Action | Example | Description |
|--------|---------|-------------|
| Wait for element | `- wait_for: "Continue"` | Wait until appears |
| Wait with timeout | `- wait_for: {element: "X", timeout: 30s}` | Custom timeout |
| If exists | `- if_exists: "Skip"` + `then: [...]` | Run if element exists |
| If not exists | `- if_not_exists: "Error"` + `then: [...]` | Run if element absent |
| If all exist | `- if_all_exist: ["A", "B"]` + `then: [...]` | Run if ALL exist (AND) |
| If any exist | `- if_any_exist: ["A", "B"]` + `then: [...]` | Run if ANY exists (OR) |
| If screen | `- if_screen: "description"` + `then: [...]` | Run if screen matches (AI) |
| Retry | `- retry: {attempts: 3, steps: [...]}` | Retry on failure |
| Repeat | `- repeat: {times: 5, steps: [...]}` | Loop N times |

## Executing Tests

When executing YAML tests, Claude maps each action to mobile-mcp tools:

| YAML Action | mobile-mcp Tools |
|-------------|------------------|
| `tap: "X"` | `mobile_list_elements_on_screen` → find element → `mobile_click_on_screen_at_coordinates` |
| `tap: [x, y]` | `mobile_click_on_screen_at_coordinates` directly |
| `type: "X"` | `mobile_type_keys` |
| `swipe: up` | `mobile_swipe_on_screen` with direction |
| `press: back` | `mobile_press_button` |
| `wait: 2s` | Pause execution |
| `launch_app` | `mobile_launch_app` with config.app |
| `terminate_app` | `mobile_terminate_app` with config.app |
| `verify_screen: "X"` | `mobile_take_screenshot` → analyze image against expectation |
| `wait_for: "X"` | Poll `mobile_list_elements_on_screen` until element found |
| `if_exists: "X"` | Check `mobile_list_elements_on_screen`, execute `then` if found |
| `if_screen: "X"` | `mobile_take_screenshot` → analyze image, execute `then` if matches |
| `screenshot: "name"` | `mobile_take_screenshot` and note the name |

## Common Patterns

### Handling Onboarding/Popups
```yaml
setup:
  - terminate_app
  - launch_app
  - wait: 3s
  # Skip through possible onboarding screens
  - repeat:
      times: 5
      steps:
        - if_any_exist: ["Continue", "Skip", "Get Started"]
          then:
            - if_exists: "Continue"
              then:
                - tap: "Continue"
            - if_exists: "Skip"
              then:
                - tap: "Skip"
            - if_exists: "Get Started"
              then:
                - tap: "Get Started"
            - wait: 500ms
```

### Wait for Async Content
```yaml
steps:
  - tap: "Load Data"
  - wait_for:
      element: "Data loaded"
      timeout: 30s
  - verify_screen: "Data displayed correctly"
```

### Scroll to Find Element
```yaml
steps:
  - repeat:
      times: 10
      until_present: "Target Item"
      steps:
        - swipe: up
        - wait: 300ms
  - tap: "Target Item"
```

## Detailed References

For complete documentation of each action type:

- **Basic Actions**: See `references/actions.md`
- **Assertions**: See `references/assertions.md`
- **Flow Control**: See `references/flow-control.md`

## Advanced Features

### Conditional Logic

Execute steps conditionally based on runtime state. All conditionals support `then` and `else` branches with full nesting.

**Available operators:**
- `if_exists: "Element"` - Check if single element exists
- `if_not_exists: "Element"` - Check if element does NOT exist
- `if_all_exist: ["A", "B"]` - Check if ALL elements exist (AND logic)
- `if_any_exist: ["A", "B"]` - Check if ANY element exists (OR logic)
- `if_screen: "description"` - Check screen state with AI vision

**See:** `references/conditionals.md` for complete syntax and examples.

**Common examples:**
```yaml
# Handle optional dialog
- if_exists: "Upgrade Dialog"
  then:
    - tap: "Maybe Later"
  else:
    - verify_screen: "No dialog shown"

# Check premium features are all present
- if_all_exist: ["Save", "Share", "Edit"]
  then:
    - verify_screen: "Premium mode active"
  else:
    - tap: "Upgrade"

# Handle UI variations (different text for same button)
- if_any_exist: ["Login", "Sign In", "Get Started"]
  then:
    - if_exists: "Login"
      then:
        - tap: "Login"
    - if_exists: "Sign In"
      then:
        - tap: "Sign In"
    - if_exists: "Get Started"
      then:
        - tap: "Get Started"

# Complex screen state check
- if_screen: "User is logged out with login form visible"
  then:
    - type: {text: "user@example.com", submit: false}
    - tap: "Next"
  else:
    - verify_screen: "Already logged in"
```

### Preconditions (Not Yet Implemented)

Define required state with automatic setup.

See: `references/preconditions.md` for design and examples.

Basic example:
```yaml
preconditions:
  - user_logged_in: true
  - user_state: premium
```

**Status:** Documentation complete, implementation planned for future release.

## Best Practices

1. **Use `wait_for` instead of `wait`** - More reliable than fixed delays
2. **Use `if_exists` for optional elements** - Handle popups gracefully
3. **Set appropriate timeouts** - AI operations need time (30s+)
4. **Capture screenshots** - Document test execution for debugging
5. **Use descriptive verifications** - "Home screen with user avatar" not just "Home"
6. **Handle flaky operations with retry** - Network calls, animations
7. **Keep tests focused** - One flow per test, not entire journeys
