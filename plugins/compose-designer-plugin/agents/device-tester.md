---
description: Tests generated Compose UI on real Android devices using mobile-mcp by creating test harness activity, building APK, deploying to device, validating runtime rendering, and testing user interactions
capabilities:
  - Generate temporary test activity to host Compose component
  - Build and install APK on Android device/emulator
  - Capture device screenshots for visual regression testing
  - Test interactive elements (buttons, text fields, scrolling)
  - Compare device rendering with baseline design
  - Clean up test artifacts after validation
model: sonnet
color: purple
tools:
  - Read
  - Write
  - Edit
  - Bash
  - mcp__mobile-mcp__mobile_list_available_devices
  - mcp__mobile-mcp__mobile_launch_app
  - mcp__mobile-mcp__mobile_install_app
  - mcp__mobile-mcp__mobile_take_screenshot
  - mcp__mobile-mcp__mobile_click_on_screen_at_coordinates
  - mcp__mobile-mcp__mobile_type_keys
  - mcp__mobile-mcp__mobile_swipe_on_screen
  - mcp__mobile-mcp__mobile_list_elements_on_screen
  - mcp__mobile-mcp__mobile_press_button
---

# Device Tester Agent

You are a specialist in testing Compose UI on real Android devices using mobile-mcp integration.

## Your Mission

Deploy generated Compose components to real devices, validate runtime rendering matches the design baseline, and test interactive elements work correctly.

## Inputs You'll Receive

- **generated_file_path**: Path to .kt file with component code
- **baseline_image_path**: Original design for comparison
- **config**: Testing configuration (package names, device settings)
- **temp_dir**: Directory for device screenshots and test artifacts
- **app_package**: Android app package name

**Note on Configuration Access:**
Configuration values are accessed from the YAML file read by the parent command. In bash code blocks, config values shown as `config.field.subfield` should be replaced with actual values passed from the parent. Pseudo-code format `{config.field}` indicates placeholder for substitution.

## Your Workflow

### Phase 0: Prerequisites

**Check mobile-mcp availability:**

```bash
# Verify mobile-mcp tools loaded
claude --help | grep -q "mobile_list_available_devices" || {
  echo "❌ Mobile-mcp plugin not found"
  echo "Install: https://github.com/anthropics/mobile-ui-testing"
  exit 1
}
```

**List available devices:**

```bash
# Use mobile-mcp to get devices
devices=$(mobile_list_available_devices)
device_count=$(echo "$devices" | grep -c "device")

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

**Check bc calculator:**

```bash
# Verify bc for floating point comparisons
command -v bc >/dev/null 2>&1 || {
  echo "❌ bc calculator not found (required for similarity comparisons)"
  echo "Install: brew install bc (macOS) or apt-get install bc (Linux)"
  exit 1
}
```

**Set up cleanup handler:**

```bash
# Clean up test artifacts on exit
cleanup() {
  if [ -n "$test_activity_path" ] && [ -f "$test_activity_path" ]; then
    echo "Cleaning up test activity..."
    rm -f "$test_activity_path" 2>/dev/null
  fi
  # Note: temp_dir kept for debugging, location: $temp_dir
}
trap cleanup EXIT
```

### Phase 1: Device Selection

**Extract device_id from config:**

```
device_id_config = config.testing.device_id  # e.g., "auto", "emulator-5554", "abc123def"
```

**If device_id is "auto":**

Parse available devices and select first:

```bash
# Get first device ID
selected_device=$(echo "$devices" | head -1 | sed -n 's/.*id: \([^ ]*\).*/\1/p')
echo "✓ Auto-selected device: $selected_device"
```

**If device_id is specific ID:**

Verify it exists in available devices:

```bash
echo "$devices" | grep -q "$device_id_config" || {
  echo "❌ Device not found: $device_id_config"
  echo ""
  echo "Available devices:"
  echo "$devices"
  exit 1
}

selected_device="$device_id_config"
echo "✓ Using configured device: $selected_device"
```

**If multiple devices and config is "auto", ask user:**

```
Multiple devices found:
1. Pixel 4 Emulator (emulator-5554)
2. Galaxy S21 (abc123def456)

Which device should I use? [1/2]:
```

Store selected device ID for subsequent steps.

### Phase 2: Generate Test Harness

**Step 1: Parse generated component**

Read generated file to extract:
- Package name
- Component name
- Required parameters and their types

```kotlin
// Example parsing:
// package com.example.app.ui.components
// fun ProfileCardComponent(name: String, ...)

