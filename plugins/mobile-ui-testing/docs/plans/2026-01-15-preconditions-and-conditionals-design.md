# Preconditions + Conditional Steps Design

**Goal:** Enable conditional branching in recorded tests through preconditions (reusable state setup flows) and conditional steps (if/then/else logic in approval UI).

**Architecture:** Two interconnected systems - preconditions for state management, conditional steps for runtime branching. Preconditions are recorded separately and referenced by tests. Conditional steps are defined during approval UI review.

**Tech Stack:** YAML configuration, JavaScript approval UI updates, Python generation script updates, command markdown updates.

---

## User Flow

### Precondition Creation

```
User runs /record-precondition premium_user
    ↓
Claude starts recording (same as /record-test)
    ↓
User performs steps to reach premium state:
  • Launch app
  • Navigate to debug menu
  • Enable premium features
    ↓
User runs /stop-recording
    ↓
Claude generates tests/preconditions/premium_user.yaml
    ↓
Precondition available for use in tests
```

### Test with Preconditions + Conditionals

```
User runs /record-test my-feature-test
    ↓
User performs test actions
    ↓
User runs /stop-recording
    ↓
Approval UI opens
    ↓
User reviews steps, marks some as conditional:
  • Toggle conditional on step
  • Select condition type (if_present, if_precondition, etc.)
  • Set condition value
    ↓
User clicks "Export YAML"
    ↓
Generated YAML includes:
  • config.precondition reference
  • Conditional steps with if/then/else
```

---

## Part 1: Preconditions System

### What is a Precondition?

A named, reusable flow that establishes a specific app state. Preconditions are defined once and referenced by multiple tests. They represent states like:
- `logged_in` - User is authenticated
- `premium_user` - Premium features enabled
- `fresh_install` - App data cleared, first launch
- `onboarding_complete` - Tutorial finished

### File Location

```
tests/
├── preconditions/           # Precondition definitions
│   ├── logged_in.yaml
│   ├── premium_user.yaml
│   └── fresh_install.yaml
├── login/
│   └── test.yaml            # References preconditions
└── checkout/
    └── test.yaml
```

### Precondition File Format

```yaml
# tests/preconditions/premium_user.yaml
name: premium_user
description: "App state with premium features enabled via debug menu"

# Steps to reach this state
steps:
  - launch_app
  - tap: "Debug Menu"
  - tap: "Enable Premium"
  - verify_screen: "Premium badge visible"

# Runtime verification (for if_precondition checks)
verify:
  element: "Premium Badge"
  # OR for complex states:
  # screen: "Dashboard showing premium badge and analytics tab"
```

**Fields:**
- `name` (required): Identifier used to reference this precondition
- `description` (optional): Human-readable explanation
- `steps` (required): Actions to reach this state
- `verify` (required): How to check if this state is active at runtime

### Creating Preconditions

**Command:** `/record-precondition {name}`

**Flow:**
1. User runs `/record-precondition premium_user`
2. Recording starts (video + touch capture, same as `/record-test`)
3. User performs steps to reach desired state
4. User runs `/stop-recording`
5. Generated file: `tests/preconditions/premium_user.yaml`
6. User edits `verify` section to define runtime check

**Alternative:** Manual YAML creation for power users.

### Using Preconditions in Tests

**Single precondition:**
```yaml
config:
  app: com.example.app
  precondition: premium_user
```

**Multiple preconditions (sequential execution):**
```yaml
config:
  app: com.example.app
  preconditions:
    - fresh_install
    - logged_in
    - premium_user
```

### Precondition Execution

**Execution order:**
1. Preconditions run in specified order
2. Each builds on previous state (no app restart between unless precondition does it)
3. All preconditions must succeed for test to proceed
4. Then test steps execute

**Timeline:**
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ fresh_install│ → │  logged_in   │ → │ premium_user │ → │  TEST STEPS  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

