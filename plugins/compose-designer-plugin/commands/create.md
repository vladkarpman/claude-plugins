---
name: create
description: Generate Compose code from design input (screenshot/Figma/clipboard) through four-phase workflow with Paparazzi and device validation
argument-hint: --input <path|url> --name <ComponentName> --type <component|screen> [--output <dir>] [--clipboard] [--batch] [--device <device-id>]
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

### Phase Structure (Overview)

**Phase 0: Setup and Validation**
- Load configuration
- Validate arguments and dependencies
- Create task list

**Phase 1: Input Processing**
- If Figma URL: Extract tokens via Figma MCP
- If Screenshot: Use as baseline directly
- Create temp directory

**Phase 1.5: Baseline Preprocessing**
- Detect device frames in baseline image
- Crop to content area if needed
- Output: Preprocessed baseline for validation

**Phase 2: Code Generation**
- Invoke design-generator agent
- Pass Figma tokens if available
- Output: Generated .kt file

**Phase 3: Paparazzi Validation** (paparazzi-validator agent)
- Fast JVM-based screenshot testing (~5-10s per iteration)
- SSIM comparison with 0.95 threshold (stricter due to deterministic rendering)
- LLM Vision analysis on threshold failure
- Continue until threshold met or max iterations
- Output: Refined .kt file + JVM screenshots

**Phase 4: Device Validation** (visual-validator agent)
- Device-centric loop with LLM Vision primary:
  - Build → Deploy → Screenshot → LLM Compare → Refine
- SSIM as secondary metric for logging (0.92 threshold)
- Continue until LLM approves or max iterations
- Output: Validated .kt file + device screenshots

**Phase 5: Final Report**
- Summarize results from both validation phases
- Include Paparazzi and Device metrics
- Offer commit option

---

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
- `--output` (optional): Override default output directory for this run
  - If provided, use this path instead of `config.output.default_output_dir`
  - Path can be relative or absolute
  - Directory will be created if it doesn't exist

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
  {"content": "Load configuration and validate inputs", "status": "pending", "activeForm": "Loading configuration"},
  {"content": "Process design input (Phase 1)", "status": "pending", "activeForm": "Processing design input"},
  {"content": "Preprocess baseline (Phase 1.5)", "status": "pending", "activeForm": "Preprocessing baseline"},
  {"content": "Generate initial Compose code (Phase 2)", "status": "pending", "activeForm": "Generating Compose code"},
  {"content": "Paparazzi JVM validation (Phase 3)", "status": "pending", "activeForm": "Validating with Paparazzi"},
  {"content": "Device validation with LLM Vision (Phase 4)", "status": "pending", "activeForm": "Validating on device"},
  {"content": "Generate final report", "status": "pending", "activeForm": "Generating report"}
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

Mark "Process design input (Phase 1)" as completed, start "Preprocess baseline (Phase 1.5)".

### Phase 1.5: Baseline Preprocessing

Preprocess the baseline image to detect and remove device frames, crop to content area, and prepare for validation.

**Step 1: Invoke baseline-preprocessor agent**

Use Task tool to launch the preprocessing agent:

```
Task tool:
  subagent_type: "compose-designer:baseline-preprocessor"
  model: {config.model.baseline_preprocessor || config.model.default}
  description: "Preprocess baseline image"
  prompt: "Preprocess baseline image at {baseline_path}.

  Config:
  - Visual similarity threshold: {config.validation.visual_similarity_threshold}

  Detect device frames, crop to content area, and return preprocessed image path."
```

**Step 2: Store preprocessing results**

Agent will return:
- `preprocessed_baseline_path`: Path to the preprocessed image
- `frames_detected`: Boolean indicating if device frames were found
- `recommended_threshold`: Optional adjusted threshold based on content type
- `content_bounds`: Crop coordinates if frames were detected

Save these values for use in Phase 3:

```bash
# Store results from agent
preprocessed_baseline_path="{returned_path}"
frames_detected="{returned_frames_detected}"
recommended_threshold="{returned_threshold:-$config_threshold}"
```

