# Plugin Enhancements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add output directory override, project theme configuration, and component library with scan command to compose-designer plugin.

**Architecture:** Extend existing YAML config schema with new fields. Modify `create.md` command to accept `--output` flag. Create new `scan-components.md` command. Update `device-tester.md` agent to use configured theme.

**Tech Stack:** Claude Code plugin (Markdown commands/agents), YAML config, Bash/Python utilities

---

## Task 1: Add `--output` Flag to Create Command

**Files:**
- Modify: `commands/create.md:4` (argument-hint line)
- Modify: `commands/create.md:95-101` (argument validation section)

**Step 1: Update argument-hint in frontmatter**

In `commands/create.md`, change line 4:

```yaml
# Before
argument-hint: --input <path|url> --name <ComponentName> --type <component|screen> [--clipboard] [--batch] [--device <device-id>]

# After
argument-hint: --input <path|url> --name <ComponentName> --type <component|screen> [--output <dir>] [--clipboard] [--batch] [--device <device-id>]
```

**Step 2: Add output flag to argument validation section**

After line 101 (after type validation), add:

```markdown
- `--output` (optional): Override default output directory for this run
  - If provided, use this path instead of `config.output.default_output_dir`
  - Path can be relative or absolute
  - Directory will be created if it doesn't exist
```

**Step 3: Update output path calculation in Phase 2**

Find the section that calculates `output_file_path` and update:

```markdown
**Determine output file path:**

```bash
# Check for --output override
if [ -n "$output_override" ]; then
  output_dir="$output_override"
else
  output_dir="${config.output.default_output_dir}"
fi

# Create directory if needed
mkdir -p "$output_dir"

# Build full path
output_file_path="$output_dir/${name}${suffix}.kt"
```

**Step 4: Verify change manually**

Run: Review the create.md file to ensure the flag is documented.

**Step 5: Commit**

```bash
git add commands/create.md
git commit -m "feat(compose-designer): add --output flag to create command

Allows overriding default_output_dir on a per-run basis."
```

---

## Task 2: Add Theme Configuration

**Files:**
- Modify: `commands/config.md:97-170` (YAML template section)
- Modify: `test-project/.claude/compose-designer.yaml`

**Step 1: Add theme section to config template**

In `commands/config.md`, find the YAML template (around line 97) and add after the `output:` section:

```yaml
# Theme configuration for device testing
theme:
  composable: ""                           # Full path to theme composable (e.g., "com.myapp.ui.theme.AppTheme")
                                           # Leave empty to use MaterialTheme
```

**Step 2: Update test project config**

In `test-project/.claude/compose-designer.yaml`, add after `output:` section:

```yaml
# Theme configuration for device testing
theme:
  composable: "com.test.composedesigner.ui.theme.ComposeDesignerTestTheme"
```

**Step 3: Commit**

```bash
git add commands/config.md test-project/.claude/compose-designer.yaml
git commit -m "feat(compose-designer): add theme.composable config field

Allows specifying project theme for device testing."
```

---

## Task 3: Update Device Tester to Use Configured Theme

**Files:**
- Modify: `agents/device-tester.md:254-289` (test activity generation section)

**Step 1: Update test activity template**

Find the test activity generation section (Phase 2, Step 2) and update:

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
{if config.theme.composable:}
import {config.theme.composable}
{endif}

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
            {if config.theme.composable:}
            {theme_composable_name} {
            {else:}
            MaterialTheme {
            {endif}
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

**Step 2: Add instructions for theme handling**

Before the test activity template, add:

```markdown
**Step 1.5: Determine theme wrapper**

Check config for custom theme:

```bash
# Read theme composable from config
theme_composable="${config.theme.composable:-}"

if [ -n "$theme_composable" ]; then
  # Extract simple name from full path (e.g., "AppTheme" from "com.myapp.ui.theme.AppTheme")
  theme_composable_name=$(echo "$theme_composable" | sed 's/.*\.//')
  theme_import="import $theme_composable"
  echo "Using project theme: $theme_composable_name"
else
  theme_composable_name="MaterialTheme"
  theme_import=""
  echo "Using default MaterialTheme"
fi
```

**Step 3: Commit**

```bash
git add agents/device-tester.md
git commit -m "feat(compose-designer): use configured theme in device tester

Device test activity now uses theme.composable from config.
Falls back to MaterialTheme if not configured."
```

---

## Task 4: Add Component Library Config Schema

**Files:**
- Modify: `commands/config.md:97-170` (YAML template section)

**Step 1: Add component_library section to config template**

In `commands/config.md`, add after the `theme:` section:

```yaml
# Component library for reuse (auto-generated by /compose-design scan-components)
# Edit use_when hints or remove components you don't want reused
component_library:
  # Example structure (populated by scan-components):
  # buttons:
  #   - name: "PrimaryButton"
  #     import: "com.myapp.ui.components.PrimaryButton"
  #     use_when: "primary action, submit, confirm"
  #     signature: "(text: String, onClick: () -> Unit, modifier: Modifier)"
  #
  # cards:
  #   - name: "ContentCard"
  #     import: "com.myapp.ui.components.ContentCard"
  #     use_when: "card container, elevated content"
  #     signature: "(modifier: Modifier, content: @Composable () -> Unit)"
```

**Step 2: Commit**

```bash
git add commands/config.md
git commit -m "feat(compose-designer): add component_library config schema

Documents structure for reusable components list."
```

---

## Task 5: Create Scan Components Command

**Files:**
- Create: `commands/scan-components.md`
- Modify: `.claude-plugin/plugin.json` (add command reference)

**Step 1: Create the command file**

Create `commands/scan-components.md`:

```markdown
---
name: scan-components
description: Scan codebase for reusable Compose components and update config
argument-hint: [--path <scan-path>]
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---

# Compose Designer: Scan Components

Scan the codebase for `@Composable` functions and generate the `component_library` section in config.

## Usage

```bash
# Scan default paths from config
/compose-design scan-components

# Scan specific directory
/compose-design scan-components --path app/src/main/java/ui/components
```

## Instructions for Claude

### Step 1: Load Configuration

```bash
if [ ! -f .claude/compose-designer.yaml ]; then
  echo "❌ Configuration not found. Run: /compose-design config"
  exit 1
fi
```

Read config to get `output.default_output_dir` for default scan path.

### Step 2: Determine Scan Path

```bash
# Use --path argument if provided, otherwise use config default
scan_path="${path_arg:-${config.output.default_output_dir}}"

if [ ! -d "$scan_path" ]; then
  echo "❌ Scan path not found: $scan_path"
  exit 1
fi

echo "Scanning: $scan_path"
```

### Step 3: Find Composable Functions

Use Grep to find all `@Composable` function declarations:

```bash
# Find all @Composable fun declarations
grep -r "@Composable" "$scan_path" --include="*.kt" -A 2 | \
  grep -E "^[^:]+:fun [A-Z]" | \
  sed 's/:fun /|/' | \
  sort -u
```

Parse results to extract:
- File path
- Function name
- Parameters (signature)

### Step 4: Categorize Components

Group components by inferred type based on naming:

**Buttons:** Names containing "Button"
**Cards:** Names containing "Card"
**Inputs:** Names containing "Field", "Input", "TextField"
**Lists:** Names containing "List", "Item", "Row"
**Other:** Everything else

### Step 5: Generate use_when Hints

Infer `use_when` from function name:

| Name pattern | use_when hint |
|--------------|---------------|
| `PrimaryButton` | "primary action, main CTA" |
| `SecondaryButton` | "secondary action, alternative" |
| `OutlinedButton` | "outlined style, less emphasis" |
| `IconButton` | "icon-only button, toolbar" |
| `TextButton` | "text-only, minimal emphasis" |
| `Card`, `ContentCard` | "card container, elevated content" |
| `TextField`, `Input` | "text input, form field" |
| `SearchBar` | "search input, query" |
| Names with "Item" | "list item, repeated element" |

For unrecognized patterns, use generic: "reusable component"

### Step 6: Build Component Library YAML

Generate YAML structure:

```yaml
component_library:
  buttons:
    - name: "{FunctionName}"
      import: "{package}.{FunctionName}"
      use_when: "{inferred_hint}"
      signature: "{extracted_signature}"

  cards:
    - name: "..."
      ...

  inputs:
    - name: "..."
      ...

  other:
    - name: "..."
      ...
```

### Step 7: Update Config File

Read existing `.claude/compose-designer.yaml`.

If `component_library:` section exists:
- Ask user: "Component library exists. Overwrite? [Y/n]"
- If no, exit

Append or replace `component_library:` section.

Write updated config using Write tool.

### Step 8: Report Results

```
✓ Scanned: {scan_path}
✓ Found: {total_count} reusable components

Component Library:
  • Buttons: {button_count}
  • Cards: {card_count}
  • Inputs: {input_count}
  • Other: {other_count}

Updated: .claude/compose-designer.yaml

Next steps:
  1. Review component_library section
  2. Adjust use_when hints for accuracy
  3. Remove components you don't want reused
```

## Error Handling

**No composables found:**
```
⚠️  No @Composable functions found in: {scan_path}

Check:
  • Path contains Kotlin files
  • Files have @Composable annotations
  • You're scanning the right directory

Try: /compose-design scan-components --path <correct-path>
```

**Config write fails:**
```
❌ Cannot write to .claude/compose-designer.yaml

