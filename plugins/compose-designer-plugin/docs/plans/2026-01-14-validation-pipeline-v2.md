# Validation Pipeline v2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the visual validation pipeline to use LLM Vision as primary validation source, with automatic baseline preprocessing and device screenshot cropping.

**Architecture:** Three-stage pipeline: (1) baseline-preprocessor detects device frames and crops to content area, (2) visual-validator extracts component bounds from device and crops screenshot, (3) LLM Vision makes pass/fail decisions while SSIM serves as secondary metric for logging.

**Tech Stack:** Python (pillow, scikit-image), mobile-mcp tools, LLM Vision (Opus), Kotlin/Compose

---

## Overview

### Current Problems
1. Baseline images may contain device frames, composite layouts (multiple devices), or full-screen context
2. Device screenshots include status bar, navigation bar, and full screen content
3. SSIM comparison fails when baseline and screenshot have different scopes
4. SSIM threshold (from `config.validation.visual_similarity_threshold`) is too rigid for semantic validation

### Solution
1. **Baseline Preprocessing**: Detect device frames, crop to content area, handle composite layouts
2. **Device Screenshot Cropping**: Extract component bounds via view hierarchy, crop to match
3. **LLM Vision Primary**: Let LLM decide pass/fail based on semantic correctness, SSIM for logging only

### Configuration Values Used
All thresholds and settings come from `.claude/compose-designer.yaml`:
- `config.validation.visual_similarity_threshold` - SSIM threshold for sanity check (default: 0.92)
- `config.validation.max_ralph_iterations` - Max refinement iterations (default: 10)
- `config.model.visual_validator` - Model for validation (default: opus)
- `config.model.baseline_preprocessor` - Model for preprocessing (default: opus)

---

## Task 1: Update Configuration Schema

**Files:**
- Modify: `commands/config.md`
- Modify: `test-project/.claude/compose-designer.yaml`

**Step 1: Add new config fields to config.md template**

Add to the validation section in the YAML template:

```yaml
# Validation thresholds
validation:
  visual_similarity_threshold: 0.92    # SSIM sanity check threshold (from config)
  max_ralph_iterations: 10             # Max iterations for refinement loop
  preview_screenshot_delay: "auto"     # "auto" or milliseconds
  primary_method: "llm_vision"         # "llm_vision" or "ssim" (legacy)
  ssim_sanity_threshold: 0.4           # Flag for review if LLM passes but SSIM below this
```

**Step 2: Update test-project config**

Add to `test-project/.claude/compose-designer.yaml`:

```yaml
validation:
  visual_similarity_threshold: 0.92
  max_ralph_iterations: 10
  preview_screenshot_delay: "auto"
  primary_method: "llm_vision"
  ssim_sanity_threshold: 0.4
```

**Step 3: Verify YAML is valid**

Run: `python3 -c "import yaml; yaml.safe_load(open('test-project/.claude/compose-designer.yaml'))"`
Expected: No errors

**Step 4: Commit**

```bash
git add commands/config.md test-project/.claude/compose-designer.yaml
git commit -m "feat(config): add LLM vision validation settings"
```

---

## Task 2: Enhance Baseline Preprocessor Agent

**Files:**
- Modify: `agents/baseline-preprocessor.md`

**Step 1: Update agent description and capabilities**

Replace the current agent content with enhanced version that:
- Detects device frames using LLM Vision
- Handles composite layouts (multiple devices in one image)
- Crops to content area automatically
- Calculates realistic similarity targets based on image complexity
- Returns structured output with metadata

**Step 2: Update agent prompt structure**

The agent should accept:
```
Inputs:
- baseline_image_path: Path to original baseline image
- config: Parsed compose-designer.yaml

Outputs (JSON):
- cropped_image_path: Path to preprocessed baseline
- original_bounds: {x, y, width, height} of detected content area
- frames_detected: Number of device frames found
- primary_frame_index: Which frame was selected (0-indexed)
- complexity_score: 0.0-1.0 indicating visual complexity
- recommended_threshold: Suggested SSIM threshold based on complexity
- metadata: Additional context for debugging
```

**Step 3: Add detection logic instructions**

Agent should:
1. Use LLM Vision to detect device frames (bezels, notches, status bars)
2. If multiple frames: select primary (largest or leftmost)
3. Crop to content area (exclude device chrome)
4. Analyze complexity (gradients, shadows, fine details)
5. Calculate recommended threshold: `max(0.85, config.validation.visual_similarity_threshold - complexity_adjustment)`

