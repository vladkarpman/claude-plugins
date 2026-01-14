# Report Generation System Design

> **For Claude:** When generating test reports, follow this design exactly. Do not improvise report format or structure.

## Overview

Standardized test report generation with JSON data + HTML template approach.

**Components:**
1. **JSON Schema** - Formal test results format
2. **HTML Template** - `templates/report.html` with placeholder syntax
3. **Generator Script** - `scripts/generate-report.py`

**Data flow:**
```
Test Execution → JSON results → generate-report.py → HTML report
```

## Report Folder Structure

```
tests/reports/
└── {YYYY-MM-DD}_{test-name}/
    ├── report.json          # Source of truth
    ├── report.html          # Generated view
    └── screenshots/
        ├── step_001.png
        ├── step_002.png
        └── ...
```

## JSON Schema

### Required Fields

```yaml
test_file: string              # Path to YAML test file
device:
  id: string                   # Device identifier
  name: string                 # Human-readable name
  platform: "android"|"ios"
started_at: string             # ISO 8601 timestamp
ended_at: string               # ISO 8601 timestamp
status: "completed"|"interrupted"|"error"
summary:
  total: integer
  passed: integer
  failed: integer
  duration_seconds: number
tests: []                      # Array of test results
```

### Test Object (Required)

```yaml
tests[]:
  name: string
  status: "passed"|"failed"|"skipped"
  steps_completed: integer
  steps_total: integer
  duration_seconds: number
  steps: []                    # Array of step results
```

### Step Object (Required)

```yaml
tests[].steps[]:
  number: integer              # Step number (1, 2, 3...)
  action: string               # "tap '7'", "verify_screen '...'"
  status: "passed"|"failed"
  result: string               # Success message or error
  screenshot: string           # Relative path: "screenshots/step_001.png"
```

### Optional Fields

```yaml
device.version: string
device.type: "physical"|"emulator"
summary.skipped: integer
tests[].description: string
tests[].steps[].duration_ms: integer
tests[].failure:
  step: integer
  type: "assertion_mismatch"|"element_not_found"|"screen_state_mismatch"|"timeout"
  expected: string
  actual: string
  message: string
  available_elements: string[]
```

## Default Behavior

**Reports are enabled by default.**

```
/run-test tests/login.test.yaml            → Generates report
/run-test tests/login.test.yaml --no-report → Skips report
```

### Configuration

In `.claude/mobile-ui-testing.yaml`:

```yaml
# Report generation (default: true)
generate_reports: true

# Screenshot capture mode (default: all)
# - all: Capture after every step
# - failures: Only capture on failed steps
# - none: No screenshots
screenshots: "all"
```

## HTML Template

### Placeholder Syntax

```
{{field}}                      → Direct value replacement
{{#each items}}...{{/each}}    → Loop over array
{{#if condition}}...{{/if}}    → Conditional block
```

### Template Structure

```html
<!-- Header -->
{{testFile}}, {{timestamp}}, {{device.name}}, {{device.platform}}

<!-- Summary cards -->
{{summary.total}}, {{summary.passed}}, {{summary.failed}}, {{summary.duration_seconds}}

<!-- Test list -->
{{#each tests}}
  {{name}}, {{status}}, {{description}}
  {{steps_completed}}/{{steps_total}}, {{duration_seconds}}

  <!-- Steps (expandable) -->
  {{#each steps}}
    {{number}}, {{action}}, {{status}}, {{result}}
    {{#if screenshot}}<img src="{{screenshot}}">{{/if}}
  {{/each}}

  <!-- Failure details -->
  {{#if failure}}
    {{failure.type}}, {{failure.message}}
    {{failure.expected}}, {{failure.actual}}
  {{/if}}
{{/each}}
```

### Status Colors

| Status | Color | Hex |
|--------|-------|-----|
| passed | Green | #10b981 |
| failed | Red | #ef4444 |
| skipped | Gray | #6b7280 |

## Generator Script

### Usage

```bash
python3 scripts/generate-report.py <json_path> [--output <html_path>]

# Default output: same directory as JSON, named report.html
python3 scripts/generate-report.py tests/reports/2026-01-14_calc/report.json
# → tests/reports/2026-01-14_calc/report.html
```

### Requirements

- Python 3.8+
- No external dependencies (stdlib only: json, re, pathlib)

### Responsibilities

1. Load JSON from input path
2. Load HTML template from `$CLAUDE_PLUGIN_ROOT/templates/report.html`
3. Process placeholders:
   - Replace `{{field}}` with values
   - Expand `{{#each}}` loops
   - Evaluate `{{#if}}` conditionals
4. Write HTML to output path

## Screenshot Capture

### Timing

Capture screenshot **after every action completes**, before moving to next step.

### Naming Convention

```
screenshots/step_{NNN}.png
```

Where NNN is zero-padded step number (001, 002, ...).

### Storage

Screenshots stored relative to report folder. JSON references them as relative paths:

```json
{
  "screenshot": "screenshots/step_001.png"
}
```

## Implementation Checklist

- [ ] Create `scripts/generate-report.py`
- [ ] Update `templates/report.html` with step-level details
- [ ] Update `/run-test` command to:
  - [ ] Collect step-level results
  - [ ] Capture screenshots after each step
  - [ ] Write JSON report
  - [ ] Call generate-report.py
  - [ ] Default reports on, `--no-report` to skip
- [ ] Update `scripts/load-config.py` to handle new options
- [ ] Update CLAUDE.md with report documentation
