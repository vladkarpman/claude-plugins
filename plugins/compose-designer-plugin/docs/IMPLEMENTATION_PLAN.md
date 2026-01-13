# Compose Designer Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a universal Claude Code plugin that transforms screenshots/Figma designs into production-ready Compose code with self-validation using ralph-wiggum loop + mobile-mcp testing.

**Architecture:** Three-phase workflow: (1) Generate initial Compose code from design input, (2) Visual validation using @Preview with ralph-wiggum loop for iterative refinement, (3) Device testing with mobile-mcp for interaction validation. Plugin is project-agnostic with configurable conventions.

**Tech Stack:** Claude Code plugin system, ralph-wiggum for self-correction, mobile-mcp for device automation, image similarity algorithms for visual diff

---

## Task 1: Create Plugin Structure

**Files:**
- Create: `.claude/plugins/compose-designer/plugin.json`
- Create: `.claude/plugins/compose-designer/README.md`
- Create: `.claude/plugins/compose-designer/commands/create.md`
- Create: `.claude/plugins/compose-designer/agents/design-generator.md`
- Create: `.claude/plugins/compose-designer/agents/visual-validator.md`

**Step 1: Create plugin manifest**

Create `.claude/plugins/compose-designer/plugin.json`:

```json
{
  "name": "compose-designer",
  "version": "1.0.0",
  "description": "Transform screenshots and Figma designs into production-ready Jetpack Compose code with automated validation",
  "author": "Your Name",
  "commands": [
    {
      "name": "create",
      "description": "Generate Compose code from design (screenshot/Figma)",
      "file": "commands/create.md"
    },
    {
      "name": "config",
      "description": "Initialize or update compose-designer configuration",
      "file": "commands/config.md"
    }
  ],
  "agents": [
    {
      "name": "design-generator",
      "description": "Generates Compose code from design input",
      "file": "agents/design-generator.md",
      "tools": ["Read", "Write", "Bash", "WebFetch", "Glob"]
    },
    {
      "name": "visual-validator",
      "description": "Validates generated UI using ralph-wiggum loop",
      "file": "agents/visual-validator.md",
      "tools": ["Read", "Edit", "Bash", "Skill"]
    },
    {
      "name": "device-tester",
      "description": "Tests UI on device using mobile-mcp",
      "file": "agents/device-tester.md",
      "tools": ["Bash", "mcp__mobile-mcp__*"]
    }
  ]
}
```

**Step 2: Create plugin README**

Create `.claude/plugins/compose-designer/README.md`:

```markdown
# Compose Designer Plugin

Transform screenshots and Figma designs into production-ready Jetpack Compose code with automated validation.

## Features

- **Multi-input support**: Screenshots, Figma links, clipboard, batch folders
- **Figma token extraction**: Extracts colors, typography, spacing from Figma API
- **Self-validation**: Ralph-wiggum loop ensures visual accuracy (92%+ similarity)
- **Device testing**: Mobile-mcp integration for real runtime validation
- **Project-agnostic**: Configurable naming conventions and architecture patterns

## Usage

### Initialize Configuration

```bash
/compose-design config
```

Creates `.claude/compose-designer.yaml` with defaults. Customize for your project.

### Generate from Screenshot

```bash
/compose-design create --input screenshot.png --name ProfileCard --type component
```

### Generate from Figma

```bash
/compose-design create --input "figma://file/ABC123?node-id=1:234" --name LoginScreen --type screen
```

### Batch Generation

```bash
/compose-design create --input ./designs/ --batch
```

### Quick Test from Clipboard

```bash
/compose-design create --clipboard --name QuickTest --type component
```

## Configuration

Edit `.claude/compose-designer.yaml`:

```yaml
naming:
  component_suffix: "Component"
  screen_suffix: "Screen"
  preview_annotation: "@Preview"

validation:
  visual_similarity_threshold: 0.92
  max_ralph_iterations: 8
```

See full config schema in commands/config.md

## Workflow

1. **Phase 1: Generation** - Analyze design, generate Compose code with @Preview
2. **Phase 2: Visual Validation** - Ralph-wiggum loop refines code until visual match
3. **Phase 3: Device Testing** - Mobile-mcp tests interactions on real device
4. **Output** - Production-ready Compose file with validation report

## Requirements

- Android Studio or Gradle setup for preview rendering
- (Optional) Figma API token for design token extraction
- (Optional) Mobile device/emulator for Phase 3 testing
```

**Step 3: Commit plugin structure**

```bash
git add .claude/plugins/compose-designer/
git commit -m "feat: create compose-designer plugin structure"
```

---

## Task 2: Create Configuration Command

**Files:**
- Create: `.claude/plugins/compose-designer/commands/config.md`

**Step 1: Create config command**

Create `.claude/plugins/compose-designer/commands/config.md`:

```markdown
---
name: config
description: Initialize or update compose-designer configuration file
args:
  - name: reset
    description: Reset to defaults
    required: false
---

# Compose Designer Configuration

Initialize or update the `.claude/compose-designer.yaml` configuration file.

## Usage

```bash
# Initialize with defaults
/compose-design config

# Reset to defaults
/compose-design config --reset
```

## Instructions for Claude

When this command is invoked:

1. Check if `.claude/compose-designer.yaml` exists
   - If exists and no `--reset` flag: Ask user if they want to update or view current config
   - If exists and `--reset` flag: Confirm with user, then overwrite
   - If not exists: Create with defaults

2. Create the configuration file with this template:

```yaml
# Compose Designer Configuration
# Edit this file to customize code generation for your project

# Project conventions
naming:
  component_suffix: "Component"        # Suffix for UI components (e.g., ButtonComponent)
  screen_suffix: "Screen"              # Suffix for screen composables (e.g., HomeScreen)
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
  preview_screenshot_delay_ms: 500     # Delay before capturing preview

# Activity testing (Phase 3)
testing:
  test_activity_package: "com.example.app.test"
  test_activity_name: "ComposeTestActivity"
  device_id: "auto"                    # 'auto' or specific device ID
  rebuild_required: true               # Set false for dynamic injection (advanced)

# Figma integration (optional)
figma:
  extract_tokens: true                 # Extract design tokens from Figma
  api_token_env: "FIGMA_TOKEN"         # Environment variable for Figma API token
  fallback_to_image: true              # Fall back to image-only if token extraction fails

# Output preferences
output:
  package_base: "com.example.app"      # Base package name
  default_output_dir: "app/src/main/java"  # Output directory for generated files
  include_comments: false              # Add explanatory comments to generated code
  extract_theme_from_existing: true    # Learn colors/typography from existing code
```

3. After creating/updating, show the user:
   - Location of config file
   - Key settings they might want to customize
   - Link to plugin README for full documentation

4. Validate the YAML structure and warn about any issues

## Example Output

```
✓ Created .claude/compose-designer.yaml

Key settings to review:
  • naming.component_suffix: "Component"
  • validation.visual_similarity_threshold: 0.92
  • output.package_base: "com.example.app"

Edit .claude/compose-designer.yaml to customize for your project.
See .claude/plugins/compose-designer/README.md for full documentation.
```
```

**Step 2: Commit config command**

```bash
git add .claude/plugins/compose-designer/commands/config.md
git commit -m "feat: add config command for initialization"
```

---

## Task 3: Create Main Generation Command

**Files:**
- Create: `.claude/plugins/compose-designer/commands/create.md`

**Step 1: Create create command**

Create `.claude/plugins/compose-designer/commands/create.md`:

```markdown
---
name: create
description: Generate Compose code from design input (screenshot/Figma/clipboard)
args:
  - name: input
    description: Path to image, Figma URL, 'clipboard', or folder path for batch
    required: false
  - name: name
    description: Name for generated component/screen (e.g., ProfileCard, LoginScreen)
    required: true
  - name: type
    description: Type of composable to generate (component or screen)
    required: true
    choices: ["component", "screen"]
  - name: clipboard
    description: Use image from clipboard
    required: false
  - name: batch
    description: Process all images in folder
    required: false
---

# Compose Designer: Create

Generate Jetpack Compose code from design input with automated validation.

## Usage Examples

```bash
# From screenshot
/compose-design create --input screenshot.png --name ProfileCard --type component

# From Figma
/compose-design create --input "figma://file/ABC?node-id=1:234" --name LoginScreen --type screen

# From clipboard
/compose-design create --clipboard --name QuickButton --type component

