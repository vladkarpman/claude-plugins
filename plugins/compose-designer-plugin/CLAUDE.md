# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The **compose-designer** plugin transforms design mockups (screenshots, Figma designs) into production-ready Jetpack Compose code through an automated three-phase workflow with visual validation and device testing.

**Core Capabilities:**
- Multi-input support: Screenshots, Figma URLs, clipboard images, batch processing
- Self-validating via ralph-wiggum iterative refinement (92%+ visual accuracy)
- Real device testing via mobile-mcp integration
- Theme extraction and integration from existing project code
- Production-ready, idiomatic Compose code generation

## Common Commands

### Plugin Usage

```bash
# Initialize configuration (required first step)
/compose-design config

# Generate from screenshot
/compose-design create --input button-design.png --name CustomButton --type component

# Generate from Figma
export FIGMA_TOKEN="your-token"
/compose-design create --input "https://www.figma.com/file/ABC?node-id=1:234" --name LoginScreen --type screen

# Generate from clipboard
/compose-design create --clipboard --name QuickButton --type component

# Batch process folder
/compose-design create --input ./designs/ --batch
```

### Plugin Development

```bash
# Validate plugin structure and components
./tests/validate-plugin.sh

# Test Python utilities
python3 utils/image-similarity.py baseline.png preview.png
python3 utils/image-similarity.py baseline.png preview.png --output diff.png

# Test Figma client (requires FIGMA_TOKEN)
./utils/figma-client.sh parse "https://www.figma.com/file/ABC?node-id=1:234"
./utils/figma-client.sh fetch-node "https://www.figma.com/file/ABC?node-id=1:234"
./utils/figma-client.sh export "https://www.figma.com/file/ABC?node-id=1:234" output.png

# Load plugin locally for testing
claude --plugin-dir .
```

### Dependencies Installation

```bash
# Required Python packages
pip3 install scikit-image pillow numpy

# Optional: Figma API token
export FIGMA_TOKEN="figd_your_token_here"
```

## Architecture

### Three-Phase Workflow Pipeline

The plugin orchestrates three specialized agents that execute sequentially:

```
User Command: /compose-design create
    ↓
Phase 0: Setup (create.md command)
    • Load .claude/compose-designer.yaml config
    • Validate arguments and dependencies
    • Process input (download Figma, load screenshot)
    • Create temp directory for artifacts
    ↓
Phase 1: Generation (design-generator agent)
    • Analyze design visually via LLM vision
    • Extract design tokens (colors, typography, spacing)
    • Search for existing theme files (Color.kt, Type.kt)
    • Generate idiomatic Compose code
    • Create preview function with mock data
    Output: ComponentName.kt + baseline.png
    ↓
Phase 2: Validation (visual-validator agent)
    Ralph-Wiggum Loop:
    1. Render preview screenshot (Gradle/Android Studio)
    2. Calculate SSIM similarity (Python utility)
    3. If < threshold (92%): analyze diff, refine code
    4. Repeat until threshold met or max iterations
    Output: Validated .kt + preview/diff images
    ↓
Phase 3: Device Testing (device-tester agent)
    • Generate test activity harness
    • Build debug APK and deploy to device
    • Capture device screenshot, validate rendering
    • Test interactions (clicks, text input, scrolling)
    • Cleanup: remove test artifacts
    Output: Device test report + screenshots
    ↓
Final Report + User Prompt to Review/Commit
```

### Agent Architecture

**Commands** (orchestrators):
- `commands/config.md` - Interactive configuration wizard
- `commands/create.md` - Main workflow orchestrator, spawns agents

**Agents** (specialized workers invoked via Task tool):
- `agents/baseline-preprocessor.md` - Detects device frames, crops to content area
- `agents/design-generator.md` - Vision-based design analysis and code generation
- `agents/visual-validator.md` - Ralph-wiggum iterative refinement loop
- `agents/device-tester.md` - Mobile-mcp device testing integration

**Utilities** (CLI tools invoked by agents):
- `utils/image-similarity.py` - SSIM calculator with diff visualization
- `utils/figma-client.sh` - Figma API client (parse, fetch, export)

### Agent Communication Pattern

Agents receive structured inputs from parent command:

```kotlin
// Example: design-generator agent inputs
{
  baseline_image_path: "/path/to/design.png",
  config: { /* parsed YAML */ },
  name: "ProfileCard",
  type: "component",
  output_file_path: "/path/to/output.kt",
  figma_tokens: { /* optional */ }
}
```

Agents communicate via:
- **File system**: Write generated .kt files, images, reports
- **Return values**: Success/failure status in agent completion message
- **Temp directory**: Share artifacts between phases

### Configuration Management

**Location**: `.claude/compose-designer.yaml` (project root)

**Required fields** (user must provide):
- `output.package_base` - Base package name (e.g., "com.example.app")
- `testing.test_activity_package` - Test package for device testing

**Smart defaults**: All other fields have intelligent defaults based on Android conventions.

