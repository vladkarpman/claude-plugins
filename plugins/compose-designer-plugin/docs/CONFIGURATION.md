# Configuration Reference

Complete guide to configuring the compose-designer plugin.

## Overview

Configuration lives in `.claude/compose-designer.yaml` at your project root. Run `/compose-design config` to generate a starter config with smart defaults.

## Required Fields

You must set these two fields - the plugin will prompt if missing:

```yaml
output:
  package_base: "com.yourapp"              # Your app's base package

testing:
  test_activity_package: "com.yourapp.test"  # Package for test activity
```

## Configuration Sections

- [Model Configuration](#model-configuration)
- [Naming Conventions](#naming-conventions)
- [Architecture](#architecture)
- [Preview Settings](#preview-settings)
- [Validation](#validation)
- [Batch Processing](#batch-processing)
- [Device Testing](#device-testing)
- [Figma Integration](#figma-integration)
- [Output Preferences](#output-preferences)
- [Theme Configuration](#theme-configuration) *(new in v0.6.0)*
- [Component Library](#component-library) *(new in v0.6.0)*

---

## Model Configuration

Controls which Claude model each agent uses. Vision-heavy agents benefit from more capable models.

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `default` | string | `"opus"` | `opus`, `sonnet`, `haiku` |
| `design_generator` | string | inherits `default` | `opus`, `sonnet`, `haiku` |
| `visual_validator` | string | inherits `default` | `opus`, `sonnet`, `haiku` |
| `baseline_preprocessor` | string | inherits `default` | `opus`, `sonnet`, `haiku` |
| `device_tester` | string | inherits `default` | `opus`, `sonnet`, `haiku` |

### Model Options

- **`opus`** - Most capable. Best for complex designs, nuanced visual analysis. Slower and more expensive. Recommended default for highest quality.
- **`sonnet`** - Balanced capability and speed. Good for faster iteration during development.
- **`haiku`** - Fastest and cheapest. Use for simple components or quick prototyping.

### Example

```yaml
model:
  default: "opus"              # Highest quality for all agents
  design_generator: "opus"     # Complex visual analysis needs capability
  visual_validator: "opus"     # Precise diff reasoning benefits from opus
  device_tester: "sonnet"      # Interactions are simpler, sonnet suffices
```

---

## Naming Conventions

Controls how generated files and composables are named.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `component_suffix` | string | `"Component"` | Suffix for components (e.g., `ButtonComponent`) |
| `screen_suffix` | string | `"Screen"` | Suffix for screens (e.g., `LoginScreen`) |
| `preview_annotation` | string | `"@Preview"` | Annotation for preview functions |

### Example

```yaml
naming:
  component_suffix: "Component"    # ProfileCardComponent.kt
  screen_suffix: "Screen"          # SettingsScreen.kt
  preview_annotation: "@Preview"
```

---

## Architecture

Controls code generation patterns for state management.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `stateless_components` | bool | `true` | Generate stateless composables by default |
| `state_hoisting` | bool | `true` | Hoist state to parent composable |
| `remember_saveable` | bool | `false` | Use `rememberSaveable` instead of `remember` |

### Example

```yaml
architecture:
  stateless_components: true    # Composables receive state as parameters
  state_hoisting: true          # State managed by parent
  remember_saveable: false      # Use remember (not rememberSaveable)
```

---

## Preview Settings

Controls how `@Preview` composables are generated.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `show_background` | bool | `true` | Show background in preview |
| `background_color` | string | `"#FFFFFF"` | Background color (hex) |
| `device_spec` | string | `"spec:width=411dp,height=891dp"` | Device dimensions (Pixel 4 default) |
| `font_scale` | float | `1.0` | Font scaling factor |

### Example

```yaml
preview:
  show_background: true
  background_color: "#FFFFFF"
  device_spec: "spec:width=411dp,height=891dp"
  font_scale: 1.0
```

---

## Validation

Controls the ralph-wiggum visual validation loop.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `visual_similarity_threshold` | float | `0.92` | SSIM threshold (0.0-1.0). Higher = stricter |
| `max_ralph_iterations` | int | `10` | Maximum refinement iterations |
| `preview_screenshot_delay` | string/int | `"auto"` | Delay before capturing preview |

### `visual_similarity_threshold`

Controls how closely the generated preview must match the original design:
- **0.85-0.90** - Loose matching, faster iteration, may miss details
- **0.90-0.94** - Balanced (default range)
- **0.95-1.0** - Strict matching, slower but more accurate

### `preview_screenshot_delay`

- **`"auto"`** - Plugin determines optimal delay. Use this normally.
- **Milliseconds** (e.g., `3000`) - Fixed delay. Use if previews render incomplete due to slow emulator or complex animations.

### Example

```yaml
validation:
  visual_similarity_threshold: 0.92    # 92% similarity required
  max_ralph_iterations: 10             # Try up to 10 refinements
  preview_screenshot_delay: "auto"     # Auto-detect delay
```

---

## Batch Processing

Controls how multiple designs are processed.

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `mode` | string | `"sequential"` | `sequential`, `parallel` |

### Options

- **`"sequential"`** - Process one design at a time. Safer, easier to debug failures. Recommended for most cases.
- **`"parallel"`** - Process multiple designs concurrently. Faster but harder to trace errors. Use for large batches of similar, simple components.

### Example

```yaml
batch:
  mode: "sequential"    # One at a time for reliability
```

---

## Device Testing

Controls how the plugin tests generated components on real Android devices.

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `test_activity_package` | string | **required** | Any valid package name |
| `test_activity_name` | string | `"ComposeTestActivity"` | Any valid class name |
| `device_id` | string | `"auto"` | `auto`, device ID, name pattern |
| `interaction_depth` | string | `"comprehensive"` | `basic`, `comprehensive` |
| `cleanup_artifacts` | string | `"ask"` | `always`, `never`, `ask` |

### `device_id`

Specifies which Android device to use for testing:

- **`"auto"`** - Selects first available device from `adb devices`. Best for single-device setups.
- **Specific ID** - Use exact device ID like `"emulator-5554"` or `"RFCN123ABC"`. Find yours by running `adb devices` in terminal.
- **Name pattern** - Use wildcards like `"Pixel*"` or `"*Emulator*"` to match device names. Useful when device IDs change between sessions.

### `interaction_depth`

Controls what gets tested on the device:

- **`"basic"`** - Tests rendering only. Verifies component displays correctly without crashes. Faster.
- **`"comprehensive"`** - Tests rendering plus interactions: button clicks, text input, scrolling, state changes. Slower but more thorough.

### `cleanup_artifacts`

Controls cleanup after device testing:

- **`"always"`** - Auto-remove test activity and APK after testing. Keeps project clean but loses debugging artifacts.
- **`"never"`** - Keep all artifacts. Useful for debugging but clutters project.
- **`"ask"`** - Prompt after each test run. Recommended when learning the workflow.

### Example

```yaml
testing:
  test_activity_package: "com.yourapp.test"
  test_activity_name: "ComposeTestActivity"
  device_id: "auto"                    # Use first available device
  interaction_depth: "comprehensive"   # Full interaction testing
  cleanup_artifacts: "ask"             # Prompt for cleanup decision
```

---

## Figma Integration

Controls Figma API integration for design token extraction.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `extract_tokens` | bool | `true` | Extract colors, typography, spacing from Figma |
| `api_token_source` | string | `"env"` | Where to read API token |
| `api_token` | string | `""` | Token value (if source is `config`) |
| `fallback_to_image` | bool | `true` | Use image if token extraction fails |

### `api_token_source`

- **`"env"`** - Read from `$FIGMA_TOKEN` environment variable. More secure, recommended for shared repos. Set with `export FIGMA_TOKEN="figd_..."`.
- **`"config"`** - Store token in config file. Convenient for personal projects but avoid committing to version control.

### Example

```yaml
figma:
  extract_tokens: true
  api_token_source: "env"        # Read from $FIGMA_TOKEN
  fallback_to_image: true        # Still works if token extraction fails
```

---

## Output Preferences

Controls where and how generated code is written.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `package_base` | string | **required** | Base package name for generated code |
| `default_output_dir` | string | `"app/src/main/java"` | Output directory |
| `include_comments` | bool | `false` | Add explanatory comments to code |
| `extract_theme_from_existing` | bool | `true` | Use existing theme colors/typography |

### `extract_theme_from_existing`

When `true`, the plugin searches for existing theme files and uses them:
- `Color.kt`, `Colors.kt` → `MaterialTheme.colorScheme.primary`
- `Type.kt`, `Typography.kt` → `MaterialTheme.typography.titleLarge`
- `Theme.kt`, `AppTheme.kt` → Theme structure

Benefits: Consistent colors, no hardcoded hex values, automatic dark mode support.

### Example

```yaml
output:
  package_base: "com.yourapp"
  default_output_dir: "app/src/main/java"
  include_comments: false
  extract_theme_from_existing: true    # Use existing theme
```

---

## Theme Configuration

*New in v0.6.0*

Controls the theme wrapper used during device testing. When configured, device tests render your component inside your app's actual theme instead of the generic MaterialTheme.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `composable` | string | `""` (empty) | Full path to theme composable |

### `composable`

Specifies the fully-qualified name of your theme composable:
- **Empty string** (default) - Uses `MaterialTheme` as wrapper
- **Full path** - Uses your custom theme (e.g., `"com.yourapp.ui.theme.AppTheme"`)

### Example

```yaml
theme:
  composable: "com.yourapp.ui.theme.AppTheme"
```

**Result in test activity:**

```kotlin
import com.yourapp.ui.theme.AppTheme

setContent {
    AppTheme {  // Your theme instead of MaterialTheme
        YourComponent()
    }
}
```

---

## Component Library

*New in v0.6.0*

Specifies reusable components that the design generator should prefer over generating new code. Auto-populate this section by running `/compose-design scan-components`.

| Field | Type | Description |
|-------|------|-------------|
| `buttons` | list | Button components |
| `cards` | list | Card components |
| `inputs` | list | Input/TextField components |
| `lists` | list | List item components |
| `other` | list | Other reusable components |

### Component Entry Fields

Each component entry has:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Component function name |
| `import` | string | Full import path |
| `use_when` | string | Hints for when to use this component |
| `signature` | string | Function signature |

### `use_when` Hints

The `use_when` field helps the design generator match design elements to library components:
- Use comma-separated keywords describing when to use the component
- Include synonyms and common use cases
- The generator matches design context against these hints

### Example

```yaml
component_library:
  buttons:
    - name: "PrimaryButton"
      import: "com.yourapp.ui.components.PrimaryButton"
      use_when: "primary action, submit, confirm, main CTA"
      signature: "(text: String, onClick: () -> Unit, modifier: Modifier)"

    - name: "SecondaryButton"
      import: "com.yourapp.ui.components.SecondaryButton"
      use_when: "secondary action, cancel, alternative"
      signature: "(text: String, onClick: () -> Unit, modifier: Modifier)"

  cards:
    - name: "ContentCard"
      import: "com.yourapp.ui.components.ContentCard"
      use_when: "card container, elevated content, content wrapper"
      signature: "(modifier: Modifier, content: @Composable () -> Unit)"

  inputs:
    - name: "AppTextField"
      import: "com.yourapp.ui.components.AppTextField"
      use_when: "text input, form field, user input"
      signature: "(value: String, onValueChange: (String) -> Unit, modifier: Modifier)"
```

### Auto-Generation

Run `/compose-design scan-components` to auto-generate this section:

```bash
# Scan default output directory
/compose-design scan-components

# Scan specific path
/compose-design scan-components --path app/src/main/java/ui/components
```

The command:
1. Finds all `@Composable` functions in the scan path
2. Categorizes by naming (Button, Card, Input, etc.)
3. Infers `use_when` hints from function names
4. Updates your config with the component library

After scanning, review and adjust `use_when` hints for accuracy.

---

## Complete Example

Full configuration with all options:

```yaml
# .claude/compose-designer.yaml

model:
  default: "opus"
  design_generator: "opus"
  visual_validator: "opus"
  baseline_preprocessor: "opus"
  device_tester: "opus"

naming:
  component_suffix: "Component"
  screen_suffix: "Screen"
  preview_annotation: "@Preview"

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
  max_ralph_iterations: 10
  preview_screenshot_delay: "auto"

batch:
  mode: "sequential"

testing:
  test_activity_package: "com.yourapp.test"  # REQUIRED
  test_activity_name: "ComposeTestActivity"
  device_id: "auto"
  interaction_depth: "comprehensive"
  cleanup_artifacts: "ask"

figma:
  extract_tokens: true
  api_token_source: "env"
  fallback_to_image: true

output:
  package_base: "com.yourapp"  # REQUIRED
  default_output_dir: "app/src/main/java"
  include_comments: false
  extract_theme_from_existing: true

# Theme for device testing (v0.6.0+)
theme:
  composable: "com.yourapp.ui.theme.AppTheme"

# Component library for reuse (v0.6.0+)
# Auto-generate with: /compose-design scan-components
component_library:
  buttons:
    - name: "PrimaryButton"
      import: "com.yourapp.ui.components.PrimaryButton"
      use_when: "primary action, submit, confirm"
      signature: "(text: String, onClick: () -> Unit, modifier: Modifier)"
  cards:
    - name: "ContentCard"
      import: "com.yourapp.ui.components.ContentCard"
      use_when: "card container, elevated content"
      signature: "(modifier: Modifier, content: @Composable () -> Unit)"
```

---

## Common Presets

### Fast Iteration (Development)

Optimized for speed during development:

```yaml
model:
  default: "sonnet"
validation:
  visual_similarity_threshold: 0.85
  max_ralph_iterations: 5
testing:
  interaction_depth: "basic"
  cleanup_artifacts: "always"
```

### High Quality (Production)

Optimized for accuracy before shipping:

```yaml
model:
  default: "opus"
validation:
  visual_similarity_threshold: 0.95
  max_ralph_iterations: 12
testing:
  interaction_depth: "comprehensive"
```

### CI/CD Pipeline

Optimized for automated builds:

```yaml
model:
  default: "sonnet"
validation:
  visual_similarity_threshold: 0.90
  max_ralph_iterations: 6
testing:
  device_id: "emulator-5554"       # Fixed emulator ID
  cleanup_artifacts: "always"
batch:
  mode: "parallel"
```