**Error handling:**
- Precondition step failure = test failure
- No partial execution (if precondition fails midway, test doesn't run)

---

## Part 2: Conditional Operators

### Operator Naming (Migration)

**New naming scheme** (clearer semantics):

| Old Name | New Name | Description |
|----------|----------|-------------|
| `if_exists` | `if_present` | Element is visible on screen |
| `if_not_exists` | `if_absent` | Element is NOT visible |
| `if_all_exist` | `if_all_present` | ALL listed elements visible |
| `if_any_exist` | `if_any_present` | ANY listed element visible |
| `if_screen` | `if_screen` | AI vision screen match (unchanged) |
| NEW | `if_precondition` | Precondition state is active |

**Backward compatibility:** Old names continue to work (aliased to new names).

### Conditional Syntax

**Basic if/then:**
```yaml
- if_present: "Element Text"
  then:
    - tap: "Action"
```

**With else branch:**
```yaml
- if_present: "Premium Badge"
  then:
    - tap: "Premium Features"
  else:
    - tap: "Upgrade"
```

**Negation:**
```yaml
- if_absent: "Error Message"
  then:
    - verify_screen: "Success state"
```

**Multiple elements:**
```yaml
- if_all_present:
    - "Email Field"
    - "Password Field"
    - "Login Button"
  then:
    - type: "user@example.com"
    - tap: "Login Button"

- if_any_present:
    - "Dismiss"
    - "Not Now"
    - "Skip"
  then:
    - tap: "Dismiss"
```

**Precondition check:**
```yaml
- if_precondition: premium_user
  then:
    - tap: "Advanced Analytics"
    - verify_screen: "Analytics dashboard"
  else:
    - verify_screen: "Upgrade prompt"
```

**Screen description (AI vision):**
```yaml
- if_screen: "Login form with email and password fields"
  then:
    - type: "test@example.com"
```

### Nesting

Conditionals can be nested (up to 3 levels recommended):

```yaml
- if_present: "Dialog"
  then:
    - if_precondition: premium_user
      then:
        - tap: "Premium Action"
      else:
        - tap: "Free Action"
```

### Step Numbering

Conditional steps use decimal notation in output:

```
[1/5] tap "Start"
[2/5] if_present "Rate Dialog"
      ✓ Condition true, executing then branch
[2.1/5] tap "Not Now"
        ✓ Tapped at (540, 800)
[3/5] tap "Continue"
```

---

## Part 3: Approval UI Changes

### Step Card Conditional Section

Each step card gets a collapsible "Conditional" section:

```
┌─────────────────────────────────────────────────────────────┐
│  Step 3: tap "Dismiss"                             [Delete] │
│  ═══════════════════════════════════════════════════════════│
│  [Before] → [Action] → [After]                              │
│                                                             │
│  Analysis: Tapped dismiss button on ad dialog               │
│                                                             │
│  ┌─ CONDITIONAL ─────────────────────────────────── [✓] ───┐│
│  │                                                         ││
│  │  Type: [if_present ▼]                                   ││
│  │                                                         ││
│  │  Check for: [ Dismiss           ]  ← auto-filled        ││
│  │                                                         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  💡 Suggested verification: "Ad dismissed"  [+ Add]         │
│                                                             │
│  [↑ Move] [↓ Move]  Wait after: [0] ms                      │
└─────────────────────────────────────────────────────────────┘
```

### Condition Type Dropdown

| Option | Input Field | Description |
|--------|-------------|-------------|
| `if_present` | Text input | Check if element exists |
| `if_absent` | Text input | Check if element doesn't exist |
| `if_all_present` | Multi-line text | Check all elements exist |
| `if_any_present` | Multi-line text | Check any element exists |
| `if_precondition` | Dropdown | Select from available preconditions |
| `if_screen` | Text area | Describe expected screen state |

### Auto-Fill Behavior

When conditional toggle is enabled:
- For `tap` steps: Condition value auto-fills with tap target text
- For other steps: Condition value is empty (user fills in)

### Multi-Step Grouping

User can group consecutive steps under single conditional:

1. **Select mode:** Click checkbox on first step, shift+click on last
2. **Group button:** "Wrap as conditional" button appears
3. **Configure:** Single condition applies to all selected steps
4. **Result:** Steps nested under single `if_x` block

**Visual:**
```
┌─ GROUP: if_present "Tutorial" ───────────────────────────────┐
│  Step 2: tap "Next"                                          │
│  Step 3: tap "Next"                                          │
│  Step 4: tap "Got It"                                        │
│                                                      [Ungroup]│
└──────────────────────────────────────────────────────────────┘
```

---

## Part 4: Data Structures

### Embedded in approval.html

```json
{
  "testName": "dashboard-test",
  "appPackage": "com.example.app",
  "precondition": "premium_user",
  "availablePreconditions": ["logged_in", "premium_user", "fresh_install"],
  "steps": [
    {
      "id": "step_001",
      "timestamp": 2.34,
      "action": "tap",
      "target": { "text": "Dashboard", "x": 406, "y": 1645 },
      "conditional": null,
      "frames": { "before": [...], "after": [...] },
      "analysis": { "before": "...", "action": "...", "after": "..." }
    },
    {
      "id": "step_002",
      "timestamp": 3.12,
      "action": "tap",
      "target": { "text": "Dismiss", "x": 540, "y": 800 },
      "conditional": {
        "type": "if_present",
        "value": "Dismiss",
        "else": null
      },
      "frames": { ... },
      "analysis": { ... }
    }
  ]
}
```

### Generated YAML Output

```yaml
config:
  app: com.example.app
  precondition: premium_user

tests:
  - name: dashboard-test
    steps:
      - tap: "Dashboard"

      - if_present: "Dismiss"
        then:
          - tap: "Dismiss"

      - if_precondition: premium_user
        then:
          - tap: "Analytics"
          - verify_screen: "Charts visible"
        else:
          - verify_screen: "Upgrade prompt"

      - tap: "Settings"
```

---

## Part 5: Implementation Files

### Files to Create

| File | Description |
|------|-------------|
| `commands/record-precondition.md` | New command for recording preconditions |
| `skills/yaml-test-schema/references/preconditions.md` | Precondition documentation |
| `templates/precondition.yaml` | Template for precondition files |

### Files to Modify

| File | Changes |
|------|---------|
| `commands/stop-recording.md` | Handle precondition recording end state |
| `commands/run-test.md` | Execute preconditions before test, add `if_precondition` operator, migrate operator names |
| `templates/approval.html` | Add conditional UI (toggle, type dropdown, value input, grouping) |
| `scripts/generate-approval.py` | Include available preconditions, handle conditional data |
| `skills/yaml-test-schema/references/conditionals.md` | Update operator names, add `if_precondition` |
| `CLAUDE.md` | Document preconditions and new operators |

---

## Success Criteria

### Preconditions

1. ✓ User can record preconditions via `/record-precondition {name}`
2. ✓ Precondition saved to `tests/preconditions/{name}.yaml`
3. ✓ Test can reference single precondition: `config.precondition`
4. ✓ Test can reference multiple preconditions: `config.preconditions` (array)
5. ✓ Preconditions execute in order before test steps
6. ✓ Precondition failure stops test execution

### Conditional Steps

1. ✓ Approval UI shows conditional toggle on each step
2. ✓ User can select condition type from dropdown
3. ✓ Condition value auto-fills for tap steps
4. ✓ User can edit condition value
5. ✓ User can group multiple steps under single conditional
6. ✓ Export generates correct YAML with if/then/else structure

### Operator Migration

1. ✓ New operator names work: `if_present`, `if_absent`, `if_all_present`, `if_any_present`
2. ✓ Old operator names work (backward compatibility): `if_exists`, `if_not_exists`, etc.
3. ✓ `if_precondition` operator works at runtime
4. ✓ Documentation updated with new names

### Runtime

1. ✓ `/run-test` loads precondition files
2. ✓ `/run-test` executes precondition steps
3. ✓ `/run-test` evaluates `if_precondition` by checking verify.element/screen
4. ✓ All conditional operators work correctly
