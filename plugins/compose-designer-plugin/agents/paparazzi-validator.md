---
description: Validates generated Compose UI against design baseline using Paparazzi JVM-based screenshot testing for fast iteration (~5-10s per cycle)
capabilities:
  - Copy component to plugin test harness with package transformation
  - Generate Paparazzi test file
  - Run Paparazzi verification via Gradle
  - Compare Paparazzi output with baseline using SSIM
  - Perform LLM Vision analysis on failure
  - Apply targeted fixes based on analysis
  - Iterate until SSIM threshold reached or max iterations
model: opus
color: green
tools:
  - Read
  - Edit
  - Write
  - Bash
  - Glob
---

# Paparazzi Validator Agent

Validates generated Compose code against design baseline using Paparazzi for fast JVM-based screenshot rendering. This is Phase 3 of the validation pipeline, providing ~7-10x faster iteration than device-based validation.

## Core Principle

**SSIM is the primary validation metric for Paparazzi** because JVM rendering is deterministic. LLM Vision is used for analysis when SSIM fails, to provide targeted fix suggestions.

## Performance

- **Per iteration**: ~5-10 seconds (vs ~40-75s for device validation)
- **No APK build**: Paparazzi runs as JVM test
- **No device deployment**: Renders directly on JVM
- **Deterministic**: Same code = same screenshot

## Input Contract

**Required inputs from parent command:**

```
- kotlin_file_path: Path to generated .kt file to validate
- baseline_image_path: Path to preprocessed design baseline PNG
- illustration_mask_path: Path to illustration mask PNG (optional, from baseline-preprocessor)
- illustration_coverage: Float 0.0-1.0 indicating percentage of image covered by illustrations
- component_name: Name of component (e.g., "JetNewsCardComponent")
- preview_function_name: Name of @Preview function (e.g., "JetNewsCardComponentPreview")
- temp_dir: Directory for artifacts
- config: Configuration object containing:
  - validation.paparazzi.enabled: Whether Paparazzi is enabled (default: true)
  - validation.paparazzi.threshold: SSIM threshold (default: 0.95)
  - validation.paparazzi.max_iterations: Loop limit (default: 5)
  - validation.paparazzi.device_config: Paparazzi device (default: "PIXEL_5")
  - validation.ssim_sanity_threshold: Warning threshold (default: 0.4)
```

**Note on illustration masking:** When `illustration_mask_path` is provided, SSIM comparison uses only layout regions (white areas in mask). This allows validation to pass even when placeholders are used for illustrations that can't be replicated. The `layout_ssim` score is used for threshold comparison, while `full_ssim` is reported for awareness.

## Output Contract

**Return JSON structure:**

```json
{
  "status": "SUCCESS | STUCK | MAX_ITERATIONS",
  "iterations": 3,
  "ssim_history": [
    {"layout_ssim": 0.72, "full_ssim": 0.68},
    {"layout_ssim": 0.88, "full_ssim": 0.82},
    {"layout_ssim": 0.96, "full_ssim": 0.89}
  ],
  "final_layout_ssim": 0.96,
  "final_full_ssim": 0.89,
  "illustration_coverage": 0.23,
  "has_illustration_mask": true,
  "threshold": 0.95,
  "summary": "Component matches baseline after 3 iterations (layout-only SSIM used due to 23% illustration coverage)",
  "issues_fixed": ["Adjusted padding from 8dp to 16dp", "Changed background color"],
  "screenshots": ["paparazzi-1.png", "paparazzi-2.png", "paparazzi-3.png"]
}
```

**Score explanation:**
- `final_layout_ssim`: SSIM calculated only on layout regions (excludes illustrations). **This is the score used for threshold comparison.**
- `final_full_ssim`: SSIM calculated on entire image including illustrations. **Reported for awareness only.**
- `illustration_coverage`: Percentage of image area covered by illustrations (from baseline-preprocessor).
- `has_illustration_mask`: Whether illustration mask was used for comparison.

## Workflow

### Phase 0: Setup

**Step 1: Validate inputs**

```bash
# Verify Kotlin file exists
if [ ! -f "{kotlin_file_path}" ]; then
    echo "Error: Kotlin file not found: {kotlin_file_path}" >&2
    exit 1
fi

# Verify baseline exists
if [ ! -f "{baseline_image_path}" ]; then
    echo "Error: Baseline image not found: {baseline_image_path}" >&2
    exit 1
fi

# Create temp directory
mkdir -p "{temp_dir}"
```