# Batch from folder
/compose-design create --input ./designs/ --batch
```

## Instructions for Claude

### Phase 0: Setup and Validation

1. **Load configuration**
   - Read `.claude/compose-designer.yaml`
   - If not exists, run `/compose-design config` first
   - Validate all required config fields

2. **Validate arguments**
   - Ensure `--name` is provided
   - Ensure `--type` is either "component" or "screen"
   - If `--batch`, ensure `--input` is a directory
   - If `--clipboard`, ignore `--input` argument

3. **Process input**
   - **Image file**: Verify file exists and is image format (.png, .jpg, .jpeg)
   - **Figma URL**: Parse figma:// or https://figma.com URL
   - **Clipboard**: Read clipboard image data
   - **Folder**: Find all .png/.jpg files in directory

4. **Use TodoWrite** to create task list:
   ```
   - Load configuration and validate inputs
   - Process design input (extract baseline image)
   - Generate initial Compose code
   - Phase 2: Visual validation (ralph-wiggum loop)
   - Phase 3: Device testing (mobile-mcp)
   - Generate final report and ask for confirmation
   ```

### Phase 1: Initial Code Generation

Use the `design-generator` agent:

```bash
Task tool with subagent_type="compose-designer:design-generator"
Prompt: "Generate Compose code for {name} from {input_source}"
Pass: config, input_path, name, type, baseline_image_path
```

**Agent tasks:**
1. **Process design input**
   - If Figma URL:
     - Check for `FIGMA_TOKEN` env var (from config `figma.api_token_env`)
     - If token exists and `figma.extract_tokens: true`:
       - Call Figma API to extract colors, text styles, spacing
       - Export frame as PNG baseline
     - If no token or extraction fails and `figma.fallback_to_image: true`:
       - Use Figma screenshot as baseline (via WebFetch or Figma MCP)
   - If image file: Use as baseline directly
   - Save baseline to temp location: `/tmp/compose-designer/baseline-{timestamp}.png`

2. **Analyze design visually**
   - Use LLM vision to analyze baseline image
   - Identify: layout hierarchy (Column/Row/Box), UI elements (Button/Text/Image), colors, spacing, text styles
   - If Figma tokens available: merge with visual analysis for accuracy

3. **Generate Compose code**
   - Apply naming from config: `{name}{component_suffix or screen_suffix}`
   - Generate composable function:
     - Stateless if `architecture.stateless_components: true`
     - Add `Modifier` parameter
     - Include mock data parameters
   - Generate `@Preview` function:
     - Use config `preview.preview_annotation`
     - Apply `preview.device_spec`, `preview.background_color`
     - Call main composable with mock data
   - Apply package from config `output.package_base`
   - If `output.extract_theme_from_existing: true`:
     - Search codebase for Color.kt, Type.kt
     - Use existing theme colors instead of hardcoding
   - Write to: `{output.default_output_dir}/{package_path}/{name}{suffix}.kt`

4. **Return to main flow**
   - Output: Generated file path, baseline image path
   - Mark TodoWrite item complete

### Phase 2: Visual Validation (Ralph-Wiggum Loop)

Use the `visual-validator` agent with ralph-wiggum:

```bash
Skill tool: ralph-wiggum:ralph-loop
Context: "Validate Compose UI visual accuracy against baseline"
Task for ralph: "Refine Compose code to match baseline design"
Validation: Visual similarity >= config.validation.visual_similarity_threshold
Max iterations: config.validation.max_ralph_iterations
```

**Agent tasks (ralph-wiggum loop):**

1. **Render preview screenshot**
   - Use Gradle task or Android Studio CLI:
     ```bash
     ./gradlew :app:generateDebugPreviewImages
     ```
   - Or use IntelliJ IDEA preview API if available
   - Apply `preview_screenshot_delay_ms` before capture
   - Save to: `/tmp/compose-designer/preview-iteration-{n}.png`

2. **Calculate visual diff**
   - Use image similarity algorithm (SSIM or perceptual hash)
   - Libraries: ImageMagick compare, Python PIL + scikit-image, or Node.js pixelmatch
   - Command example:
     ```bash
     compare -metric SSIM baseline.png preview.png diff.png
     ```
   - Parse similarity score (0.0 to 1.0)

3. **Ralph-wiggum decision**
   - If similarity >= threshold: Exit loop, proceed to Phase 3
   - If similarity < threshold AND iterations < max:
     - Generate diff visualization (overlay red boxes on differences)
     - Pass to LLM:
       ```
       Current similarity: 0.87 (target: 0.92)
       Differences detected:
       - Region (100,50)-(200,100): Color mismatch
       - Region (50,200)-(150,250): Spacing too tight

       Analyze the Compose code and fix visual discrepancies.
       Focus on: colors, padding, margins, text sizes, alignment.
       ```
     - LLM regenerates code using Edit tool
     - Loop back to step 1
   - If iterations >= max: Exit with warning, show best attempt

4. **Return to main flow**
   - Output: Final similarity score, iteration count, diff images
   - Mark TodoWrite item complete

### Phase 3: Device Testing (Mobile-MCP)

Use the `device-tester` agent:

```bash
Task tool with subagent_type="compose-designer:device-tester"
Prompt: "Test generated Compose UI on device"
Pass: generated_file_path, baseline_image_path, config
```

**Agent tasks:**

1. **Generate test harness**
   - Create `{testing.test_activity_name}.kt`:
     ```kotlin
     package {testing.test_activity_package}

     import android.os.Bundle
     import androidx.activity.ComponentActivity
     import androidx.activity.compose.setContent
     import {generated_component_import}

     class ComposeTestActivity : ComponentActivity() {
         override fun onCreate(savedInstanceState: Bundle?) {
             super.onCreate(savedInstanceState)
             setContent {
                 // Generated component with mock data
                 {ComponentName}(/* mock data */)
             }
         }
     }
     ```
   - Update `AndroidManifest.xml` to register activity:
     ```xml
     <activity android:name=".test.ComposeTestActivity" />
     ```

2. **Build and deploy**
   - If `testing.rebuild_required: true`:
     ```bash
     ./gradlew assembleDebug
     ```
   - Get available devices:
     ```bash
     mobile_list_available_devices
     ```
   - Select device from config or prompt user if `device_id: "auto"`
   - Install APK:
     ```bash
     mobile_install_app --device {device_id} --path app/build/outputs/apk/debug/app-debug.apk
     ```

3. **Launch and capture**
   - Launch test activity:
     ```bash
     mobile_launch_app --device {device_id} --packageName {app_package}/.test.ComposeTestActivity
     ```
   - Wait for render (add delay if needed)
   - Take screenshot:
     ```bash
     mobile_take_screenshot --device {device_id}
     ```
   - Save to: `/tmp/compose-designer/device-screenshot.png`

4. **Visual regression check**
   - Compare device screenshot vs baseline
   - Calculate similarity (should be high if Phase 2 succeeded)
   - If similarity drops significantly (<0.85):
     - Report: "Preview rendered correctly but device rendering differs"
     - Common causes: theme not applied, missing resources, dynamic text sizing

5. **Interaction testing**
   - Analyze baseline design to infer interactions:
     - Buttons → should be tappable
     - Text fields → should accept text input
     - Scrollable content → should scroll
   - Find elements:
     ```bash
     mobile_list_elements_on_screen --device {device_id}
     ```
   - Test interactions:
     ```bash
     # Example: Tap button
     mobile_click_on_screen_at_coordinates --device {device_id} --x {x} --y {y}

     # Example: Type in field
     mobile_type_keys --device {device_id} --text "test input" --submit false
     ```
   - Verify state changes (button enabled, text appears, etc.)

6. **Cleanup**
   - Remove test activity from manifest
   - Optionally uninstall test APK
   - Keep generated component code

7. **Return to main flow**
   - Output: Device similarity score, interaction test results
   - Mark TodoWrite item complete

### Phase 4: Final Report and Confirmation

1. **Generate comprehensive report**
   ```
   ✓ Design-to-Code Complete: {ComponentName}

   Phase 1: Code Generation
   ✓ Input: {input_source}
   ✓ Baseline: {baseline_image_path}
   ✓ Generated: {output_file_path}

   Phase 2: Visual Validation (Ralph-Wiggum)
   ✓ Iterations: {iteration_count}/{max_iterations}
   ✓ Final similarity: {similarity_score} (target: {threshold})
   ✓ Status: {"PASS" if similarity >= threshold else "WARNING"}

   Phase 3: Device Testing
   ✓ Device: {device_name}
   ✓ Runtime similarity: {device_similarity}
   ✓ Interactions: {passed_count}/{total_count} passed

   Generated Files:
   - Component: {output_file_path}
   - Baseline: {baseline_image_path}
   - Validation artifacts: /tmp/compose-designer/{timestamp}/

   Next Steps:
   [ ] Review generated code
   [ ] Integrate into your feature module
   [ ] Add real data/ViewModel integration
   [ ] Run project-specific tests
   ```

2. **Ask user for confirmation**
   - "Review the generated code. Ready to commit? [Y/n]"
   - If yes: Keep generated file, commit with message
   - If no: Keep file but don't commit, ask if they want to retry with different config

3. **Commit (if approved)**
   ```bash
   git add {output_file_path}
   git commit -m "feat: add {ComponentName} generated from design

   Generated using compose-designer plugin.
   Visual similarity: {similarity_score}
   Device tested: ✓"
   ```

4. **Mark all todos complete**

## Error Handling

- **Config missing**: Run `/compose-design config` first
- **Input not found**: Verify file path or Figma URL
- **Preview rendering fails**: Check Gradle setup, provide troubleshooting steps
- **Mobile device not found**: List available devices, ask user to connect
- **Visual similarity not reached**: Show best attempt, provide diff images, suggest manual refinement
- **Figma token missing**: Fall back to image-only mode if `fallback_to_image: true`

## Notes

- Phase 3 (device testing) can be skipped with `--skip-device-test` flag
- Batch mode processes each design sequentially with the same workflow
- All temp files saved to `/tmp/compose-designer/{timestamp}/` for debugging
- Ralph-wiggum loop output is verbose; show progress to user
```