**Step 3: Update todo**

Mark "Preprocess baseline (Phase 1.5)" as completed, start "Generate initial Compose code (Phase 2)".

### Phase 2: Code Generation (design-generator agent)

**Determine output file path:**

```bash
# Check for --output override
if [ -n "$output_override" ]; then
  output_dir="$output_override"
else
  output_dir="${config.output.default_output_dir}"
fi

# Create directory if needed
mkdir -p "$output_dir"

# Build full path
output_file_path="$output_dir/${name}${suffix}.kt"
```

**Step 1: Invoke design-generator agent**

Use Task tool to launch agent:

```
Task tool:
  subagent_type: "compose-designer:design-generator"
  model: {config.model.design_generator || config.model.default}
  description: "Generate Compose code from design"
  prompt: "Generate Compose code for {name} ({type}) from baseline image at {baseline_path}.

  Config:
  - Package: {config.output.package_base}
  - Output dir: {output_dir}
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

Mark "Generate initial Compose code (Phase 2)" as completed, start "Paparazzi JVM validation (Phase 3)".

### Phase 3: Paparazzi Validation (paparazzi-validator agent)

Fast JVM-based screenshot testing that iterates quickly without device deployment. Uses the plugin's test harness with Paparazzi for deterministic rendering.

**Step 1: Check if Paparazzi validation enabled**

```bash
# Read config
paparazzi_enabled=$(grep -A 5 "paparazzi:" .claude/compose-designer.yaml | grep "enabled:" | awk '{print $2}')
if [ "$paparazzi_enabled" = "false" ]; then
  echo "⚠️  Paparazzi validation disabled in config, skipping to device validation"
  # Skip to Phase 4
fi
```

**Step 2: Invoke paparazzi-validator agent**

Use Task tool:

```
Task tool:
  subagent_type: "compose-designer:paparazzi-validator"
  model: {config.model.paparazzi_validator || config.model.default}
  description: "Validate UI with Paparazzi JVM"
  prompt: "Validate Compose code in {output_file_path} against baseline {preprocessed_baseline_path} using Paparazzi.

  Inputs:
  - kotlin_file_path: {output_file_path}
  - baseline_image_path: {preprocessed_baseline_path}
  - component_name: {name}
  - preview_function: {name}Preview
  - temp_dir: {temp_dir}
  - config:
    - validation.paparazzi.threshold: {config.validation.paparazzi.threshold}
    - validation.paparazzi.max_iterations: {config.validation.paparazzi.max_iterations}
    - validation.paparazzi.device_config: {config.validation.paparazzi.device_config}
    - validation.ssim_sanity_threshold: {config.validation.ssim_sanity_threshold}

  The agent will:
  1. Copy component to test harness with package transformation
  2. Generate Paparazzi test file
  3. Run ./gradlew testDebugUnitTest
  4. Compare snapshot with baseline using SSIM
  5. If below threshold: analyze diff with LLM Vision, refine code, repeat
  6. Return when threshold met or max iterations reached

  Save snapshots and diffs to: {temp_dir}/paparazzi/"
```

**Step 3: Review Paparazzi validation results**

Agent will return JSON:
```json
{
  "status": "SUCCESS|THRESHOLD_NOT_MET|MAX_ITERATIONS",
  "final_ssim": 0.96,
  "iterations": 3,
  "snapshots": ["paparazzi/snapshot-1.png", ...],
  "diff_images": ["paparazzi/diff-1.png", ...],
  "summary": "Paparazzi validation passed with 96% similarity after 3 iterations."
}
```

**Step 4: Handle Paparazzi outcome**

If status is SUCCESS:
- Continue to Phase 4 (Device Validation)
- Pass refined code from Paparazzi phase

If status is THRESHOLD_NOT_MET or MAX_ITERATIONS:
```
Ask user: "Paparazzi validation incomplete. SSIM: {final_ssim:.2%} (target: {threshold:.2%})
Iterations: {iterations}/{max_iterations}