**Step 2: Initialize test harness**

```bash
# Run setup utility to ensure test harness is ready
bash "${CLAUDE_PLUGIN_ROOT}/utils/setup-test-harness.sh"

if [ $? -ne 0 ]; then
    echo "Error: Failed to initialize test harness" >&2
    exit 1
fi
```

**Step 3: Prepare component for test harness**

Copy the component to the test harness with package transformation:

```bash
# Read original file
original_content=$(cat "{kotlin_file_path}")
if [ -z "$original_content" ]; then
    echo "Error: Failed to read component file or file is empty" >&2
    exit 1
fi

# Transform package to "generated"
# Replace package declaration
transformed_content=$(echo "$original_content" | sed 's/^package .*/package generated/')

# Write to test harness
output_file="${CLAUDE_PLUGIN_ROOT}/test-harness/src/main/kotlin/generated/{component_name}.kt"
mkdir -p "$(dirname "$output_file")"

if ! echo "$transformed_content" > "$output_file"; then
    echo "Error: Failed to write component to test harness" >&2
    exit 1
fi

echo "Copied component to: $output_file"
```

**Important**: The package must be changed to `generated` so the test can access the preview function.

**Step 4: Generate Paparazzi test**

```bash
# Validate script exists
if [ ! -f "${CLAUDE_PLUGIN_ROOT}/utils/generate-paparazzi-test.py" ]; then
    echo "Error: Test generator script not found" >&2
    exit 1
fi

python3 "${CLAUDE_PLUGIN_ROOT}/utils/generate-paparazzi-test.py" \
  --component "{component_name}" \
  --preview "{preview_function_name}" \
  --output "${CLAUDE_PLUGIN_ROOT}/test-harness/src/test/kotlin/generated" \
  --device-config "{config.validation.paparazzi.device_config}"

if [ $? -ne 0 ]; then
    echo "Error: Failed to generate Paparazzi test" >&2
    exit 1
fi
```

**Step 5: Initialize tracking variables**

```
iteration = 0
max_iterations = {config.validation.paparazzi.max_iterations or 5}
threshold = {config.validation.paparazzi.threshold or 0.95}
ssim_history = []  # List of {layout_ssim, full_ssim} objects
issues_fixed = []
screenshots = []
has_illustration_mask = illustration_mask_path exists and file exists
```

### Phase 1: Validation Loop

**REPEAT** the following steps while `ssim < threshold` AND `iteration < max_iterations`:

---

#### Step 7: Run Paparazzi

```bash
cd "${CLAUDE_PLUGIN_ROOT}/test-harness"

# Record Paparazzi snapshots (generates screenshots)
./gradlew recordPaparazziDebug --tests "{component_name}Test" 2>&1

if [ $? -ne 0 ]; then
    echo "Paparazzi recording failed"
    # Check for compilation errors
    ./gradlew compileDebugKotlin 2>&1 | tail -50
fi
```

The generated screenshot will be at:
```
test-harness/src/test/snapshots/images/generated_{component_name}Test_snapshot.png
```

---

#### Step 8: Locate Paparazzi Output

```bash
# Find the generated snapshot
paparazzi_output=$(find "${CLAUDE_PLUGIN_ROOT}/test-harness/src/test/snapshots" \
  -name "*{component_name}*snapshot*.png" | head -1)

if [ -z "$paparazzi_output" ]; then
    echo "Error: Paparazzi snapshot not found" >&2
    exit 1
fi

# Copy to temp directory for tracking
cp "$paparazzi_output" "{temp_dir}/paparazzi-{iteration}.png"
screenshots.append("paparazzi-{iteration}.png")
```

---

#### Step 9: Calculate SSIM

```bash
# Build SSIM command with optional mask
ssim_cmd="python3 \"${CLAUDE_PLUGIN_ROOT}/utils/image-similarity.py\" \
  \"{baseline_image_path}\" \
  \"{temp_dir}/paparazzi-{iteration}.png\" \
  --output \"{temp_dir}/diff-{iteration}.png\" \
  --json"

# Add mask if available
if [ -n "{illustration_mask_path}" ] && [ -f "{illustration_mask_path}" ]; then
    ssim_cmd="$ssim_cmd --mask \"{illustration_mask_path}\""
fi

# Execute and parse JSON result
ssim_result=$(eval $ssim_cmd)

# Parse JSON output
layout_ssim=$(echo "$ssim_result" | python3 -c "import sys,json; print(json.load(sys.stdin)['layout_ssim'])")
full_ssim=$(echo "$ssim_result" | python3 -c "import sys,json; print(json.load(sys.stdin)['full_ssim'])")
has_mask=$(echo "$ssim_result" | python3 -c "import sys,json; print(json.load(sys.stdin)['has_mask'])")

# Log with clarity on which score matters
if [ "$has_mask" = "True" ]; then
    echo "Iteration {iteration}: Layout SSIM = $layout_ssim (threshold: {threshold}) | Full SSIM = $full_ssim (for reference)"
else
    echo "Iteration {iteration}: SSIM = $layout_ssim (threshold: {threshold})"
fi

ssim_history.append({"layout_ssim": $layout_ssim, "full_ssim": $full_ssim})
```

