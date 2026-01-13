# E2E Test Design for compose-designer Plugin

## Goal

Verify the plugin works end-to-end: a real design input generates Compose code that compiles and renders on a device.

## Approach

**Claude CLI Automation** - Run the full workflow via `claude` CLI, testing the actual user experience.

## Test Input

- Image: `test-project/test-images/jetnews.png`
- Component name: `JetNewsScreen`
- Type: `screen`

## Script Location

`tests/e2e-test.sh`

## Structure

### 1. Prerequisites Check

Before running, verify:
- `claude` CLI installed and accessible
- Python packages available (scikit-image, pillow, numpy)
- Android device/emulator connected (via `adb devices`)
- Gradle works in test-project
- Test image exists

### 2. Environment Setup

- Change to `test-project/` directory
- Create clean output directory for test artifacts
- Set 10-minute timeout for full run

### 3. Execute Test

```bash
claude --plugin-dir ../.. -p "Run /compose-design create \
  --input test-images/jetnews.png \
  --name JetNewsScreen \
  --type screen" \
  --output-format json
```

### 4. Success Criteria

**Phase 1 - Input Processing:**
- Baseline image copied/processed
- No "file not found" or "invalid image" errors

**Phase 2 - Code Generation:**
- File exists: `app/src/main/java/com/test/composedesigner/JetNewsScreen.kt`
- Contains `@Composable` annotation
- Contains `@Preview` function

**Phase 3 - Visual Validation:**
- Output mentions similarity score
- Score meets threshold (>=0.92) or user accepted lower

**Phase 4 - Device Testing:**
- Output mentions "device screenshot" or "runtime similarity"
- No "device not found" or "install failed" errors

**Final Verification:**
```bash
./gradlew compileDebugKotlin --quiet
grep -q "@Composable" "$output_file"
grep -q "@Preview" "$output_file"
```

### 5. Error Handling

**Prerequisite failures** - Exit immediately with clear message and remediation steps.

**Timeout** - Kill after 10 minutes, report which phase was running.

**Phase failures** - Capture output, show relevant error context.

### 6. Output Format

```
═══════════════════════════════════════════════════
  compose-designer E2E Test
═══════════════════════════════════════════════════

Prerequisites:
  ✓ Claude CLI found
  ✓ Python packages available
  ✓ Android device connected (Pixel_6_API_33)
  ✓ Gradle operational
  ✓ Test image exists

Running: /compose-design create --input jetnews.png --name JetNewsScreen --type screen

Phases:
  ✓ Input processing
  ✓ Code generation (142 lines)
  ✓ Visual validation (similarity: 94.2%, 3 iterations)
  ✓ Device testing (runtime similarity: 91.8%)

Verification:
  ✓ Output file exists
  ✓ Contains @Composable
  ✓ Contains @Preview
  ✓ Compiles successfully

═══════════════════════════════════════════════════
  ✓ E2E TEST PASSED (4m 32s)
═══════════════════════════════════════════════════
```

## Interactive Prompts

The test will auto-accept prompts for:
- Validation threshold acceptance
- Commit prompts
- Cleanup prompts

Use `--yes` flag or pipe responses as needed.

## Exit Codes

- `0` - Test passed
- `1` - Test failed
