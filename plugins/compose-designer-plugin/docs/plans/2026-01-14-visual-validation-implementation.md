# Visual Validation Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace preview-based visual validation with device-centric validation using SSIM + LLM vision dual comparison.

**Architecture:** Device screenshots are captured via mobile-mcp, compared against baseline using SSIM for threshold and LLM vision for semantic feedback. Figma MCP extracts precise tokens when available.

**Tech Stack:** Python (SSIM), mobile-mcp (device interaction), Figma MCP (token extraction), Bash scripting

---

## Task 1: Add LLM Vision Comparison Utility

**Files:**
- Create: `utils/vision-compare.md`

**Step 1: Create vision comparison prompt template**

Create `utils/vision-compare.md`:

```markdown
# Vision Compare Utility

Compare two UI images and return structured differences.

## Usage

Called by visual-validator agent with two image paths.

## Prompt Template

You are comparing a baseline design image against a current device screenshot.

Analyze both images and identify specific differences in:
- Colors (hex values if possible)
- Spacing/padding (in dp)
- Font sizes (in sp)
- Corner radius (in dp)
- Layout alignment
- Missing or extra elements

Return a JSON object:

\`\`\`json
{
  "similarity_assessment": "high|medium|low",
  "differences": [
    {
      "element": "element name or description",
      "property": "color|spacing|fontSize|cornerRadius|alignment|other",
      "baseline": "value in baseline",
      "current": "value in current screenshot",
      "fix": "specific code change suggestion"
    }
  ],
  "priority_fixes": ["list of most impactful fixes to try first"]
}
\`\`\`

Be specific. Instead of "colors are different", say "button background is #FFFFFF in baseline but #F5F5F5 in current".
```

**Step 2: Verify file created**

Run: `cat utils/vision-compare.md | head -20`
Expected: Shows the prompt template header

**Step 3: Commit**

```bash
git add utils/vision-compare.md
git commit -m "feat: add LLM vision comparison utility template"
```

---

## Task 2: Enhance image-similarity.py with JSON Output

**Files:**
- Modify: `utils/image-similarity.py`

**Step 1: Read current implementation**

Run: `cat utils/image-similarity.py`
Understand current structure before modifying.

**Step 2: Add JSON output option**

Add `--json` flag that outputs structured result:

```python
# Add to argument parser (after existing args)
parser.add_argument('--json', action='store_true',
                    help='Output result as JSON')

# Replace the print statement at the end with:
if args.json:
    import json
    result = {
        "similarity": float(f"{similarity:.4f}"),
        "threshold_met": similarity >= 0.92,
        "baseline": args.baseline,
        "current": args.current,
        "diff_image": args.output if args.output else None
    }
    print(json.dumps(result))
else:
    print(f"{similarity:.4f}")
```

**Step 3: Test JSON output**

Run: `python3 utils/image-similarity.py /tmp/tuman-vpn-test.png /tmp/tuman-vpn-test.png --json`
Expected: `{"similarity": 1.0, "threshold_met": true, ...}`

**Step 4: Test with diff images**

Run: `python3 utils/image-similarity.py /tmp/compose-designer.E4W2KR/baseline.png /tmp/compose-designer.E4W2KR/device-screenshot.png --json --output /tmp/diff.png`
Expected: JSON with similarity score and diff image path

**Step 5: Commit**

```bash
git add utils/image-similarity.py
git commit -m "feat: add JSON output option to image-similarity.py"
```

---

## Task 3: Create Figma Token Extraction Utility

**Files:**
- Create: `utils/figma-tokens.sh`

**Step 1: Create token extraction script**

Create `utils/figma-tokens.sh`:

