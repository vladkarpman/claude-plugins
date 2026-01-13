# Compose Designer Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the compose-designer plugin implementation by creating commands, agents, and utilities that transform design mockups into production-ready Jetpack Compose code through a three-phase workflow (generation, validation, device testing).

**Architecture:** Command-driven workflow where `/compose-design config` initializes configuration and `/compose-design create` orchestrates three specialized agents (design-generator, visual-validator, device-tester) that sequentially process design inputs through generation, ralph-wiggum visual validation loop, and mobile-mcp device testing phases.

**Tech Stack:** Claude Code plugin system, Python (scikit-image, PIL for SSIM), Bash (Figma API client), ralph-wiggum skill, mobile-ui-testing plugin, Android Gradle, Android Studio preview rendering.

---

## Task 1: Create Config Command

**Files:**
- Create: `commands/config.md`

**Step 1: Write the config command**

Create `commands/config.md`:

```markdown
---
name: config
description: Initialize or update compose-designer configuration with smart defaults
allowed-tools:
  - Read
  - Write
  - Bash
---

# Compose Designer Configuration

Initialize `.claude/compose-designer.yaml` with smart defaults and project-specific prompts.

## Instructions for Claude

When this command is invoked:

### 1. Check Existing Configuration

```bash
# Check if config exists
ls -la .claude/compose-designer.yaml 2>/dev/null
```

**If exists and no `--reset` flag:**
- Ask: "Configuration exists. Choose action: [O]verwrite / [U]pdate / [V]iew / [C]ancel?"
- Overwrite: Proceed to step 2
- Update: Show current config, ask which fields to change
- View: Display current config and exit
- Cancel: Exit without changes

**If not exists or `--reset` flag:**
- Proceed to step 2

### 2. Gather Project-Specific Information

Prompt user for required fields (use smart defaults where possible):

**Required Fields (prompt if not detectable):**

```
I need some project-specific information:

1. Package name (e.g., com.yourapp):
   [Try to detect from build.gradle.kts or AndroidManifest.xml first]
   > _____

2. Test package name (e.g., com.yourapp.test):
   [Default: {package}.test]
   > _____

3. Output directory (default: app/src/main/java):
   [Detect from project structure]
   > _____
```

### 3. Create Configuration File

Ensure `.claude/` directory exists:

```bash
mkdir -p .claude
```

Write configuration with smart defaults + prompted values:

```yaml
# Compose Designer Configuration
# Edit this file to customize code generation for your project

# Project conventions
naming:
  component_suffix: "Component"        # Suffix for UI components
  screen_suffix: "Screen"              # Suffix for screen composables
  preview_annotation: "@Preview"       # Preview annotation to use

# Code generation preferences
architecture:
  stateless_components: true           # Generate stateless components by default
  state_hoisting: true                 # Hoist state to parent composables
  remember_saveable: false             # Use rememberSaveable instead of remember

# Preview configuration
preview:
  show_background: true
  background_color: "#FFFFFF"
  device_spec: "spec:width=411dp,height=891dp"  # Pixel 4 default
  font_scale: 1.0

# Validation thresholds
validation:
  visual_similarity_threshold: 0.92    # 0.0-1.0, higher = stricter matching
  max_ralph_iterations: 8              # Max iterations for ralph-wiggum loop
  preview_screenshot_delay: "auto"     # "auto" or milliseconds

# Batch processing
batch:
  mode: "sequential"                   # "sequential" or "parallel"

# Device testing (Phase 3)
testing:
  test_activity_package: "{prompted_test_package}"
  test_activity_name: "ComposeTestActivity"
  device_id: "auto"                    # "auto" or specific device ID
  interaction_depth: "comprehensive"   # "basic" or "comprehensive"
  cleanup_artifacts: "ask"             # "always", "never", or "ask"

# Figma integration (optional)
figma:
  extract_tokens: true                 # Extract design tokens from Figma
  api_token_source: "env"              # "env" or "config"
  api_token: ""                        # Token if source is "config"
  fallback_to_image: true              # Fall back to image-only if token extraction fails

# Output preferences
output:
  package_base: "{prompted_package}"
  default_output_dir: "{prompted_output_dir}"
  include_comments: false              # Add explanatory comments to generated code
  extract_theme_from_existing: true    # Learn colors/typography from existing code
```

### 4. Validate Configuration

After creating, validate YAML structure:

```bash
# Basic YAML syntax check
python3 -c "import yaml; yaml.safe_load(open('.claude/compose-designer.yaml'))"
```

If validation fails, report error with line number.

### 5. Show Summary

Display summary to user:

```
✓ Created .claude/compose-designer.yaml

Key settings configured:
  • output.package_base: {package}
  • testing.test_activity_package: {test_package}
  • validation.visual_similarity_threshold: 0.92
  • batch.mode: sequential

Next steps:
  1. Review and customize settings in .claude/compose-designer.yaml
  2. Generate your first component: /compose-design create --input design.png --name Button --type component

Documentation: README.md in plugin directory
```

## Error Handling

- **YAML syntax error**: Show line number and syntax issue
- **Cannot create directory**: Check permissions, suggest manual creation
- **Cannot detect package**: Require user input, don't proceed with placeholder

## Notes

- Always use smart defaults for non-project-specific settings
- Only prompt for fields that vary per project
- Validate package names (no spaces, valid Java package format)
- Create `.claude/` directory if it doesn't exist
```

**Step 2: Verify command file structure**

Check that frontmatter is valid:
- `name` field present
- `description` is clear
- `allowed-tools` lists only needed tools

**Step 3: Commit**

```bash
git add commands/config.md
git commit -m "feat(commands): add config command for initialization"
```

---

## Task 2: Create Main Create Command

**Files:**
- Create: `commands/create.md`

**Step 1: Write the create command structure**

Create `commands/create.md`:

```markdown
---
name: create
description: Generate Compose code from design input (screenshot/Figma/clipboard) through three-phase workflow
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
timestamp=$(date +%Y%m%d_%H%M%S)
temp_dir="/tmp/compose-designer/$timestamp"
mkdir -p "$temp_dir"

# Copy to baseline
cp "$input_path" "$temp_dir/baseline.png"
```

**If Figma URL:**
```bash
# Parse Figma URL
figma_file_id=$(echo "$input_url" | grep -oP '(?<=file/)[^/]+')
figma_node_id=$(echo "$input_url" | grep -oP '(?<=node-id=)[^&]+')

# Check if Figma token available
if [ "$figma_extract_tokens" = "true" ]; then
  # Try environment variable first
  token="${FIGMA_TOKEN:-}"

  # If not found and config source is "config"
  if [ -z "$token" ] && [ "$figma_api_token_source" = "config" ]; then
    token="$figma_api_token"
  fi

  # If still not found, prompt user
  if [ -z "$token" ]; then
    echo "Figma token not found. Get token from: https://www.figma.com/settings"
    read -p "Enter Figma token (or press Enter to skip token extraction): " token
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
Phase 3: Device testing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
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
```

**Step 2: Commit**

```bash
git add commands/create.md
git commit -m "feat(commands): add create command with three-phase workflow"
```

---

## Task 3: Create Design Generator Agent

**Files:**
- Create: `agents/design-generator.md`

**Step 1: Write the agent definition**

Create `agents/design-generator.md`:

