# Compose Designer Plugin Structure

Complete technical documentation of the compose-designer plugin architecture, components, and implementation details.

## Directory Structure

```
compose-designer/
├── .claude-plugin/
│   └── plugin.json                    # Plugin manifest
├── commands/
│   ├── config.md                      # /compose-design config command
│   └── create.md                      # /compose-design create command
├── agents/
│   ├── design-generator.md            # Phase 1: Code generation agent
│   ├── visual-validator.md            # Phase 2: Validation agent
│   └── device-tester.md               # Phase 3: Testing agent
├── utils/
│   ├── image-similarity.py            # SSIM visual similarity calculator
│   └── figma-client.sh                # Figma API client
├── examples/
│   ├── README.md                      # Example usage guide
│   ├── button-example.png.txt         # Button example placeholder
│   └── card-example.png.txt           # Card example placeholder
├── tests/
│   └── validate-plugin.sh             # Plugin validation script
├── docs/
│   ├── PLUGIN_STRUCTURE.md            # This file
│   ├── IMPLEMENTATION_PLAN.md         # Implementation Q&A
│   └── plans/
│       └── 2026-01-13-compose-designer-implementation.md
└── README.md                          # User-facing documentation
```

## Component Details

### Plugin Manifest (.claude-plugin/plugin.json)

**Purpose**: Defines plugin metadata for Claude Code plugin system.

**Contents**:
```json
{
  "name": "compose-designer",
  "version": "0.1.0",
  "description": "Transform design mockups into production-ready Jetpack Compose code",
  "author": {
    "name": "Vlad Karpman",
    "email": "vladkarpman@example.com"
  }
}
```

### Commands

#### config.md

**Slash Command**: `/compose-design config`

**Purpose**: Interactive configuration wizard that creates `.claude/compose-designer.yaml` with project-specific settings.

**Required User Input**:
- `output.package_base`: Base package name (e.g., `com.example.app`)
- `testing.test_activity_package`: Test package for device testing

**Smart Defaults**: Provides intelligent defaults for all other settings.

**Allowed Tools**: Read, Write, Bash, AskUserQuestion

#### create.md

**Slash Command**: `/compose-design create --input <path|url> --name <Name> --type <component|screen>`

**Purpose**: Main workflow orchestrator that runs the three-phase generation pipeline.

**Phases**:
1. **Phase 1 (Generation)**: Invokes design-generator agent
2. **Phase 2 (Validation)**: Invokes visual-validator agent
3. **Phase 3 (Testing)**: Invokes device-tester agent

**Allowed Tools**: Read, Write, Bash, Task, TodoWrite, AskUserQuestion

### Agents

#### design-generator.md

**Type**: Agent
**Model**: sonnet
**Color**: blue

**Purpose**: Analyzes design mockups and generates initial Jetpack Compose code with theme integration.

**Capabilities**:
- Process screenshots and Figma designs
- Extract design tokens (colors, typography, spacing)
- Generate idiomatic Compose code
- Integrate with existing theme
- Create realistic mock data and previews

**Tools**: Read, Write, Bash, Glob, Grep, AskUserQuestion

**Input**:
- Design image path or Figma URL
- Component name and type
- Configuration from `.claude/compose-designer.yaml`

**Output**:
- Generated `.kt` file with Compose code
- Baseline design image for validation
- Text report with generation details

**Key Features**:
- Searches for existing theme files (Color.kt, Type.kt, Theme.kt)
- Maps design colors to theme colors
- Extracts Material Icons from design
- Generates stateless components with state hoisting
- Creates complete preview functions with mock data

#### visual-validator.md

**Type**: Agent
**Model**: sonnet
**Color**: green

**Purpose**: Validates generated Compose UI against baseline design using ralph-wiggum iterative refinement loop.

**Capabilities**:
- Render Compose preview screenshots
- Calculate visual similarity using SSIM algorithm
- Invoke ralph-wiggum loop for iterative refinement
- Generate visual diff overlays
- Refine code based on diff analysis

**Tools**: Read, Edit, Bash, Skill

**Input**:
- Generated `.kt` file path
- Baseline design image path
- Configuration with similarity threshold
- Temp directory for artifacts

**Output**:
- Refined `.kt` file with validated code
- Preview screenshots (per iteration)
- Visual diff images (per iteration)
- Validation report with similarity scores

**Ralph-Wiggum Loop**:
1. Render preview screenshot
2. Calculate SSIM similarity vs baseline
3. If < threshold (default 92%), analyze differences
4. Apply targeted code refinements
5. Repeat until threshold reached or max iterations (default 8)

**Common Refinements**:
- Color adjustments (hardcoded → theme)
- Spacing corrections (padding, gaps, margins)
- Typography fixes (fontSize, fontWeight, lineHeight)
- Alignment corrections (Start, Center, End)
- Sizing adjustments (fillMaxWidth, fixed dimensions)

#### device-tester.md

**Type**: Agent
**Model**: sonnet
**Color**: purple