```bash
#!/bin/bash
# Extract design tokens from Figma via MCP
#
# Usage: ./figma-tokens.sh <figma-url>
# Output: JSON with extracted color, spacing, typography tokens

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

error() { echo -e "${RED}Error: $1${NC}" >&2; exit 1; }
info() { echo -e "${GREEN}$1${NC}" >&2; }

# Parse Figma URL to extract node ID
parse_url() {
    local url="$1"
    # Reuse existing figma-client.sh parsing
    "${SCRIPT_DIR}/figma-client.sh" parse "$url"
}

# Main
if [ -z "${1:-}" ]; then
    error "Usage: $0 <figma-url>"
fi

FIGMA_URL="$1"

info "Extracting design tokens from Figma..."
info "Note: This script outputs token info. Use Figma MCP tools directly for full extraction."

# Parse URL
IFS='|' read -r file_id node_id <<< "$(parse_url "$FIGMA_URL")"

echo "{"
echo "  \"file_id\": \"$file_id\","
echo "  \"node_id\": \"$node_id\","
echo "  \"extraction_method\": \"figma_mcp\","
echo "  \"tools_to_use\": ["
echo "    \"mcp__figma-desktop__get_design_context\","
echo "    \"mcp__figma-desktop__get_variable_defs\","
echo "    \"mcp__figma-desktop__get_screenshot\""
echo "  ]"
echo "}"
```

**Step 2: Make executable**

Run: `chmod +x utils/figma-tokens.sh`

**Step 3: Test script**

Run: `./utils/figma-tokens.sh "https://www.figma.com/design/71S15RDmRITiWR7Na6uKbt/Tuman-VPN---Screens?node-id=1748-854"`
Expected: JSON with file_id, node_id, and tools list

**Step 4: Commit**

```bash
git add utils/figma-tokens.sh
git commit -m "feat: add Figma token extraction utility"
```

---

## Task 4: Rewrite visual-validator Agent

**Files:**
- Modify: `agents/visual-validator.md`

**Step 1: Read current implementation**

Run: `cat agents/visual-validator.md`
Understand current structure.

**Step 2: Rewrite agent with device-centric approach**

Replace entire contents of `agents/visual-validator.md`:

```markdown
---
description: Validates generated Compose UI against design baseline using device screenshots and dual comparison (SSIM + LLM vision)
capabilities:
  - Deploy APK to connected Android device
  - Capture device screenshots via mobile-mcp
  - Calculate SSIM similarity score
  - Analyze visual differences using LLM vision
  - Apply targeted fixes based on feedback
  - Iterate until threshold reached or max iterations
model: sonnet
color: blue
tools:
  - Read
  - Edit
  - Bash
  - mcp__mobile-mcp__mobile_list_available_devices
  - mcp__mobile-mcp__mobile_install_app
  - mcp__mobile-mcp__mobile_launch_app
  - mcp__mobile-mcp__mobile_take_screenshot
  - mcp__mobile-mcp__mobile_save_screenshot
---

# Visual Validator Agent

Validates generated Compose code against design baseline through iterative device-based refinement.

## Inputs Required

- `kotlin_file_path`: Path to generated .kt file
- `baseline_image_path`: Path to design baseline PNG
- `package_name`: Android app package name
- `temp_dir`: Directory for artifacts
- `threshold`: SSIM threshold (default: 0.92)
- `max_iterations`: Maximum refinement iterations (default: 8)

## Validation Loop

### Step 1: Build APK

```bash
./gradlew assembleDebug
```

If build fails, report error and stop.

### Step 2: Deploy to Device

```
mcp__mobile-mcp__mobile_install_app(
  device: <selected_device_id>,
  path: "app/build/outputs/apk/debug/app-debug.apk"
)

mcp__mobile-mcp__mobile_launch_app(
  device: <selected_device_id>,
  packageName: <package_name>
)
```

Wait 2 seconds for app to render.

### Step 3: Capture Screenshot

```
mcp__mobile-mcp__mobile_save_screenshot(
  device: <selected_device_id>,
  saveTo: "{temp_dir}/iteration-{n}.png"
)
```

### Step 4: SSIM Comparison

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/utils/image-similarity.py" \
  "{baseline_image_path}" \
  "{temp_dir}/iteration-{n}.png" \
  --json \
  --output "{temp_dir}/diff-{n}.png"
```

Parse JSON result for similarity score.

### Step 5: Check Threshold

