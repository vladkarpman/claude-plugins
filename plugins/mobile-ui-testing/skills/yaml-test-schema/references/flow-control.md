# YAML Test Flow Control Reference

Complete reference for flow control actions in YAML mobile tests.

## Wait For Element

### Basic Wait
```yaml
- wait_for: "Continue"
```
Waits until element with text "Continue" appears on screen.

### Wait with Options
```yaml
- wait_for:
    element: "Loading complete"
    timeout: 30s        # Max wait time (default: 10s)
    poll_interval: 1s   # Check frequency (default: 500ms)
```

### Wait for Element Gone
```yaml
- wait_for_gone: "Loading spinner"
- wait_for_gone:
    element: "Please wait..."
    timeout: 60s
```

## Conditional Execution

**Note:** For comprehensive conditional logic documentation, see [conditionals.md](./conditionals.md) for all 5 operators and advanced patterns.

### If Element Exists
```yaml
- if_exists: "Skip"
  then:
    - tap: "Skip"
    - wait: 1s
```
Executes `then` steps only if element exists.

### If Element Exists with Else
```yaml
- if_exists: "Premium"
  then:
    - tap: "Premium"
  else:
    - tap: "Basic"
```

### If Element Not Exists
```yaml
- if_not_exists: "Logged In"
  then:
    - tap: "Login"
    - type: "user@example.com"
```

## Retry Logic

### Basic Retry
```yaml
- retry:
    attempts: 3
    steps:
      - tap: "Submit"
      - wait_for: "Success"
```
Retries the entire step sequence up to 3 times on failure.

### Retry with Delay
```yaml
- retry:
    attempts: 5
    delay: 2s           # Wait between attempts
    steps:
      - tap: "Refresh"
      - verify_contains: "Updated"
```

### Retry Until Success
```yaml
- retry:
    attempts: 10
    until: "Welcome"    # Stop when this element appears
    steps:
      - swipe: up
      - wait: 500ms
```

## Loops

### Repeat Fixed Times
```yaml
- repeat:
    times: 5
    steps:
      - tap: "Next"
      - wait: 1s
```

### Repeat While Element Exists
```yaml
- repeat:
    while_present: "More items"
    max_iterations: 20  # Safety limit
    steps:
      - swipe: up
      - wait: 500ms
```

### Repeat Until Element Appears
```yaml
- repeat:
    until_present: "End of list"
    max_iterations: 50
    steps:
      - swipe: up
      - wait: 300ms
```

## Timeouts

### Step-Level Timeout
```yaml
- tap: "Generate"
  timeout: 5s
```

### Action Group Timeout
```yaml
- group:
    timeout: 120s       # 2 minute timeout for entire group
    steps:
      - tap: "Start AI Generation"
      - wait_for: "Generation complete"
      - screenshot: "result"
```

## Error Handling

### Continue on Failure
```yaml
- tap: "Optional button"
  continue_on_failure: true
```
Test continues even if this step fails.

### Try-Catch Pattern
```yaml
- try:
    steps:
      - tap: "Primary action"
      - verify_screen: "Success"
  catch:
    steps:
      - screenshot: "error_state"
      - tap: "Cancel"
```

## Execution Flow

### Skip Steps Conditionally
```yaml
- skip_if_present: "Already completed"
  steps:
    - tap: "Setup"
    - tap: "Configure"
    - tap: "Complete"
```

### Break from Loop
```yaml
- repeat:
    times: 100
    steps:
      - swipe: up
      - if_present: "Target item"
        then:
          - tap: "Target item"
          - break  # Exit the loop
```

## Mobile-MCP Tool Mapping

| YAML Flow Control | Implementation |
|-------------------|----------------|
| `wait_for` | Poll `mobile_list_elements_on_screen` until found |
| `wait_for_gone` | Poll `mobile_list_elements_on_screen` until not found |
| `if_present` | Check `mobile_list_elements_on_screen`, branch |
| `retry` | Loop execution with attempt counter |
| `repeat` | Loop execution with iteration counter |
| `group` | Sequential execution with shared timeout |

## Best Practices

1. **Always set reasonable timeouts** - Don't let tests hang forever
2. **Use `if_present` for optional elements** - Dialogs, popups, promos
3. **Add safety limits to loops** - `max_iterations` prevents infinite loops
4. **Screenshot on failure** - Helps diagnose issues
5. **Use retry for flaky operations** - Network, animations
6. **Prefer `wait_for` over `wait`** - More reliable than fixed delays
