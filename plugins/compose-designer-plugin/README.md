# Compose Designer Plugin

Transform design mockups (screenshots, Figma designs) into production-ready Jetpack Compose code through an automated three-phase workflow with visual validation and device testing.

## Features

- **🎨 Multi-Input Support**: Screenshots, Figma links, clipboard, batch processing
- **🔄 Self-Validating**: Ralph-wiggum loop ensures 92%+ visual accuracy
- **📱 Device Testing**: Mobile-mcp integration validates on real devices
- **🎯 Smart Defaults**: Works out-of-the-box with sensible conventions
- **⚙️ Configurable**: Adapts to your project's naming and architecture patterns
- **🚀 Production-Ready**: Generates clean, idiomatic Compose code with theme integration
- **📦 Component Reuse**: Auto-detects and reuses existing components from your codebase
- **🎭 Project Theme**: Device tests render with your app's actual theme

## Prerequisites

### Required

- **Gradle**: For building and preview rendering
- **Android Studio or IntelliJ IDEA**: For Compose preview generation
- **Claude Code**: With ralph-wiggum and mobile-ui-testing plugins installed
- **Python 3.7+** with packages:
  ```bash
  pip3 install scikit-image pillow numpy
  ```

### Optional

- **Figma API Token**: For design token extraction (colors, typography, spacing)
  ```bash
  export FIGMA_TOKEN="your-figma-personal-access-token"
  ```
- **Android Device/Emulator**: For Phase 3 device testing (highly recommended)

## Installation

```bash
# Clone or download to your project
cd your-android-project
git clone https://github.com/vladkarpman/vladkarpman-plugins
cd vladkarpman-plugins/compose-designer

# Initialize configuration
claude
/compose-design config
```

## Quick Start

### 1. Initialize Configuration

```bash
/compose-design config
```

This creates `.claude/compose-designer.yaml` with smart defaults. Edit to match your project:

```yaml
output:
  package_base: "com.yourapp"              # Your app package (required)
  default_output_dir: "app/src/main/java"  # Output directory

testing:
  test_activity_package: "com.yourapp.test"  # Test package (required)
```

### 2. Generate from Screenshot

```bash
/compose-design create --input button-design.png --name CustomButton --type component
```

### 3. Generate from Figma

```bash
# Set token (one-time setup)
export FIGMA_TOKEN="your-token"

/compose-design create --input "https://www.figma.com/file/ABC123?node-id=1:234" --name LoginScreen --type screen
```

### 4. Quick Test from Clipboard

Copy a design screenshot, then:

```bash
/compose-design create --clipboard --name QuickButton --type component
```

### 5. Override Output Directory

```bash
/compose-design create --input design.png --name Card --type component --output ./features/cards/ui/
```

### 6. Scan for Reusable Components

```bash
# Auto-generate component library from your codebase
/compose-design scan-components

# Scan specific directory
/compose-design scan-components --path app/src/main/java/ui/components
```

## Three-Phase Workflow

### Phase 1: Generation

1. **Input Processing**: Downloads Figma assets, extracts design tokens, or loads screenshot
2. **Visual Analysis**: LLM vision analyzes layout structure, colors, spacing, typography
3. **Code Generation**: Creates Compose code following your project conventions
4. **Theme Integration**: Uses existing theme colors/typography when available
5. **Preview Creation**: Generates `@Preview` function with realistic mock data

**Output**: `{Name}Component.kt` or `{Name}Screen.kt`

### Phase 2: Visual Validation (Ralph-Wiggum Loop)

1. **Preview Rendering**: Generates preview screenshot via Gradle or Android Studio
2. **Similarity Calculation**: Compares preview vs baseline using SSIM algorithm
3. **Iterative Refinement**: If similarity < 92%, identifies differences and refines code
4. **Convergence**: Repeats until similarity ≥ threshold or max iterations reached

**Output**: Validated code with 92%+ visual accuracy

### Phase 3: Device Testing (Mobile-MCP)

1. **Test Harness**: Creates temporary activity to host component
2. **Build & Deploy**: Builds APK and installs on device
3. **Visual Regression**: Captures device screenshot and validates rendering
4. **Interaction Testing**: Tests buttons, text fields, scrolling, state changes
5. **Cleanup**: Removes test activity, keeps generated component

**Output**: Device-validated code ready for integration

## Configuration Reference

Configuration lives in `.claude/compose-designer.yaml`. For detailed documentation of all options, see **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)**.