**Theme integration**: When `output.extract_theme_from_existing: true`, agents search for:
- Color files: `Color.kt`, `Colors.kt` → `MaterialTheme.colorScheme.primary`
- Typography: `Type.kt`, `Typography.kt` → `MaterialTheme.typography.titleLarge`
- Theme files: `Theme.kt`, `AppTheme.kt` → Theme structure

## Key Technical Details

### Visual Similarity Validation (SSIM)

The visual-validator agent uses SSIM (Structural Similarity Index) to compare preview screenshots against baseline designs:

- **Algorithm**: Multi-channel RGB SSIM via scikit-image
- **Default threshold**: 0.92 (92% similarity)
- **Process**: Preview is resized to baseline dimensions, converted to RGB, then compared
- **Output**: Similarity score (0.0-1.0) + optional diff visualization with 3x contrast

**Usage in agents**:
```bash
similarity=$(python3 "${CLAUDE_PLUGIN_ROOT}/utils/image-similarity.py" \
  baseline.png preview.png --output diff.png)
```

### Ralph-Wiggum Integration

The visual-validator agent invokes the ralph-wiggum skill to drive iterative refinement:

```
Skill tool: "ralph-wiggum:ralph-loop"
Context: "Refine Compose UI to match baseline design"
Validation: Visual similarity >= 0.92
Max iterations: 8
```

Ralph-wiggum manages the loop; the agent provides iteration logic (render → compare → refine).

### Figma API Integration

When Figma URLs are provided:

1. **Parse URL**: Extract file ID and node ID
2. **Fetch tokens**: GET `/v1/files/:file_id/nodes?ids=:node_id` with auth header
3. **Extract values**:
   - Colors: fills, strokes → `Color(0xFFRRGGBB)`
   - Typography: fontSize, fontWeight, lineHeight → `TextStyle(...)`
   - Spacing: layoutMode, itemSpacing → padding/gap values
4. **Export image**: POST `/v1/images/:file_id` with node ID, format, scale
5. **Fallback**: If token extraction fails and `figma.fallback_to_image: true`, use exported image only

**Token requirement**: Set `FIGMA_TOKEN` env var or add to config.

### Mobile-MCP Device Testing

The device-tester agent uses mobile-mcp tools to test on real devices:

**Prerequisites**:
- Android device connected (USB debugging enabled) OR emulator running
- Verify: `adb devices` shows device

**Test flow**:
1. Generate test activity that hosts the component
2. Build debug APK: `./gradlew assembleDebug`
3. Install: `mcp__mobile-mcp__mobile_install_app`
4. Launch: `mcp__mobile-mcp__mobile_launch_app`
5. Capture: `mcp__mobile-mcp__mobile_take_screenshot`
6. Interact: Click buttons, type text, verify state changes
7. Cleanup: Remove test activity, uninstall APK

## Important Conventions

### Script Portability

All bash scripts must be portable (macOS/Linux):

- ✅ Use: `#!/usr/bin/env python3` or `#!/bin/bash`
- ✅ Use: `sed` with basic syntax (no GNU extensions)
- ✅ Use: `grep` without `-P` flag (Perl regex not on macOS)
- ✅ Quote all variables: `"$variable"`
- ✅ Use `${CLAUDE_PLUGIN_ROOT}` to reference plugin files

### Plugin File References

Always use `$CLAUDE_PLUGIN_ROOT` in scripts:

```bash
# GOOD
python3 "${CLAUDE_PLUGIN_ROOT}/utils/image-similarity.py" baseline.png preview.png

# BAD - hardcoded relative path
python3 ./utils/image-similarity.py baseline.png preview.png
```

### Error Handling

All scripts must:
- Exit with non-zero on errors
- Print clear error messages to stderr
- Validate prerequisites before proceeding
- Provide actionable remediation steps

Example:
```bash
python3 -c "import skimage" 2>/dev/null || {
  echo "❌ Python scikit-image not installed" >&2
  echo "Install: pip3 install scikit-image pillow numpy" >&2
  exit 1
}
```

### Naming Conventions

**Components**: `{Name}Component.kt` (e.g., `ButtonComponent.kt`)
**Screens**: `{Name}Screen.kt` (e.g., `LoginScreen.kt`)
**Previews**: `@Preview` function named `{ComponentName}Preview()`

Suffixes are configurable via `config.naming.component_suffix` and `config.naming.screen_suffix`.

## Plugin Development

### Validation Script

The validation script checks plugin integrity:

```bash
./tests/validate-plugin.sh
```

**Validates**:
- Plugin manifest JSON syntax and required fields
- Command files: YAML frontmatter, required fields
- Agent files: YAML frontmatter, required fields
- Utility scripts: executability, help output
- Security: no hardcoded secrets, proper quoting
- Portability: no `grep -P`, `${CLAUDE_PLUGIN_ROOT}` usage