Check permissions and try again.
```
```

**Step 2: Register command in plugin.json**

In `.claude-plugin/plugin.json`, add to commands array:

```json
"commands": [
  "./commands/config.md",
  "./commands/create.md",
  "./commands/scan-components.md"
]
```

**Step 3: Commit**

```bash
git add commands/scan-components.md .claude-plugin/plugin.json
git commit -m "feat(compose-designer): add scan-components command

Scans codebase for @Composable functions and generates
component_library section in config."
```

---

## Task 6: Update Design Generator to Use Component Library

**Files:**
- Modify: `agents/design-generator.md:109-169` (workflow section)

**Step 1: Add component library check to workflow**

After "Step 2: Search for Existing Theme", add new step:

```markdown
### Step 2.5: Check Component Library

If `config.component_library` exists and has entries:

**Read component library:**

```bash
# Parse component_library from config
# Build lookup map: category -> [components]
```

**During code generation:**

When generating UI elements, check if a matching component exists:

1. For buttons: Check `component_library.buttons`
   - Match based on `use_when` hints
   - Example: "submit button" matches component with use_when containing "submit"

2. For cards: Check `component_library.cards`

3. For inputs: Check `component_library.inputs`

**If match found:**

```kotlin
// Instead of generating:
Button(
    onClick = onSubmit,
    modifier = Modifier.fillMaxWidth()
) {
    Text("Submit")
}

// Generate:
PrimaryButton(
    text = "Submit",
    onClick = onSubmit,
    modifier = Modifier.fillMaxWidth()
)
```

Add required import from component's `import` field.

**If no match found:**

Generate fresh code as usual.

**Report component reuse:**

Track which library components were used:

```
Component Library Usage:
  ✓ PrimaryButton (buttons) - "Submit" button
  ✓ ContentCard (cards) - main container
  ○ SecondaryButton - not used
```
```

**Step 2: Commit**

```bash
git add agents/design-generator.md
git commit -m "feat(compose-designer): use component library in design generator

Generator now checks component_library config and reuses
existing components when appropriate."
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `CLAUDE.md` (add new features)
- Modify: `README.md` (if exists, update usage)

**Step 1: Update CLAUDE.md**

Add to "Common Commands" section:

```markdown
### Component Library

```bash
# Scan codebase for reusable components
/compose-design scan-components

# Scan specific directory
/compose-design scan-components --path app/src/main/java/ui/components
```

Add to "Configuration Management" section:

```markdown
**New config fields:**

```yaml
# Theme for device testing
theme:
  composable: "com.myapp.ui.theme.AppTheme"

# Component library (auto-generated by scan-components)
component_library:
  buttons:
    - name: "PrimaryButton"
      import: "com.myapp.ui.components.PrimaryButton"
      use_when: "primary action, submit"
      signature: "(text: String, onClick: () -> Unit)"
```

**Command flags:**

```bash
# Override output directory
/compose-design create --input design.png --name ProfileScreen --type screen --output ./features/profile/ui/
```
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(compose-designer): document new features

Add documentation for:
- --output flag
- theme.composable config
- component_library config
- scan-components command"
```

---

## Task 8: Integration Test

**Files:**
- No new files, manual testing

**Step 1: Test --output flag**

```bash
cd test-project

# Test with override
/compose-design create --input test-images/simple/button.png --name TestButton --type component --output ./app/src/main/java/com/test/composedesigner/custom/

# Verify file created in custom directory
ls -la ./app/src/main/java/com/test/composedesigner/custom/TestButtonComponent.kt
```

**Step 2: Test theme configuration**

```bash
# Verify test activity uses ComposeDesignerTestTheme
# (already configured in test-project config)

# Run device test and check theme is applied
/compose-design create --input test-images/simple/button.png --name ThemeTestButton --type component
```

**Step 3: Test scan-components**

```bash
# Run scan
/compose-design scan-components

# Verify config updated
cat .claude/compose-designer.yaml | grep -A 20 "component_library:"
```

**Step 4: Commit test results**

```bash
git add -A
git commit -m "test(compose-designer): verify new features work

Tested:
- --output flag creates files in custom directory
- theme.composable used in device tester
- scan-components generates component library"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add --output flag | commands/create.md |
| 2 | Add theme config | commands/config.md, test-project config |
| 3 | Use theme in device tester | agents/device-tester.md |
| 4 | Add component_library schema | commands/config.md |
| 5 | Create scan-components command | commands/scan-components.md, plugin.json |
| 6 | Use component library in generator | agents/design-generator.md |
| 7 | Update documentation | CLAUDE.md |
| 8 | Integration test | Manual verification |

**Total commits:** 8
**Estimated implementation:** ~1 hour
