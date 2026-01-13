# Conditional Logic Reference

**Implementation Status:** ✅ Fully implemented (Phase 1)

**Available Operators:**
- ✅ `if_exists` - Single element check
- ✅ `if_not_exists` - Inverse element check
- ✅ `if_all_exist` - Multiple elements (AND logic)
- ✅ `if_any_exist` - Multiple elements (OR logic)
- ✅ `if_screen` - AI vision-based screen matching

**Future Operators (Phase 2):**
- 🔄 `if_element_enabled` - Element state check (requires mobile-mcp support)
- 🔄 `if_orientation` - Device orientation check
- 🔄 `if_network` - Network connectivity check

Conditionals allow tests to branch based on runtime screen state, enabling handling of optional dialogs, varied app states, and dynamic UI flows.

## Syntax

All conditionals use the same structure:

```yaml
- condition_type: "Element Text" or ["x", "y"]
  then:
    - action: value
    - action: value
  else:  # optional
    - action: value
```

## Available Conditionals

### if_exists

Execute `then` block if element is found on screen, `else` block otherwise.

```yaml
- if_exists: "Enable Notifications"
  then:
    - tap: "Enable Notifications"
  else:
    - tap: "Continue"
```

**When to use:**
- Optional permission dialogs
- Conditional UI elements (banners, prompts)
- A/B tested features

### if_not_exists

Inverse of `if_exists` - execute `then` block if element is NOT found.

```yaml
- if_not_exists: "Login"
  then:
    - tap: "Account"
    - tap: "Logout"
    - wait_for: "Login"
```

**When to use:**
- Ensure logged-out state
- Skip already-completed setup steps
- Detect missing expected elements (error states)

### if_all_exist

Execute `then` block only if ALL specified elements are present.

```yaml
- if_all_exist:
    - "Email"
    - "Password"
    - "Login"
  then:
    - type_in: { element: "Email", text: "user@example.com" }
    - type_in: { element: "Password", text: "password123" }
    - tap: "Login"
```

**When to use:**
- Verify complete form/screen loaded
- Multi-element state checks
- Compound prerequisites

### if_any_exist

Execute `then` block if ANY of the specified elements are present.

```yaml
- if_any_exist:
    - "Rate Us"
    - "Leave Review"
    - "Not Now"
  then:
    - tap: "Not Now"
```

**When to use:**
- Handle multiple possible dialog variations
- Dismiss any of several interrupt screens
- Detect presence of error messages (where text varies)

### if_screen

Execute `then` block if screen matches AI-analyzed description.

```yaml
- if_screen: "Login screen with email and password fields"
  then:
    - type_in: { element: "Email", text: "user@example.com" }
    - tap: "Login"
  else:
    - tap: "Logout"
    - wait_for: "Login"
```

**When to use:**
- Complex screen state detection (multiple indicators)
- When element text is unreliable (images, icons)
- Contextual understanding needed (e.g., "error state")

**Performance note:** AI vision analysis is slower than element checks. Prefer `if_exists` when possible.

### if_element_enabled (Not Yet Implemented)

**Status:** Deferred to Phase 2 (requires mobile-mcp support)

**Reason:** The mobile-mcp `list_elements_on_screen` tool doesn't expose element enabled/disabled state. This operator will be added when the underlying tool supports it.

**Workaround:** Use `if_exists` combined with `verify_screen` for clickability checks:

```yaml
- if_exists: "Submit Button"
  then:
    - verify_screen: "Submit button is enabled and clickable"
    - tap: "Submit Button"
```

**Planned usage (when implemented):**
```yaml
- if_element_enabled: "Submit"
  then:
    - tap: "Submit"
  else:
    - tap: "Email"
    - type: "user@example.com"
    - wait_until_enabled: "Submit"
    - tap: "Submit"
```

**When to use (future):**
- Check form validation state
- Detect interactive vs disabled buttons
- Conditional interaction based on element state

## Use Cases

### Optional Permission Dialogs

Handle OS permission prompts that may not appear (already granted):

