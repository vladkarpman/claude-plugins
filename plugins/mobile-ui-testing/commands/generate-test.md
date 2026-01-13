---
name: generate-test
description: Generate a YAML test from natural language description
argument-hint: "<description>"
allowed-tools:
  - Write
  - Read
  - Glob
  - Bash
  - AskUserQuestion
---

# Generate Test - Natural Language to YAML

Convert a natural language description into a YAML test file.

## Execution Steps

### Step 1: Get Description

**If argument provided:** Use it as `{DESCRIPTION}`.

**If no argument:** Use `AskUserQuestion`:
```
Question: "Describe the test you want to create (e.g., 'user logs in with email and password, sees home screen')"
```

### Step 2: Detect App Package

**Tool:** `Glob` with pattern `tests/*/test.yaml`

**If files found:** Use `Bash`:
```bash
grep -h "app:" tests/*/test.yaml | head -1 | sed 's/.*app: *//'
```

**If no files:** Use `AskUserQuestion`:
```
Question: "What is the app package name?"
```

### Step 3: Generate Test Name

Convert description to kebab-case:
- "user logs in with email" → `user-logs-in-with-email`
- "checkout flow" → `checkout-flow`

Store as `{TEST_NAME}`.

### Step 4: Parse Actions from Description

Extract actions from the description:

| Phrase | YAML Action |
|--------|-------------|
| "tap X" / "click X" / "press X" | `- tap: "X"` |
| "type X" / "enter X" | `- type: "X"` |
| "scroll down/up" / "swipe down/up" | `- swipe: down/up` |
| "wait for X" / "see X" | `- wait_for: "X"` |
| "verify X" / "check X" | `- verify_screen: "X"` |
| "go to X" / "navigate to X" | `- tap: "X"` |

### Step 5: Create Test Folder

**Tool:** `Bash`
```bash
mkdir -p tests/{TEST_NAME}/baselines tests/{TEST_NAME}/reports
```

### Step 6: Write Test File

**Tool:** `Write` to `tests/{TEST_NAME}/test.yaml`

```yaml
# {TEST_NAME}
# Generated from: "{DESCRIPTION}"

config:
  app: {APP_PACKAGE}

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: {Readable test name}
    description: {DESCRIPTION}
    timeout: 60s
    steps:
      # Generated steps from description
      {GENERATED_STEPS}
      - verify_screen: "{Expected final state}"
```

### Step 7: Output Result

```
Generated: tests/{TEST_NAME}/test.yaml

Test: {Test name}
Steps: {count} actions

Preview:
{show first 5 steps}

Run with: /run-test tests/{TEST_NAME}/
```

## Examples

**Input:** "user logs in with email and password then sees home screen"

**Output:**
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
      - wait: 2s
      - verify_screen: "Home screen after successful login"
```

**Input:** "scroll through feed and like the first post"

**Output:**
```yaml
tests:
  - name: Like first post in feed
    steps:
      - wait_for: "Feed"
      - swipe: up
      - wait: 1s
      - tap: "Like"
      - verify_screen: "Post liked"
```

## Tips

Encourage descriptive prompts:
- Good: "user opens settings, enables dark mode, and returns to home"
- Too vague: "test settings"

If description is unclear, ask for clarification.