**Purpose**: Tests generated Compose UI on real Android devices using mobile-mcp integration.

**Capabilities**:
- Generate test harness activity
- Build and deploy APK
- Perform visual regression testing
- Test user interactions
- Clean up test artifacts

**Tools**: Read, Write, Edit, Bash, mcp__mobile-mcp__* (all mobile-mcp tools)

**Input**:
- Validated `.kt` file path
- Baseline design image
- Device ID (or "auto")
- Testing configuration

**Output**:
- Device test report
- Device screenshots
- Interaction test results
- Build/deployment logs

**Test Phases**:
1. **Pre-flight**: Verify mobile-mcp, device connection, Gradle
2. **Build**: Create test activity, build debug APK
3. **Deploy**: Install APK on device
4. **Visual Test**: Capture screenshot, compare to baseline
5. **Interaction Test**: Test buttons, text fields, scrolling, state
6. **Cleanup**: Remove test activity, uninstall test app

**Interaction Testing**:
- **Basic**: Click buttons, enter text, verify state changes
- **Comprehensive**: Scroll gestures, long press, multi-touch, edge cases

### Utilities

#### image-similarity.py

**Language**: Python 3.7+

**Purpose**: Calculate SSIM (Structural Similarity Index) between two images.

**Dependencies**:
```bash
pip3 install scikit-image pillow numpy
```

**Usage**:
```bash
python3 image-similarity.py baseline.png preview.png [--output diff.png]
```

**Returns**: Similarity score (0.0 to 1.0) to stdout

**Algorithm**: SSIM with multichannel RGB comparison
- Resizes preview to match baseline dimensions
- Converts to RGB if needed
- Calculates SSIM score
- Optionally generates enhanced diff visualization (3x contrast)

#### figma-client.sh

**Language**: Bash (portable: macOS/Linux)

**Purpose**: Bash client for Figma API to parse URLs, fetch node data, and export images.

**Environment Variables**:
```bash
export FIGMA_TOKEN="figd_your_token_here"
```

**Commands**:

1. **parse**: Extract file ID and node ID from Figma URL
   ```bash
   ./figma-client.sh parse "https://www.figma.com/file/ABC?node-id=1:234"
   # Output: ABC123|1:234
   ```

2. **fetch-node**: Fetch node data (colors, typography, layout) as JSON
   ```bash
   ./figma-client.sh fetch-node "https://www.figma.com/file/ABC?node-id=1:234"
   # Output: JSON with node properties
   ```

3. **export**: Export node as image file
   ```bash
   ./figma-client.sh export "https://www.figma.com/file/ABC?node-id=1:234" output.png [format] [scale]
   # Formats: png (default), jpg, svg, pdf
   # Scale: 1-4 (default: 2 for retina)
   ```

**Features**:
- Portable sed patterns (no grep -oP)
- Error handling with clear messages
- Progress output to stderr
- Exit codes: 0 (success), 1 (error)

### Tests

#### validate-plugin.sh

**Language**: Bash

**Purpose**: Comprehensive validation of plugin structure, configuration, and components.

**Usage**:
```bash
./tests/validate-plugin.sh
```

**Exit Codes**:
- 0: All critical validations passed
- 1: One or more validations failed

**Validation Sections**:

1. **Plugin Manifest**: JSON syntax, required fields
2. **Command Files**: Existence, YAML frontmatter, required fields
3. **Agent Files**: Existence, YAML frontmatter, required fields
4. **Utility Scripts**: Existence, executability, help output
5. **Example Files**: Existence, format
6. **Directory Structure**: Required directories
7. **Documentation**: README, implementation plan
8. **Security Checks**: No hardcoded secrets, proper quoting
9. **Cross-Platform Compatibility**: No grep -oP, CLAUDE_PLUGIN_ROOT usage

**Output Format**:
- ✓ Green: Passed checks
- ⚠ Yellow: Warnings (non-critical)
- ✗ Red: Failed checks (critical)

## Configuration Schema

### .claude/compose-designer.yaml

Full configuration with all available options:

```yaml
# Project conventions
naming:
  component_suffix: "Component"
  screen_suffix: "Screen"
  preview_annotation: "@Preview"

# Code generation
architecture:
  stateless_components: true
  state_hoisting: true
  remember_saveable: false

# Preview settings
preview:
  show_background: true
  background_color: "#FFFFFF"
  device_spec: "spec:width=411dp,height=891dp"
  font_scale: 1.0

# Validation thresholds
validation:
  visual_similarity_threshold: 0.92
  max_ralph_iterations: 8
  preview_screenshot_delay: "auto"

# Batch processing
batch:
  mode: "sequential"

# Device testing
testing:
  test_activity_package: "com.example.app.test"
  test_activity_name: "ComposeTestActivity"
  device_id: "auto"
  interaction_depth: "comprehensive"
  cleanup_artifacts: "ask"

# Figma integration
figma:
  extract_tokens: true
  api_token_source: "env"
  api_token: ""
  fallback_to_image: true

# Output preferences
output:
  package_base: "com.example.app"
  default_output_dir: "app/src/main/java"
  include_comments: false
  extract_theme_from_existing: true
```