**Step 4: Commit**

```bash
git add agents/baseline-preprocessor.md
git commit -m "feat(baseline-preprocessor): add device frame detection and auto-cropping"
```

---

## Task 3: Add Test Tags to Generated Components

**Files:**
- Modify: `agents/design-generator.md`

**Step 1: Update generation instructions**

Add instruction to design-generator agent to include test tags:

```kotlin
// Generated component should include testTag for validation
Card(
    modifier = modifier
        .testTag("{ComponentName}")  // Always add this
        .fillMaxWidth()
        .clickable(onClick = onCardClick),
    // ...
)
```

**Step 2: Add testTag import instruction**

Ensure generated code includes:
```kotlin
import androidx.compose.ui.platform.testTag
```

**Step 3: Document the convention**

Add to agent instructions:
- Test tag format: `"{ComponentName}"` (matches the component name parameter)
- Applied to root composable element
- Used by visual-validator for component bounds extraction

**Step 4: Commit**

```bash
git add agents/design-generator.md
git commit -m "feat(design-generator): add testTag to generated components for validation"
```

---

## Task 4: Create Component Bounds Extraction Utility

**Files:**
- Create: `utils/extract-component-bounds.py`

**Step 1: Write the utility script**

```python
#!/usr/bin/env python3
"""
Extract component bounds from mobile-mcp view hierarchy JSON.

Usage:
    python3 extract-component-bounds.py <hierarchy_json> <test_tag>

Output:
    JSON with bounds: {"x": 0, "y": 100, "width": 1080, "height": 500, "found": true}
"""

import json
import sys

def find_element_by_tag(elements, test_tag):
    """Recursively search for element with matching testTag."""
    for element in elements:
        # Check various tag fields
        if element.get('testTag') == test_tag:
            return element
        if element.get('resource-id', '').endswith(test_tag):
            return element
        if element.get('content-desc') == test_tag:
            return element

        # Recurse into children
        children = element.get('children', [])
        if children:
            result = find_element_by_tag(children, test_tag)
            if result:
                return result

    return None

def extract_bounds(element):
    """Extract bounds from element."""
    bounds = element.get('bounds', {})
    return {
        'x': bounds.get('x', 0),
        'y': bounds.get('y', 0),
        'width': bounds.get('width', 0),
        'height': bounds.get('height', 0),
        'found': True
    }

def main():
    if len(sys.argv) < 3:
        print('Usage: extract-component-bounds.py <hierarchy_json> <test_tag>', file=sys.stderr)
        sys.exit(1)

    hierarchy_path = sys.argv[1]
    test_tag = sys.argv[2]

    try:
        with open(hierarchy_path, 'r') as f:
            hierarchy = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(json.dumps({'found': False, 'error': str(e)}))
        sys.exit(1)

    # Handle both list and dict formats
    elements = hierarchy if isinstance(hierarchy, list) else [hierarchy]

    element = find_element_by_tag(elements, test_tag)

    if element:
        print(json.dumps(extract_bounds(element)))
    else:
        print(json.dumps({'found': False, 'error': f'Element with tag "{test_tag}" not found'}))
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**Step 2: Make executable**

Run: `chmod +x utils/extract-component-bounds.py`

**Step 3: Test the utility**

Run: `echo '[{"testTag": "TestCard", "bounds": {"x": 0, "y": 100, "width": 1080, "height": 500}}]' > /tmp/test-hierarchy.json && python3 utils/extract-component-bounds.py /tmp/test-hierarchy.json TestCard`
Expected: `{"x": 0, "y": 100, "width": 1080, "height": 500, "found": true}`

**Step 4: Commit**

```bash
git add utils/extract-component-bounds.py
git commit -m "feat(utils): add component bounds extraction utility"
```

---

## Task 5: Create Image Cropping Utility

**Files:**
- Modify: `utils/image-similarity.py` (add crop function)
- OR Create: `utils/crop-image.py`

**Step 1: Create crop-image.py utility**

```python
#!/usr/bin/env python3
"""
Crop image to specified bounds.

Usage:
    python3 crop-image.py <input_image> <output_image> <x> <y> <width> <height>

Example:
    python3 crop-image.py screenshot.png cropped.png 0 100 1080 500
"""

import sys
from PIL import Image