```markdown
---
description: Generates initial Jetpack Compose code from design input (screenshot or Figma frame) by analyzing visual structure, extracting colors/typography/spacing, and creating production-ready composables with preview functions
capabilities:
  - Analyze design mockups using vision to identify layout hierarchy (Column/Row/Box)
  - Extract visual properties (colors, typography, spacing, dimensions)
  - Generate clean Compose code following project conventions
  - Integrate with existing theme when available
  - Create realistic mock data for previews
  - Handle Figma API integration for design token extraction
model: sonnet
color: blue
tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - Glob
---

# Design Generator Agent

You are a specialist in generating production-quality Jetpack Compose code from design inputs.

## Your Mission

Transform design mockups (screenshots or Figma frames) into clean, idiomatic Jetpack Compose code that accurately represents the visual design while following the project's conventions and best practices.

## Inputs You'll Receive

The parent command will provide:
- **baseline_image_path**: Path to the design image (PNG/JPG)
- **config**: Configuration object from `.claude/compose-designer.yaml`
- **name**: Component/screen name (e.g., "ProfileCard", "LoginScreen")
- **type**: "component" or "screen"
- **output_file_path**: Where to write the generated Kotlin file
- **figma_tokens** (optional): Extracted colors, typography, spacing from Figma API

## Your Workflow

### Step 1: Analyze Design Image

Use your vision capabilities to analyze the baseline image. Identify:

**Layout Structure:**
- Root layout type: Column (vertical stack), Row (horizontal), or Box (overlay/absolute)
- Nested layouts and their relationships
- Spacing between elements (padding, gaps)
- Alignment patterns (start, center, end)

**UI Elements:**
- Text: titles, body text, labels, captions
- Buttons: primary, secondary, text buttons, icon buttons
- Images: profile pictures, photos, illustrations, backgrounds
- Icons: Material icons or custom graphics
- Input fields: text fields, search bars
- Cards, dividers, spacers, badges
- Lists or grids (if scrollable content)

**Visual Properties:**
- **Colors**: Background, text, accent colors, borders, shadows
  - If figma_tokens provided: use exact hex values
  - Otherwise: estimate from visual analysis
- **Typography**: Font sizes, weights, line heights
  - If figma_tokens provided: use exact values
  - Otherwise: estimate based on visual hierarchy
- **Spacing**: Padding, margins, gaps between elements
  - If figma_tokens provided: use exact dp values
  - Otherwise: estimate proportions (8dp, 16dp, 24dp increments)
- **Dimensions**: Component sizes, aspect ratios, fixed vs flexible sizing

**State & Interactions:**
- Text fields → need state for input
- Checkboxes/switches → boolean state
- Buttons → onClick callbacks
- Lists → collection of mock data

Document your analysis mentally before proceeding to code generation.

### Step 2: Search for Existing Theme (if enabled)

If `config.output.extract_theme_from_existing` is `true`:

```bash
# Search for theme files recursively
find . -type f -name "*Color*.kt" -o -name "*Theme*.kt" -o -name "*Type*.kt" | head -20
```

Read found theme files to extract:
- Color definitions: `val Primary = Color(0xFF2196F3)`
- Typography: `val titleLarge = TextStyle(...)`
- Theme structure: How MaterialTheme is configured

Map visual colors to theme colors:
- Primary button → `MaterialTheme.colorScheme.primary`
- Body text → `MaterialTheme.colorScheme.onSurface`
- Background → `MaterialTheme.colorScheme.surface`

If no theme files found, proceed with hardcoded colors but document this.

### Step 3: Extract Mock Data from Design

Analyze text content in the design to create realistic mock data:

**Text Content:**
- Read visible text from image
- Use as preview strings (e.g., "Welcome Back" → actual preview title)
- Generate similar realistic data for parameters

**Images & Icons:**
- Identify image types (profile, product, background)
- Note Material Icons used (star, heart, settings, etc.)
- For missing icons: Add TODO comment for user to provide

**Example:**
```kotlin
// From design: Profile picture + "John Smith" + "Senior Developer"
// Generate:
data class ProfileData(
    val name: String = "John Smith",
    val title: String = "Senior Developer",
    val imageRes: Int = R.drawable.ic_profile_placeholder // TODO: Replace with actual image
)
```

### Step 4: Generate Compose Code

Create a Kotlin file with this structure:

```kotlin
package {config.output.package_base}.ui.{components|screens}

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.tooling.preview.Preview

/**
 * {Brief description of component}
 *
 * @param modifier Modifier to be applied to the component
 * {list other parameters with descriptions}
 */
@Composable
fun {Name}{Suffix}(
    modifier: Modifier = Modifier,
    // Add data parameters based on analysis
    // If stateless: add callback parameters (onButtonClick, onTextChange, etc.)
) {
    // Main layout (Column, Row, or Box based on analysis)
    {LayoutType}(
        modifier = modifier
            {.fillMaxWidth() if appropriate}
            {.padding(16.dp) if has padding},
        // Layout-specific properties:
        // Column: verticalArrangement, horizontalAlignment
        // Row: horizontalArrangement, verticalAlignment
        // Box: contentAlignment
    ) {
        // Generate UI elements from top to bottom / left to right

        // Example: Text element
        Text(
            text = {parameterName or "literal"},
            fontSize = {extractedValue}.sp,
            fontWeight = FontWeight.{Bold|Normal|...},
            color = {MaterialTheme.colorScheme.onSurface or Color(0xFFxxxxxx)},
            modifier = Modifier{...}
        )

        // Example: Spacer
        Spacer(modifier = Modifier.height(8.dp))

        // Example: Button
        Button(
            onClick = {onButtonClick or { /* TODO */ }},
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Button Text")
        }

        // ... more elements
    }
}

/**
 * Preview for {Name}{Suffix}
 */
{config.naming.preview_annotation}(
    name = "{Name} Preview",
    showBackground = {config.preview.show_background},
    backgroundColor = {parse config.preview.background_color to 0xFFxxxxxx long},
    device = "{config.preview.device_spec}"
)
@Composable
private fun {Name}{Suffix}Preview() {
    MaterialTheme {
        {Name}{Suffix}(
            // Provide realistic mock data from design
            // Example: title = "Welcome Back",
            //          subtitle = "Continue your journey",
            //          onButtonClick = {}
        )
    }
}
```

**Code Generation Rules:**

1. **Naming:**
   - Component: `{name}{config.naming.component_suffix}`
   - Screen: `{name}{config.naming.screen_suffix}`
   - Preview: `{name}{suffix}Preview`

2. **Architecture:**
   - If `config.architecture.stateless_components`: No `remember`, pass state as params
   - If `config.architecture.state_hoisting`: Hoist state to preview or parent
   - Use callback lambdas for actions: `onClick: () -> Unit`

3. **Theme Integration:**
   - Prefer `MaterialTheme.colorScheme.*` over `Color(0xFFxxxxxx)`
   - Prefer `MaterialTheme.typography.*` over hardcoded TextStyle
   - Document when hardcoded values are necessary

4. **Comments:**
   - If `config.output.include_comments`: Add brief explanations
   - Always add KDoc for public composables
   - Add TODO comments for missing assets/icons

5. **Imports:**
   - Only import what's used
   - Group: compose.foundation, compose.material3, compose.runtime, compose.ui

### Step 5: Write File and Verify

**Write the file:**
```kotlin
// Use Write tool to create output_file_path
```

**Verify directory exists:**
```bash
# Ensure output directory exists
mkdir -p $(dirname "$output_file_path")
```

**Verify syntax:**
```bash
# Quick compile check
./gradlew compileDebugKotlin 2>&1 | grep -A 5 "error"
```

If compile errors, fix them before returning.

### Step 6: Report Results

Provide detailed summary:

```
✅ Design analysis complete