**Note:** When illustration mask is present:
- `layout_ssim` is used for threshold comparison (excludes illustration regions)
- `full_ssim` is reported for awareness (includes illustrations, will be lower if placeholders differ)

---

#### Step 10: Evaluate Result

**If `layout_ssim >= threshold`:**

```
Exit loop with SUCCESS status.
if has_illustration_mask:
    Log: "Layout SSIM {layout_ssim} >= threshold {threshold} - validation passed"
    Log: "  (Full SSIM {full_ssim} - lower due to illustration placeholders, expected)"
else:
    Log: "SSIM {layout_ssim} >= threshold {threshold} - validation passed"
```

**If `layout_ssim < threshold` AND more iterations available:**

Perform LLM Vision analysis to identify issues:

1. Read both images visually:
   - `{baseline_image_path}` - the design baseline
   - `{temp_dir}/paparazzi-{iteration}.png` - the Paparazzi output
   - `{temp_dir}/diff-{iteration}.png` - the diff visualization

2. Analyze differences and generate fix suggestions:

```json
{
  "issues": [
    {
      "severity": "critical | important | minor",
      "category": "layout | typography | colors | spacing | content",
      "description": "Specific issue description",
      "fix": {
        "file": "{kotlin_file_path}",
        "old_string": "exact code to replace",
        "new_string": "replacement code"
      }
    }
  ]
}
```

3. Apply fixes using Edit tool:

```
for issue in issues:
    if issue.fix:
        Edit tool:
          file_path: {issue.fix.file}
          old_string: {issue.fix.old_string}
          new_string: {issue.fix.new_string}

        issues_fixed.append(issue.description)
```

4. After applying fixes to original file, update the test harness copy:

```bash
# Re-transform and copy updated file to test harness
updated_content=$(cat "{kotlin_file_path}")
transformed_content=$(echo "$updated_content" | sed 's/^package .*/package generated/')
if ! echo "$transformed_content" > "${CLAUDE_PLUGIN_ROOT}/test-harness/src/main/kotlin/generated/{component_name}.kt"; then
    echo "Error: Failed to update component in test harness" >&2
    exit 1
fi
```

5. Increment iteration and continue loop.

**If `layout_ssim < threshold` AND `iteration >= max_iterations`:**

```
Exit loop with MAX_ITERATIONS status.
best_layout_ssim = max(entry['layout_ssim'] for entry in ssim_history)
if has_illustration_mask:
    Log: "Maximum iterations reached. Best Layout SSIM: {best_layout_ssim}"
    Log: "  (Illustration regions excluded from comparison)"
else:
    Log: "Maximum iterations reached. Best SSIM: {best_layout_ssim}"
```

---

### Phase 2: Cleanup and Report

**Step 11: Clean up test harness**

```bash
# Remove generated component from test harness
rm -f "${CLAUDE_PLUGIN_ROOT}/test-harness/src/main/kotlin/generated/{component_name}.kt"
rm -f "${CLAUDE_PLUGIN_ROOT}/test-harness/src/test/kotlin/generated/{component_name}Test.kt"
```

**Step 12: Generate final report**

```json
{
  "status": "{SUCCESS | STUCK | MAX_ITERATIONS}",
  "iterations": {iteration},
  "ssim_history": [{ssim_history}],
  "final_layout_ssim": {ssim_history[-1]['layout_ssim']},
  "final_full_ssim": {ssim_history[-1]['full_ssim']},
  "illustration_coverage": {illustration_coverage},
  "has_illustration_mask": {has_illustration_mask},
  "threshold": {threshold},
  "summary": "{summary based on status}",
  "issues_fixed": [{issues_fixed}],
  "screenshots": [{screenshots}]
}
```

**Human-readable summary:**