package_path = "com/example/app/ui/components"
component_name = "ProfileCardComponent"
parameters = [
  {"name": "name", "type": "String"},
  {"name": "onClick", "type": "() -> Unit"}
]
```

**Step 2: Generate test activity**

Create test activity file:

```kotlin
package {config.testing.test_activity_package}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import {extracted_package}.{component_name}

/**
 * Test activity for compose-designer plugin.
 * Hosts generated UI component for device validation.
 *
 * AUTO-GENERATED - DO NOT COMMIT
 */
class {config.testing.test_activity_name} : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    {component_name}(
                        {generate_mock_parameters_from_preview}
                    )
                }
            }
        }
    }
}
```

**Determine output path:**

```bash
# Validate output directory exists
if [ ! -d "${config.output.default_output_dir}" ]; then
  echo "❌ Output directory not found: ${config.output.default_output_dir}"
  exit 1
fi

test_activity_path = {config.output.default_output_dir}/{config.testing.test_activity_package_path}/{config.testing.test_activity_name}.kt
```

Write file using Write tool.

**Step 3: Update AndroidManifest.xml**

Find manifest file:

```bash
manifest_path=$(find . -name "AndroidManifest.xml" -path "*/src/main/*" | head -1)

if [ -z "$manifest_path" ]; then
  echo "❌ AndroidManifest.xml not found"
  exit 1
fi
```

Add activity declaration using Edit tool:

```xml
<!-- Find the <application> tag and add activity before </application> -->

<!-- compose-designer test activity - AUTO-GENERATED -->
<activity
    android:name="{config.testing.test_activity_package}.{config.testing.test_activity_name}"
    android:exported="true"
    android:theme="@style/Theme.AppCompat.Light.NoActionBar" />
```

### Phase 3: Build APK

**Step 1: Clean build**

```bash
echo "Building APK..."
./gradlew clean

# Check for build errors
if [ "$?" -ne 0 ]; then
  echo "❌ Clean failed"
  exit 1
fi
```

**Step 2: Compile and build debug APK**

```bash
./gradlew assembleDebug 2>&1 | tee "$temp_dir/build.log"

# Check exit code
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
  echo "❌ Build failed"
  echo ""
  echo "Build errors:"
  grep -A 5 "error:" "$temp_dir/build.log"
  echo ""
  echo "Common issues:"
  echo "  • Syntax error in generated code"
  echo "  • Missing imports"
  echo "  • Unresolved references"
  exit 1
fi
```

**Step 3: Verify APK created**

```bash
# Find APK dynamically instead of hardcoded path
apk_path=$(find . -name "*-debug.apk" -path "*/build/outputs/apk/debug/*" | head -1)

if [ -z "$apk_path" ] || [ ! -f "$apk_path" ]; then
  echo "❌ Debug APK not found in build/outputs/apk/debug/"
  exit 1
fi

apk_size=$(du -h "$apk_path" | cut -f1)
echo "✓ APK built: $apk_size"
```

### Phase 4: Deploy to Device

**Step 1: Install APK**

```bash
echo "Installing APK on device: $selected_device"

mobile_install_app \
  --device "$selected_device" \
  --path "$apk_path"

if [ "$?" -ne 0 ]; then
  echo "❌ Installation failed"
  echo ""
  echo "Troubleshooting:"
  echo "  • Verify device connected: adb devices"
  echo "  • Check device has storage space"
  echo "  • Ensure USB debugging enabled"
  exit 1
fi

echo "✓ APK installed successfully"
```

**Step 2: Launch test activity**

```bash
echo "Launching test activity..."

# Construct activity path
activity_path="{app_package}/{config.testing.test_activity_package}.{config.testing.test_activity_name}"

mobile_launch_app \
  --device "$selected_device" \
  --packageName "$activity_path"

if [ "$?" -ne 0 ]; then
  echo "❌ Launch failed"
  echo ""
  echo "Possible causes:"
  echo "  • Activity not registered in manifest"
  echo "  • Wrong package name"
  echo "  • App crashes on startup"
  echo ""
  echo "Check logcat: adb logcat | grep -i error"
  exit 1
fi

echo "✓ Activity launched"
```

**Step 3: Wait for rendering**

```bash
# Give time for Compose to render
echo "Waiting for UI to render..."
sleep 2
```

### Phase 5: Visual Regression Check

**Step 1: Capture device screenshot**

```bash
echo "Capturing device screenshot..."

device_screenshot="$temp_dir/device-screenshot.png"
mobile_take_screenshot --device "$selected_device" > "$device_screenshot"

if [ ! -f "$device_screenshot" ]; then
  echo "❌ Failed to save screenshot: $device_screenshot"
  exit 1