**Step 2: Commit create command**

```bash
git add .claude/plugins/compose-designer/commands/create.md
git commit -m "feat: add create command with three-phase workflow"
```

---

## Task 4: Create Design Generator Agent

**Files:**
- Create: `.claude/plugins/compose-designer/agents/design-generator.md`

**Step 1: Create design generator agent**

Create `.claude/plugins/compose-designer/agents/design-generator.md`:

```markdown
---
name: design-generator
description: Generates initial Compose code from design input (screenshot/Figma)
color: blue
tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - Glob
---

# Design Generator Agent

You are a specialist in generating Jetpack Compose code from design inputs.

## Your Task

Generate production-quality Compose code that accurately represents the provided design (screenshot or Figma frame).

## Inputs You'll Receive

From the main command, you'll receive:
- `config`: Configuration object from `.claude/compose-designer.yaml`
- `input_source`: "figma", "image", or "clipboard"
- `input_path`: File path or Figma URL
- `name`: Component/screen name (e.g., "ProfileCard")
- `type`: "component" or "screen"
- `baseline_image_path`: Where to save baseline image

## Your Workflow

### Step 1: Process Design Input

**If Figma URL:**
1. Parse the Figma URL to extract file ID and node ID
2. Check if `FIGMA_TOKEN` environment variable exists (from config)
3. If token exists and `config.figma.extract_tokens` is true:
   - Call Figma REST API to fetch node data:
     ```bash
     curl -H "X-Figma-Token: $FIGMA_TOKEN" \
       "https://api.figma.com/v1/files/{file_id}/nodes?ids={node_id}"
     ```
   - Parse JSON response to extract:
     - Colors: fills, strokes → `Color(0xFFxxxxxx)`
     - Text styles: fontSize, fontWeight, lineHeight → `TextStyle(...)`
     - Spacing: padding, gaps, margins → `{value}.dp`
     - Layout: type (FRAME, AUTO_LAYOUT) → Column/Row/Box
   - Export frame as PNG:
     ```bash
     curl -H "X-Figma-Token: $FIGMA_TOKEN" \
       "https://api.figma.com/v1/images/{file_id}?ids={node_id}&format=png" \
       -o {baseline_image_path}
     ```
4. If no token or extraction fails:
   - If `config.figma.fallback_to_image` is true:
     - Use Figma screenshot (via WebFetch or manual instruction)
     - Save to `baseline_image_path`
   - Else: Report error and abort

**If image file:**
1. Verify file exists using Bash
2. Copy to `baseline_image_path` for consistency
3. No token extraction (image-only mode)

**If clipboard:**
1. Use clipboard tool/command to extract image
2. Save to `baseline_image_path`

### Step 2: Analyze Design Visually

Use LLM vision capabilities (you are multimodal) to analyze the baseline image:

1. **Identify layout structure:**
   - Is it a Column (vertical stack)?
   - Is it a Row (horizontal stack)?
   - Is it a Box (overlapping/absolute positioning)?
   - Are there nested layouts?

2. **Identify UI elements:**
   - Text fields (label + value, editable vs read-only)
   - Buttons (primary, secondary, text buttons)
   - Images (profile pics, icons, photos)
   - Icons (material icons, custom)
   - Cards, dividers, spacers
   - Lists (scrollable, fixed)

3. **Extract visual properties:**
   - **Colors**: Background, text, accents, borders
     - If Figma tokens available: use exact hex values
     - Else: estimate from pixels
   - **Typography**: Font sizes, weights, line heights
     - If Figma tokens available: use exact values
     - Else: estimate (e.g., "24sp for title, 16sp for body")
   - **Spacing**: Padding, margins, gaps between elements
     - If Figma tokens available: use exact dp values
     - Else: estimate proportions
   - **Dimensions**: Component sizes, aspect ratios

4. **Infer state requirements:**
   - Text fields → need mutableStateOf for text input
   - Checkboxes/switches → need mutableStateOf for boolean
   - Lists → need mock data list

### Step 3: Generate Compose Code

Generate a Kotlin file with the following structure:

```kotlin
package {config.output.package_base}.{feature_or_module}

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
 * {Brief description of what this component does}
 *
 * Generated by compose-designer plugin
 */
@Composable
fun {Name}{Suffix}(
    modifier: Modifier = Modifier,
    // Add parameters for data (if type=component)
    // For stateless components, add callback parameters
) {
    // Main layout (Column/Row/Box based on analysis)
    {LayoutType}(
        modifier = modifier{.fillMaxWidth()}{.padding(16.dp)},
        // Layout-specific properties
        // Column: verticalArrangement, horizontalAlignment
        // Row: horizontalArrangement, verticalAlignment
        // Box: contentAlignment
    ) {
        // Generate UI elements from analysis

        // Example Text:
        Text(
            text = "Title",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF000000) // or theme color if extracted
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Example Button:
        Button(
            onClick = { /* callback parameter */ },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Action")
        }

        // ... more elements
    }
}

/**
 * Preview for {Name}{Suffix}
 */
{config.preview.preview_annotation}(
    name = "{Name} Preview",
    showBackground = {config.preview.show_background},
    backgroundColor = {parse config.preview.background_color to 0xFFxxxxxx},
    device = "{config.preview.device_spec}"
)
@Composable
private fun {Name}{Suffix}Preview() {
    {Name}{Suffix}(
        // Provide mock data for preview
    )
}
```

**Code generation rules:**

1. **Naming conventions:**
   - Component name: `{name}{config.naming.component_suffix}` or `{name}{config.naming.screen_suffix}`
   - Preview function: `{name}{suffix}Preview`

2. **Architecture patterns:**
   - If `config.architecture.stateless_components: true`:
     - Don't use `remember` or `mutableStateOf` inside
     - Pass state as parameters
     - Use callback lambdas for actions
   - If `config.architecture.state_hoisting: true`:
     - Hoist state to preview or parent
   - If `config.architecture.remember_saveable: true`:
     - Use `rememberSaveable` instead of `remember` for state

3. **Theme integration:**
   - If `config.output.extract_theme_from_existing: true`:
     - Search codebase for `Color.kt`, `Type.kt`, `Theme.kt`
     - Use existing theme values:
       ```kotlin
       // Instead of:
       Color(0xFF2196F3)
       // Use:
       MaterialTheme.colorScheme.primary
       ```
     - Match font sizes to existing typography scale

4. **Comments:**
   - If `config.output.include_comments: false`:
     - Minimal comments, self-documenting code
   - Else:
     - Add brief explanations for complex layouts

5. **Write to file:**
   - Path: `{config.output.default_output_dir}/{package_path}/{name}{suffix}.kt`
   - Ensure directory exists (create if needed)

### Step 4: Report Results

Return to the main command with:
```
✓ Design analysis complete
✓ Generated: {output_file_path}
✓ Baseline saved: {baseline_image_path}

Component structure:
- Layout: {Column/Row/Box}
- Elements: {count} UI elements
- State: {stateless/stateful}
- Theme: {theme_colors_used ? "Integrated" : "Hardcoded colors"}

Ready for Phase 2: Visual Validation
```

## Tips for Accurate Generation

- **Layout**: Start with the outermost container, work inward
- **Spacing**: Use consistent spacing (8.dp, 16.dp, 24.dp increments)
- **Colors**: Prefer theme colors over hardcoded hex values
- **Text**: Match font sizes to Material3 typography scale
- **Images**: Use placeholder painters for preview, parameter for real use
- **Lists**: Generate 3-5 mock items for preview
- **Icons**: Use Material Icons when possible, note if custom needed

## Error Handling

- **Figma API fails**: Fall back to image-only mode if configured
- **Baseline image missing**: Abort with clear error message
- **Output directory doesn't exist**: Create it
- **Invalid config**: Report specific issue, suggest fix
```

**Step 2: Commit design generator agent**

```bash
git add .claude/plugins/compose-designer/agents/design-generator.md
git commit -m "feat: add design-generator agent for code generation"
```