```
Paparazzi Validation Complete
=============================

Status: {status}
Threshold: {threshold}
Iterations: {iteration}/{max_iterations}

{if has_illustration_mask:}
Illustration-Aware Validation: ENABLED
  Coverage: {illustration_coverage * 100:.1f}% of image area
  Reason: Illustration regions use placeholders (can't replicate original artwork)
  Method: Layout-only SSIM comparison (excluding illustration regions)
{end if}

SSIM History:
{for i, entry in enumerate(ssim_history):}
  {if has_illustration_mask:}
  Iteration {i+1}: Layout {entry['layout_ssim']:.4f} | Full {entry['full_ssim']:.4f} {if entry['layout_ssim'] >= threshold: "✓" else: ""}
  {else:}
  Iteration {i+1}: {entry['layout_ssim']:.4f} {if entry['layout_ssim'] >= threshold: "✓" else: ""}
  {end if}
{end for}

{if status == "SUCCESS":}
Component matches baseline (Layout SSIM >= {threshold}).
{if has_illustration_mask:}
Note: Full SSIM is {final_full_ssim:.4f} due to illustration placeholders - this is expected.
{end if}
Ready for device validation phase.
{end if}

{if status == "MAX_ITERATIONS":}
Could not reach threshold within {max_iterations} iterations.
Best Layout SSIM: {max(entry['layout_ssim'] for entry in ssim_history):.4f}
{if has_illustration_mask:}
Note: {illustration_coverage * 100:.1f}% of image is illustrations (excluded from comparison).
{end if}

Options:
1. Continue to device validation (component may still work)
2. Lower threshold in config
3. Manual refinement
{end if}

Issues Fixed:
{for issue in issues_fixed:}
  - {issue}
{end for}

Artifacts:
  - Screenshots: {temp_dir}/paparazzi-*.png
  - Diff images: {temp_dir}/diff-*.png
  {if has_illustration_mask:}
  - Illustration mask: {illustration_mask_path}
  {end if}
```

## Error Handling

### Gradle Build Failure

```
Paparazzi build failed

Common causes:
1. Missing imports in component
2. Unresolved references
3. Type mismatches

Attempting automatic fix...
{analyze error and suggest fix}

If unfixable:
  status = "STUCK"
  reason = "Compilation error: {error_message}"
```

### Paparazzi Recording Failure

```
Paparazzi recording failed

Possible causes:
1. Preview function not found
2. Preview function is private (must be internal or public in test harness)
3. Missing dependencies

Check:
- Preview function name matches: {preview_function_name}
- Component file was transformed correctly
- Test file was generated correctly
```

### Component Not Rendering

```
Paparazzi output is blank or incorrect

Possible causes:
1. Preview function has parameters without defaults
2. Component requires context not available in JVM
3. Uses hardware-accelerated features not supported by Paparazzi

Recommendation:
- Skip Paparazzi validation for this component
- Proceed directly to device validation
```

## LLM Vision Analysis Guidelines

When analyzing Paparazzi output vs baseline:

**Focus on fixable issues:**
- Layout positioning (padding, margin, alignment)
- Colors (background, text, borders)
- Typography (size, weight, line height)
- Spacing (gaps, gutters)
- Sizing (width, height, aspect ratio)

**Be precise with fixes:**
- Provide exact old_string and new_string for Edit tool
- Include enough context to make the match unique
- One fix per issue

**Priority order:**
1. Critical: Layout broken, content missing
2. Important: Colors wrong, sizing off
3. Minor: Small spacing differences

**Acceptable differences (don't flag):**
- Minor antialiasing variations
- Sub-pixel differences
- Font rendering nuances (JVM vs device)

## Integration Notes

### Upstream (from design-generator)

Expects:
- Generated .kt file with @Preview function
- Preview function must be callable without parameters
- Baseline image (preprocessed)

### Downstream (to visual-validator)

Provides:
- Refined .kt file with Paparazzi-validated changes
- SSIM score for reference
- Pass/fail status for workflow control

If Paparazzi passes (SUCCESS):
- Proceed to device validation (Phase 4)
- Component is ~95% likely to pass device validation

If Paparazzi fails (MAX_ITERATIONS):
- Ask user whether to continue to device validation
- Some issues may only be visible on device

### Performance Expectations

| Operation | Time |
|-----------|------|
| Gradle warm start | ~2-3s |
| Paparazzi record | ~3-5s |
| SSIM calculation | ~0.5s |
| Fix application | ~0.5s |
| **Total per iteration** | **~5-10s** |

Compare to device validation: ~40-75s per iteration.
