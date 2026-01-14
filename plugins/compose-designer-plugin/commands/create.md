---
name: create
description: Generate Compose code from design input (screenshot/Figma/clipboard) through three-phase workflow
argument-hint: --input <path|url> --name <ComponentName> --type <component|screen> [--clipboard] [--batch] [--device <device-id>]
allowed-tools:
  - Read
  - Write
  - Bash
  - Task
  - TodoWrite
  - AskUserQuestion
---

# Compose Designer: Create

Generate Jetpack Compose code from design input with automated validation and device testing.

## Usage Examples

```bash
# From screenshot
/compose-design create --input screenshot.png --name ProfileCard --type component

# From Figma
/compose-design create --input "https://www.figma.com/file/ABC?node-id=1:234" --name LoginScreen --type screen

# From clipboard
/compose-design create --clipboard --name QuickButton --type component

# Batch from folder
/compose-design create --input ./designs/ --batch
```

## Instructions for Claude

### Phase 0: Setup and Validation

**Step 1: Load configuration**

```bash
# Check if config exists
if [ ! -f .claude/compose-designer.yaml ]; then
  echo "Configuration not found. Run: /compose-design config"
  exit 1
fi
```

Read and parse configuration using Read tool.

**Step 2: Validate arguments**

Check required arguments:
- `--name` must be provided
- `--type` must be "component" or "screen"
- If `--batch`: `--input` must be directory
- If `--clipboard`: ignore `--input` argument

Exit with clear error if validation fails.

**Step 3: Validate dependencies**

Check required tools are available:

```bash
# Check Python packages
python3 -c "import skimage, PIL, numpy" 2>/dev/null || {
  echo "❌ Required Python packages missing"
  echo "Install: pip3 install scikit-image pillow numpy"
  exit 1
}

# Check Gradle
./gradlew --version >/dev/null 2>&1 || {
  echo "❌ Gradle not found"
  echo "Ensure you're in an Android project root"
  exit 1
}
```

**Step 4: Create task list**

Use TodoWrite to create workflow tasks:

```json
[
  {"content": "Load configuration and validate inputs", "status": "in_progress", "activeForm": "Loading configuration and validating inputs"},
  {"content": "Process design input (Phase 0)", "status": "pending", "activeForm": "Processing design input"},
  {"content": "Generate initial Compose code (Phase 1)", "status": "pending", "activeForm": "Generating initial Compose code"},
  {"content": "Visual validation with ralph-wiggum (Phase 2)", "status": "pending", "activeForm": "Running visual validation"},
  {"content": "Device testing with mobile-mcp (Phase 3)", "status": "pending", "activeForm": "Testing on device"},
  {"content": "Generate final report", "status": "pending", "activeForm": "Generating final report"}
]
```

### Phase 1: Design Input Processing

**Step 1: Process input source**

**If image file:**
```bash
# Verify file exists
if [ ! -f "$input_path" ]; then
  echo "❌ Image file not found: $input_path"
  exit 1
fi

# Create temp directory
temp_dir=$(mktemp -d /tmp/compose-designer.XXXXXX)
timestamp=$(basename "$temp_dir")

# Copy to baseline
cp "$input_path" "$temp_dir/baseline.png"
```