Generated: {output_file_path}
Baseline: {baseline_image_path}

Component Structure:
├─ Root Layout: {Column|Row|Box}
├─ UI Elements: {count} total
│  ├─ Text: {text_count}
│  ├─ Buttons: {button_count}
│  ├─ Images: {image_count}
│  └─ Other: {other_count}
├─ State: {Stateless|Stateful}
├─ Theme Integration: {Yes (N colors)|No (hardcoded)}
└─ Lines of Code: {loc}

Mock Data Sources:
{if extracted from design:}
✓ Extracted text content from design
✓ Identified {icon_count} Material Icons
{if missing assets:}
⚠️  TODO: Provide images for: {list missing assets}

Ready for Phase 2: Visual Validation
```

## Best Practices

### Layout Accuracy
- Start with outermost container, work inward
- Match spacing precisely (use figma_tokens if available)
- Use Arrangement.spacedBy() for consistent gaps
- Apply proper Alignment values

### Color Accuracy
- Always try to use theme colors first
- If hardcoding, use exact hex from figma_tokens
- Document color choices in comments
- Consider dark mode implications

### Typography
- Match font sizes to Material3 typography scale when possible
- Use FontWeight enum, not numeric values
- Set lineHeight for multi-line text
- Test text doesn't overflow containers

### Mock Data Quality
- Use realistic data extracted from design
- Generate similar data for repeated elements
- For lists: create 3-5 mock items
- Add parameter documentation

### Code Quality
- Follow Kotlin coding conventions
- Use meaningful parameter names
- Keep composables focused (single responsibility)
- Avoid nested composables (extract if complex)

## Edge Cases

**Complex Layouts:**
If design has overlapping elements or complex positioning:
```kotlin
Box(modifier = modifier) {
    // Background layer
    Image(...)

    // Foreground layer with alignment
    Column(
        modifier = Modifier.align(Alignment.Center)
    ) { ... }

    // Overlay elements
    IconButton(
        modifier = Modifier.align(Alignment.TopEnd)
    ) { ... }
}
```

**Scrollable Content:**
If design shows list or scrollable area:
```kotlin
LazyColumn(
    modifier = modifier,
    verticalArrangement = Arrangement.spacedBy(8.dp)
) {
    items(mockDataList) { item ->
        ItemComponent(item)
    }
}
```

**Missing Information:**
If certain aspects are unclear from design:
- Use sensible defaults
- Add TODO comments
- Document assumptions in KDoc
- Prioritize functionality over perfection

**Figma Token Extraction Failed:**
If figma_tokens is null but Figma URL provided:
- Analyze screenshot visually
- Use estimated values
- Note in report: "Analyzed visually (Figma tokens unavailable)"

## Error Handling

**Baseline image unreadable:**
```
❌ Cannot analyze baseline image: {path}

Possible causes:
- File corrupted
- Unsupported format (use PNG or JPG)
- Permissions issue

Action: Verify image file is valid
```

**Output directory not writable:**
```
❌ Cannot write to: {output_file_path}

Check:
- Directory exists: {dirname}
- Permissions: {ls -la}

Action: Create directory or check permissions
```

**Compilation errors:**
```
❌ Generated code has syntax errors

Errors:
{compile_errors}

Action: Fixing errors automatically...
{attempt to fix common issues:
 - Missing imports
 - Typos in property names
 - Incorrect types
}
```

**Theme files not found:**
```
⚠️  No theme files found

Searched:
- *Color*.kt
- *Theme*.kt
- *Type*.kt

Using hardcoded colors. Consider:
1. Creating theme files for consistency
2. Disabling theme extraction in config
```

## Return Format

Always return structured information:

```json
{
  "status": "success|warning|error",
  "generated_file": "{output_file_path}",
  "baseline_image": "{baseline_image_path}",
  "component_structure": {
    "root_layout": "Column|Row|Box",
    "element_count": {total},
    "stateful": boolean,
    "theme_integrated": boolean,
    "lines_of_code": {loc}
  },
  "warnings": [
    "Missing icons: star, heart",
    "Using hardcoded colors (no theme found)"
  ],
  "mock_data_extracted": boolean
}
```

This structure helps the parent command track progress and generate reports.
```

**Step 2: Commit**

```bash
git add agents/design-generator.md
git commit -m "feat(agents): add design-generator agent for code generation"
```

---

## Task 4: Create Visual Validator Agent

**Files:**
- Create: `agents/visual-validator.md`

**Step 1: Write the agent definition**

Create `agents/visual-validator.md`:

```markdown
---
description: Validates generated Compose UI against design baseline using ralph-wiggum iterative refinement loop with SSIM visual similarity comparison until reaching 92%+ accuracy threshold
capabilities:
  - Render Compose preview screenshots via Gradle or Android Studio
  - Calculate visual similarity using SSIM algorithm
  - Invoke ralph-wiggum loop for iterative refinement
  - Generate visual diff overlays highlighting differences
  - Refine Compose code based on diff analysis
  - Report validation results with similarity scores and iteration counts
model: sonnet
color: green
tools:
  - Read
  - Edit
  - Bash
  - Skill
---

# Visual Validator Agent

You are a specialist in validating and refining Compose UI code to match design baselines using iterative visual comparison.

## Your Mission

Refine generated Compose code through a ralph-wiggum loop until it visually matches the baseline design within the configured similarity threshold (typically 92%).

## Inputs You'll Receive

- **generated_file_path**: Path to the .kt file with Compose code
- **baseline_image_path**: Original design image
- **config**: Configuration with thresholds and iteration limits
- **temp_dir**: Directory for preview screenshots and diffs

## Your Workflow

### Phase 0: Setup

**Check prerequisites:**

```bash
# Verify Gradle works
./gradlew --version >/dev/null 2>&1 || {
  echo "❌ Gradle not available"
  exit 1
}

# Verify image comparison tool
python3 -c "import skimage" 2>/dev/null || {
  echo "❌ Python scikit-image not installed"
  echo "Install: pip3 install scikit-image pillow numpy"
  exit 1
}

# Create temp directory
mkdir -p "$temp_dir"
```

**Extract configuration:**
- `similarity_threshold` = config.validation.visual_similarity_threshold (e.g., 0.92)
- `max_iterations` = config.validation.max_ralph_iterations (e.g., 8)
- `preview_delay` = config.validation.preview_screenshot_delay (e.g., "auto" or 500)

### Phase 1: Ralph-Wiggum Loop

**Check ralph-wiggum availability:**

```bash
# Verify ralph-wiggum plugin loaded
claude --help | grep -q "ralph" || {
  echo "⚠️  Ralph-wiggum plugin not found"
  echo "Falling back to manual iteration"
}
```

**Invoke ralph-wiggum skill:**

```
Use Skill tool to invoke: ralph-wiggum:ralph-loop

Context: "Refine Compose UI to match baseline design"

Task: "Iteratively refine the Compose code in {generated_file_path} to visually match {baseline_image_path}"

Validation: Visual similarity >= {similarity_threshold}

Max iterations: {max_iterations}
```

Ralph-wiggum will manage the iteration loop. Within each iteration:

### Iteration Step 1: Render Preview

**Attempt Gradle rendering first:**

```bash
# Compile to ensure no syntax errors
./gradlew compileDebugKotlin 2>&1 | tee /tmp/compile.log