### Required Fields

```yaml
output:
  package_base: "com.yourapp"              # Your app's base package

testing:
  test_activity_package: "com.yourapp.test"  # Package for test activity
```

### Quick Reference

| Section | Key Fields | Options |
|---------|------------|---------|
| `model` | `default`, `design_generator`, `visual_validator` | `opus`, `sonnet`, `haiku` |
| `naming` | `component_suffix`, `screen_suffix` | Any string |
| `validation` | `visual_similarity_threshold` | `0.0` - `1.0` (default: `0.92`) |
| `validation` | `max_ralph_iterations` | Integer (default: `10`) |
| `testing` | `device_id` | `"auto"`, device ID, or name pattern (`"Pixel*"`) |
| `testing` | `interaction_depth` | `"basic"`, `"comprehensive"` |
| `testing` | `cleanup_artifacts` | `"always"`, `"never"`, `"ask"` |
| `batch` | `mode` | `"sequential"`, `"parallel"` |
| `figma` | `api_token_source` | `"env"`, `"config"` |

### Minimal Config Example

```yaml
model:
  default: "opus"

output:
  package_base: "com.yourapp"

testing:
  test_activity_package: "com.yourapp.test"
  device_id: "auto"
```

### New in v0.6.0

```yaml
# Theme for device testing (wraps preview in your app theme)
theme:
  composable: "com.yourapp.ui.theme.AppTheme"

# Component library (auto-generated by scan-components)
component_library:
  buttons:
    - name: "PrimaryButton"
      import: "com.yourapp.ui.components.PrimaryButton"
      use_when: "primary action, submit"
      signature: "(text: String, onClick: () -> Unit)"
  cards:
    - name: "ContentCard"
      import: "com.yourapp.ui.components.ContentCard"
      use_when: "content container, elevated surface"
      signature: "(modifier: Modifier, content: @Composable () -> Unit)"
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for complete examples and preset configurations.

## Usage Examples

### Basic Component from Screenshot

```bash
/compose-design create --input designs/button.png --name PrimaryButton --type component
```

**Generated**: `PrimaryButtonComponent.kt`

```kotlin
@Composable
fun PrimaryButtonComponent(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier
    ) {
        Text(text = text)
    }
}

@Preview
@Composable
private fun PrimaryButtonComponentPreview() {
    PrimaryButtonComponent(
        text = "Get Started",
        onClick = {}
    )
}
```

### Full Screen from Figma

```bash
/compose-design create \
  --input "https://www.figma.com/file/ABC?node-id=1:234" \
  --name ProfileSettings \
  --type screen
```

**Generated**: `ProfileSettingsScreen.kt` with:
- Extracted Figma colors, typography, spacing
- Integrated with existing theme
- Stateful composable with state hoisting
- Complete preview with realistic mock data

### Batch Processing

```bash
# Process all designs in folder
/compose-design create --input ./designs/components/ --batch
```

**Folder structure**:
```
designs/components/
├── button-primary.png
├── button-secondary.png
├── card-product.png
└── icon-star.png
```

**Output**: Generates 4 components sequentially with full validation.

## Advanced Features

### Theme Integration

When `extract_theme_from_existing: true`, the plugin searches for:
- `Color.kt`, `Colors.kt` → `MaterialTheme.colorScheme.primary`
- `Type.kt`, `Typography.kt` → `MaterialTheme.typography.titleLarge`
- `Theme.kt`, `AppTheme.kt` → Theme structure

**Benefits**:
- Consistent colors across codebase
- No hardcoded hex values
- Automatic dark mode support

### Mock Data Extraction

The plugin analyzes screenshots to extract realistic mock data:
- **Text**: Actual text from design → preview strings
- **Images**: Detects profile pics, icons → placeholder references
- **Icons**: Identifies Material Icons → `Icons.Filled.Star`
- **Missing Assets**: Prompts you to provide images/icons

### Figma Design Tokens

With Figma API token, the plugin extracts precise values:
- **Colors**: `#2196F3` → `Color(0xFF2196F3)`
- **Typography**: fontSize, fontWeight, lineHeight → `TextStyle`
- **Spacing**: padding, gaps, margins → `{value}.dp`
- **Layout**: Frame types → Column/Row/Box

Set up:
```bash
# Get token from Figma: Settings → Account → Personal Access Tokens
export FIGMA_TOKEN="figd_abc123..."

# Or add to config
figma:
  api_token_source: "config"
  api_token: "figd_abc123..."
```