**If Figma URL:**
```bash
# Parse Figma URL
figma_file_id=$(echo "$input_url" | sed -n 's|.*file/\([^/?]*\).*|\1|p')
figma_node_id=$(echo "$input_url" | sed -n 's|.*node-id=\([^&]*\).*|\1|p')

# Check if Figma token available
if [ "$figma_extract_tokens" = "true" ]; then
  # Try environment variable first
  token="${FIGMA_TOKEN:-}"

  # If not found and config source is "config"
  if [ -z "$token" ] && [ "$figma_api_token_source" = "config" ]; then
    if [ -n "$figma_api_token" ]; then
      token="$figma_api_token"
    fi
  fi

  # If still not found, prompt user
  if [ -z "$token" ]; then
    echo "Figma token not found. Get token from: https://www.figma.com/settings"
    read -s -p "Enter Figma token (or press Enter to skip token extraction): " token; echo
  fi

  # If token provided, extract
  if [ -n "$token" ]; then
    # Use figma-client.sh utility (to be created)
    bash "${CLAUDE_PLUGIN_ROOT}/utils/figma-client.sh" export \
      "$input_url" \
      "$temp_dir/baseline.png"
  fi
fi

# Fallback to image if no token or extraction failed
if [ ! -f "$temp_dir/baseline.png" ]; then
  if [ "$figma_fallback_to_image" = "true" ]; then
    echo "⚠️  Falling back to image-only mode"
    echo "Please screenshot the Figma frame and save to: $temp_dir/baseline.png"
    read -p "Press Enter when ready..."
  else
    echo "❌ Figma extraction failed and fallback disabled"
    exit 1
  fi
fi
```

**If clipboard:**
```bash
# macOS clipboard to file
osascript -e 'the clipboard as «class PNGf»' | \
  perl -ne 'print pack "H*", substr($_,11,-3)' > "$temp_dir/baseline.png"

# Verify clipboard had image
if [ ! -s "$temp_dir/baseline.png" ]; then
  echo "❌ No image found in clipboard"
  exit 1
fi
```

**Step 2: Update todo**

Mark "Process design input" as completed, start "Generate initial Compose code".

### Phase 2: Code Generation (design-generator agent)

**Step 1: Invoke design-generator agent**

Use Task tool to launch agent:

```
Task tool:
  subagent_type: "compose-designer:design-generator"
  description: "Generate Compose code from design"
  prompt: "Generate Compose code for {name} ({type}) from baseline image at {baseline_path}.

  Config:
  - Package: {config.output.package_base}
  - Output dir: {config.output.default_output_dir}
  - Component suffix: {config.naming.component_suffix}
  - Screen suffix: {config.naming.screen_suffix}
  - Extract theme: {config.output.extract_theme_from_existing}

  Create the composable function and preview in: {output_file_path}"
```

**Step 2: Wait for agent completion**

Agent will return:
- Generated file path
- Component structure summary
- Any warnings or issues

**Step 3: Verify output**

```bash
# Check file was created
if [ ! -f "$output_file_path" ]; then
  echo "❌ Code generation failed"
  exit 1
fi

# Verify it compiles
./gradlew compileDebugKotlin
```

**Step 4: Update todo**

Mark "Generate initial Compose code" as completed, start "Visual validation".

### Phase 3: Visual Validation (visual-validator agent)

**Step 1: Check ralph-wiggum availability**

```bash
# Check if ralph-wiggum plugin is available
claude --help | grep -q "ralph-loop" || {
  echo "⚠️  Ralph-wiggum plugin not found"
  echo "Install: https://github.com/anthropics/ralph-wiggum-plugin"
  read -p "Skip validation phase? [y/N]: " skip
  [ "$skip" = "y" ] && return 0
}
```

**Step 2: Invoke visual-validator agent**

Use Task tool with ralph-wiggum integration:

```
Task tool:
  subagent_type: "compose-designer:visual-validator"
  description: "Validate UI visual accuracy"
  prompt: "Refine Compose code in {output_file_path} to match baseline {baseline_path}.

  Validation:
  - Target similarity: {config.validation.visual_similarity_threshold}
  - Max iterations: {config.validation.max_ralph_iterations}
  - Preview delay: {config.validation.preview_screenshot_delay}

  Use ralph-wiggum loop to iteratively improve until similarity threshold reached.
  Save preview screenshots and diffs to: {temp_dir}/"
```

**Step 3: Review validation results**

Agent will return:
- Final similarity score
- Iteration count
- Status (PASS/WARNING/FAIL)
- Diff image paths

**Step 4: Handle validation outcome**