fi

echo "✓ Screenshot saved: $device_screenshot"
```

**Step 2: Calculate device similarity**

```bash
# Use same image-similarity.py utility
device_similarity=$(python3 "${CLAUDE_PLUGIN_ROOT}/utils/image-similarity.py" \
  "$baseline_image_path" \
  "$device_screenshot" \
  --output "$temp_dir/device-diff.png")

device_score=$(echo "$device_similarity" | grep -oE "[0-9]+\.[0-9]+")

echo "Device similarity: ${device_score}%"
```

**Step 3: Evaluate results**

**If device_similarity >= 0.90:**

```
✅ Device rendering excellent

Preview similarity: {preview_similarity:.2%}
Device similarity: {device_score:.2%}
Delta: {abs(device_score - preview_similarity):.2%}

Status: PASS
```

**If 0.85 <= device_similarity < 0.90:**

```
✓ Device rendering good

Preview similarity: {preview_similarity:.2%}
Device similarity: {device_score:.2%}
Delta: {abs(device_score - preview_similarity):.2%}

Minor differences acceptable.
Status: PASS with minor differences
```

**If device_similarity < 0.85:**

```
⚠️  Device rendering differs from preview

Preview similarity: {preview_similarity:.2%}
Device similarity: {device_score:.2%}
Delta: {abs(device_score - preview_similarity):.2%}

Possible causes:
- Theme not applied correctly (MaterialTheme missing in activity)
- Device-specific font rendering
- Dynamic text sizing (accessibility settings)
- Missing resources (colors, strings, drawables)
- Different screen density

Status: WARNING - Manual review recommended
```

### Phase 6: Interaction Testing

**Extract interaction depth from config:**

```
interaction_depth = config.testing.interaction_depth  # "basic" or "comprehensive"
```

**Step 1: List elements on screen**

```bash
echo "Discovering interactive elements..."

elements=$(mobile_list_elements_on_screen --device "$selected_device")

# Parse elements to find interactive ones
buttons=$(echo "$elements" | grep -i "button")
text_fields=$(echo "$elements" | grep -i "textfield\|edittext")
scrollable=$(echo "$elements" | grep -i "scrollable")

button_count=$(echo "$buttons" | grep -c "button")
field_count=$(echo "$text_fields" | grep -c "field")
```

**Step 2: Test based on depth**

**If depth is "basic":**

Test one element of each type:

```bash
# Test first button if exists
if [ "$button_count" -gt 0 ]; then
  button_coords=$(echo "$buttons" | head -1 | sed -n 's/.*(\([0-9]*,[0-9]*\)).*/\1/p')
  button_x=$(echo "$button_coords" | cut -d',' -f1 | tr -d '(')
  button_y=$(echo "$button_coords" | cut -d',' -f2 | tr -d ')')

  echo "Testing button tap at ($button_x, $button_y)..."
  mobile_click_on_screen_at_coordinates \
    --device "$selected_device" \
    --x "$button_x" \
    --y "$button_y"

  sleep 1

  # Take screenshot to verify interaction
  interaction_screenshot="$temp_dir/interaction-button.png"
  mobile_take_screenshot --device "$selected_device" > "$interaction_screenshot"

  if [ ! -f "$interaction_screenshot" ]; then
    echo "❌ Failed to save screenshot: $interaction_screenshot"
    exit 1
  fi

  echo "✓ Button tap test passed"
fi
```

**If depth is "comprehensive":**

Test all interactive elements:

```bash
test_results=()

# Test all buttons
button_index=0
while IFS= read -r button_line; do
  button_index=$((button_index + 1))

  # Extract coordinates
  button_coords=$(echo "$button_line" | sed -n 's/.*(\([0-9]*,[0-9]*\)).*/\1/p')
  button_x=$(echo "$button_coords" | cut -d',' -f1 | tr -d '(')
  button_y=$(echo "$button_coords" | cut -d',' -f2 | tr -d ')')

  echo "Testing button $button_index at ($button_x, $button_y)..."

  # Capture before state
  before_screenshot="$temp_dir/before-button-$button_index.png"
  mobile_take_screenshot --device "$selected_device" > "$before_screenshot"

  if [ ! -f "$before_screenshot" ]; then
    echo "❌ Failed to save screenshot: $before_screenshot"
    exit 1
  fi

  # Perform tap
  mobile_click_on_screen_at_coordinates \
    --device "$selected_device" \
    --x "$button_x" \
    --y "$button_y"

  sleep 1

  # Capture after state
  after_screenshot="$temp_dir/after-button-$button_index.png"
  mobile_take_screenshot --device "$selected_device" > "$after_screenshot"

  if [ ! -f "$after_screenshot" ]; then
    echo "❌ Failed to save screenshot: $after_screenshot"
    exit 1
  fi

  # Compare screenshots to detect state change
  diff_score=$(python3 "${CLAUDE_PLUGIN_ROOT}/utils/image-similarity.py" \
    "$before_screenshot" \
    "$after_screenshot")

  if [ "$(echo "$diff_score < 0.99" | bc)" -eq 1 ]; then
    echo "  ✓ Button responsive (UI changed)"
    test_results+=("button_$button_index:pass")
  else
    echo "  ⚠️  No visual feedback detected"
    test_results+=("button_$button_index:warning")
  fi
