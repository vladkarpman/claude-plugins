# Device Selection Design

## Problem

The compose-designer plugin needs flexible device selection for testing:
- Users want to specify a device via CLI without editing config
- When multiple devices are available, users should choose which one to use
- The current `testing.device_id: "auto"` behavior needs refinement

## Solution

Implement a priority-based device selection chain.

## Selection Logic

```
CLI --device flag
       ↓ (not provided)
Config testing.device_id (if not "auto")
       ↓ (is "auto")
Single device available → use automatically
       ↓ (multiple devices)
Interactive picker
```

### Priority Chain

1. **CLI flag (`--device`)** - Highest priority, explicit override
2. **Config (`testing.device_id`)** - If set to specific ID (not "auto")
3. **Auto-selection** - If only one device available
4. **Interactive picker** - When multiple devices and no specific device provided

### Validation

- If specified device (via CLI or config) doesn't exist → error with available devices list
- If no devices available → error with setup instructions

## Implementation

### Files to Modify

1. `commands/create.md` - Add `--device` argument
2. `agents/device-tester.md` - Update Phase 1 device selection logic

### Command Argument

```yaml
# In create.md frontmatter
arguments:
  - name: device
    description: Device ID for testing (overrides config)
    required: false
```

### Device-Tester Agent Logic

**Inputs:**
- `device_override`: Device ID from CLI `--device` flag (optional)
- `config.testing.device_id`: From YAML config

**Selection:**

```
1. If device_override provided:
   - Verify device exists in available list
   - Error if not found
   - Use it

2. Else if config.testing.device_id != "auto":
   - Verify device exists
   - Error if not found
   - Use it

3. Else (config is "auto"):
   - List available devices
   - If count == 0: Error with setup instructions
   - If count == 1: Use automatically
   - If count > 1: Show interactive picker
```

### Interactive Picker

Use `AskUserQuestion` tool when multiple devices available:

```
Multiple devices found. Which one to use for testing?

1. Pixel 4 API 33 (emulator-5554)
2. Samsung Galaxy S21 (R3CN...)
```

## Error Messages

### Device Not Found

```
❌ Device not found: {specified_id}

Available devices:
  • emulator-5554 (Pixel 4 API 33)
  • R3CN... (Samsung Galaxy S21)

Fix: Use one of the above IDs, or set device_id: "auto" in config
```

### No Devices Available

```
❌ No Android devices found

Connect a device:
  • Physical: Enable USB debugging in Developer Options
  • Emulator: Launch from Android Studio → Tools → AVD Manager

Verify: adb devices
```

## Scope

**Changes:**
- `commands/create.md` - Add `--device` argument
- `agents/device-tester.md` - Update Phase 1 selection logic

**No changes:**
- Config schema (already has `testing.device_id`)
- Other agents (design-generator, visual-validator, baseline-preprocessor)