If `similarity >= threshold`:
- Report SUCCESS
- Return final score and iteration count

If `iteration >= max_iterations`:
- Report MAX_ITERATIONS_REACHED
- Show final diff image
- Ask user for guidance

### Step 6: LLM Vision Analysis

Read both images (baseline and current screenshot).

Analyze differences and identify specific issues:
- Color mismatches (provide hex values)
- Spacing errors (provide dp values)
- Font size differences (provide sp values)
- Layout alignment issues
- Missing or extra elements

Output structured feedback:
```json
{
  "differences": [...],
  "priority_fixes": [...]
}
```

### Step 7: Apply Fixes

Edit the Kotlin file to address priority fixes:

1. Read current file content
2. For each priority fix:
   - Locate the relevant code section
   - Apply the specific change
3. Save file

### Step 8: Loop

Increment iteration counter.
Go back to Step 1.

## Stuck Detection

Track last 3 similarity scores. If improvement < 0.01 for 3 consecutive iterations:

1. Stop loop
2. Show side-by-side comparison
3. Show diff image
4. Show LLM analysis
5. Ask user:
   - "Manual adjustment needed?"
   - "Lower threshold?"
   - "Accept current result?"

## Output

Return JSON:
```json
{
  "status": "SUCCESS|STUCK|MAX_ITERATIONS",
  "final_similarity": 0.93,
  "iterations": 4,
  "screenshots": ["iteration-1.png", ...],
  "diff_images": ["diff-1.png", ...]
}
```
```

**Step 3: Verify frontmatter is valid YAML**

Run: `head -20 agents/visual-validator.md`
Expected: Valid YAML frontmatter with tools list including mobile-mcp

**Step 4: Commit**

```bash
git add agents/visual-validator.md
git commit -m "feat: rewrite visual-validator for device-centric validation"
```

---

## Task 5: Update design-generator Agent for Figma MCP

**Files:**
- Modify: `agents/design-generator.md`

**Step 1: Read current implementation**

Run: `cat agents/design-generator.md`

**Step 2: Add Figma MCP integration section**

Add after the existing "Inputs Required" section:

```markdown
## Figma Token Extraction (when Figma URL provided)

If input is a Figma URL, extract precise design tokens BEFORE generating code:

### Step 1: Get Design Context

Use Figma MCP tool:
```
mcp__figma-desktop__get_design_context(
  nodeId: "<extracted_node_id>",
  clientLanguages: "kotlin",
  clientFrameworks: "jetpack-compose"
)
```

Parse response for:
- Component hierarchy
- Layout structure (row, column, stack)
- Component types (text, button, image, etc.)

### Step 2: Get Variable Definitions

Use Figma MCP tool:
```
mcp__figma-desktop__get_variable_defs(
  nodeId: "<extracted_node_id>"
)
```

Parse response for:
- Colors: Map Figma color names to hex values
- Spacing: Extract padding, margin, gap values
- Typography: Font family, size, weight, line height
- Corner radius values
- Shadow/elevation values

### Step 3: Get Screenshot as Baseline

Use Figma MCP tool:
```
mcp__figma-desktop__get_screenshot(
  nodeId: "<extracted_node_id>"
)
```

Save screenshot as baseline for validation phase.

### Step 4: Generate Code with Precise Values

When generating Compose code, use EXACT values from Figma:

Instead of:
```kotlin
// LLM guessing
color = Color.White
padding = 16.dp
```

Use:
```kotlin
// Precise from Figma
color = Color(0xFFFFFFFF)  // From variable_defs
padding = 16.dp             // From variable_defs spacing token
```

This results in ~80-85% accuracy on first generation vs ~60-70% with screenshots.
```

**Step 3: Add Figma MCP tools to frontmatter**

Update the tools list in frontmatter to include:
```yaml
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - mcp__figma-desktop__get_design_context
  - mcp__figma-desktop__get_variable_defs
  - mcp__figma-desktop__get_screenshot