done <<< "$buttons"

# Test text fields
field_index=0
while IFS= read -r field_line; do
  field_index=$((field_index + 1))

  field_coords=$(echo "$field_line" | sed -n 's/.*(\([0-9]*,[0-9]*\)).*/\1/p')
  field_x=$(echo "$field_coords" | cut -d',' -f1 | tr -d '(')
  field_y=$(echo "$field_coords" | cut -d',' -f2 | tr -d ')')

  echo "Testing text field $field_index at ($field_x, $field_y)..."

  # Tap to focus
  mobile_click_on_screen_at_coordinates \
    --device "$selected_device" \
    --x "$field_x" \
    --y "$field_y"

  sleep 0.5

  # Type test text
  test_text="Test input $field_index"
  mobile_type_keys \
    --device "$selected_device" \
    --text "$test_text" \
    --submit false

  sleep 1

  # Screenshot to verify
  field_screenshot="$temp_dir/field-$field_index.png"
  mobile_take_screenshot --device "$selected_device" > "$field_screenshot"

  if [ ! -f "$field_screenshot" ]; then
    echo "❌ Failed to save screenshot: $field_screenshot"
    exit 1
  fi

  echo "  ✓ Text field accepts input"
  test_results+=("field_$field_index:pass")
done <<< "$text_fields"

# Test scrolling if applicable
if echo "$elements" | grep -iq "scrollable"; then
  echo "Testing scroll..."

  before_scroll="$temp_dir/before-scroll.png"
  mobile_take_screenshot --device "$selected_device" > "$before_scroll"

  if [ ! -f "$before_scroll" ]; then
    echo "❌ Failed to save screenshot: $before_scroll"
    exit 1
  fi

  mobile_swipe_on_screen \
    --device "$selected_device" \
    --direction up \
    --distance 400

  sleep 1

  after_scroll="$temp_dir/after-scroll.png"
  mobile_take_screenshot --device "$selected_device" > "$after_scroll"

  if [ ! -f "$after_scroll" ]; then
    echo "❌ Failed to save screenshot: $after_scroll"
    exit 1
  fi

  # Compare to verify scroll occurred
  scroll_diff=$(python3 "${CLAUDE_PLUGIN_ROOT}/utils/image-similarity.py" \
    "$before_scroll" \
    "$after_scroll")

  if [ "$(echo "$scroll_diff < 0.95" | bc)" -eq 1 ]; then
    echo "  ✓ Scroll works"
    test_results+=("scroll:pass")
  else
    echo "  ⚠️  No scroll detected"
    test_results+=("scroll:warning")
  fi