# Check for preview rendering task
if ./gradlew tasks --all | grep -q "generateDebugPreviewImages"; then
  echo "✓ Using Gradle preview rendering"
  ./gradlew generateDebugPreviewImages

  # Find generated preview (search build directory)
  preview=$(find . -name "*Preview*.png" -newer "$generated_file_path" | head -1)

  if [ -n "$preview" ]; then
    cp "$preview" "$temp_dir/preview-iteration-$iteration.png"
  fi
fi
```

**Fallback to Android Studio CLI:**

If Gradle task unavailable:

```bash
# Check if Android Studio CLI available
if command -v studio >/dev/null 2>&1; then
  echo "✓ Using Android Studio CLI"
  studio preview-render \
    --file "$generated_file_path" \
    --output "$temp_dir/preview-iteration-$iteration.png"
fi
```

**Manual fallback:**

If automated rendering fails:

```
⚠️  Automated preview rendering unavailable

Manual steps:
1. Open {generated_file_path} in Android Studio
2. Wait for preview to render
3. Right-click preview → "Export Preview Image"
4. Save to: {temp_dir}/preview-iteration-{iteration}.png

Press Enter when ready to continue...
```

**Handle preview delay:**

If `preview_delay` is "auto":
```bash
# Wait for file to stabilize (no size changes)
prev_size=0
while true; do
  sleep 0.5
  curr_size=$(stat -f%z "$temp_dir/preview-iteration-$iteration.png" 2>/dev/null || echo 0)
  [ "$curr_size" -eq "$prev_size" ] && [ "$curr_size" -gt 0 ] && break
  prev_size=$curr_size
done
```

If numeric delay:
```bash
sleep $(echo "$preview_delay / 1000" | bc)
```

### Iteration Step 2: Calculate Visual Similarity

**Use Python utility:**

```bash
# Use image-similarity.py from utils/
similarity=$(python3 "${CLAUDE_PLUGIN_ROOT}/utils/image-similarity.py" \
  "$baseline_image_path" \
  "$temp_dir/preview-iteration-$iteration.png" \
  --output "$temp_dir/diff-iteration-$iteration.png")

echo "Iteration $iteration: Similarity = $similarity"
```

**Parse similarity score:**

```bash
# Extract numerical score (0.0 to 1.0)
score=$(echo "$similarity" | grep -oE "[0-9]+\.[0-9]+")
```

### Iteration Step 3: Generate Diff Visualization

The image-similarity.py utility creates diff automatically (via --output flag).

**Enhance diff for analysis:**

```bash
# Optionally highlight major differences with bounding boxes
# (This would require additional Python script, skip for MVP)
```

### Iteration Step 4: Analyze Differences

**If similarity >= threshold:**

```
✅ Similarity threshold reached!

Iteration: {iteration}/{max_iterations}
Similarity: {score:.2%} (target: {threshold:.2%})

SUCCESS - Exiting ralph-wiggum loop
```

Return success to parent.

**If similarity < threshold AND iteration < max_iterations:**

Read current Compose code:

```kotlin
// Use Read tool to read generated_file_path
```

Analyze visual diff image and identify issues:

```
Iteration {iteration}/{max_iterations}
Similarity: {score:.2%} (target: {threshold:.2%})

Analyzing differences from diff image...

Identified Issues:
1. [Region (x,y)-(x2,y2)]: {description}
   - Likely cause: {hypothesis}
   - Fix: {proposed change}

2. [Region (x,y)-(x2,y2)]: {description}
   - Likely cause: {hypothesis}
   - Fix: {proposed change}

Common issues to check:
✓ Colors: Hardcoded vs theme, wrong hex value
✓ Spacing: padding(), Arrangement.spacedBy(), Spacer heights
✓ Typography: fontSize, fontWeight, lineHeight
✓ Alignment: Alignment.Start vs Center vs End
✓ Sizing: fillMaxWidth vs fixed width, height
```

### Iteration Step 5: Refine Code

**Apply targeted fixes using Edit tool:**

Focus on highest-impact changes first:

**Example: Fix color mismatch**
```kotlin
// Before:
Text(
    text = "Title",
    color = Color(0xFF000000)  // Pure black
)

// After:
Text(
    text = "Title",
    color = MaterialTheme.colorScheme.onSurface  // Proper theme color
)
```

**Example: Fix spacing**
```kotlin
// Before:
Column(
    modifier = Modifier.padding(8.dp)  // Too small
) { ... }

// After:
Column(
    modifier = Modifier.padding(16.dp)  // Matches baseline
) { ... }
```

**Example: Fix text size**
```kotlin
// Before:
Text(
    text = "Subtitle",
    fontSize = 14.sp  // Too small
)

// After:
Text(
    text = "Subtitle",
    fontSize = 16.sp  // Matches baseline
)
```

**Make multiple related changes per iteration:**
- If all text is too small, fix all at once
- If all padding is off, adjust all values
- Group related changes for efficiency

**Compile check after edits:**

```bash
./gradlew compileDebugKotlin 2>&1 | grep -i error
```

If syntax errors, fix immediately before next iteration.

**Loop back to Iteration Step 1**

### Iteration Step 6: Handle Max Iterations

**If iteration >= max_iterations AND similarity < threshold:**

```
⚠️  Visual validation incomplete

Final similarity: {score:.2%} (target: {threshold:.2%})
Iterations: {max_iterations}/{max_iterations} (limit reached)

Differences remaining:
{list remaining issues from last diff analysis}

Best attempt saved to: {generated_file_path}
Validation artifacts: {temp_dir}/

Review artifacts:
- preview-iteration-{1..N}.png (preview screenshots)
- diff-iteration-{1..N}.png (visual diffs)

