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

**Auto-detect project information:**

```bash
# Try to detect package from build.gradle.kts
package=$(grep -E "^\s*namespace\s*=\s*['\"]" build.gradle.kts 2>/dev/null | grep -oP "(?<=['\"]).*(?=['\"])" | head -1)

# If not found, try AndroidManifest.xml
if [ -z "$package" ]; then
    package=$(grep -oP 'package="\K[^"]+' app/src/main/AndroidManifest.xml 2>/dev/null | head -1)
fi

# Detect output directory
output_dir=$(find . -type d -name "java" -path "*/src/main/*" 2>/dev/null | head -1 | sed 's|^./||')

# Default if not found
output_dir="${output_dir:-app/src/main/java}"
```

**Required Fields (prompt if not detectable):**

```
I need some project-specific information:

1. Package name (e.g., com.yourapp):
   [Detected: $package] Use this? [Y/n]
   > _____

2. Test package name (e.g., com.yourapp.test):
   [Default: {package}.test]
   > _____

3. Output directory (default: app/src/main/java):
   [Detected: $output_dir] Use this? [Y/n]
   > _____
```

**Validate package names:**
- Must follow Java package naming: lowercase, dots, no spaces
- Regex pattern: `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`
- Reject invalid names and re-prompt user

### 3. Create Configuration File

Ensure `.claude/` directory exists:

```bash
mkdir -p .claude
```

Write configuration with smart defaults + prompted values:

**IMPORTANT:** Replace these placeholders with actual values:
- `{prompted_package}` → replace with the package name from user input
- `{prompted_test_package}` → replace with the test package name from user input
- `{prompted_output_dir}` → replace with the output directory from user input

The final YAML file must have actual values, not placeholder tokens.

```yaml
# Compose Designer Configuration
# Edit this file to customize code generation for your project

# Agent model configuration
model:
  default: "opus"                        # Fallback for any agent not specified below
  design_generator: "opus"               # Analyzes designs, generates code (vision-heavy)
  visual_validator: "opus"               # Compares screenshots, suggests fixes (vision-heavy)
  baseline_preprocessor: "opus"          # Detects device frames, crops images
  device_tester: "opus"                  # Tests interactions on device

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

# Validation settings
validation:
  ssim_sanity_threshold: 0.4           # Flag for review if LLM passes but SSIM below this

  # Paparazzi phase (JVM-based fast iteration)
  paparazzi:
    enabled: true                      # Enable Paparazzi validation (Phase 3)
    threshold: 0.95                    # SSIM threshold (stricter - deterministic JVM rendering)
    max_iterations: 5                  # Max iterations in Paparazzi phase
    device_config: "PIXEL_5"           # Paparazzi device configuration

  # Device phase (Android device/emulator verification)
  device:
    enabled: true                      # Enable device validation (Phase 4) - default: true
    threshold: 0.92                    # SSIM threshold for sanity check
    max_iterations: 5                  # Max iterations in device phase

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

# Theme configuration for device testing
theme:
  composable: ""                           # Full path to theme composable (e.g., "com.myapp.ui.theme.AppTheme")
                                           # Leave empty to use MaterialTheme
```

### 4. Validate Configuration

**Check Prerequisites:**
- Verify Python 3 is available: `command -v python3 >/dev/null || echo "Warning: python3 not found, skipping YAML validation"`
- If Python available but PyYAML missing, provide install instruction

After creating, validate YAML structure:

```bash
# YAML syntax check with error handling
python3 -c "
import yaml
import sys
try:
    with open('.claude/compose-designer.yaml', 'r', encoding='utf-8') as f:
        yaml.safe_load(f)
    print('✓ YAML validation passed')
except yaml.YAMLError as e:
    print(f'✗ YAML syntax error: {e}', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'✗ Validation failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1
```

If validation fails, report error with line number.

### 5. Show Summary

Display summary to user:

```
✓ Created .claude/compose-designer.yaml

Key settings configured:
  • output.package_base: {package}
  • testing.test_activity_package: {test_package}
  • validation.paparazzi.threshold: 0.95 (JVM iteration)
  • validation.device.threshold: 0.92 (final verification)
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