Options:
1. Continue to device validation anyway (may catch issues there)
2. Manual refinement (I'll help improve the code)
3. Adjust threshold and retry
4. Abort workflow

What would you like to do? [1/2/3/4]: "
```

**Step 5: Update todo**

Mark "Paparazzi JVM validation (Phase 3)" as completed, start "Device validation with LLM Vision (Phase 4)".

### Phase 4: Device Validation (visual-validator agent)

The visual-validator agent performs device-centric validation: deploy to device, capture screenshots, compare with SSIM + LLM vision, and iterate until threshold is reached.

**Step 1: Check if device validation enabled**

```bash
# Read config
device_enabled=$(grep -A 5 "device:" .claude/compose-designer.yaml | grep "enabled:" | awk '{print $2}')
if [ "$device_enabled" = "false" ]; then
  echo "⚠️  Device validation disabled in config, skipping to final report"
  # Skip to Phase 5
fi
```

**Step 2: Check device availability**

```bash
# Check if mobile-mcp tools available
claude --help | grep -q "mobile_list_available_devices" || {
  echo "⚠️  Mobile-mcp plugin not found"
  echo "Install: https://github.com/mobile-dev-inc/mobile-mcp"
  read -p "Skip device validation phase? [y/N]: " skip
  [ "$skip" = "y" ] && return 0
}

# List available devices
devices=$(mobile_list_available_devices)
if [ -z "$devices" ]; then
  echo "❌ No Android devices found"
  echo ""
  echo "Connect a device:"
  echo "  • Physical: Enable USB debugging"
  echo "  • Emulator: Launch from Android Studio"
  read -p "Skip device validation phase? [y/N]: " skip
  [ "$skip" = "y" ] && return 0
  exit 1
fi
```

**Step 3: Invoke visual-validator agent**

Use Task tool:

```
Task tool:
  subagent_type: "compose-designer:visual-validator"
  model: {config.model.visual_validator || config.model.default}
  description: "Validate UI on device"
  prompt: "Validate Compose code in {output_file_path} against preprocessed baseline {preprocessed_baseline_path}.

  Inputs:
  - kotlin_file_path: {output_file_path}
  - baseline_image_path: {baseline_path}
  - preprocessed_baseline_path: {preprocessed_baseline_path}
  - component_name: {name}
  - package_name: {config.output.package_base}
  - temp_dir: {temp_dir}
  - config:
    - validation.device.threshold: {config.validation.device.threshold}
    - validation.device.max_iterations: {config.validation.device.max_iterations}
    - validation.ssim_sanity_threshold: {config.validation.ssim_sanity_threshold}

  Use LLM Vision as primary validation. SSIM for logging only.

  The agent will:
  1. Build APK and deploy to device
  2. Capture device screenshot
  3. Compare with LLM Vision (primary) and SSIM (secondary/logging)
  4. If LLM detects differences: analyze issues, apply fixes, repeat
  5. Return when LLM approves or max iterations reached

  Save screenshots and diffs to: {temp_dir}/device/"
```

**Step 4: Review validation results**

Agent will return JSON:
```json
{
  "status": "SUCCESS|STUCK|MAX_ITERATIONS",
  "llm_verdict": "PASS|FAIL",
  "llm_confidence": "HIGH|MEDIUM|LOW",
  "final_ssim": 0.93,
  "iterations": 4,
  "screenshots": ["device/iteration-1.png", ...],
  "diff_images": ["device/diff-1.png", ...],
  "sanity_warning": false,
  "summary": "LLM approved with high confidence. Minor spacing differences noted but within acceptable bounds."
}
```

**Step 5: Handle validation outcome**

If status is STUCK or MAX_ITERATIONS:
```
Ask user: "Visual validation incomplete. LLM Verdict: {llm_verdict} (Confidence: {llm_confidence}).
SSIM: {final_ssim:.2%} (threshold: {threshold:.2%})

Options:
1. Accept current result and continue
2. Manual refinement (I'll help you improve the code)
3. Adjust threshold and retry
4. Abort workflow

What would you like to do? [1/2/3/4]: "
```

**Step 6: Update todo**

Mark "Device validation with LLM Vision (Phase 4)" as completed, start "Generate final report".

### Phase 5: Final Report and Commit

**Step 1: Generate comprehensive report**

Compile results from all phases:

```
✅ Design-to-Code Complete: {ComponentName}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 Phase 1.5: Baseline Preprocessing
✓ Frames detected: {frames_detected ? "Yes (cropped to content)" : "No (used original)"}
✓ Preprocessed baseline: {preprocessed_baseline_path}

📥 Phase 2: Code Generation
✓ Input: {input_source}
✓ Baseline: {baseline_path}
✓ Generated: {output_file_path}
✓ Lines of code: {loc}
✓ Figma tokens: {used_figma_tokens ? "✓ Extracted" : "N/A (screenshot input)"}

⚡ Phase 3: Paparazzi Validation (JVM)
✓ Status: {paparazzi_status}
✓ Final SSIM: {paparazzi_ssim:.2%} (threshold: {config.validation.paparazzi.threshold:.2%})
✓ Iterations: {paparazzi_iterations}/{config.validation.paparazzi.max_iterations}
✓ Time: ~{paparazzi_time}s ({paparazzi_iterations} × ~5-10s per iteration)
{if paparazzi_status != "SUCCESS": "⚠️  {paparazzi_status}: {paparazzi_summary}"}

📱 Phase 4: Device Validation
✓ Method: LLM Vision primary (SSIM secondary)
✓ LLM Verdict: {llm_verdict} (Confidence: {llm_confidence})
✓ Iterations: {device_iterations}/{config.validation.device.max_iterations}
✓ Final SSIM: {device_ssim:.2%} (threshold: {config.validation.device.threshold:.2%})
✓ Status: {device_status}
✓ Device: {device_name}
{if sanity_warning: "⚠️  LLM passed but SSIM below sanity threshold - manual review recommended"}
{if device_status != "SUCCESS": "⚠️  {device_status}: {device_summary}"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Generated Files:
  • Component: {output_file_path}
  • Baseline: {baseline_path}
  • Preprocessed: {preprocessed_baseline_path}
  • Artifacts: {temp_dir}/
    - paparazzi/snapshot-*.png (JVM screenshots)
    - paparazzi/diff-*.png (Paparazzi diffs)
    - device/iteration-*.png (device screenshots)
    - device/diff-*.png (device diffs)

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
- Paparazzi SSIM: {paparazzi_ssim:.1%} ({paparazzi_iterations} iterations)
- Device SSIM: {device_ssim:.1%} ({device_iterations} iterations)
- LLM Verdict: {llm_verdict} (Confidence: {llm_confidence})
- Device tested: ✓ ({device_name})

Phase 2: Code generation
Phase 3: Paparazzi validation (JVM)
Phase 4: Device validation (LLM Vision primary)"
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

**Paparazzi validation threshold not reached:**
```
⚠️  Paparazzi (JVM) validation incomplete

Final SSIM: {score:.1%} (threshold: {threshold:.1%})
Iterations: {iterations}/{max_iterations} (limit reached)

Differences:
{list major visual differences from LLM analysis}

Options:
1. Continue to device validation (may catch remaining issues)
2. Manual refinement (I'll help improve code)
3. Lower threshold to {score:.1%} and retry
4. Abort workflow

What would you like to do? [1/2/3/4]:
```

**Device validation threshold not reached:**
```
⚠️  Device validation incomplete

LLM Verdict: {llm_verdict} (Confidence: {llm_confidence})
Final SSIM: {score:.1%} (threshold: {threshold:.1%})
Iterations: {iterations}/{max_iterations} (limit reached)

Differences:
{list major visual differences from LLM analysis}

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
