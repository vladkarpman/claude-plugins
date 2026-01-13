---
name: create-test
description: Create a new YAML test file with proper structure
argument-hint: <test-name>
allowed-tools:
  - Write
  - Read
  - Glob
  - Bash
  - AskUserQuestion
---

# Create Test - Scaffold New Test File

Create a new YAML test file from template.

## Execution Steps

### Step 1: Get Test Name

**If argument provided:** Use it as `{TEST_NAME}`.

**If no argument:** Use `AskUserQuestion`:
```
Question: "What would you like to name this test? (e.g., login, onboarding, checkout)"
```

### Step 2: Detect App Package

**Tool:** `Glob` with pattern `tests/*/test.yaml`

**If files found:** Use `Bash`:
```bash
grep -h "app:" tests/*/test.yaml | head -1 | sed 's/.*app: *//'
```
Store result as `{APP_PACKAGE}`.

**If no files:** Use `AskUserQuestion`:
```
Question: "What is the app package name? (e.g., com.example.app)"
```

### Step 3: Create Test Folder

**Tool:** `Bash`
```bash
mkdir -p tests/{TEST_NAME}/baselines tests/{TEST_NAME}/reports
```

### Step 4: Write Test File

**Tool:** `Write` to `tests/{TEST_NAME}/test.yaml`

```yaml
# {TEST_NAME} Test
# Created: {TODAY_DATE}

config:
  app: {APP_PACKAGE}

setup:
  - terminate_app
  - launch_app
  - wait: 3s

teardown:
  - terminate_app

tests:
  - name: {TEST_NAME}
    description: Add description here
    timeout: 60s
    steps:
      # Add your test steps here
      # Examples:
      # - tap: "Button"
      # - type: "Input text"
      # - swipe: up
      # - wait: 1s
      # - verify_screen: "Expected state"
      - wait: 1s
      - screenshot: "initial_state"
```

### Step 5: Output Success

```
Created: tests/{TEST_NAME}/test.yaml

Next steps:
  1. Edit the file to add your test steps
  2. Run with: /run-test tests/{TEST_NAME}/

Quick reference:
  - tap: "Button"       Tap element by text
  - type: "text"        Type into focused field
  - swipe: up           Swipe direction
  - wait: 2s            Wait for duration
  - wait_for: "X"       Wait until element appears
  - verify_screen: "X"  Verify screen state
```

## Folder Structure

```
tests/{TEST_NAME}/
├── test.yaml
├── baselines/
└── reports/
```