---

## Task 5: Create Visual Validator Agent

**Files:**
- Create: `.claude/plugins/compose-designer/agents/visual-validator.md`

**Step 1: Create visual validator agent**

Create `.claude/plugins/compose-designer/agents/visual-validator.md`:

```markdown
---
name: visual-validator
description: Validates generated Compose UI using ralph-wiggum loop and visual diff
color: green
tools:
  - Read
  - Edit
  - Bash
  - Skill
---

# Visual Validator Agent

You are a specialist in validating and refining Compose UI code to match design baselines using the ralph-wiggum self-correction loop.

## Your Task

Iteratively refine the generated Compose code until it visually matches the baseline design within the configured similarity threshold.

## Inputs You'll Receive

- `generated_file_path`: Path to generated .kt file
- `baseline_image_path`: Path to original design image
- `config`: Configuration object
- `similarity_threshold`: Target similarity (e.g., 0.92)
- `max_iterations`: Maximum refinement iterations (e.g., 8)

## Your Workflow

You will use the ralph-wiggum loop skill to iteratively refine the UI. The loop will automatically handle iterations and stopping conditions.

### Preparation (Before Ralph Loop)

1. **Verify prerequisites:**
   - Gradle setup is functional
   - Preview rendering is available
   - Image comparison tool is installed (ImageMagick or Python PIL)

2. **Set up temp directory:**
   ```bash
   mkdir -p /tmp/compose-designer/{timestamp}
   ```

### Ralph-Wiggum Loop

Invoke the ralph-wiggum skill:

```
/ralph-loop --task "Refine Compose UI to match baseline" \
            --validation "visual-similarity" \
            --threshold {similarity_threshold} \
            --max-iterations {max_iterations}
```

**Within each iteration, you will:**

#### Iteration Step 1: Render Preview

Render the Compose preview to an image:

```bash
# Option A: Using Gradle task (if available)
./gradlew :app:compileDebugKotlin
./gradlew :app:generateDebugPreviewImages

# Option B: Using Android Studio CLI (if available)
studio-preview-render {generated_file_path} --output /tmp/compose-designer/{timestamp}/preview-{iteration}.png

# Option C: Manual instruction if automated rendering unavailable
# Tell user to manually screenshot the preview in Android Studio
```

Wait for `config.validation.preview_screenshot_delay_ms` before capturing.

Save to: `/tmp/compose-designer/{timestamp}/preview-iteration-{n}.png`

#### Iteration Step 2: Calculate Visual Similarity

Use image comparison algorithm:

**Option A: ImageMagick (preferred)**
```bash
# Install if needed
brew install imagemagick  # macOS
apt-get install imagemagick  # Linux

# Compare images
compare -metric SSIM \
  {baseline_image_path} \
  /tmp/compose-designer/{timestamp}/preview-iteration-{n}.png \
  /tmp/compose-designer/{timestamp}/diff-iteration-{n}.png 2>&1 | tee similarity.txt

# Parse similarity score from output
```

**Option B: Python PIL + scikit-image**
```python
from skimage.metrics import structural_similarity as ssim
from PIL import Image
import numpy as np

# Load images
baseline = np.array(Image.open(baseline_path))
preview = np.array(Image.open(preview_path))

# Resize to same dimensions if needed
if baseline.shape != preview.shape:
    preview = np.array(Image.fromarray(preview).resize(baseline.shape[:2][::-1]))

# Calculate SSIM
score = ssim(baseline, preview, multichannel=True)
print(f"Similarity: {score:.4f}")
```

**Option C: Node.js pixelmatch**
```javascript
const fs = require('fs');
const PNG = require('pngjs').PNG;
const pixelmatch = require('pixelmatch');

const img1 = PNG.sync.read(fs.readFileSync('baseline.png'));
const img2 = PNG.sync.read(fs.readFileSync('preview.png'));

const diff = new PNG({ width: img1.width, height: img1.height });
const numDiffPixels = pixelmatch(img1.data, img2.data, diff.data, img1.width, img1.height, { threshold: 0.1 });

const totalPixels = img1.width * img1.height;
const similarity = 1 - (numDiffPixels / totalPixels);
console.log(`Similarity: ${similarity.toFixed(4)}`);
```

Extract similarity score (0.0 to 1.0).

#### Iteration Step 3: Generate Diff Visualization

Create a visual diff overlay showing differences:

```bash
# ImageMagick: highlight differences in red
composite -compose difference {baseline_image_path} /tmp/compose-designer/{timestamp}/preview-iteration-{n}.png /tmp/compose-designer/{timestamp}/diff-iteration-{n}.png
```

#### Iteration Step 4: Analyze Differences

Show the user/LLM:
```
Iteration {n}/{max_iterations}
Current similarity: {score} (target: {threshold})

Differences detected (from visual diff):
- Region (x1,y1)-(x2,y2): [describe difference - e.g., "Button color mismatch"]
- Region (x3,y3)-(x4,y4): [describe difference - e.g., "Padding too small"]
- ...

Analysis:
[Analyze the Compose code and identify likely causes]

Common issues to check:
- Colors: Hardcoded vs theme colors
- Spacing: padding(), spacedBy(), height()/width()
- Text: fontSize, fontWeight, lineHeight
- Alignment: Alignment.Start vs Center vs End
- Sizes: fillMaxWidth vs fixed width
```

#### Iteration Step 5: Ralph Decision Point

Ralph-wiggum evaluates:
- **If similarity >= threshold**: SUCCESS → Exit loop
- **If iterations >= max_iterations**: MAX_REACHED → Exit with best attempt
- **Else**: CONTINUE → Proceed to refinement

#### Iteration Step 6: Refine Code

Use the Edit tool to fix identified issues:

```kotlin
// Example refinements:

// Before:
Text(
    text = "Title",
    fontSize = 20.sp,  // Too small
    color = Color(0xFF000000)  // Should use theme
)

// After:
Text(
    text = "Title",
    fontSize = 24.sp,  // Increased to match baseline
    color = MaterialTheme.colorScheme.onSurface  // Use theme color
)

// Before:
Column(modifier = Modifier.padding(8.dp)) {  // Padding too small
    // ...
}

// After:
Column(modifier = Modifier.padding(16.dp)) {  // Increased padding
    // ...
}

// Before:
Button(
    onClick = { },
    colors = ButtonDefaults.buttonColors(
        containerColor = Color(0xFF1976D2)  // Wrong blue shade
    )
) { }

// After:
Button(
    onClick = { },
    colors = ButtonDefaults.buttonColors(
        containerColor = Color(0xFF2196F3)  // Corrected to match baseline
    )
) { }
```

Make targeted edits using the Edit tool:
- Focus on the most significant differences first
- Change one aspect at a time (color, spacing, or size)
- Preserve code structure and logic

Loop back to Iteration Step 1.

### Post-Loop: Final Report

After ralph-wiggum loop exits:

1. **Success (similarity >= threshold):**
   ```
   ✓ Visual validation PASSED

   Final similarity: {score} (target: {threshold})
   Iterations: {n}/{max_iterations}

   Refinements made:
   - {list of changes across iterations}

   Validation artifacts saved to:
   /tmp/compose-designer/{timestamp}/
   - preview-iteration-{1..n}.png
   - diff-iteration-{1..n}.png

   Ready for Phase 3: Device Testing
   ```

2. **Max iterations reached (similarity < threshold):**
   ```
   ⚠ Visual validation incomplete

   Final similarity: {score} (target: {threshold})
   Iterations: {max_iterations}/{max_iterations} (limit reached)

   Best attempt saved. Differences remaining:
   - {list remaining differences}

   Suggestions:
   - Review diff images in /tmp/compose-designer/{timestamp}/
   - Consider manual refinement
   - Adjust config.validation.visual_similarity_threshold if acceptable

   Proceed to Phase 3? [Y/n]
   ```

## Tips for Effective Refinement

1. **Prioritize large differences:**
   - Fix layout structure before fine-tuning spacing
   - Fix colors before adjusting shades
   - Fix element sizes before adjusting padding

2. **Common issues and fixes:**
   - **Color mismatch**: Check theme colors vs hardcoded hex
   - **Spacing off**: Adjust padding, spacedBy, Spacer heights
   - **Text size wrong**: Increment/decrement fontSize by 2.sp
   - **Alignment wrong**: Change Alignment enum values
   - **Element missing**: Add missing composable
   - **Extra element**: Remove or hide with conditional

3. **Iteration efficiency:**
   - Make multiple related changes per iteration (e.g., fix all text sizes at once)
   - Don't make the same change twice (learn from previous iterations)
   - If stuck (similarity not improving), try a different approach

4. **Similarity plateau:**
   - If similarity stops improving (<1% change for 2 iterations), consider:
     - The baseline has elements not reproducible in Compose (e.g., exact font rendering)
     - The threshold may be too strict
     - Manual refinement may be needed

## Error Handling

- **Preview rendering fails**: Provide Gradle/Studio troubleshooting, ask user to render manually
- **Image comparison tool missing**: Offer alternative tools, provide installation instructions
- **Similarity calculation error**: Use fallback method or ask user to manually evaluate
- **Code syntax error after refinement**: Fix immediately before next iteration
```