## Troubleshooting

### Preview Rendering Fails

**Error**: `Could not render preview`

**Solutions**:
1. Verify Gradle works: `./gradlew build`
2. Check Android Studio installed
3. Ensure preview annotation matches config
4. Try rendering manually in Android Studio

### Visual Similarity Not Reached

**Error**: `Final similarity: 0.87 (target: 0.92)`

**Solutions**:
1. Review diff images in `/tmp/compose-designer/{timestamp}/`
2. Lower threshold: `visual_similarity_threshold: 0.87`
3. Increase iterations: `max_ralph_iterations: 12`
4. Manually refine based on diff feedback

### Figma Token Issues

**Error**: `Failed to fetch node data`

**Solutions**:
1. Verify token: `echo $FIGMA_TOKEN`
2. Check permissions in Figma settings
3. Enable fallback: `figma.fallback_to_image: true`
4. Use screenshot instead

### No Device Found

**Error**: `No Android devices found`

**Solutions**:
1. Connect physical device (enable USB debugging)
2. Start emulator: Android Studio → AVD Manager
3. Verify: `adb devices` shows device
4. Check device_id in config

### Python Dependencies Missing

**Error**: `Required packages not installed`

**Solution**:
```bash
pip3 install scikit-image pillow numpy
```

## Workflow Tips

### Optimal Workflow

1. **Start Simple**: Generate individual components first
2. **Batch Later**: Once validated, batch-process similar components
3. **Theme First**: Set up theme integration before generating
4. **Iterate**: Use validation feedback to improve designs

### Performance Optimization

**Faster Iterations**:
- Lower similarity threshold: `0.88-0.90`
- Reduce max iterations: `4-6`
- Use parallel batch mode

**Higher Quality**:
- Higher similarity threshold: `0.94-0.96`
- Increase max iterations: `10-12`
- Always run device testing

### Best Practices

1. **Review Generated Code**: Always review before integrating
2. **Add Real Data**: Replace mock data with ViewModels/state
3. **Test Interactions**: Add business logic to callbacks
4. **Version Control**: Commit baseline images for regression testing
5. **Iterate on Designs**: Refine designs based on validation feedback

## Architecture

### Component Interaction

```
User Command
    ↓
/compose-design create
    ↓
[Phase 1] design-generator agent
    ├─→ Process input (Figma/screenshot)
    ├─→ Analyze design visually
    ├─→ Generate Compose code
    └─→ Output: .kt file + baseline.png
    ↓
[Phase 2] visual-validator agent
    ├─→ Render preview
    ├─→ Calculate similarity (SSIM)
    ├─→ Ralph-wiggum loop (iterate if < threshold)
    └─→ Output: Validated code + diff images
    ↓
[Phase 3] device-tester agent
    ├─→ Generate test activity
    ├─→ Build & deploy APK
    ├─→ Test interactions
    └─→ Output: Device report
    ↓
Final Report + Commit Prompt
```

### File Organization

```
your-project/
├── .claude/
│   └── compose-designer.yaml       # Project configuration
├── app/src/main/java/
│   └── com/yourapp/
│       ├── ui/components/
│       │   └── ButtonComponent.kt  # Generated component
│       └── ui/screens/
│           └── LoginScreen.kt      # Generated screen
└── /tmp/compose-designer/{timestamp}/
    ├── baseline.png                # Original design
    ├── preview-iteration-1.png     # Validation previews
    ├── diff-iteration-1.png        # Visual diffs
    └── device-screenshot.png       # Device capture
```

## Contributing

Found a bug or have a suggestion? Open an issue at:
https://github.com/vladkarpman/vladkarpman-plugins/issues

## License

MIT License - see LICENSE file for details

## Changelog

### v0.6.0
- **`--output` flag**: Override output directory per command run
- **Theme configuration**: `theme.composable` for device tests to use your app's theme
- **Component library**: `component_library` config for reusing existing components
- **`/compose-design scan-components`**: Auto-generate component library from codebase
- Design generator now reuses library components when appropriate

### v0.1.0 (Initial Release)
- Three-phase workflow (generation, validation, testing)
- Screenshot and Figma input support
- Ralph-wiggum visual validation loop
- Mobile-mcp device testing integration
- Configurable project conventions
- Theme extraction from existing code
- Batch processing support