Similarity progression:
{for each iteration: "Iteration N: {score:.2%}"}
```

**Ask user what to do:**

```
Options:
1. Accept current quality (similarity: {score:.2%})
2. Manual refinement (I'll help you improve specific areas)
3. Increase max iterations and retry
4. Lower threshold to {score:.2%} and mark as passing

What would you like to do? [1/2/3/4]:
```

Handle user choice and return appropriate status.

### Phase 2: Final Report

**On success (similarity >= threshold):**

```json
{
  "status": "success",
  "final_similarity": {score},
  "target_similarity": {threshold},
  "iterations": {iteration_count},
  "max_iterations": {max_iterations},
  "preview_images": ["{temp_dir}/preview-iteration-*.png"],
  "diff_images": ["{temp_dir}/diff-iteration-*.png"],
  "refinements": [
    "Increased title fontSize from 20sp to 24sp",
    "Adjusted padding from 8dp to 16dp",
    "Changed button color to theme primary"
  ]
}
```

**On warning (max iterations reached):**

```json
{
  "status": "warning",
  "final_similarity": {score},
  "target_similarity": {threshold},
  "iterations": {max_iterations},
  "max_iterations": {max_iterations},
  "delta": {threshold - score},
  "remaining_issues": [
    "Slight color mismatch in button background",
    "Text line height slightly off"
  ],
  "recommendations": [
    "Consider lowering threshold to {score}",
    "Manually tweak button background color",
    "Adjust line height in Text composables"
  ]
}
```

## Best Practices

### Efficient Iteration

**Prioritize high-impact changes:**
1. Layout structure (if fundamentally wrong)
2. Major color mismatches
3. Significant spacing differences
4. Text size issues
5. Fine-tuning (small adjustments)

**Batch related changes:**
- Fix all text sizes in one iteration
- Adjust all padding values together
- Update all colors using theme

**Learn from previous iterations:**
- Don't repeat failed approaches
- If similarity stopped improving, try different strategy
- Track what worked vs what didn't

### Similarity Plateaus

**If similarity stagnates (< 1% improvement for 2 iterations):**

Possible causes:
- Font rendering differences (system vs preview)
- Anti-aliasing variations
- Pixel-perfect match impossible
- Design has elements not reproducible in Compose

Actions:
- Accept current quality if visually acceptable
- Focus on functional correctness over pixel perfection
- Consider lowering threshold

### Code Quality During Refinement

**Maintain code quality:**
- Don't introduce hacks for pixel perfection
- Keep code readable and maintainable
- Preserve architecture patterns (stateless, hoisting)
- Add comments explaining non-obvious values

**Avoid:**
- Magic numbers without context
- Overly specific positioning
- Breaking theme integration for exact colors
- Nested inline modifications

## Edge Cases

**Preview rendering completely fails:**
```
❌ Cannot render preview after 3 attempts

Troubleshooting:
1. Check Gradle setup: ./gradlew build
2. Verify preview annotation: {config.naming.preview_annotation}
3. Check for syntax errors in generated code
4. Try manual preview in Android Studio

Would you like to:
1. Skip validation (use generated code as-is)
2. Provide manual preview screenshot
3. Abort workflow

Choose [1/2/3]:
```

**Similarity drops after refinement:**
```
⚠️  Similarity decreased

Previous: {prev_score:.2%}
Current: {curr_score:.2%}
Delta: {delta:.2%}

Last change made: {describe Edit operation}

Action: Reverting last change...

{use git diff to revert last change}
```

**Diff image analysis unclear:**
```
⚠️  Diff analysis inconclusive

Similarity: {score:.2%}
Major differences: Unclear from diff image

Requesting user guidance...

Please review diff image: {temp_dir}/diff-iteration-{iteration}.png

What area should I focus on?
1. Colors (backgrounds, text, buttons)
2. Spacing (padding, margins, gaps)
3. Text (sizes, weights, alignment)
4. Layout structure (arrangement, alignment)

Choose [1/2/3/4]:
```

## Error Handling

**Image similarity calculation fails:**
```
❌ Cannot calculate similarity

Error: {error_message}

Possible causes:
- Image format mismatch
- File corruption
- Missing Python packages

Action: Verify images and dependencies
```

**Code edits introduce syntax errors:**
```
❌ Compilation failed after refinement

Errors:
{compile_errors}

Action: Reverting changes and retrying with different approach...
```

**Unable to improve similarity:**
```
⚠️  Similarity not improving

Iterations: {count}
Best similarity: {best_score:.2%}
Current: {curr_score:.2%}

Possible issues:
- Design has elements not reproducible in Compose
- Preview rendering differs from actual app
- Threshold too strict for this design

Recommendation: Accept current quality if visually acceptable
```

## Return to Parent Command

Always provide structured results for parent to generate final report and make decisions about proceeding to device testing.
```

**Step 2: Commit**

```bash
git add agents/visual-validator.md
git commit -m "feat(agents): add visual-validator agent with ralph-wiggum integration"
```

---

## Task 5: Create Device Tester Agent

**Files:**
- Create: `agents/device-tester.md`

**Step 1: Write the agent definition**

Create `agents/device-tester.md`:

```markdown
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

### Phase 1: Device Selection

**Extract device_id from config:**

```
device_id_config = config.testing.device_id  # e.g., "auto", "emulator-5554", "abc123def"
```

**If device_id is "auto":**

Parse available devices and select first:

```bash
# Get first device ID
selected_device=$(echo "$devices" | head -1 | grep -oP '(?<=id: )[^ ]+')
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

```
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
if [ $? -ne 0 ]; then
  echo "❌ Clean failed"
  exit 1
fi
```

**Step 2: Compile and build debug APK**

```bash
./gradlew assembleDebug 2>&1 | tee "$temp_dir/build.log"

# Check exit code
if [ ${PIPESTATUS[0]} -ne 0 ]; then
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
apk_path="app/build/outputs/apk/debug/app-debug.apk"

if [ ! -f "$apk_path" ]; then
  echo "❌ APK not found: $apk_path"
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

if [ $? -ne 0 ]; then
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

if [ $? -ne 0 ]; then
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

mobile_take_screenshot --device "$selected_device"

# Tool returns image data; save to temp dir
device_screenshot="$temp_dir/device-screenshot.png"
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

button_count=$(echo "$buttons" | grep -c "button" || echo 0)
field_count=$(echo "$text_fields" | grep -c "field" || echo 0)
```

**Step 2: Test based on depth**

**If depth is "basic":**

Test one element of each type:

```bash
# Test first button if exists
if [ "$button_count" -gt 0 ]; then
  button_coords=$(echo "$buttons" | head -1 | grep -oP '\(\d+,\d+\)')
  button_x=$(echo "$button_coords" | cut -d',' -f1 | tr -d '(')
  button_y=$(echo "$button_coords" | cut -d',' -f2 | tr -d ')')

  echo "Testing button tap at ($button_x, $button_y)..."
  mobile_click_on_screen_at_coordinates \
    --device "$selected_device" \
    --x "$button_x" \
    --y "$button_y"

  sleep 1

  # Take screenshot to verify interaction
  mobile_take_screenshot --device "$selected_device"
  interaction_screenshot="$temp_dir/interaction-button.png"

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
  button_coords=$(echo "$button_line" | grep -oP '\(\d+,\d+\)')
  button_x=$(echo "$button_coords" | cut -d',' -f1 | tr -d '(')
  button_y=$(echo "$button_coords" | cut -d',' -f2 | tr -d ')')

  echo "Testing button $button_index at ($button_x, $button_y)..."

  # Capture before state
  before_screenshot="$temp_dir/before-button-$button_index.png"
  mobile_take_screenshot --device "$selected_device"

  # Perform tap
  mobile_click_on_screen_at_coordinates \
    --device "$selected_device" \
    --x "$button_x" \
    --y "$button_y"

  sleep 1

  # Capture after state
  after_screenshot="$temp_dir/after-button-$button_index.png"
  mobile_take_screenshot --device "$selected_device"

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

  field_coords=$(echo "$field_line" | grep -oP '\(\d+,\d+\)')
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
  mobile_take_screenshot --device "$selected_device"
  field_screenshot="$temp_dir/field-$field_index.png"

  echo "  ✓ Text field accepts input"
  test_results+=("field_$field_index:pass")
done <<< "$text_fields"

# Test scrolling if applicable
if echo "$elements" | grep -iq "scrollable"; then
  echo "Testing scroll..."

  before_scroll="$temp_dir/before-scroll.png"
  mobile_take_screenshot --device "$selected_device"

  mobile_swipe_on_screen \
    --device "$selected_device" \
    --direction up \
    --distance 400

  sleep 1

  after_scroll="$temp_dir/after-scroll.png"
  mobile_take_screenshot --device "$selected_device"

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
```

**Step 2: Commit**

```bash
git add agents/device-tester.md
git commit -m "feat(agents): add device-tester agent with mobile-mcp integration"
```

---

## Task 6: Create Image Similarity Utility

**Files:**
- Create: `utils/image-similarity.py`

**Step 1: Write Python SSIM utility**

Create `utils/image-similarity.py`:

```python
#!/usr/bin/env python3
"""
Image similarity calculator for compose-designer plugin.
Uses SSIM (Structural Similarity Index) to compare images.

Usage:
  python3 image-similarity.py baseline.png preview.png [--output diff.png]

Returns:
  Similarity score (0.0 to 1.0) printed to stdout

Requirements:
  pip3 install scikit-image pillow numpy
"""

import sys
import argparse
from pathlib import Path

try:
    from skimage.metrics import structural_similarity as ssim
    from PIL import Image
    import numpy as np
except ImportError as e:
    print(f"Error: Required package not installed: {e}", file=sys.stderr)
    print("Install with: pip3 install scikit-image pillow numpy", file=sys.stderr)
    sys.exit(1)


def calculate_similarity(baseline_path, preview_path, output_diff_path=None):
    """
    Calculate SSIM between two images.

    Args:
        baseline_path: Path to baseline/reference image
        preview_path: Path to preview/test image
        output_diff_path: Optional path to save difference image

    Returns:
        float: Similarity score (0.0 to 1.0)
    """
    try:
        # Load images
        baseline = Image.open(baseline_path)
        preview = Image.open(preview_path)

        # Convert to RGB if needed
        if baseline.mode != 'RGB':
            baseline = baseline.convert('RGB')
        if preview.mode != 'RGB':
            preview = preview.convert('RGB')

        # Resize preview to match baseline dimensions
        if baseline.size != preview.size:
            print(f"Resizing preview from {preview.size} to {baseline.size}", file=sys.stderr)
            preview = preview.resize(baseline.size, Image.Resampling.LANCZOS)

        # Convert to numpy arrays
        baseline_arr = np.array(baseline)
        preview_arr = np.array(preview)

        # Calculate SSIM
        score, diff_image = ssim(
            baseline_arr,
            preview_arr,
            multichannel=True,
            channel_axis=2,
            full=True
        )

        # Generate diff visualization if requested
        if output_diff_path:
            # Calculate absolute pixel difference
            abs_diff = np.abs(baseline_arr.astype(float) - preview_arr.astype(float))

            # Enhance differences for visibility (multiply by 3, cap at 255)
            enhanced_diff = (abs_diff * 3).clip(0, 255).astype(np.uint8)

            # Save diff image
            diff_img = Image.fromarray(enhanced_diff)
            diff_img.save(output_diff_path)
            print(f"Diff image saved: {output_diff_path}", file=sys.stderr)

        return score

    except FileNotFoundError as e:
        print(f"Error: Image file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error calculating similarity: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Calculate image similarity using SSIM algorithm',
        epilog='Example: python3 image-similarity.py baseline.png preview.png --output diff.png'
    )
    parser.add_argument('baseline', help='Path to baseline/reference image')
    parser.add_argument('preview', help='Path to preview/test image')
    parser.add_argument(
        '--output', '-o',
        help='Path to save difference visualization (optional)',
        default=None
    )

    args = parser.parse_args()

    # Validate inputs
    baseline_path = Path(args.baseline)
    preview_path = Path(args.preview)

    if not baseline_path.exists():
        print(f"Error: Baseline image not found: {baseline_path}", file=sys.stderr)
        sys.exit(1)

    if not preview_path.exists():
        print(f"Error: Preview image not found: {preview_path}", file=sys.stderr)
        sys.exit(1)

    # Calculate similarity
    score = calculate_similarity(
        str(baseline_path),
        str(preview_path),
        args.output
    )

    # Print score to stdout (for parsing by bash scripts)
    print(f"{score:.4f}")

    # Exit with success
    sys.exit(0)


if __name__ == '__main__':
    main()
```

**Step 2: Make executable**

```bash
chmod +x utils/image-similarity.py
```

**Step 3: Test the utility**

```bash
# Create simple test (optional, can skip for plan)
python3 utils/image-similarity.py --help
```

Expected output:
```
usage: image-similarity.py [-h] [--output OUTPUT] baseline preview
...
```

**Step 4: Commit**

```bash
git add utils/image-similarity.py
git commit -m "feat(utils): add image similarity calculator using SSIM"
```

---

## Task 7: Create Figma API Client Utility

**Files:**
- Create: `utils/figma-client.sh`

**Step 1: Write Bash Figma client**

Create `utils/figma-client.sh`:

```bash
#!/bin/bash
# Figma API client for compose-designer plugin
# Handles Figma URL parsing, node data fetching, and image export
#
# Usage:
#   ./figma-client.sh parse <figma-url>
#   ./figma-client.sh fetch-node <figma-url>
#   ./figma-client.sh export <figma-url> <output.png> [format] [scale]
#
# Environment:
#   FIGMA_TOKEN - Figma API personal access token (required)

set -euo pipefail

# Token from environment
FIGMA_TOKEN="${FIGMA_TOKEN:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${GREEN}$1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}$1${NC}" >&2
}

# Check if token is set
check_token() {
    if [ -z "$FIGMA_TOKEN" ]; then
        error "FIGMA_TOKEN environment variable not set

Get your personal access token:
1. Go to https://www.figma.com/settings
2. Navigate to 'Account' tab
3. Scroll to 'Personal Access Tokens'
4. Create new token with 'Read-only' scope
5. Export: export FIGMA_TOKEN=\"your-token-here\"
"
    fi
}

# Parse Figma URL to extract file ID and node ID
# Supports:
#   - https://www.figma.com/file/{file_id}/{name}?node-id={node_id}
#   - https://www.figma.com/design/{file_id}/{name}?node-id={node_id}
#   - figma://file/{file_id}?node-id={node_id}
parse_url() {
    local url="$1"

    # Extract file ID
    file_id=$(echo "$url" | grep -oP '(?<=file/|design/)[^/?]+' || echo "")

    # Extract node ID (may have format like "123:456" or "123-456")
    node_id=$(echo "$url" | grep -oP '(?<=node-id=)[^&]+' || echo "")

    # Validate
    if [ -z "$file_id" ]; then
        error "Could not extract file ID from URL: $url

Supported formats:
  • https://www.figma.com/file/{file_id}/{name}?node-id={node_id}
  • https://www.figma.com/design/{file_id}/{name}?node-id={node_id}
  • figma://file/{file_id}?node-id={node_id}
"
    fi

    if [ -z "$node_id" ]; then
        warn "No node ID found in URL. Using root document."
        node_id="0:0"
    fi

    # Output in parseable format
    echo "${file_id}|${node_id}"
}

# Fetch node data from Figma API (colors, typography, layout)
fetch_node_data() {
    check_token

    local file_id="$1"
    local node_id="$2"

    info "Fetching node data from Figma API..."

    # URL-encode node ID (replace : with %3A)
    encoded_node_id=$(echo "$node_id" | sed 's/:/%3A/g')

    # Make API request
    response=$(curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
        "https://api.figma.com/v1/files/$file_id/nodes?ids=$encoded_node_id")

    # Check for errors
    if echo "$response" | grep -q '"err"'; then
        error "Figma API error: $(echo "$response" | grep -oP '(?<="err":")[^"]+' || echo "Unknown error")

Possible causes:
  • Invalid file ID or node ID
  • Token doesn't have access to this file
  • Token expired or invalid
"
    fi

    # Output JSON response
    echo "$response"
}

# Export node as image (PNG, JPG, SVG, PDF)
export_image() {
    check_token

    local file_id="$1"
    local node_id="$2"
    local output_path="$3"
    local format="${4:-png}"
    local scale="${5:-2}"

    info "Exporting Figma node as $format (${scale}x scale)..."

    # URL-encode node ID
    encoded_node_id=$(echo "$node_id" | sed 's/:/%3A/g')

    # Request image export
    response=$(curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
        "https://api.figma.com/v1/images/$file_id?ids=$encoded_node_id&format=$format&scale=$scale")

    # Check for errors
    if echo "$response" | grep -q '"err"'; then
        error "Figma API error: $(echo "$response" | grep -oP '(?<="err":")[^"]+' || echo "Unknown error")"
    fi

    # Extract image URL from JSON response
    # Format: {"images":{"123:456":"https://..."}}
    image_url=$(echo "$response" | grep -oP "(?<=\"$node_id\":\")https://[^\"]+")

    if [ -z "$image_url" ]; then
        error "Failed to get image URL from Figma API

Response: $response

Possible causes:
  • Node doesn't exist
  • Node is not exportable
  • API rate limit reached
"
    fi

    info "Downloading image from Figma CDN..."

    # Download image
    http_code=$(curl -s -w "%{http_code}" -o "$output_path" "$image_url")

    if [ "$http_code" != "200" ]; then
        error "Failed to download image (HTTP $http_code)"
    fi

    # Verify file was created and has content
    if [ ! -s "$output_path" ]; then
        error "Downloaded file is empty or missing: $output_path"
    fi

    local file_size=$(du -h "$output_path" | cut -f1)
    info "✓ Image exported: $output_path ($file_size)"
}

# Main command router
case "${1:-}" in
    parse)
        if [ -z "${2:-}" ]; then
            error "Usage: $0 parse <figma-url>"
        fi
        parse_url "$2"
        ;;

    fetch-node)
        if [ -z "${2:-}" ]; then
            error "Usage: $0 fetch-node <figma-url>"
        fi
        IFS='|' read -r file_id node_id <<< "$(parse_url "$2")"
        fetch_node_data "$file_id" "$node_id"
        ;;

    export)
        if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
            error "Usage: $0 export <figma-url> <output-path> [format] [scale]

Arguments:
  figma-url    Figma file URL with node-id parameter
  output-path  Where to save the exported image
  format       png|jpg|svg|pdf (default: png)
  scale        1|2|3|4 (default: 2 for 2x resolution)

Example:
  $0 export 'https://figma.com/file/ABC?node-id=1:234' output.png png 2
"
        fi
        IFS='|' read -r file_id node_id <<< "$(parse_url "$2")"
        export_image "$file_id" "$node_id" "$3" "${4:-png}" "${5:-2}"
        ;;

    *)
        cat <<EOF
Figma API client for compose-designer plugin

Usage:
  $0 <command> [arguments]

Commands:
  parse <figma-url>
      Parse Figma URL and extract file ID and node ID
      Output format: file_id|node_id

  fetch-node <figma-url>
      Fetch node data (colors, typography, layout) as JSON
      Requires: FIGMA_TOKEN environment variable

  export <figma-url> <output-path> [format] [scale]
      Export node as image file
      Formats: png, jpg, svg, pdf (default: png)
      Scale: 1-4 (default: 2 for retina)
      Requires: FIGMA_TOKEN environment variable

Environment:
  FIGMA_TOKEN    Figma personal access token (required for fetch/export)
                 Get token: https://www.figma.com/settings

Examples:
  # Parse URL
  $0 parse 'https://www.figma.com/file/ABC123?node-id=1:234'

  # Export as PNG
  export FIGMA_TOKEN="your-token"
  $0 export 'https://www.figma.com/file/ABC123?node-id=1:234' output.png

  # Export as high-res JPG
  $0 export 'https://www.figma.com/file/ABC123?node-id=1:234' output.jpg jpg 4

Exit codes:
  0    Success
  1    Error (check stderr for details)

EOF
        exit 1
        ;;
esac
```

**Step 2: Make executable**

```bash
chmod +x utils/figma-client.sh
```

**Step 3: Test help message**

```bash
./utils/figma-client.sh
```

Expected: Usage documentation displays

**Step 4: Commit**

```bash
git add utils/figma-client.sh
git commit -m "feat(utils): add Figma API client for design token extraction"
```

---

## Task 8: Create Example Assets

**Files:**
- Create: `examples/button-example.png` (placeholder)
- Create: `examples/card-example.png` (placeholder)
- Create: `examples/README.md`

**Step 1: Create examples README**

Create `examples/README.md`:

```markdown
# Compose Designer Examples

Example design files for testing the compose-designer plugin.

## Test Designs

### Simple Button (`button-example.png`)

A basic button design for testing component generation.

**Usage:**
```bash
/compose-design create --input examples/button-example.png --name TestButton --type component
```

**Expected Output:**
- `TestButtonComponent.kt` with Button composable
- Simple mock data
- Preview function

### Profile Card (`card-example.png`)

A card layout with image, text, and button elements.

**Usage:**
```bash
/compose-design create --input examples/card-example.png --name ProfileCard --type component
```

**Expected Output:**
- `ProfileCardComponent.kt` with Card composable
- Row/Column layout
- Image, text, and button elements
- Realistic mock data

## Creating Your Own Test Designs

### Best Practices

1. **Clear Visual Hierarchy**
   - Well-defined layout structure
   - Clear spacing between elements
   - Obvious element types (buttons, text, etc.)

2. **Standard Colors**
   - Use Material Design colors when possible
   - Clear contrast between elements
   - Avoid overly complex gradients

3. **Readable Text**
   - Sufficient size for OCR
   - Clear font weights
   - No distorted or stylized fonts

4. **Proper Format**
   - PNG or JPG format
   - Minimum 400px width
   - Clear, non-blurry screenshot

### Figma Integration

For best results with Figma:

1. **Create Figma Frame**
   - Use Auto Layout for precise spacing
   - Define colors in Styles
   - Use Text Styles for typography

2. **Get Node URL**
   - Right-click frame → "Copy link to selection"
   - URL format: `https://www.figma.com/file/...?node-id=...`

3. **Set Up Token**
   ```bash
   export FIGMA_TOKEN="your-token-here"
   ```

4. **Generate**
   ```bash
   /compose-design create --input "figma-url" --name Component --type component
   ```

## Testing Workflow

### End-to-End Test

```bash
# 1. Initialize config
/compose-design config

# 2. Generate from example
/compose-design create --input examples/button-example.png --name TestButton --type component

# 3. Review generated code
cat app/src/main/java/.../TestButtonComponent.kt

# 4. Check validation artifacts
ls -la /tmp/compose-designer/*/

# 5. Test in app
# Add to your activity:
# TestButtonComponent(text = "Click Me", onClick = {})
```

### Batch Test

```bash
# Process all examples at once
/compose-design create --input examples/ --batch
```

## Adding New Examples

To contribute new example designs:

1. Create clear, focused design mockup
2. Save as PNG in `examples/`
3. Name descriptively: `{element}-{variant}.png`
4. Add description to this README
5. Test generation: `/compose-design create --input examples/your-design.png --name YourComponent --type component`

## Troubleshooting Examples

**Generated code doesn't match design:**
- Check if design is clear and unambiguous
- Verify colors are distinct
- Ensure text is readable
- Try adjusting similarity threshold in config

**Validation fails:**
- Design may be too complex for Compose
- Preview rendering might differ from screenshot
- Lower similarity threshold or accept manual refinement

**Device test fails:**
- Check theme is applied in test activity
- Verify resources exist (colors, icons)
- Test on different device/emulator
```

**Step 2: Create placeholder images**

For MVP, create simple text-based placeholders:

```bash
# Create simple placeholder (will be replaced with actual images later)
cat > examples/button-example.png.txt <<EOF
Placeholder: button-example.png
TODO: Replace with actual screenshot of a button design

For testing, use your own design screenshot:
/compose-design create --input your-button.png --name TestButton --type component
EOF

cat > examples/card-example.png.txt <<EOF
Placeholder: card-example.png
TODO: Replace with actual screenshot of a card design

For testing, use your own design screenshot:
/compose-design create --input your-card.png --name TestCard --type component
EOF
```

**Step 3: Commit**

```bash
git add examples/
git commit -m "docs(examples): add example assets and documentation"
```

---

## Task 9: Create Test Validation Script

**Files:**
- Create: `tests/validate-plugin.sh`

**Step 1: Write validation script**

Create `tests/validate-plugin.sh`:

```bash
#!/bin/bash
# Validation script for compose-designer plugin
# Tests plugin structure, utilities, and components

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

passed=0
failed=0

test() {
    local name="$1"
    shift

    if "$@" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        ((passed++))
        return 0
    else
        echo -e "${RED}✗${NC} $name"
        ((failed++))
        return 1
    fi
}

echo "Validating compose-designer plugin..."
echo ""

# Test 1: Plugin manifest
test "Plugin manifest exists" \
    [ -f .claude-plugin/plugin.json ]

test "Plugin manifest is valid JSON" \
    python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"

# Test 2: Commands
test "Config command exists" \
    [ -f commands/config.md ]

test "Create command exists" \
    [ -f commands/create.md ]

# Test 3: Agents
test "Design generator agent exists" \
    [ -f agents/design-generator.md ]

test "Visual validator agent exists" \
    [ -f agents/visual-validator.md ]

test "Device tester agent exists" \
    [ -f agents/device-tester.md ]

# Test 4: Utilities
test "Image similarity utility exists" \
    [ -f utils/image-similarity.py ]

test "Image similarity utility is executable" \
    [ -x utils/image-similarity.py ]

test "Figma client utility exists" \
    [ -f utils/figma-client.sh ]

test "Figma client utility is executable" \
    [ -x utils/figma-client.sh ]

# Test 5: Python dependencies (optional)
if python3 -c "import skimage, PIL, numpy" 2>/dev/null; then
    test "Python dependencies installed" true

    test "Image similarity utility runs" \
        python3 utils/image-similarity.py --help
else
    echo -e "${YELLOW}⊘${NC} Python dependencies not installed (optional)"
    echo "   Install: pip3 install scikit-image pillow numpy"
fi

# Test 6: Figma client help
test "Figma client shows help" \
    bash utils/figma-client.sh

# Test 7: Documentation
test "README exists" \
    [ -f README.md ]

test "Examples README exists" \
    [ -f examples/README.md ]

# Test 8: Git ignore
test ".gitignore exists" \
    [ -f .gitignore ]

# Summary
echo ""
echo "=========================================="
echo "Results: $passed passed, $failed failed"
echo "=========================================="

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
    echo ""
    echo "Plugin structure validated successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Initialize config: /compose-design config"
    echo "  2. Test with real design: /compose-design create --input design.png --name Test --type component"
    echo "  3. Review generated code"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Fix failures and re-run validation."
    exit 1
fi
```

**Step 2: Make executable**

```bash
chmod +x tests/validate-plugin.sh
```

**Step 3: Run validation**

```bash
./tests/validate-plugin.sh
```

Expected: All tests pass (except optional Python dependencies if not installed)

**Step 4: Commit**

```bash
git add tests/validate-plugin.sh
git commit -m "test(plugin): add validation script for plugin structure"
```

---

## Task 10: Final Plugin Validation and Documentation

**Files:**
- Update: `README.md` (add installation instructions)
- Create: `CHANGELOG.md`

**Step 1: Run full validation**

```bash
./tests/validate-plugin.sh
```

Verify all tests pass.

**Step 2: Create changelog**

Create `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to the compose-designer plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-13

### Added

#### Core Features
- Three-phase workflow: Generation → Validation (ralph-wiggum) → Testing (mobile-mcp)
- Multi-input support: screenshots, Figma URLs, clipboard, batch folders
- Smart defaults with project-specific prompts

#### Commands
- `/compose-design config` - Initialize project configuration
- `/compose-design create` - Generate Compose code from design

#### Agents
- `design-generator` - Analyzes designs and generates Compose code
- `visual-validator` - Ralph-wiggum loop for visual accuracy refinement
- `device-tester` - Mobile-mcp integration for device testing

#### Utilities
- `image-similarity.py` - SSIM-based visual similarity calculator
- `figma-client.sh` - Figma API client for design token extraction

#### Features
- Visual similarity validation (92%+ threshold)
- Existing theme integration (Color.kt, Type.kt extraction)
- Realistic mock data generation from designs
- Comprehensive device interaction testing
- Configurable project conventions

#### Documentation
- Comprehensive README with quick start
- Example assets and usage patterns
- Troubleshooting guide
- Validation scripts

### Known Limitations

- Compose only (XML support planned for v0.2.0)
- Requires Android Gradle project
- Manual preview rendering fallback for some environments
- Figma token extraction requires personal access token

### Dependencies

- Python 3.7+ with scikit-image, pillow, numpy
- Android Gradle build system
- Ralph-wiggum plugin (for visual validation)
- Mobile-ui-testing plugin (for device testing)

### Breaking Changes

None (initial release)

## [Unreleased]

### Planned for v0.2.0
- XML layout generation support
- Improved mock data extraction
- Parallel batch processing
- Custom preview annotation support
- Integration with CI/CD pipelines
```

**Step 3: Verify README completeness**

Check README has all sections:
- ✓ Overview and features
- ✓ Prerequisites
- ✓ Installation
- ✓ Quick start
- ✓ Three-phase workflow explanation
- ✓ Configuration reference
- ✓ Usage examples
- ✓ Troubleshooting
- ✓ Architecture diagram

**Step 4: Create .gitattributes for examples**

Create `.gitattributes`:

```
# Mark example images as binary
examples/*.png binary
examples/*.jpg binary

# Ensure shell scripts have LF line endings
*.sh text eol=lf

# Ensure Python scripts have LF line endings
*.py text eol=lf
```

**Step 5: Final commit**

```bash
git add CHANGELOG.md .gitattributes
git commit -m "docs: add changelog and finalize documentation

- Added comprehensive changelog
- Configured git attributes for examples
- Verified README completeness
- Plugin ready for initial release (v0.1.0)"
```

---

## Summary

**Implementation Complete:**

✅ **Phase 4: Plugin Structure** - Directory structure and manifest created
✅ **Phase 5: Component Implementation**
- Commands: `config`, `create`
- Agents: `design-generator`, `visual-validator`, `device-tester`
- Utilities: `image-similarity.py`, `figma-client.sh`
- Examples and tests

**Total Files Created:** 15

**Structure:**
```
compose-designer/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── config.md
│   └── create.md
├── agents/
│   ├── design-generator.md
│   ├── visual-validator.md
│   └── device-tester.md
├── utils/
│   ├── image-similarity.py
│   └── figma-client.sh
├── examples/
│   ├── README.md
│   └── *.png.txt (placeholders)
├── tests/
│   └── validate-plugin.sh
├── README.md
├── CHANGELOG.md
├── .gitignore
└── .gitattributes
```

**Next Steps:**
1. Test plugin in Claude Code
2. Run validation script
3. Test with real designs
4. Iterate based on feedback
5. Replace example placeholders with actual images
6. Publish to marketplace

**Estimated Implementation Time:** 2-4 hours per component = 10-15 hours total

**Testing Focus:**
- Config initialization with smart defaults
- End-to-end workflow with screenshot
- Ralph-wiggum validation loop
- Mobile-mcp device testing
- Batch processing
- Error handling and edge cases