**Required Fields** (prompted if missing):
- `output.package_base`
- `testing.test_activity_package`

## Workflow Details

### Three-Phase Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ User Input: /compose-design create --input X --name Y --type Z │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 0: Setup & Validation                                     │
│ • Load .claude/compose-designer.yaml                            │
│ • Validate arguments                                            │
│ • Process input (download Figma, load screenshot, etc.)         │
│ • Create temp directory for artifacts                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Generation (design-generator agent)                    │
│ • Analyze design visually                                       │
│ • Extract design tokens (if Figma)                              │
│ • Search for existing theme files                               │
│ • Generate Compose code                                         │
│ • Create preview function with mock data                        │
│ • Verify compilation                                            │
│ Output: ComponentName.kt + baseline.png                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: Validation (visual-validator agent)                    │
│ Ralph-Wiggum Loop:                                              │
│   1. Render preview screenshot                                  │
│   2. Calculate SSIM similarity                                  │
│   3. If < threshold:                                            │
│      • Generate diff visualization                              │
│      • Analyze differences                                      │
│      • Refine code (colors, spacing, typography)                │
│      • Go to step 1                                             │
│   4. If >= threshold or max iterations: exit                    │
│ Output: Validated .kt + preview screenshots + diff images       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: Device Testing (device-tester agent)                   │
│ • Generate test activity                                        │
│ • Build debug APK                                               │
│ • Install on device                                             │
│ • Visual regression test (screenshot comparison)                │
│ • Interaction testing (buttons, text fields, scrolling)         │
│ • Cleanup (remove test activity, uninstall APK)                 │
│ Output: Device report + screenshots                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Final Report                                                    │
│ • Summary of all phases                                         │
│ • Similarity scores                                             │
│ • Device test results                                           │
│ • Location of generated file                                    │
│ • Validation artifacts directory                                │
│ • Prompt to review and commit                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Dependencies

### Required

- **Claude Code CLI**: Latest version
- **Plugins**:
  - ralph-wiggum: For iterative refinement loop
  - mobile-ui-testing (mobile-mcp): For device testing
- **Android Development**:
  - Gradle (for building and preview rendering)
  - Android Studio or IntelliJ IDEA (for Compose preview)
- **Python 3.7+**:
  - scikit-image
  - pillow
  - numpy

### Optional

- **Figma API Token**: For design token extraction
- **Android Device/Emulator**: For Phase 3 testing

## File Size and Metrics

**Total Files**: 17

**By Type**:
- Commands: 2 files
- Agents: 3 files
- Utilities: 2 files
- Documentation: 5 files
- Tests: 1 file
- Examples: 3 files
- Config: 1 file

**Total Lines of Code** (approximate):
- design-generator.md: ~500 lines
- visual-validator.md: ~610 lines
- device-tester.md: ~830 lines
- create.md: ~400 lines
- config.md: ~150 lines
- image-similarity.py: ~137 lines
- figma-client.sh: ~262 lines
- validate-plugin.sh: ~310 lines

## Development History

**Implementation Approach**: Subagent-driven development with two-stage review
- Fresh subagent per task (10 tasks total)
- Spec compliance review → Code quality review
- Review loops: Fix issues → Re-review until approved

**Tasks**:
1. Create Config Command
2. Create Main Create Command
3. Create Design Generator Agent (7 quality fixes)
4. Create Visual Validator Agent (12 quality fixes)
5. Create Device Tester Agent (8 quality fixes)
6. Create Image Similarity Utility
7. Create Figma API Client Utility (4 portability fixes)
8. Create Example Assets
9. Create Test Validation Script (3 fixes)
10. Final Plugin Validation and Documentation

**Quality Gates Applied**:
- Cross-platform compatibility (macOS/Linux)
- Security validation (no hardcoded secrets)
- Portable bash patterns (no grep -oP)
- Error handling and validation
- Proper quoting and exit codes
- CLAUDE_PLUGIN_ROOT usage for portability

## Maintenance

### Running Validation

```bash
./tests/validate-plugin.sh
```

Validates:
- Plugin structure and manifest
- Command and agent files
- Utility scripts functionality
- Documentation completeness
- Security and portability

### Adding New Features

When adding components:
1. Update plugin.json if needed
2. Follow existing naming conventions
3. Add validation checks to validate-plugin.sh
4. Update README.md and this file
5. Test with validation script

### Cross-Platform Testing

Test on both macOS and Linux:
```bash
# macOS
./tests/validate-plugin.sh

# Linux (via Docker or VM)
docker run -it ubuntu:latest
apt-get update && apt-get install -y python3 python3-pip bc
pip3 install scikit-image pillow numpy
./tests/validate-plugin.sh
```

## License

MIT License - see LICENSE file for details.