```

**Step 4: Commit**

```bash
git add agents/design-generator.md
git commit -m "feat: add Figma MCP integration to design-generator"
```

---

## Task 6: Simplify create.md Command Flow

**Files:**
- Modify: `commands/create.md`

**Step 1: Read current implementation**

Run: `cat commands/create.md | head -100`

**Step 2: Update phase structure**

Find the section defining phases and update:

```markdown
### Phase Structure (Simplified)

**Phase 1: Input Processing**
- Load configuration
- Validate arguments
- If Figma URL: Extract tokens via Figma MCP
- If Screenshot: Use as baseline directly
- Create temp directory

**Phase 2: Code Generation**
- Invoke design-generator agent
- Pass Figma tokens if available
- Output: Generated .kt file

**Phase 3: Device Validation** (merged from old Phase 2+3)
- Invoke visual-validator agent
- Device-centric loop:
  - Build → Deploy → Screenshot → Compare → Refine
- Continue until SSIM ≥ threshold or max iterations
- Output: Validated .kt file + screenshots

**Phase 4: Final Report**
- Summarize results
- Offer commit option
```

**Step 3: Update TodoWrite task list**

Find the task list section and update:

```json
[
  {"content": "Load configuration and validate inputs", "status": "pending", "activeForm": "Loading configuration"},
  {"content": "Process input and extract Figma tokens (if URL)", "status": "pending", "activeForm": "Processing input"},
  {"content": "Generate initial Compose code", "status": "pending", "activeForm": "Generating code"},
  {"content": "Device validation loop (SSIM + LLM vision)", "status": "pending", "activeForm": "Validating on device"},
  {"content": "Generate final report", "status": "pending", "activeForm": "Generating report"}
]
```

**Step 4: Commit**

```bash
git add commands/create.md
git commit -m "feat: simplify create.md with merged device validation phase"
```

---

## Task 7: Update plugin.json with New Tools

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: Read current plugin.json**

Run: `cat .claude-plugin/plugin.json`

**Step 2: Verify agents are registered**

Ensure all agents in `agents/` array:
- `./agents/baseline-preprocessor.md`
- `./agents/design-generator.md`
- `./agents/visual-validator.md`
- `./agents/device-tester.md`

**Step 3: Bump version**

Update version field:
```json
"version": "0.3.0"
```

(Minor version bump for new feature)

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 0.3.0 for visual validation redesign"
```

---

## Task 8: Integration Test

**Files:**
- No new files, testing existing

**Step 1: Test with Screenshot Input**

Run the full workflow:
```bash
# In test-project directory
/compose-design create --input test-images/jetnews.png --name TestCard --type component
```

Expected:
- Code generates
- Deploys to device
- SSIM comparison runs
- Iterates until threshold
- Final report shows similarity score

**Step 2: Test with Figma Input**

Run:
```bash
/compose-design create --input "https://www.figma.com/design/71S15RDmRITiWR7Na6uKbt/Tuman-VPN---Screens?node-id=1748-854" --name TumanSettings --type screen
```

Expected:
- Figma MCP extracts tokens
- Code generates with precise values
- Fewer iterations needed (precise start)
- Final report shows similarity score

**Step 3: Verify SSIM threshold met**

Check final similarity in report:
- Screenshot path: Should reach 92%+ in ≤8 iterations
- Figma path: Should reach 92%+ in ≤5 iterations

**Step 4: Final commit**

```bash
git add -A
git commit -m "test: verify visual validation redesign integration"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | LLM vision comparison utility | `utils/vision-compare.md` |
| 2 | JSON output for image-similarity.py | `utils/image-similarity.py` |
| 3 | Figma token extraction utility | `utils/figma-tokens.sh` |
| 4 | Rewrite visual-validator agent | `agents/visual-validator.md` |
| 5 | Add Figma MCP to design-generator | `agents/design-generator.md` |
| 6 | Simplify create.md flow | `commands/create.md` |
| 7 | Update plugin version | `.claude-plugin/plugin.json` |
| 8 | Integration testing | (no new files) |

**Total: 8 tasks, ~30-40 minutes estimated**