If similarity < threshold:
```
Ask user: "Visual validation incomplete. Similarity: {score} (target: {threshold}).

Options:
1. Continue to device testing (accept current quality)
2. Manual refinement (I'll help you improve the code)
3. Adjust threshold (change config and retry)
4. Abort workflow

What would you like to do? [1/2/3/4]: "
```

**Step 5: Update todo**

Mark "Visual validation" as completed, start "Device testing".

### Phase 4: Device Testing (device-tester agent)

**Step 1: Check mobile-mcp availability**

```bash
# Check if mobile-mcp tools available
claude --help | grep -q "mobile_list_available_devices" || {
  echo "⚠️  Mobile-mcp plugin not found"
  echo "Install: https://github.com/anthropics/mobile-ui-testing"
  read -p "Skip device testing? [y/N]: " skip
  [ "$skip" = "y" ] && return 0
}
```

**Step 2: Check device availability**

```bash
# List available devices
devices=$(mobile_list_available_devices)
device_count=$(echo "$devices" | wc -l)

if [ "$device_count" -eq 0 ]; then
  echo "❌ No Android devices found"
  echo ""
  echo "Connect a device:"
  echo "  • Physical: Enable USB debugging"
  echo "  • Emulator: Launch from Android Studio"
  echo ""
  read -p "Skip device testing? [y/N]: " skip
  [ "$skip" = "y" ] && return 0
  exit 1
fi
```

**Step 3: Invoke device-tester agent**

Use Task tool:

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

  Steps:
  1. Generate test activity
  2. Build and install APK
  3. Launch and capture screenshot
  4. Test interactions (buttons, fields, etc.)
  5. Clean up test activity

  Compare device screenshot with baseline: {baseline_path}
  Save artifacts to: {temp_dir}/"
```

**Step 4: Review testing results**

Agent will return:
- Device similarity score
- Interaction test results (passed/failed)
- Any runtime issues
- Screenshot paths

**Step 5: Update todo**

Mark "Device testing" as completed, start "Generate final report".

### Phase 5: Final Report and Commit

**Step 1: Generate comprehensive report**

Compile results from all phases:

```
✅ Design-to-Code Complete: {ComponentName}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 Phase 1: Code Generation
✓ Input: {input_source}
✓ Baseline: {baseline_path}
✓ Generated: {output_file_path}
✓ Lines of code: {loc}
✓ Components: {component_count}

🎨 Phase 2: Visual Validation
✓ Method: Ralph-wiggum loop
✓ Iterations: {iteration_count}/{max_iterations}
✓ Final similarity: {similarity_score:.2%} (target: {threshold:.2%})
✓ Status: {PASS/WARNING}
{if WARNING: "⚠️  Similarity below threshold but acceptable"}