```yaml
- tap: "Enable Location"
- if_exists: "Allow"
  then:
    - tap: "Allow"
# Continue regardless of whether permission prompt appeared
- wait_for: "Map View"
```

### State Branching

Different flows based on user state (logged in vs out):

```yaml
- if_exists: "Profile Picture"
  then:
    # Already logged in
    - tap: "Settings"
  else:
    # Need to log in first
    - tap: "Login"
    - type_in: { element: "Email", text: "user@example.com" }
    - tap: "Submit"
    - wait_for: "Profile Picture"
    - tap: "Settings"
```

### Error Handling

Detect and recover from error states:

```yaml
- tap: "Submit"
- if_any_exist:
    - "Network Error"
    - "Server Unavailable"
    - "Retry"
  then:
    - tap: "Retry"
    - wait: 2s
    - tap: "Submit"
```

### Onboarding Flows

Skip tutorial screens that don't show on repeat sessions:

```yaml
- launch_app
- if_exists: "Get Started"
  then:
    # First time user flow
    - tap: "Get Started"
    - tap: "Next"
    - tap: "Next"
    - tap: "Done"
  else:
    # Returning user - already on home screen
    - verify_screen: "Home screen with navigation bar"
```

### Multi-Variant Testing

Handle A/B tested UI differences:

```yaml
- if_exists: "New Dashboard"
  then:
    # Test variant A
    - tap: "New Dashboard"
    - tap: "Analytics"
  else:
    # Test variant B (or control)
    - tap: "Dashboard"
    - swipe: { direction: "down" }
    - tap: "Analytics"
```

## Best Practices

### ✅ DO

**Use element checks for simple presence/absence:**

```yaml
- if_exists: "Allow Notifications"
  then:
    - tap: "Allow Notifications"
```

**Chain conditionals for complex flows:**

```yaml
- if_not_exists: "Login"
  then:
    - if_exists: "Profile"
      then:
        - tap: "Profile"
        - tap: "Logout"
```

**Prefer specific element text over screen descriptions:**

```yaml
# Good
- if_exists: "Continue"
  then:
    - tap: "Continue"

# Avoid (slower)
- if_screen: "Screen with continue button"
  then:
    - tap: "Continue"
```

**Use `if_any_exist` for variant handling:**

```yaml
- if_any_exist:
    - "Got It"
    - "OK"
    - "Dismiss"
  then:
    - tap: "Got It"  # Will tap whichever exists
```

### ❌ DON'T

**Don't nest conditionals more than 2 levels deep:**

```yaml
# Too complex - hard to read and maintain
- if_exists: "A"
  then:
    - if_exists: "B"
      then:
        - if_exists: "C"
          then:
            - tap: "D"
```

**Don't use conditionals for deterministic flows:**

```yaml
# Bad - login flow is always the same
- if_exists: "Login"
  then:
    - tap: "Login"

# Good - just tap it
- tap: "Login"
```

**Don't use `if_screen` when element checks suffice:**

```yaml
# Slow - uses AI vision
- if_screen: "Login screen"
  then:
    - tap: "Login"

# Fast - direct element check
- if_exists: "Login"
  then:
    - tap: "Login"
```

**Don't rely on conditionals for flaky waits:**

```yaml
# Bad - hiding timing issues
- if_exists: "Loading"
  then:
    - wait: 5s

# Good - explicit wait for loaded state
- wait_for: "Content Loaded"
```

## Execution Behavior

### Instant Evaluation

Conditionals perform instant checks without retries or polling:

```yaml
# ✓ GOOD: Wait first, then check
- wait_for: "Home"
- if_exists: "Upgrade Dialog"
  then:
    - tap: "Maybe Later"

# ✗ BAD: Relying on conditional to wait
- if_exists: "Upgrade Dialog"  # May execute before element appears
  then:
    - tap: "Maybe Later"
```

If you need to wait for an element before checking conditions, use `wait_for` explicitly.

### Nesting Support

Conditionals support unlimited nesting depth:

```yaml
- if_exists: "A"
  then:
    - if_exists: "B"
      then:
        - if_exists: "C"
          then:
            - tap: "Deep nested action"
```

**Best practice:** Keep nesting to 2-3 levels maximum for readability.

