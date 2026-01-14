# Device Selection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add flexible device selection with CLI override and interactive picker for compose-designer plugin.

**Architecture:** Priority chain: CLI `--device` → config `device_id` → auto-select single device → interactive picker for multiple devices.

**Tech Stack:** Markdown (Claude Code plugin commands/agents), YAML frontmatter, AskUserQuestion tool

---

## Task 1: Add --device Argument to Create Command

**Files:**
- Modify: `commands/create.md:4` (argument-hint line)
- Modify: `commands/create.md:318-343` (Phase 4 device-tester invocation)

**Step 1: Update argument-hint**

In `commands/create.md`, change line 4 from:
```
argument-hint: --input <path|url> --name <ComponentName> --type <component|screen> [--clipboard] [--batch]
```

To:
```
argument-hint: --input <path|url> --name <ComponentName> --type <component|screen> [--clipboard] [--batch] [--device <device-id>]
```

**Step 2: Update device-tester agent invocation**

In `commands/create.md`, find the device-tester Task tool invocation (around line 320) and add `device_override` parameter:

Change from:
```
Task tool:
  subagent_type: "compose-designer:device-tester"
  description: "Test UI on device"
  prompt: "Test generated Compose component in {output_file_path} on Android device.

  Config:
  - Test package: {config.testing.test_activity_package}
  - Test activity: {config.testing.test_activity_name}
  - Device ID: {config.testing.device_id}
  - Interaction depth: {config.testing.interaction_depth}
```

To:
```
Task tool:
  subagent_type: "compose-designer:device-tester"
  description: "Test UI on device"
  prompt: "Test generated Compose component in {output_file_path} on Android device.

  Config:
  - Test package: {config.testing.test_activity_package}
  - Test activity: {config.testing.test_activity_name}
  - Device ID: {config.testing.device_id}
  - Device override (CLI): {device_argument or 'none'}
  - Interaction depth: {config.testing.interaction_depth}
```

**Step 3: Verify syntax**

Read the file and ensure YAML frontmatter is valid.

**Step 4: Commit**

```bash
git add commands/create.md
git commit -m "feat(compose-designer): add --device CLI argument to create command"
```

---

## Task 2: Update Device-Tester Agent Selection Logic

**Files:**
- Modify: `agents/device-tester.md:108-153` (Phase 1: Device Selection)

**Step 1: Replace Phase 1 content**

In `agents/device-tester.md`, replace the entire "### Phase 1: Device Selection" section (lines 108-153) with:

```markdown
### Phase 1: Device Selection

**Inputs you'll receive for device selection:**
- `device_override`: Device ID from CLI `--device` flag (or "none")
- `config.testing.device_id`: From YAML config ("auto" or specific ID)

**Selection priority chain:**

```
1. CLI --device flag (highest priority)
       ↓ (not provided or "none")
2. Config device_id (if not "auto")
       ↓ (is "auto")
3. Single device → use automatically
       ↓ (multiple devices)
4. Interactive picker
```

**Step 1: List available devices**

Use mobile-mcp tool:

```bash
# Get available devices
devices=$(mcp__mobile-mcp__mobile_list_available_devices)
device_count=$(echo "$devices" | grep -c "id:")

if [ "$device_count" -eq 0 ]; then
  echo "❌ No Android devices found"
  echo ""
  echo "Connect a device:"
  echo "  • Physical: Enable USB debugging in Developer Options"
  echo "  • Emulator: Launch from Android Studio → Tools → AVD Manager"
  echo ""
  echo "Verify: adb devices"
  exit 1
fi

echo "Found $device_count device(s)"
```

**Step 2: Apply selection priority**

**Priority 1 - CLI override:**

If `device_override` is provided and not "none":

```bash
# Verify CLI-specified device exists
if ! echo "$devices" | grep -q "$device_override"; then
  echo "❌ Device not found: $device_override"
  echo ""
  echo "Available devices:"
  echo "$devices" | grep "id:" | sed 's/^/  • /'
  echo ""
  echo "Fix: Use one of the above IDs"
  exit 1
fi

selected_device="$device_override"
echo "✓ Using CLI-specified device: $selected_device"
```

**Priority 2 - Config device_id:**

Else if `config.testing.device_id` is not "auto":

```bash
device_id_config="{config.testing.device_id}"

# Verify config-specified device exists
if ! echo "$devices" | grep -q "$device_id_config"; then
  echo "❌ Device not found: $device_id_config"
  echo ""
  echo "Available devices:"
  echo "$devices" | grep "id:" | sed 's/^/  • /'
  echo ""
  echo "Fix: Update testing.device_id in .claude/compose-designer.yaml"
  echo "     Or set to 'auto' for automatic selection"
  exit 1
fi

selected_device="$device_id_config"
echo "✓ Using config-specified device: $selected_device"
```

**Priority 3 - Auto-select single device:**

Else if only one device available:

```bash
selected_device=$(echo "$devices" | grep "id:" | head -1 | sed 's/.*id: \([^ ]*\).*/\1/')
echo "✓ Auto-selected device: $selected_device"
```

**Priority 4 - Interactive picker:**

Else (multiple devices, no specific selection):

Use AskUserQuestion tool to let user choose:

```
Multiple devices found. Which one to use for testing?

Options built from device list:
- Each device as an option with id and name
- Example: "Pixel 4 API 33 (emulator-5554)"
```

After user selects:

```bash
selected_device="{user_selected_device_id}"
echo "✓ User selected device: $selected_device"
```

**Step 3: Store selected device**

The `selected_device` variable is now set and will be used in subsequent phases.
```

**Step 2: Verify markdown structure**

Read the file and ensure section headers are properly nested.

**Step 3: Commit**

```bash
git add agents/device-tester.md
git commit -m "feat(compose-designer): implement device selection priority chain

- CLI --device flag (highest priority)
- Config testing.device_id (if not 'auto')
- Auto-select when single device
- Interactive picker for multiple devices"
```

---

## Task 3: Verify and Test

**Step 1: Validate plugin structure**

```bash
./tests/validate-plugin.sh
```

Expected: All checks pass.

**Step 2: Manual review**

Read both modified files to verify:
- argument-hint includes `[--device <device-id>]`
- device-tester agent has full priority chain logic
- Error messages are clear and actionable

**Step 3: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix(compose-designer): address validation issues"
```

---

## Summary

| Task | File | Change |
|------|------|--------|
| 1 | `commands/create.md` | Add `--device` argument, pass to agent |
| 2 | `agents/device-tester.md` | Replace Phase 1 with priority chain |
| 3 | Both | Validate and test |

**Total commits:** 2-3 (one per task, plus optional fix)