📱 Phase 3: Device Testing
✓ Device: {device_name}
✓ Runtime similarity: {device_similarity:.2%}
✓ Interactions tested: {interaction_count}
✓ Interactions passed: {passed_count}/{interaction_count}
{if failures: "⚠️  Failed: {failed_interactions}"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Generated Files:
  • Component: {output_file_path}
  • Baseline: {baseline_path}
  • Artifacts: {temp_dir}/
    - preview-iteration-*.png
    - diff-iteration-*.png
    - device-screenshot.png

📋 Next Steps:
  [ ] Review generated code
  [ ] Integrate into your feature module
  [ ] Add real data/ViewModel integration
  [ ] Connect callbacks to business logic
  [ ] Run project-specific tests

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Step 2: Ask about commit**

Use AskUserQuestion:

```json
{
  "questions": [{
    "question": "Review complete. Would you like to commit the generated code?",
    "header": "Commit",
    "options": [
      {
        "label": "Yes, commit now (Recommended)",
        "description": "Commit generated code with detailed message"
      },
      {
        "label": "Review first, commit later",
        "description": "I'll review the code manually before committing"
      },
      {
        "label": "Regenerate with different config",
        "description": "Adjust settings and try again"
      }
    ],
    "multiSelect": false
  }]
}
```

**Step 3: Commit if approved**

If user approves:

```bash
git add "$output_file_path"
git commit -m "feat: add {ComponentName} generated from design

Generated using compose-designer plugin:
- Input: {input_source}
- Visual similarity: {similarity_score:.1%}
- Device tested: ✓ ({device_name})
- Interactions: {passed_count}/{interaction_count} passed

Phase 1: Code generation
Phase 2: Visual validation ({iteration_count} iterations)
Phase 3: Device testing"
```

**Step 4: Mark all todos complete**

Update TodoWrite to mark all tasks completed.

**Step 5: Cleanup (based on config)**

If `config.testing.cleanup_artifacts` is:
- `"always"`: Delete temp directory
- `"never"`: Keep all artifacts
- `"ask"`: Prompt user

```bash
if [ "$cleanup" = "always" ]; then
  rm -rf "$temp_dir"
  echo "✓ Cleaned up temporary artifacts"
elif [ "$cleanup" = "ask" ]; then
  read -p "Keep validation artifacts in $temp_dir? [Y/n]: " keep
  [ "$keep" != "n" ] || rm -rf "$temp_dir"
fi
```

## Batch Processing

For `--batch` flag:

**Step 1: Find all images in directory**

```bash
find "$input_dir" -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | sort
```

**Step 2: Process based on batch mode**

If `config.batch.mode` is `"sequential"`:
- Process each image one-by-one
- Wait for each to complete before starting next
- Show progress: "Processing 3/10: button-primary.png"

If `config.batch.mode` is `"parallel"`:
- Launch multiple Task tools simultaneously
- Monitor all in parallel
- Collect results when all complete

**Step 3: Generate batch summary report**

```
✅ Batch Processing Complete

Processed: {total_count} designs
Succeeded: {success_count}
Failed: {failure_count}
Time: {duration}

Results:
{for each file:}
  ✓ {filename} → {ComponentName} ({similarity:.1%})

{if failures:}
Failed:
  ✗ {filename}: {error_message}
```

## Error Handling

Handle all failure scenarios gracefully:

**Configuration missing:**
```
❌ Configuration not found

Run: /compose-design config

This will create .claude/compose-designer.yaml with project settings.
```

**Invalid arguments:**
```
❌ Invalid arguments: {specific_error}

Usage: /compose-design create --input <path|url> --name <Name> --type <component|screen>

Examples:
  /compose-design create --input button.png --name PrimaryButton --type component
  /compose-design create --clipboard --name QuickCard --type component

See: README.md for full documentation
```

**Dependency missing:**
```
❌ Required dependency not found: {dependency}

{specific installation instructions}

Retry after installing dependencies.
```

**Preview rendering fails:**
```
❌ Preview rendering failed

Troubleshooting:
1. Verify Gradle works: ./gradlew build
2. Check Android Studio installed
3. Try manual preview in Android Studio

Would you like to:
1. Skip validation (use generated code as-is)
2. Retry with different settings
3. Abort workflow

Choose [1/2/3]:
```

**Device not found:**
```
❌ No Android devices found

Connect a device:
  • Physical device: Enable USB debugging in Developer Options
  • Emulator: Launch from Android Studio → AVD Manager

Verify: adb devices

Would you like to:
1. Skip device testing (validation only)
2. Wait and retry
3. Abort workflow

Choose [1/2/3]:
```

**Similarity threshold not reached:**
```
⚠️  Visual validation incomplete

Final similarity: {score:.1%} (target: {threshold:.1%})
Iterations: {max_iterations}/{max_iterations} (limit reached)

Differences:
{list major visual differences from last diff}

Options:
1. Accept current quality and continue
2. Manual refinement (I'll help improve code)
3. Lower threshold to {score:.1%} and retry
4. Abort workflow

What would you like to do? [1/2/3/4]:
```

## Notes

- Always validate inputs before starting workflow
- Show progress clearly (use TodoWrite)
- Make errors actionable with specific next steps
- Provide escape hatches at each phase
- Generate detailed reports for debugging
- Clean up temporary files based on config