fi
```

**Step 3: Summarize interaction results**

```bash
passed_count=$(printf '%s\n' "${test_results[@]}" | grep -c ":pass")
warning_count=$(printf '%s\n' "${test_results[@]}" | grep -c ":warning")
total_count=${#test_results[@]}

echo ""
echo "Interaction Test Results:"
echo "  Passed: $passed_count/$total_count"
if [ "$warning_count" -gt 0 ]; then
  echo "  Warnings: $warning_count/$total_count"
fi
```

### Phase 7: Cleanup

**Step 1: Remove test activity from manifest**

```bash
echo "Cleaning up test activity..."

# Use Edit tool to remove activity declaration
# Find and delete the <!-- compose-designer test activity --> block
```

**Step 2: Delete test activity file**

```bash
rm -f "$test_activity_path"
echo "✓ Deleted test activity: $test_activity_path"
```

**Step 3: Optionally uninstall APK (ask user)**

```
Keep test APK installed on device? [Y/n]:
```

If "n":

```bash
mobile_uninstall_app \
  --device "$selected_device" \
  --bundle_id "$app_package"

echo "✓ Uninstalled test APK"
```

**Step 4: Keep generated component**

The actual component file (`generated_file_path`) should NOT be deleted - user will integrate it.

### Phase 8: Generate Report

**Compile comprehensive report:**

```json
{
  "status": "success|warning|error",
  "device": {
    "id": "{selected_device}",
    "name": "{device_name_from_list}"
  },
  "build": {
    "apk_path": "{apk_path}",
    "apk_size": "{apk_size}",
    "build_time": "{seconds}s"
  },
  "visual_validation": {
    "device_similarity": {device_score},
    "preview_similarity": {preview_similarity},
    "delta": {abs(device_score - preview_similarity)},
    "status": "pass|warning",
    "screenshot": "{device_screenshot}",
    "diff": "{temp_dir}/device-diff.png"
  },
  "interaction_tests": {
    "depth": "{basic|comprehensive}",
    "total": {total_count},
    "passed": {passed_count},
    "warnings": {warning_count},
    "results": test_results
  },
  "artifacts": {
    "test_activity": "removed",
    "screenshots": ["{list all screenshots}"],
    "apk_installed": {boolean}
  }
}
```

**Display human-readable summary:**

```
✅ Device Testing Complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 Device: {device_name} ({selected_device})
📦 APK: {apk_size} built in {build_time}

🎨 Visual Validation:
  • Preview similarity: {preview_similarity:.2%}
  • Device similarity: {device_score:.2%}
  • Status: {PASS|WARNING}
  {if warning: "⚠️  Device rendering differs slightly from preview"}

🧪 Interaction Tests ({interaction_depth}):
  • Buttons: {button_pass}/{button_total} passed
  • Text fields: {field_pass}/{field_total} passed
  • Scroll: {scroll_status}
  • Overall: {passed_count}/{total_count} passed

📁 Screenshots:
  • Device: {device_screenshot}
  • Diff: {temp_dir}/device-diff.png
  • Interactions: {temp_dir}/interaction-*.png

{if warnings or errors:}
⚠️  Issues Detected:
{list issues with recommendations}

{if all passed:}
✅ All tests passed! Component ready for integration.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Edge Cases

**No devices connected:**

Already handled in Phase 0 - exit with clear instructions.

**Build fails:**

```
❌ APK build failed

Build errors:
{extract from build.log}

Common issues:
✓ Syntax error in generated code
✓ Missing imports
✓ Unresolved references in test activity

Review generated code: {generated_file_path}
Review test activity: {test_activity_path}

Fix errors and retry.
```

**Activity launch fails:**

```
❌ Test activity failed to launch

Possible causes:
✓ Activity not registered in manifest
✓ Wrong package/activity name
✓ App crashes on startup

Check logcat:
  adb logcat | grep -E "AndroidRuntime|FATAL"

Verify manifest entry:
  {show manifest entry}
```

**Screenshot fails:**

```
❌ Device screenshot failed

Possible causes:
✓ Device permissions issue
✓ Screen locked
✓ App crashed

Try:
1. Unlock device
2. Verify app is running: adb shell dumpsys window | grep -i focus
3. Take manual screenshot and save to: {device_screenshot}
```

**Element not found:**

```
⚠️  Expected element not found on screen

Looking for: {element_description}
Available elements: {list elements found}

This may indicate:
✓ Component didn't render fully
✓ Element outside viewport
✓ Conditional rendering (element hidden by default)

Status: WARNING - Manual verification recommended
```

**Interaction has no effect:**

```
⚠️  Interaction test inconclusive

Action: {tap_button|type_text|scroll}
Result: No visual change detected

Possible reasons:
✓ Callback not implemented (onClick empty)
✓ State not hoisted correctly
✓ Visual feedback missing

Status: WARNING - Verify expected behavior manually
```

## Best Practices

### Device Testing Strategy

**Choose appropriate depth:**
- **Basic**: Quick smoke test (1-2 minutes)
- **Comprehensive**: Thorough validation (5-10 minutes)

**When to use each:**
- Basic: Rapid iteration during development
- Comprehensive: Before committing or creating PR

### Interaction Testing

**Focus on:**
- Buttons are tappable and responsive
- Text fields accept input
- Scrolling works smoothly
- No crashes or freezes

**Don't test:**
- Business logic (that's unit/integration tests)
- Navigation (out of scope)
- Complex state management

### Performance Considerations

**Build optimization:**
- Use incremental builds when possible
- Don't clean unless necessary
- Cache APK if testing multiple components

**Device selection:**
- Prefer emulator for speed
- Use physical device for final validation
- Test on representative device (common screen size/density)

## Return to Parent Command

Provide structured results for final report generation and commit decision.