def main():
    if len(sys.argv) < 7:
        print('Usage: crop-image.py <input> <output> <x> <y> <width> <height>', file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    x = int(sys.argv[3])
    y = int(sys.argv[4])
    width = int(sys.argv[5])
    height = int(sys.argv[6])

    try:
        img = Image.open(input_path)

        # Crop: (left, upper, right, lower)
        cropped = img.crop((x, y, x + width, y + height))

        cropped.save(output_path)
        print(f'Cropped to {width}x{height} at ({x}, {y})')

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**Step 2: Make executable**

Run: `chmod +x utils/crop-image.py`

**Step 3: Test the utility**

Run: `python3 utils/crop-image.py test-project/test-images/jetnews.png /tmp/test-crop.png 0 0 200 200 && ls -la /tmp/test-crop.png`
Expected: File created with cropped dimensions

**Step 4: Commit**

```bash
git add utils/crop-image.py
git commit -m "feat(utils): add image cropping utility"
```

---

## Task 6: Implement LLM Vision Validation Prompt

**Files:**
- Create: `prompts/llm-vision-validation.md`

**Step 1: Create the validation prompt template**

```markdown
# Visual Validation Task

Compare the device screenshot against the design baseline to determine if the implementation matches the design intent.

## Images
- **Design Baseline**: {baseline_image}
- **Device Screenshot**: {screenshot_image}
- **Component Name**: {component_name}

## Evaluation Criteria

### 1. Layout Structure (Critical)
- Are elements positioned correctly relative to each other?
- Is the visual hierarchy preserved?
- Are nested containers structured properly?

### 2. Typography (Important)
- Are font sizes approximately correct?
- Is font weight (bold/regular) correct?
- Is text alignment correct?

### 3. Colors & Theming (Important)
- Do colors match or align with Material theme conventions?
- Are accent colors in the right places?
- Is contrast appropriate?

### 4. Spacing (Moderate)
- Are margins and padding approximately correct?
- Is element spacing consistent?
- Minor pixel differences are acceptable.

### 5. Content Completeness (Critical)
- Is all visible content from the design present?
- Are icons/images in correct positions?
- Is text content accurate?

## Acceptable Differences
- Minor pixel variations (±5px)
- Platform-specific rendering (antialiasing, shadows)
- Material theme color adaptation
- System font substitution
- Status bar / navigation bar differences

## Response Format

Respond with EXACTLY this JSON structure:

```json
{
  "status": "PASS | ITERATE | STUCK",
  "confidence": "HIGH | MEDIUM | LOW",
  "summary": "One sentence overall assessment",
  "issues": [
    {
      "severity": "critical | important | minor",
      "category": "layout | typography | colors | spacing | content",
      "description": "Specific issue description",
      "fix": "Exact code change to make"
    }
  ],
  "reasoning": "If STUCK, explain why this cannot be fixed with code changes"
}
```

### Status Definitions
- **PASS**: Implementation matches design intent. Minor acceptable differences only.
- **ITERATE**: Fixable issues found. Apply suggested fixes and re-validate.
- **STUCK**: Fundamental mismatch that cannot be resolved with code changes (e.g., missing assets, wrong design reference).

### Confidence Levels
- **HIGH**: Clear assessment, obvious match or mismatch
- **MEDIUM**: Some ambiguity, but reasonable judgment made
- **LOW**: Difficult to assess, may need human review
```

**Step 2: Commit**

```bash
git add prompts/llm-vision-validation.md
git commit -m "feat(prompts): add LLM vision validation prompt template"
```

---

## Task 7: Update Visual Validator Agent

**Files:**
- Modify: `agents/visual-validator.md`

**Step 1: Update agent to use LLM Vision as primary**

Replace the current validation loop with:

```markdown
## Validation Loop (LLM Vision Primary)

### Step 1: Preprocess baseline (if not already done)
- Check if preprocessed baseline exists
- If not, invoke baseline-preprocessor agent first

### Step 2: Build and deploy
- Build debug APK: `./gradlew assembleDebug`
- Install on device: `mcp__mobile-mcp__mobile_install_app`
- Launch app: `mcp__mobile-mcp__mobile_launch_app`

### Step 3: Capture and crop device screenshot
- Take screenshot: `mcp__mobile-mcp__mobile_take_screenshot`
- Get view hierarchy: `mcp__mobile-mcp__mobile_list_elements_on_screen`
- Save hierarchy to temp file
- Extract component bounds: `python3 "${CLAUDE_PLUGIN_ROOT}/utils/extract-component-bounds.py" hierarchy.json "{ComponentName}"`
- Crop screenshot to bounds: `python3 "${CLAUDE_PLUGIN_ROOT}/utils/crop-image.py" screenshot.png cropped.png {bounds}`

### Step 4: LLM Vision validation (PRIMARY)
- Load prompt template from `prompts/llm-vision-validation.md`
- Substitute variables: baseline_image, screenshot_image, component_name
- Analyze both images with LLM Vision
- Parse JSON response for status, issues, fixes

### Step 5: Calculate SSIM (SECONDARY - logging only)
- Run: `python3 "${CLAUDE_PLUGIN_ROOT}/utils/image-similarity.py" preprocessed_baseline.png cropped_screenshot.png`
- Log result: "Iteration {n}: SSIM {score}, LLM: {status}"
- Do NOT use SSIM for pass/fail decision

### Step 6: Handle LLM verdict
- If status == "PASS":
  - Log success
  - If SSIM < config.validation.ssim_sanity_threshold: add warning for human review
  - Exit loop successfully

- If status == "ITERATE":
  - Apply each fix from issues array
  - Increment iteration counter
  - If iterations >= config.validation.max_ralph_iterations: exit with MAX_ITERATIONS status
  - Continue to Step 2

- If status == "STUCK":
  - Log failure reason
  - Exit loop with STUCK status

### Step 7: Return results
Return JSON:
```json
{
  "status": "SUCCESS | STUCK | MAX_ITERATIONS",
  "llm_verdict": "PASS | ITERATE | STUCK",
  "llm_confidence": "HIGH | MEDIUM | LOW",
  "iterations": 3,
  "ssim_history": [0.42, 0.67, 0.81],
  "final_ssim": 0.81,
  "summary": "LLM assessment summary",
  "issues_fixed": ["list of issues that were fixed"],
  "screenshots": ["iteration-1.png", "iteration-2.png", "iteration-3.png"],
  "sanity_warning": false
}
```
```

**Step 2: Update inputs section**

```markdown
## Inputs
- kotlin_file_path: Path to generated .kt file
- baseline_image_path: Path to original baseline (will be preprocessed if needed)
- preprocessed_baseline_path: (optional) Path to already preprocessed baseline
- component_name: Name of component (used for testTag lookup)
- package_name: Package for the component
- temp_dir: Directory for artifacts
- config: Parsed compose-designer.yaml with:
  - validation.visual_similarity_threshold (for sanity check)
  - validation.max_ralph_iterations (loop limit)
  - validation.ssim_sanity_threshold (flag threshold)
  - validation.primary_method (should be "llm_vision")
```

**Step 3: Update outputs section**

```markdown
## Outputs
Returns JSON with:
- status: "SUCCESS" | "STUCK" | "MAX_ITERATIONS"
- llm_verdict: Final LLM verdict
- llm_confidence: LLM confidence level
- iterations: Number of iterations performed
- ssim_history: Array of SSIM scores per iteration
- final_ssim: Last SSIM score
- summary: LLM summary of final state
- issues_fixed: List of issues that were addressed
- screenshots: Array of screenshot paths
- sanity_warning: true if LLM passed but SSIM below sanity threshold
```

**Step 4: Commit**

```bash
git add agents/visual-validator.md
git commit -m "feat(visual-validator): implement LLM Vision primary validation"
```

---

## Task 8: Update Create Command Orchestrator

**Files:**
- Modify: `commands/create.md`

**Step 1: Update Phase 1 to invoke baseline-preprocessor**

After processing input source, add:

```markdown
### Phase 1.5: Baseline Preprocessing

**Step 1: Invoke baseline-preprocessor agent**

Task tool:
  subagent_type: "compose-designer:baseline-preprocessor"
  model: {config.model.baseline_preprocessor || config.model.default}
  description: "Preprocess baseline image"
  prompt: "Preprocess baseline image at {baseline_path}.

  Config:
  - Visual similarity threshold: {config.validation.visual_similarity_threshold}

  Detect device frames, crop to content area, and return preprocessed image path."

**Step 2: Store preprocessing results**

Save returned values:
- preprocessed_baseline_path
- frames_detected
- recommended_threshold
```

**Step 2: Update Phase 3 to pass preprocessed baseline**

Update visual-validator invocation:

```markdown
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
    - validation.visual_similarity_threshold: {config.validation.visual_similarity_threshold}
    - validation.max_ralph_iterations: {config.validation.max_ralph_iterations}
    - validation.ssim_sanity_threshold: {config.validation.ssim_sanity_threshold}
    - validation.primary_method: {config.validation.primary_method}

  Use LLM Vision as primary validation. SSIM for logging only.
  Save screenshots and diffs to: {temp_dir}/"
```

**Step 3: Update final report format**

```markdown
📱 Phase 3: Device Validation
✓ Method: LLM Vision primary (SSIM secondary)
✓ LLM Verdict: {llm_verdict} (Confidence: {llm_confidence})
✓ Iterations: {iteration_count}/{config.validation.max_ralph_iterations}
✓ Final SSIM: {final_ssim:.2%} (threshold: {config.validation.visual_similarity_threshold:.2%})
✓ Status: {status}
✓ Device: {device_name}
{if sanity_warning: "⚠️  LLM passed but SSIM below sanity threshold - manual review recommended"}
{if status != "SUCCESS": "⚠️  {status}: {summary}"}
```

**Step 4: Commit**

```bash
git add commands/create.md
git commit -m "feat(create): integrate LLM Vision validation pipeline"
```

---

## Task 9: Update Plugin Validation Script

**Files:**
- Modify: `tests/validate-plugin.sh`

**Step 1: Add validation for new files**

Add checks for:
- `prompts/llm-vision-validation.md` exists
- `utils/extract-component-bounds.py` exists and is executable
- `utils/crop-image.py` exists and is executable

**Step 2: Add utility tests**

```bash
# Test extract-component-bounds.py
echo '[{"testTag": "Test", "bounds": {"x": 0, "y": 0, "width": 100, "height": 100}}]' > /tmp/test-hierarchy.json
result=$(python3 "${PLUGIN_DIR}/utils/extract-component-bounds.py" /tmp/test-hierarchy.json Test 2>/dev/null)
if echo "$result" | grep -q '"found": true'; then
  echo "✓ extract-component-bounds.py works"
else
  echo "✗ extract-component-bounds.py failed"
  exit 1
fi
```

**Step 3: Commit**

```bash
git add tests/validate-plugin.sh
git commit -m "test(validate): add checks for new validation utilities"
```

---

## Task 10: Integration Test

**Files:**
- No file changes, manual testing

**Step 1: Reset test environment**

```bash
cd test-project
# Ensure config has new fields
cat .claude/compose-designer.yaml
```

**Step 2: Run full workflow**

```bash
/compose-design create --input test-images/jetnews.png --name JetNewsCard --type component
```

**Step 3: Verify each phase**

- Phase 0: Config loads with new validation fields
- Phase 1: Baseline preprocessed (frames detected, cropped)
- Phase 2: Code generated with testTag included
- Phase 3: LLM Vision validates (check llm_verdict in output)
- Phase 4: Report shows LLM-based results

**Step 4: Verify edge cases**

1. Test with simple single-device baseline
2. Test with composite layout (multiple devices)
3. Test with no device frame (raw UI screenshot)

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat(compose-designer): validation pipeline v2 complete

- LLM Vision as primary validation source
- Automatic baseline preprocessing with device frame detection
- Component bounds extraction from view hierarchy
- SSIM as secondary metric for logging
- Configurable thresholds from compose-designer.yaml"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Update configuration schema | commands/config.md, test-project/.claude/compose-designer.yaml |
| 2 | Enhance baseline-preprocessor agent | agents/baseline-preprocessor.md |
| 3 | Add test tags to generated components | agents/design-generator.md |
| 4 | Create component bounds extraction utility | utils/extract-component-bounds.py |
| 5 | Create image cropping utility | utils/crop-image.py |
| 6 | Create LLM Vision validation prompt | prompts/llm-vision-validation.md |
| 7 | Update visual-validator agent | agents/visual-validator.md |
| 8 | Update create command orchestrator | commands/create.md |
| 9 | Update plugin validation script | tests/validate-plugin.sh |
| 10 | Integration test | N/A |

**Key Config Values Used:**
- `config.validation.visual_similarity_threshold` - SSIM sanity threshold
- `config.validation.max_ralph_iterations` - Loop limit
- `config.validation.ssim_sanity_threshold` - Flag threshold for human review
- `config.validation.primary_method` - "llm_vision" (default)
- `config.model.*` - Per-agent model selection