**Output**:
- ✓ Green: Pass
- ⚠ Yellow: Warning (non-critical)
- ✗ Red: Fail (critical)

Exit code 0 = all critical checks passed.

### Adding New Agents

When adding agents:

1. Create `agents/{name}.md` with YAML frontmatter:
   ```yaml
   ---
   description: Brief description
   capabilities:
     - Capability 1
     - Capability 2
   model: sonnet
   color: blue
   tools:
     - Read
     - Write
     - Bash
   ---
   ```

2. Register in `.claude-plugin/plugin.json`:
   ```json
   "agents": [
     "./agents/existing-agent.md",
     "./agents/new-agent.md"
   ]
   ```

3. Invoke via Task tool in commands:
   ```
   Task tool:
     - subagent_type: "compose-designer:new-agent"
     - description: "Brief task description"
     - prompt: "Detailed instructions with inputs..."
   ```

4. Add validation checks to `tests/validate-plugin.sh`

### Cross-Platform Testing

Test on both macOS and Linux:

```bash
# macOS
./tests/validate-plugin.sh

# Linux via Docker
docker run -it ubuntu:latest
apt-get update && apt-get install -y python3 python3-pip bc
pip3 install scikit-image pillow numpy
./tests/validate-plugin.sh
```

### Dependency Management

**Required** (plugin will not work without):
- Claude Code CLI with ralph-wiggum and mobile-ui-testing plugins
- Python 3.7+ with scikit-image, pillow, numpy
- Gradle (for preview rendering)
- Android Studio or IntelliJ IDEA (for Compose tooling)

**Optional** (enhanced functionality):
- Figma API token (for design token extraction)
- Android device/emulator (for Phase 3 testing)

**Checking dependencies in code**:
```bash
# Python packages
python3 -c "import skimage, PIL, numpy" 2>/dev/null || exit 1

# Gradle
./gradlew --version >/dev/null 2>&1 || exit 1

# Ralph-wiggum plugin
claude --help | grep -q "ralph" || echo "Warning: ralph-wiggum not found"
```

## Troubleshooting

### Preview Rendering Fails

**Symptom**: `Could not render preview`

**Check**:
1. Gradle builds successfully: `./gradlew build`
2. Android Studio installed and preview tooling available
3. Preview annotation matches config: `@Preview` (default)
4. Generated code compiles without errors

**Fix**: Try rendering manually in Android Studio to identify the issue.

### Visual Similarity Not Reached

**Symptom**: `Final similarity: 0.87 (target: 0.92)`

**Check**:
1. Review diff images in temp directory: `/tmp/compose-designer/{timestamp}/`
2. Identify specific differences: colors, spacing, alignment, sizing

**Fix**:
- Lower threshold: `validation.visual_similarity_threshold: 0.87`
- Increase iterations: `validation.max_ralph_iterations: 12`
- Manually refine based on diff feedback and re-run validation

### Figma Token Issues

**Symptom**: `Failed to fetch node data`

**Check**:
1. Token is set: `echo $FIGMA_TOKEN`
2. Token has correct permissions in Figma settings
3. URL format is correct: `https://www.figma.com/file/{FILE_ID}?node-id={NODE_ID}`

**Fix**:
- Enable fallback: `figma.fallback_to_image: true`
- Use screenshot instead of Figma URL

### Device Testing Failures

**Symptom**: `No Android devices found`

**Check**:
1. Device connected: `adb devices` shows device
2. USB debugging enabled on device
3. ADB bridge running: `adb start-server`

**Fix**:
- Start emulator: Android Studio → AVD Manager
- Check config: `testing.device_id: "auto"` or specify device ID

## File Structure

```
compose-designer-plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/
│   ├── config.md                # Configuration wizard
│   └── create.md                # Main workflow orchestrator
├── agents/
│   ├── baseline-preprocessor.md # Design preprocessing
│   ├── design-generator.md      # Code generation
│   ├── visual-validator.md      # Ralph-wiggum validation
│   └── device-tester.md         # Mobile-mcp testing
├── utils/
│   ├── image-similarity.py      # SSIM calculator (Python)
│   └── figma-client.sh          # Figma API client (Bash)
├── tests/
│   └── validate-plugin.sh       # Plugin validation script
├── examples/
│   └── README.md                # Example usage guide
├── docs/
│   ├── PLUGIN_STRUCTURE.md      # Technical documentation
│   └── IMPLEMENTATION_PLAN.md   # Development Q&A
└── README.md                    # User-facing documentation
```

## Development History

This plugin was built using **subagent-driven development** with two-stage review:
1. Fresh subagent per task (10 tasks total)
2. Spec compliance review → Code quality review
3. Review loops: Fix issues → Re-review until approved

Quality gates applied:
- Cross-platform compatibility (macOS/Linux)
- Security validation (no hardcoded secrets)
- Portable bash patterns (no `grep -P`)
- Proper error handling and validation
- `${CLAUDE_PLUGIN_ROOT}` usage for portability