**Step 2: Commit visual validator agent**

```bash
git add .claude/plugins/compose-designer/agents/visual-validator.md
git commit -m "feat: add visual-validator agent with ralph-wiggum loop"
```

---

## Task 6: Create Device Tester Agent

**Files:**
- Create: `.claude/plugins/compose-designer/agents/device-tester.md`

**Step 1: Create device tester agent**

Create `.claude/plugins/compose-designer/agents/device-tester.md`:

```markdown
---
name: device-tester
description: Tests generated Compose UI on real device using mobile-mcp
color: purple
tools:
  - Bash
  - Read
  - Write
  - Edit
  - mcp__mobile-mcp__*
---

# Device Tester Agent

You are a specialist in testing Compose UI on real Android devices using the mobile-mcp integration.

## Your Task

Deploy the generated Compose component to a real device, validate visual accuracy, and test interactions.

## Inputs You'll Receive

- `generated_file_path`: Path to generated .kt file with component
- `baseline_image_path`: Original design for comparison
- `config`: Configuration object with testing settings
- `app_package`: Android app package name

## Your Workflow

### Step 1: Generate Test Harness

Create a test activity to host the generated component:

1. **Create ComposeTestActivity.kt:**

```kotlin
package {config.testing.test_activity_package}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
// Import generated component
import {import_path_from_generated_file}.{ComponentName}