### Error Handling

- **Malformed syntax** (missing `then` key): Test fails immediately
- **API failures** (element list retrieval, screenshot): Condition treated as false, test continues
- **Empty branches**: Valid no-op, continues to next step
- **Nested failures**: Inner conditional failures don't affect outer conditionals

### Step Numbering

Branch steps use decimal notation:

```
[3/8] if_exists "Dialog"
      ✓ Condition true, executing then branch (2 steps)
[3.1/8] tap "OK"
        ✓ Tapped at (540, 800)
[3.2/8] wait 1s
        ✓ Waited 1.0 seconds
[4/8] verify_screen "Dialog closed"
```

## When to Use Conditionals vs Separate Tests

### Use Conditionals When:

- ✅ Same test needs to handle optional interrupts (permission dialogs)
- ✅ App state varies between test runs (logged in vs out)
- ✅ Testing graceful degradation (network errors)
- ✅ A/B test variants need single test coverage

### Use Separate Tests When:

- ✅ Testing distinct features (login vs checkout)
- ✅ Different setup requirements (logged in vs logged out)
- ✅ Failure isolation needed (one path failing shouldn't block other)
- ✅ Conditional logic becomes complex (>2 levels deep)

**Example - Bad (overuse of conditionals):**

```yaml
# Single test doing too much
- if_exists: "Login"
  then:
    # 20 steps for login flow
    - ...
  else:
    - if_exists: "Shopping Cart"
      then:
        # 15 steps for checkout flow
        - ...
      else:
        # 10 steps for browsing flow
        - ...
```

**Example - Good (separate tests):**

```yaml
# login.test.yaml
tests:
  - name: User Login
    steps:
      - tap: "Login"
      - ...

# checkout.test.yaml
tests:
  - name: Checkout Flow
    setup:
      - run_test: "login.test.yaml"  # Reuse login
    steps:
      - tap: "Cart"
      - ...
```

## Implementation Notes

- Element checks (`if_exists`, `if_all_exist`, etc.) use the same element resolution as `tap` and `wait_for`
- Screen checks (`if_screen`) invoke AI vision analysis (slower, use sparingly)
- Nested conditionals are supported but discouraged beyond 2 levels
- `else` block is always optional - test continues after conditional block
- Conditionals do not affect test pass/fail - use `verify_*` assertions for validation

## Examples by Complexity

### Simple: Optional Dialog

```yaml
- tap: "Sign Up"
- if_exists: "Allow Tracking"
  then:
    - tap: "Allow"
# No else needed - continue either way
```

### Medium: State-Based Flow

```yaml
- if_not_exists: "Dashboard"
  then:
    # Need to log in first
    - tap: "Login"
    - type_in: { element: "Email", text: "user@example.com" }
    - tap: "Submit"
    - wait_for: "Dashboard"
# Now guaranteed to be on Dashboard
- tap: "Settings"
```

### Advanced: Multi-Path Handling

```yaml
- tap: "Checkout"
- if_all_exist:
    - "Name"
    - "Address"
    - "Payment Method"
  then:
    # Guest checkout flow
    - type_in: { element: "Name", text: "John Doe" }
    - type_in: { element: "Address", text: "123 Main St" }
    - tap: "Continue"
  else:
    - if_exists: "Login to Continue"
      then:
        # Requires login
        - tap: "Login"
        - type_in: { element: "Email", text: "user@example.com" }
        - tap: "Submit"
        - wait_for: "Checkout"
      else:
        # Already logged in, form pre-filled
        - tap: "Continue"
```

## Example Test Files

See working examples in:
- `tests/integration/examples/conditional-basic.test.yaml` - All 5 operators with simple examples
- `tests/integration/examples/conditional-nested.test.yaml` - 2-3 level nesting demonstrations
- `tests/integration/examples/conditional-screen.test.yaml` - AI vision-based conditionals

Run examples:
```bash
/run-test tests/integration/examples/conditional-basic.test.yaml
/run-test tests/integration/examples/conditional-nested.test.yaml
/run-test tests/integration/examples/conditional-screen.test.yaml
```