/**
 * Test activity for compose-designer plugin.
 * Displays generated UI components for validation.
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
                    // Render generated component with mock data
                    {ComponentName}(
                        // TODO: Add mock data parameters
                        // Example: title = "Test Title"
                    )
                }
            }
        }
    }
}
```

Save to: `{config.output.default_output_dir}/{test_activity_package_path}/{test_activity_name}.kt`

2. **Update AndroidManifest.xml:**

Find the manifest file and add:

```xml
<activity
    android:name="{config.testing.test_activity_package}.{config.testing.test_activity_name}"
    android:exported="true"
    android:theme="@style/Theme.AppCompat.Light.NoActionBar" />
```

Use Edit tool to add this within the `<application>` tag.

### Step 2: Build APK

If `config.testing.rebuild_required` is true:

```bash
# Clean build to ensure changes are included
./gradlew clean

# Build debug APK
./gradlew assembleDebug

# Verify APK was built
ls -lh app/build/outputs/apk/debug/app-debug.apk
```

Expected: APK file exists with reasonable size (>1MB)

If build fails:
- Check for syntax errors in generated code
- Check for missing imports
- Provide error message to user

### Step 3: Select Device

Get available devices using mobile-mcp:

```bash
mobile_list_available_devices
```

Parse output to extract device IDs and names.

If `config.testing.device_id` is "auto":
- If only one device: Use it automatically
- If multiple devices: Ask user to select:
  ```
  Multiple devices found:
  1. Pixel 4 (emulator-5554)
  2. Galaxy S21 (abc123def)

  Which device should I use for testing? [1/2]
  ```

Else: Use `config.testing.device_id` directly.

Store selected device ID.

### Step 4: Install and Launch

Install APK on device:

```bash
mobile_install_app \
  --device {device_id} \
  --path app/build/outputs/apk/debug/app-debug.apk
```

Expected: Installation success message

Launch test activity:

```bash
mobile_launch_app \
  --device {device_id} \
  --packageName {app_package}/{config.testing.test_activity_package}.{config.testing.test_activity_name}
```

Wait for activity to render (1-2 seconds).

### Step 5: Capture Device Screenshot

Take screenshot using mobile-mcp:

```bash
mobile_take_screenshot --device {device_id}
```

The tool returns the screenshot image data. Save to:
`/tmp/compose-designer/{timestamp}/device-screenshot.png`

### Step 6: Visual Regression Check

Compare device screenshot against baseline:

```bash
# Use same comparison method as visual-validator agent
compare -metric SSIM \
  {baseline_image_path} \
  /tmp/compose-designer/{timestamp}/device-screenshot.png \
  /tmp/compose-designer/{timestamp}/device-diff.png 2>&1
```

Extract device similarity score.

**Evaluate results:**

- **If device_similarity >= 0.90**: Excellent, preview matched device rendering
- **If 0.85 <= device_similarity < 0.90**: Good, minor differences acceptable
- **If device_similarity < 0.85**: Investigate differences

**If similarity drops significantly from preview:**

Analyze potential causes:
```
⚠ Device rendering differs from preview
Preview similarity: {preview_similarity}
Device similarity: {device_similarity}
Delta: {delta}

Possible causes:
- Theme not applied correctly (MaterialTheme missing)
- Device-specific font rendering
- Dynamic text sizing (accessibility settings)
- Missing resources (colors, strings, drawables)
- Different screen density
```

Provide suggestions to user.

### Step 7: Interaction Testing

Infer interactions from the baseline design and test them.

**Identify interactive elements:**

Use mobile-mcp to list elements:

```bash
mobile_list_elements_on_screen --device {device_id}
```

Parse output to find:
- Buttons: elements with "Button" in type or "clickable" attribute
- Text fields: elements with "EditText" or "TextField" in type
- Scrollable areas: elements with "scrollable" attribute

**Test interactions:**

For each interactive element:

1. **Button tap test:**
   ```bash
   # Get button coordinates from list_elements
   mobile_click_on_screen_at_coordinates \
     --device {device_id} \
     --x {button_x} \
     --y {button_y}

   # Wait briefly
   sleep 1

   # Take screenshot to verify state change
   mobile_take_screenshot --device {device_id}

   # Check if UI changed (compare screenshots)
   ```

2. **Text field input test:**
   ```bash
   # Tap text field to focus
   mobile_click_on_screen_at_coordinates \
     --device {device_id} \
     --x {field_x} \
     --y {field_y}

   # Type text
   mobile_type_keys \
     --device {device_id} \
     --text "Test input 123" \
     --submit false

   # Take screenshot to verify text appeared
   mobile_take_screenshot --device {device_id}
   ```

3. **Scroll test (if applicable):**
   ```bash
   mobile_swipe_on_screen \
     --device {device_id} \
     --direction up \
     --distance 400

   # Verify content scrolled
   mobile_take_screenshot --device {device_id}
   ```

**Record results:**

```
Interaction Test Results:
✓ Button tap: Responsive (visual feedback detected)
✓ Text input: Accepted text, displayed correctly
✓ Scroll: Content scrolled smoothly
- N/A: No additional interactions inferred

Passed: {passed_count}/{total_count}
```

### Step 8: Cleanup

1. **Remove test activity from manifest:**
   - Use Edit tool to remove the `<activity>` tag added in Step 1

2. **Optionally uninstall test APK:**
   ```bash
   mobile_uninstall_app \
     --device {device_id} \
     --bundle_id {app_package}
   ```

   Only if user confirms they want cleanup.

3. **Keep generated component code:**
   - The actual component file should remain for user integration

4. **Preserve validation artifacts:**
   - Keep screenshots, diffs in `/tmp/compose-designer/{timestamp}/`
   - User may want to review them

### Step 9: Generate Report

Provide comprehensive report:

```
✓ Device Testing Complete

Device: {device_name} ({device_id})
APK: app-debug.apk ({apk_size})

Visual Validation:
- Preview similarity: {preview_similarity}
- Device similarity: {device_similarity}
- Status: {PASS if device_similarity >= 0.85 else WARNING}

Interaction Tests:
- Buttons: {button_test_results}
- Text fields: {field_test_results}
- Scroll: {scroll_test_results}
- Overall: {passed_count}/{total_count} passed

Screenshots saved:
- Device: /tmp/compose-designer/{timestamp}/device-screenshot.png
- Diff: /tmp/compose-designer/{timestamp}/device-diff.png

{If issues detected:}
⚠ Issues Detected:
- {list issues and suggestions}

{If all passed:}
✓ All tests passed! Component is ready for integration.
```

## Edge Cases and Error Handling

1. **No devices connected:**
   ```
   ✗ No Android devices found.

   Please connect a device or start an emulator:
   - Physical device: Enable USB debugging and connect
   - Emulator: Launch from Android Studio (AVD Manager)

   Then retry: /compose-design create ...
   ```

2. **Build fails:**
   - Check Gradle output for errors
   - Verify generated code syntax
   - Suggest fixes (e.g., missing imports)

3. **Activity launch fails:**
   - Verify manifest was updated correctly
   - Check if package name is correct
   - Suggest manual launch to debug

4. **Screenshot fails:**
   - Check device permissions
   - Try alternative screenshot method
   - Fall back to manual screenshot

5. **Element not found for interaction:**
   - Log warning but continue with other tests
   - Suggest manual verification

6. **Device rendering drastically different:**
   - Suggest checking theme application
   - Recommend manual review
   - Offer to skip device testing for this run

## Testing Tips

- **Mock data quality**: Use realistic mock data to test layout properly
- **Different screen sizes**: Test on different device sizes if available
- **Dark mode**: Optionally test with dark theme enabled
- **Accessibility**: Check with larger font sizes if time permits
- **Performance**: Note any lag or jank during interactions

## Notes

- Phase 3 is optional; user can skip with `--skip-device-test` flag
- Device testing catches issues previews miss: theme application, dynamic sizing, touch targets
- Keep test activity simple; focus on visual and basic interaction validation
- Advanced interaction testing (navigation, state persistence) is out of scope
```

**Step 2: Commit device tester agent**

```bash
git add .claude/plugins/compose-designer/agents/device-tester.md
git commit -m "feat: add device-tester agent for mobile-mcp integration"
```

---

## Task 7: Add Supporting Utilities

**Files:**
- Create: `.claude/plugins/compose-designer/utils/image-similarity.py`
- Create: `.claude/plugins/compose-designer/utils/figma-client.sh`

**Step 1: Create image similarity utility**

Create `.claude/plugins/compose-designer/utils/image-similarity.py`:

```python
#!/usr/bin/env python3
"""
Image similarity calculator for compose-designer plugin.
Uses SSIM (Structural Similarity Index) to compare images.

Usage:
  python image-similarity.py baseline.png preview.png [--output diff.png]
"""

import sys
import argparse
from pathlib import Path

try:
    from skimage.metrics import structural_similarity as ssim
    from PIL import Image
    import numpy as np
except ImportError:
    print("Error: Required packages not installed.", file=sys.stderr)
    print("Install with: pip install scikit-image pillow numpy", file=sys.stderr)
    sys.exit(1)


def calculate_similarity(baseline_path, preview_path, output_diff_path=None):
    """
    Calculate SSIM between two images.

    Returns:
        float: Similarity score (0.0 to 1.0)
    """
    # Load images
    baseline = Image.open(baseline_path)
    preview = Image.open(preview_path)

    # Convert to RGB if needed
    if baseline.mode != 'RGB':
        baseline = baseline.convert('RGB')
    if preview.mode != 'RGB':
        preview = preview.convert('RGB')

    # Resize to same dimensions
    if baseline.size != preview.size:
        preview = preview.resize(baseline.size, Image.LANCZOS)

    # Convert to numpy arrays
    baseline_arr = np.array(baseline)
    preview_arr = np.array(preview)

    # Calculate SSIM
    score = ssim(baseline_arr, preview_arr, multichannel=True, channel_axis=2)

    # Generate diff image if requested
    if output_diff_path:
        # Calculate absolute difference
        diff = np.abs(baseline_arr.astype(float) - preview_arr.astype(float))

        # Enhance differences for visibility
        diff = (diff * 3).clip(0, 255).astype(np.uint8)

        # Save diff image
        diff_img = Image.fromarray(diff)
        diff_img.save(output_diff_path)

    return score


def main():
    parser = argparse.ArgumentParser(description='Calculate image similarity using SSIM')
    parser.add_argument('baseline', help='Path to baseline image')
    parser.add_argument('preview', help='Path to preview image')
    parser.add_argument('--output', '-o', help='Path to save diff image (optional)')

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.baseline).exists():
        print(f"Error: Baseline image not found: {args.baseline}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.preview).exists():
        print(f"Error: Preview image not found: {args.preview}", file=sys.stderr)
        sys.exit(1)

    # Calculate similarity
    try:
        score = calculate_similarity(args.baseline, args.preview, args.output)
        print(f"{score:.4f}")  # Print to stdout for parsing

        if args.output:
            print(f"Diff image saved to: {args.output}", file=sys.stderr)

        sys.exit(0)
    except Exception as e:
        print(f"Error calculating similarity: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
```

Make executable:

```bash
chmod +x .claude/plugins/compose-designer/utils/image-similarity.py
```

**Step 2: Create Figma client utility**

Create `.claude/plugins/compose-designer/utils/figma-client.sh`:

```bash
#!/bin/bash
# Figma API client for compose-designer plugin
# Usage: ./figma-client.sh <command> <args>

set -euo pipefail

FIGMA_TOKEN="${FIGMA_TOKEN:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
        error "FIGMA_TOKEN environment variable not set"
    fi
}

# Parse Figma URL
parse_url() {
    local url="$1"

    # Extract file ID and node ID from URL
    # Format: https://www.figma.com/file/{file_id}/{name}?node-id={node_id}
    # or: figma://file/{file_id}?node-id={node_id}

    file_id=$(echo "$url" | grep -oP '(?<=file/)[^/]+' || echo "")
    node_id=$(echo "$url" | grep -oP '(?<=node-id=)[^&]+' || echo "")

    if [ -z "$file_id" ]; then
        error "Could not extract file ID from URL: $url"
    fi

    echo "$file_id|$node_id"
}

# Fetch node data (colors, typography, spacing)
fetch_node_data() {
    check_token

    local file_id="$1"
    local node_id="$2"

    info "Fetching node data from Figma..."

    curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
        "https://api.figma.com/v1/files/$file_id/nodes?ids=$node_id" \
        || error "Failed to fetch node data"
}

# Export node as image
export_image() {
    check_token

    local file_id="$1"
    local node_id="$2"
    local output_path="$3"
    local format="${4:-png}"
    local scale="${5:-2}"

    info "Exporting Figma frame to $format..."

    # Get image URL
    response=$(curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
        "https://api.figma.com/v1/images/$file_id?ids=$node_id&format=$format&scale=$scale")

    # Extract image URL from JSON
    image_url=$(echo "$response" | grep -oP '(?<="'$node_id'":"https:)[^"]+' | sed 's/^/https:/')

    if [ -z "$image_url" ]; then
        error "Failed to get image URL. Response: $response"
    fi

    # Download image
    info "Downloading image..."
    curl -s "$image_url" -o "$output_path" \
        || error "Failed to download image"

    info "Image saved to: $output_path"
}

# Main command router
case "${1:-}" in
    parse)
        parse_url "${2:-}"
        ;;
    fetch-node)
        IFS='|' read -r file_id node_id <<< "$(parse_url "${2:-}")"
        fetch_node_data "$file_id" "$node_id"
        ;;
    export)
        IFS='|' read -r file_id node_id <<< "$(parse_url "${2:-}")"
        export_image "$file_id" "$node_id" "${3:-output.png}" "${4:-png}" "${5:-2}"
        ;;
    *)
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  parse <figma-url>                      - Parse URL and extract IDs"
        echo "  fetch-node <figma-url>                 - Fetch node data (JSON)"
        echo "  export <figma-url> <output> [format] [scale]  - Export as image"
        echo ""
        echo "Environment:"
        echo "  FIGMA_TOKEN - Figma API token (required)"
        exit 1
        ;;
esac
```

Make executable:

```bash
chmod +x .claude/plugins/compose-designer/utils/figma-client.sh
```

**Step 3: Commit utilities**

```bash
git add .claude/plugins/compose-designer/utils/
git commit -m "feat: add image similarity and Figma client utilities"
```

---

## Task 8: Create Example Configuration

**Files:**
- Create: `.claude/plugins/compose-designer/examples/example-config.yaml`
- Create: `.claude/plugins/compose-designer/examples/example-usage.md`

**Step 1: Create example config**

Create `.claude/plugins/compose-designer/examples/example-config.yaml`:

```yaml
# Example Compose Designer Configuration
# Copy to your project as .claude/compose-designer.yaml and customize

naming:
  component_suffix: "Component"
  screen_suffix: "Screen"
  preview_annotation: "@Preview"  # or @MyDevices for custom

architecture:
  stateless_components: true
  state_hoisting: true
  remember_saveable: false

preview:
  show_background: true
  background_color: "#FFFFFF"
  device_spec: "spec:width=411dp,height=891dp"
  font_scale: 1.0

validation:
  visual_similarity_threshold: 0.92
  max_ralph_iterations: 8
  preview_screenshot_delay_ms: 500

testing:
  test_activity_package: "tap.photo.boost.restoration.test"
  test_activity_name: "ComposeTestActivity"
  device_id: "auto"
  rebuild_required: true

figma:
  extract_tokens: true
  api_token_env: "FIGMA_TOKEN"
  fallback_to_image: true

output:
  package_base: "tap.photo.boost.restoration"
  default_output_dir: "app/src/main/java"
  include_comments: false
  extract_theme_from_existing: true
```

**Step 2: Create usage examples**

Create `.claude/plugins/compose-designer/examples/example-usage.md`:

```markdown
# Compose Designer Usage Examples

## Example 1: Simple Button Component from Screenshot

**Input:** `button-design.png` (screenshot of a custom button)

**Command:**
```bash
/compose-design create --input button-design.png --name CustomButton --type component
```

**Output:** `CustomButtonComponent.kt`

```kotlin
package tap.photo.boost.restoration.ui.components

import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview

@Composable
fun CustomButtonComponent(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Button(
        onClick = onClick,
        modifier = modifier
    ) {
        Text(text = text)
    }
}

@Preview
@Composable
private fun CustomButtonComponentPreview() {
    CustomButtonComponent(
        text = "Click Me",
        onClick = {}
    )
}
```

---

## Example 2: Profile Card from Figma with Design Tokens

**Input:** Figma link with design system colors

**Command:**
```bash
export FIGMA_TOKEN="your-token-here"
/compose-design create --input "figma://file/ABC123?node-id=1:234" --name ProfileCard --type component
```

**Output:** `ProfileCardComponent.kt` with extracted theme colors

```kotlin
package tap.photo.boost.restoration.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp

@Composable
fun ProfileCardComponent(
    name: String,
    subtitle: String,
    profileImage: Painter,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Image(
            painter = profileImage,
            contentDescription = "Profile",
            modifier = Modifier
                .size(56.dp)
                .clip(CircleShape)
        )

        Column {
            Text(
                text = name,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Preview
@Composable
private fun ProfileCardComponentPreview() {
    ProfileCardComponent(
        name = "John Doe",
        subtitle = "Software Engineer",
        profileImage = painterResource(id = R.drawable.placeholder)
    )
}
```

---

## Example 3: Full Login Screen from Clipboard

**Input:** Screenshot copied to clipboard

**Command:**
```bash
/compose-design create --clipboard --name Login --type screen
```

**Output:** `LoginScreen.kt` with complete layout

```kotlin
package tap.photo.boost.restoration.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp

@Composable
fun LoginScreen(
    onLoginClick: (email: String, password: String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Welcome Back",
            style = MaterialTheme.typography.headlineMedium
        )

        Spacer(modifier = Modifier.height(32.dp))

        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("Email") },
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Password") },
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = { onLoginClick(email, password) },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Log In")
        }
    }
}

@Preview
@Composable
private fun LoginScreenPreview() {
    LoginScreen(onLoginClick = { _, _ -> })
}
```

---

## Example 4: Batch Generation from Folder

**Input:** Folder with multiple design screenshots

**Command:**
```bash
/compose-design create --input ./designs/ --batch
```

**Folder structure:**
```
designs/
  ├── button-primary.png
  ├── button-secondary.png
  ├── card-product.png
  └── card-user.png
```

**Output:** Generates 4 components
- `ButtonPrimaryComponent.kt`
- `ButtonSecondaryComponent.kt`
- `CardProductComponent.kt`
- `CardUserComponent.kt`

Each goes through full 3-phase validation individually.
```

**Step 3: Commit examples**

```bash
git add .claude/plugins/compose-designer/examples/
git commit -m "docs: add example configuration and usage examples"
```

---

## Task 9: Add Testing and Validation

**Files:**
- Create: `.claude/plugins/compose-designer/tests/test-plugin.sh`

**Step 1: Create plugin test script**

Create `.claude/plugins/compose-designer/tests/test-plugin.sh`:

```bash
#!/bin/bash
# Test script for compose-designer plugin
# Validates plugin structure and utilities

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

passed=0
failed=0

test() {
    local name="$1"
    shift

    if "$@"; then
        echo -e "${GREEN}✓${NC} $name"
        ((passed++))
    else
        echo -e "${RED}✗${NC} $name"
        ((failed++))
    fi
}

echo "Testing compose-designer plugin..."
echo ""

# Test 1: Plugin manifest exists and is valid JSON
test "Plugin manifest exists" \
    [ -f .claude/plugins/compose-designer/plugin.json ]

test "Plugin manifest is valid JSON" \
    jq empty .claude/plugins/compose-designer/plugin.json 2>/dev/null

# Test 2: Commands exist
test "Create command exists" \
    [ -f .claude/plugins/compose-designer/commands/create.md ]

test "Config command exists" \
    [ -f .claude/plugins/compose-designer/commands/config.md ]

# Test 3: Agents exist
test "Design generator agent exists" \
    [ -f .claude/plugins/compose-designer/agents/design-generator.md ]

test "Visual validator agent exists" \
    [ -f .claude/plugins/compose-designer/agents/visual-validator.md ]

test "Device tester agent exists" \
    [ -f .claude/plugins/compose-designer/agents/device-tester.md ]

# Test 4: Utilities exist and are executable
test "Image similarity utility exists" \
    [ -f .claude/plugins/compose-designer/utils/image-similarity.py ]

test "Image similarity utility is executable" \
    [ -x .claude/plugins/compose-designer/utils/image-similarity.py ]

test "Figma client utility exists" \
    [ -f .claude/plugins/compose-designer/utils/figma-client.sh ]

test "Figma client utility is executable" \
    [ -x .claude/plugins/compose-designer/utils/figma-client.sh ]

# Test 5: Image similarity utility works (if dependencies installed)
if python3 -c "import skimage, PIL, numpy" 2>/dev/null; then
    test "Image similarity utility runs" \
        python3 .claude/plugins/compose-designer/utils/image-similarity.py --help >/dev/null
else
    echo "⊘ Image similarity utility dependencies not installed (skipped)"
fi

# Test 6: Documentation exists
test "README exists" \
    [ -f .claude/plugins/compose-designer/README.md ]

test "Example config exists" \
    [ -f .claude/plugins/compose-designer/examples/example-config.yaml ]

test "Example usage exists" \
    [ -f .claude/plugins/compose-designer/examples/example-usage.md ]

# Summary
echo ""
echo "=========================================="
echo "Results: $passed passed, $failed failed"
echo "=========================================="

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
```

Make executable:

```bash
chmod +x .claude/plugins/compose-designer/tests/test-plugin.sh
```

**Step 2: Run tests**

```bash
.claude/plugins/compose-designer/tests/test-plugin.sh
```

Expected: All tests pass

**Step 3: Commit tests**

```bash
git add .claude/plugins/compose-designer/tests/
git commit -m "test: add plugin structure validation tests"
```

---

## Task 10: Update Project Documentation

**Files:**
- Modify: `README.md` (add plugin section)
- Create: `docs/plugins/compose-designer.md`

**Step 1: Add plugin section to main README**

Add this section to `README.md`:

```markdown
## Claude Code Plugins

### Compose Designer

Automatically generate production-ready Jetpack Compose code from design mockups (screenshots or Figma).

**Features:**
- 🎨 Multi-input support: Screenshots, Figma links, clipboard
- 🔄 Self-validating: Ralph-wiggum loop ensures 92%+ visual accuracy
- 📱 Device testing: Mobile-mcp integration for real-world validation
- ⚙️ Configurable: Adapts to your project conventions

**Quick Start:**
```bash
# Initialize configuration
/compose-design config

# Generate from screenshot
/compose-design create --input button-design.png --name CustomButton --type component
```

See [docs/plugins/compose-designer.md](docs/plugins/compose-designer.md) for full documentation.
```

**Step 2: Create detailed plugin documentation**

Create `docs/plugins/compose-designer.md`:

```markdown
# Compose Designer Plugin

Comprehensive guide to the compose-designer plugin for generating Compose UI from designs.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Workflow Details](#workflow-details)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Topics](#advanced-topics)

## Overview

The compose-designer plugin transforms design mockups (screenshots or Figma frames) into production-ready Jetpack Compose code through a three-phase workflow:

1. **Generation Phase**: Analyzes design input and generates initial Compose code
2. **Validation Phase**: Uses ralph-wiggum loop to refine code until visually accurate (92%+ similarity)
3. **Testing Phase**: Deploys to device via mobile-mcp to test interactions

### Key Features

- **Universal**: Works with any Android project using Compose
- **Intelligent**: Learns your project conventions and theme
- **Self-correcting**: Ralph-wiggum loop iteratively improves accuracy
- **Comprehensive**: Validates both visual accuracy and interactions

## Installation

The plugin is located at `.claude/plugins/compose-designer/` and is automatically available in Claude Code.

### Dependencies

**Required:**
- Gradle setup for Android project
- Android Studio or IntelliJ IDEA (for preview rendering)

**Optional:**
- Python 3.7+ with packages: `scikit-image`, `pillow`, `numpy` (for image similarity)
- Figma API token (for design token extraction)
- Mobile device or emulator (for Phase 3 testing)

**Install Python dependencies:**
```bash
pip3 install scikit-image pillow numpy
```

**Set Figma token (if using Figma input):**
```bash
export FIGMA_TOKEN="your-figma-personal-access-token"
```

## Configuration

### Initialize Configuration

Run the config command:
```bash
/compose-design config
```

This creates `.claude/compose-designer.yaml` in your project root.

### Configuration Reference

See [example-config.yaml](../../.claude/plugins/compose-designer/examples/example-config.yaml) for full schema.

**Key settings:**

```yaml
naming:
  component_suffix: "Component"  # Matches your convention

validation:
  visual_similarity_threshold: 0.92  # Adjust based on strictness (0.85-0.95)
  max_ralph_iterations: 8  # More iterations = more refinement

output:
  package_base: "tap.photo.boost.restoration"  # Your app package
  extract_theme_from_existing: true  # Learn colors from your theme
```

### Project-Specific Customization

Edit `.claude/compose-designer.yaml` to match:
- Your naming conventions (Component suffix, Screen suffix)
- Your preview annotation (@Preview, @MyDevices, etc.)
- Your architecture preferences (stateless, state hoisting)
- Your package structure

## Usage

### Basic Commands

**Initialize:**
```bash
/compose-design config
```

**Generate from screenshot:**
```bash
/compose-design create --input design.png --name ProfileCard --type component
```

**Generate from Figma:**
```bash
/compose-design create --input "figma://file/ABC?node-id=1:234" --name LoginScreen --type screen
```

**Quick test from clipboard:**
```bash
/compose-design create --clipboard --name QuickButton --type component
```

**Batch processing:**
```bash
/compose-design create --input ./designs/ --batch
```

### Input Types

1. **Screenshot** (`.png`, `.jpg`): Direct image file
2. **Figma URL**: `figma://` or `https://figma.com/file/...`
3. **Clipboard**: Image copied to clipboard
4. **Folder**: Directory containing multiple images (batch mode)

### Component vs Screen

- **component**: Reusable UI element (button, card, list item)
  - Generates stateless composable with parameters
  - Suitable for component library

- **screen**: Full-screen UI (login, profile, settings)
  - May include state management
  - Suitable for navigation destinations

## Workflow Details

### Phase 1: Generation

**What happens:**
1. Plugin loads configuration
2. Processes input (downloads Figma, reads image, extracts design tokens)
3. Analyzes design visually using LLM vision
4. Generates Compose code following your conventions
5. Creates `@Preview` function with mock data

**Output:**
- Kotlin file: `{output_dir}/{package}/{Name}{Suffix}.kt`
- Baseline image: Saved for comparison

**Time:** 30-60 seconds

### Phase 2: Visual Validation (Ralph-Wiggum)

**What happens:**
1. Renders preview using Android Studio or Gradle
2. Takes screenshot of preview
3. Compares with baseline using SSIM algorithm
4. If similarity < threshold:
   - Identifies visual differences (color, spacing, size)
   - LLM refines code to fix issues
   - Re-renders and compares
   - Repeats up to `max_ralph_iterations` times
5. Exits when similarity >= threshold or max iterations reached

**Output:**
- Refined Compose code
- Similarity score (e.g., 0.94)
- Iteration count
- Diff images for review

**Time:** 2-8 minutes (depends on iterations)

### Phase 3: Device Testing (Mobile-MCP)

**What happens:**
1. Generates test activity to host component
2. Builds and installs APK
3. Launches on device
4. Takes screenshot and compares with baseline
5. Tests interactions (taps, text input, scrolling)
6. Cleans up test activity

**Output:**
- Device similarity score
- Interaction test results (passed/failed)
- Screenshots from device

**Time:** 2-4 minutes

**Skip Phase 3:**
```bash
/compose-design create --input design.png --name Card --type component --skip-device-test
```

## Troubleshooting

### Issue: Preview rendering fails

**Symptoms:**
```
Error: Could not render preview
```

**Solutions:**
1. Ensure Gradle is set up: `./gradlew build`
2. Check Android Studio is installed
3. Verify preview annotation matches config
4. Try manual preview in Android Studio

### Issue: Visual similarity not reached

**Symptoms:**
```
⚠ Visual validation incomplete
Final similarity: 0.87 (target: 0.92)
```

**Solutions:**
1. Review diff images in `/tmp/compose-designer/{timestamp}/`
2. Lower threshold in config: `visual_similarity_threshold: 0.87`
3. Manually refine code based on diff feedback
4. Increase max iterations: `max_ralph_iterations: 12`

### Issue: Figma token extraction fails

**Symptoms:**
```
Error: Failed to fetch node data
```

**Solutions:**
1. Verify token: `echo $FIGMA_TOKEN`
2. Check token permissions in Figma settings
3. Enable fallback: `figma.fallback_to_image: true` in config
4. Use screenshot instead of Figma URL

### Issue: Device not found

**Symptoms:**
```
✗ No Android devices found.
```

**Solutions:**
1. Connect physical device with USB debugging enabled
2. Start emulator: Android Studio > AVD Manager
3. Verify: `adb devices` shows device
4. Skip device testing: `--skip-device-test` flag

## Advanced Topics

### Customizing Ralph-Wiggum Behavior

Edit config:
```yaml
validation:
  visual_similarity_threshold: 0.95  # Stricter (more iterations)
  max_ralph_iterations: 12  # Allow more refinement attempts
```

**Trade-offs:**
- Higher threshold = more accurate but slower
- More iterations = better results but longer wait

### Figma Design Token Extraction

When enabled, plugin extracts:
- Colors: Exact hex values → `Color(0xFFxxxxxx)`
- Typography: Font sizes, weights → `TextStyle(...)`
- Spacing: Padding, gaps → `{value}.dp`

**Setup:**
1. Get Figma personal access token: Settings > Account > Personal Access Tokens
2. Export token: `export FIGMA_TOKEN="..."`
3. Enable in config: `figma.extract_tokens: true`

**Benefits:**
- More accurate colors (no estimation)
- Proper design system values
- Cleaner code with theme integration

### Theme Integration

Enable learning from existing codebase:
```yaml
output:
  extract_theme_from_existing: true
```

Plugin searches for:
- `Color.kt`: Theme color definitions
- `Type.kt`: Typography scale
- `Theme.kt`: Material3 theme setup

Generates code using theme values instead of hardcoded colors:
```kotlin
// Without theme integration:
color = Color(0xFF2196F3)

// With theme integration:
color = MaterialTheme.colorScheme.primary
```

### Batch Processing Strategy

For large design systems:

1. **Organize designs:**
   ```
   designs/
     components/
       ├── buttons/
       │   ├── primary.png
       │   └── secondary.png
       └── cards/
           ├── user.png
           └── product.png
   ```

2. **Process by category:**
   ```bash
   /compose-design create --input designs/components/buttons/ --batch
   /compose-design create --input designs/components/cards/ --batch
   ```

3. **Review and integrate:**
   - Check generated components
   - Move to appropriate modules
   - Update imports and references

### Performance Optimization

**Faster iterations:**
1. Use haiku model for speed (configured per session)
2. Lower similarity threshold: `0.88-0.90` range
3. Reduce max iterations: `4-6` iterations
4. Skip device testing during development

**Higher quality:**
1. Use opus model for better analysis
2. Higher similarity threshold: `0.94-0.96` range
3. Increase max iterations: `10-12` iterations
4. Always run device testing before merge

## See Also

- [Plugin Structure](../../.claude/plugins/compose-designer/plugin.json)
- [Usage Examples](../../.claude/plugins/compose-designer/examples/example-usage.md)
- [Figma Client Utility](../../.claude/plugins/compose-designer/utils/figma-client.sh)
- [Image Similarity Utility](../../.claude/plugins/compose-designer/utils/image-similarity.py)
```

**Step 3: Commit documentation**

```bash
git add README.md docs/plugins/
git commit -m "docs: add compose-designer plugin documentation"
```

---

## Summary

**Plugin Structure:**
- 1 manifest (plugin.json)
- 2 commands (create, config)
- 3 agents (design-generator, visual-validator, device-tester)
- 2 utilities (image-similarity.py, figma-client.sh)
- Comprehensive documentation and examples

**Features:**
- Multi-input support (screenshot/Figma/clipboard/batch)
- Design token extraction from Figma
- Ralph-wiggum loop for self-validation
- Mobile-mcp integration for device testing
- Project-agnostic with configurable conventions

**Testing Focus:**
- Plugin structure validation
- Utility functionality
- End-to-end workflow (manual testing required)
- Visual similarity accuracy

**Next Steps:**
1. Test plugin with real designs
2. Gather feedback on generated code quality
3. Tune default similarity thresholds
4. Add more example designs and outputs
5. Consider adding XML view support (Phase 4)

**Estimated Effort:** L (5-7 days for full implementation)
**Dependencies:** Claude Code plugin system, ralph-wiggum skill, mobile-mcp, image comparison tools
