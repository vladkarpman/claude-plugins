# Compose Designer Agent Architecture Improvements

**Date:** 2026-01-13
**Status:** DESIGN PROPOSAL
**Author:** Claude (based on test execution findings)

## Executive Summary

After comprehensive testing of the compose-designer plugin v0.1.2, we identified 4 critical architectural issues that prevent autonomous, high-quality Compose code generation:

1. **visual-validator cannot render previews autonomously** - has ralph-wiggum Skill tool but not mobile-mcp tools
2. **Unrealistic 92% similarity targets** - baseline complexity (device frames, missing assets) makes targets impossible
3. **design-generator doesn't integrate with MainActivity** - generated components not displayed
4. **No baseline preprocessing** - composite layouts and device frames cause 30-40% similarity penalty

This document proposes a comprehensive redesign from a 3-agent linear workflow to a 4-agent architecture with preprocessing, split validation responsibilities, and realistic success criteria.

## Current State (v0.1.2)

### Existing Architecture

```
Phase 1: design-generator
  ├─ Analyzes baseline image
  ├─ Generates Component.kt
  └─ Does NOT integrate with MainActivity ❌

Phase 2: visual-validator
  ├─ Has ralph-wiggum Skill tool ✓
  ├─ Does NOT have mobile-mcp tools ❌
  ├─ Cannot render previews autonomously ❌
  └─ Target: 92% (unrealistic for many baselines) ❌

Phase 3: device-tester
  ├─ Has mobile-mcp tools ✓
  ├─ Builds and deploys APK ✓
  └─ Ended up doing visual-validator's job ⚠️
```

### Test Results

**Test case:** ChatScreen from Jetchat screenshot (test-images/jetchat.png)

**Findings:**
- Code quality: 4.25/5 ⭐⭐⭐⭐
- Final similarity: 56.70% (target: 92%, realistic max: ~70%)
- 5 iterations completed
- Required manual MainActivity integration
- visual-validator couldn't render previews (used device-tester instead)

**Critical issues documented in:** `/tmp/compose-designer.v2aKn1/FINAL_REPORT.md`

---

## Section 1: Proposed Architecture

### 4-Agent Structure

```
Phase 0: baseline-preprocessor (NEW)
  ├─ Detects device frames and crops to content
  ├─ Handles composite layouts (multiple screens)
  ├─ Calculates realistic similarity targets (60-95%)
  └─ Outputs: baseline-preprocessed.png + report.json

Phase 1: design-generator (ENHANCED)
  ├─ Reads preprocessing report for realistic target
  ├─ Generates Component.kt with theme integration
  ├─ Creates data classes for mock data
  └─ Integrates with MainActivity OR creates test activity ✓

Phase 2: Visual Validation Loop (SPLIT INTO TWO AGENTS)
  ├─ code-refiner (NEW)
  │   ├─ Analyzes visual diffs
  │   ├─ Identifies code changes needed
  │   ├─ Applies targeted edits
  │   └─ Tools: Read, Edit, Bash, Skill (ralph-wiggum)
  │
  └─ preview-renderer (NEW)
      ├─ Builds APK
      ├─ Deploys to device
      ├─ Captures screenshots
      └─ Tools: Read, Write, Bash, mobile-mcp (all device tools)

Phase 3: device-tester (FOCUSED)
  ├─ Final runtime testing only
  ├─ Interaction validation
  └─ Does NOT do preview rendering anymore
```

### Key Principles

**1. Clear Agent Boundaries**
- Each agent has one responsibility
- No overlapping workflows
- Clear inputs and outputs

**2. Full Agent Autonomy**
- Each agent has ALL tools it needs
- No agent depends on external manual steps
- Graceful degradation when optional dependencies missing

**3. Realistic Success Criteria**
- Similarity targets based on baseline complexity (60-95%)
- Device frames, missing assets, composite layouts factored in
- "Good enough" thresholds defined

**4. Graceful Degradation**
- Fallback workflows when ralph-wiggum unavailable
- Manual modes when mobile-mcp unavailable
- Partial success states (code works, validation incomplete)

---

## Section 2: baseline-preprocessor Agent

### Purpose

Preprocesses design baselines to:
1. Remove device frames (improve similarity by ~15%)
2. Handle composite layouts (extract single screen from multi-screen mockups)
3. Detect missing assets (images, stickers, custom fonts)
4. Calculate realistic similarity targets based on complexity

### Agent Specification

```yaml
---
name: baseline-preprocessor
description: Preprocesses design baselines by detecting device frames, cropping to content area, handling composite layouts, and calculating realistic similarity targets based on baseline complexity
model: sonnet
color: orange
tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---
```

### Workflow

**Phase 0: Load and Analyze**
```bash
1. Read baseline image:
   baseline = Read("{baseline_path}")

2. Analyze with vision:
   • Detect device frames (rounded corners, status bar, nav bar)
   • Detect composite layouts (multiple screens side-by-side)
   • Detect missing assets (images, stickers, custom fonts)
   • Estimate content area dimensions
```

**Phase 1: Handle Composite Layouts**
```bash
3. If composite layout detected:

   AskUserQuestion:
     question: "Baseline contains multiple screens (left, middle, right). Which screen should I generate code for?"
     header: "Screen Select"
     options:
       - label: "Left screen"
         description: "Generate code for the leftmost screen"
       - label: "Middle screen (Recommended)"
         description: "Generate code for the center screen (usually main content)"
       - label: "Right screen"
         description: "Generate code for the rightmost screen"

   # User selects: "Middle screen"
   selected_screen = "middle"
```

**Phase 2: Crop Device Frames**
```bash
4. Crop to content area using Python:

python3 - <<'EOF'
from PIL import Image
import numpy as np

# Load image
img = Image.open("{baseline_path}")
arr = np.array(img)

# Detect device frame (dark borders with RGB < 50)
mask = (arr[:,:,0] > 50) | (arr[:,:,1] > 50) | (arr[:,:,2] > 50)

# Find content bounding box
rows = np.any(mask, axis=1)
cols = np.any(mask, axis=0)
rmin, rmax = np.where(rows)[0][[0, -1]]
cmin, cmax = np.where(cols)[0][[0, -1]]

# Crop to content
content = img.crop((cmin, rmin, cmax, rmax))

# If composite, extract middle screen
if is_composite:
    width = content.width
    third = width // 3
    content = content.crop((third, 0, 2*third, content.height))

# Save preprocessed baseline
content.save("{temp_dir}/baseline-preprocessed.png")

# Report dimensions
print(f"Original: {img.width}x{img.height}")
print(f"Preprocessed: {content.width}x{content.height}")
EOF
```

**Phase 3: Calculate Realistic Target**
```python
5. Calculate realistic similarity target:

base_target = 0.92

# Device frame present
if has_device_frame:
    base_target -= 0.15  # Down to 77%

# Composite layout (multiple screens)
if is_composite:
    base_target -= 0.10  # Down to 82% (or 67% if also has frame)

# Missing assets (images, stickers, custom fonts)
missing_asset_penalty = detected_missing_assets * 0.05
base_target -= missing_asset_penalty

# Floor at 60% (below this indicates fundamental mismatch)
realistic_target = max(0.60, base_target)

# Ceiling at 95% (perfect match unrealistic due to rendering differences)
realistic_target = min(0.95, base_target)
```

**Phase 4: Generate Report**
```bash
6. Write preprocessing report:

cat > "{temp_dir}/preprocessing-report.json" <<EOF
{
  "has_device_frame": true,
  "is_composite": true,
  "selected_screen": "middle",
  "detected_missing_assets": 1,
  "realistic_similarity_target": 0.67,
  "content_dimensions": [1080, 2160],
  "notes": "Cropped middle screen from 3-screen composite. Device frame removed. Sticker image detected but cannot be replicated (similarity penalty applied)."
}
EOF

7. Report to user:

   ✅ Baseline Preprocessing Complete

   Original: 1894x1234 (3 screens with device frames)
   Preprocessed: 1080x2160 (middle screen, frame removed)

   Detected:
   • Device frame: Yes (removed, +15% similarity gain)
   • Composite layout: Yes (extracted middle screen)
   • Missing assets: 1 (sticker image, -5% penalty)

   Realistic similarity target: 67%
   (Adjusted from 92% base due to complexity)
```

### Outputs

```
{temp_dir}/
├── baseline-preprocessed.png        # Cleaned baseline for comparison
└── preprocessing-report.json        # Metadata for downstream agents
```

**preprocessing-report.json schema:**
```json
{
  "has_device_frame": boolean,
  "is_composite": boolean,
  "selected_screen": "left" | "middle" | "right" | null,
  "detected_missing_assets": number,
  "realistic_similarity_target": number,
  "content_dimensions": [width, height],
  "notes": string
}
```

### Error Handling

**Invalid image format:**
```
❌ Baseline image cannot be read

Error: {PIL_error}

Supported formats: PNG, JPG, JPEG, WebP
File: {baseline_path}

Please provide a valid image file.
```

**Cannot detect content area:**
```
⚠️  Could not automatically detect content area

The image may not have a device frame, or the frame detection failed.

Options:
1. Use original image as-is (100% similarity target)
2. Manual crop (you specify crop coordinates)
3. Abort workflow

What would you like to do? [1/2/3]:
```

---

## Section 3: design-generator Agent Enhancements

### Current Gaps

**Issue:** The design-generator creates the Compose component file but doesn't integrate it with MainActivity, leaving the app showing "Hello Android!" instead of the generated UI.

**Impact:** Breaks user experience - they see successful code generation but the app doesn't display it.

### Enhanced Workflow

**Phase 0: Setup (unchanged)**
```
1. Load configuration
2. Read preprocessing report to get realistic_similarity_target
3. Validate project structure
```

**Phase 1: Analyze Design (enhanced)**
```
4. Read preprocessed baseline image
5. Read preprocessing-report.json for:
   • realistic_similarity_target
   • detected_components (composite screens)
   • content_area dimensions
   • suggested_mock_data
6. Analyze visual hierarchy with vision
7. Search for existing theme files
```

**Phase 2: Generate Component (enhanced)**
```
8. Generate data classes if needed:
   • ChatMessage, ProductCard, etc.
   • Place in {package_base}.ui.model/

9. Generate main composable:
   • Layout structure (Column/Row/Box)
   • MaterialTheme color/typography integration
   • State hoisting with callbacks
   • KDoc documentation

10. Generate preview function:
    • Mock data instances
    • ComposeDesignerTestTheme wrapper
    • Preview annotations
```

**Phase 3: MainActivity Integration (NEW)**

**Option A: Update existing MainActivity** (preferred for simple components)
```kotlin
// Read existing MainActivity.kt
val mainActivity = Read("app/src/main/java/{package}/MainActivity.kt")

// Check if it's the default template
if (mainActivity.contains("Greeting") || mainActivity.contains("Hello Android")) {
    // Replace setContent block with generated component
    Edit(
        file_path = "app/src/main/java/{package}/MainActivity.kt",
        old_string = """
            setContent {
                ComposeDesignerTestTheme {
                    Surface {
                        Greeting("Android")
                    }
                }
            }
        """,
        new_string = """
            setContent {
                ComposeDesignerTestTheme {
                    var messageText by remember { mutableStateOf("") }

                    ChatScreenScreen(
                        chatTitle = "#composers",
                        messages = sampleMessages,
                        messageText = messageText,
                        onMessageTextChange = { messageText = it },
                        onSendClick = { messageText = "" },
                        onBackClick = { finish() }
                    )
                }
            }
        """
    )
}
```

**Option B: Create standalone test activity** (for complex components or when MainActivity is non-trivial)
```kotlin
// Generate TestChatScreenActivity.kt
Write(
    file_path = "app/src/main/java/{package}/TestChatScreenActivity.kt",
    content = """
        package {package}

        import android.os.Bundle
        import androidx.activity.ComponentActivity
        import androidx.activity.compose.setContent
        import {package}.ui.screens.ChatScreenScreen
        import {package}.ui.theme.ComposeDesignerTestTheme

        /**
         * Test activity for ChatScreenScreen component.
         * Generated by compose-designer plugin.
         */
        class TestChatScreenActivity : ComponentActivity() {
            override fun onCreate(savedInstanceState: Bundle?) {
                super.onCreate(savedInstanceState)
                setContent {
                    ComposeDesignerTestTheme {
                        // State and mock data here
                        ChatScreenScreen(...)
                    }
                }
            }
        }
    """
)

// Add to AndroidManifest.xml
```

**Decision logic:**
```
if MainActivity contains only default template:
    → Option A (update MainActivity)
elif MainActivity has complex existing UI:
    → Ask user: "MainActivity has existing UI. Create separate test activity?"
elif config.output.always_create_test_activity == true:
    → Option B (standalone activity)
```

**Phase 4: Verification (enhanced)**
```
11. Verify compilation:
    ./gradlew compileDebugKotlin

12. Report to user:
    ✅ Generated {ComponentName}
    • Component: {file_path}
    • Data models: {model_files}
    • Integration: {MainActivity updated | TestActivity created}
    • Expected similarity: {realistic_similarity_target:.1%} (from preprocessing)
    • Lines of code: {loc}
```

### Updated Tools

```yaml
tools:
  - Read      # Read baseline, config, existing code
  - Write     # Generate component, data classes, test activity
  - Edit      # Update MainActivity
  - Bash      # Verify compilation
  - Glob      # Find theme files
  - Grep      # Search for patterns
  - AskUserQuestion  # Ask about MainActivity integration
```

**Removed:** Task tool (not needed - this agent doesn't spawn sub-agents)

### Success Criteria

**Must have:**
- ✅ Generated component compiles without errors
- ✅ Component integrated with MainActivity OR test activity created
- ✅ App displays generated UI (not "Hello Android!")
- ✅ Uses MaterialTheme colors/typography (no hardcoded values)
- ✅ Stateless with callbacks

**Should have:**
- ✅ Mock data in separate data classes
- ✅ KDoc documentation
- ✅ Preview function with sample data
- ✅ Matches preprocessing report's expected structure

### Error Handling

**MainActivity integration fails:**
```
⚠️  Could not automatically update MainActivity (complex existing UI)

Created test activity instead:
  • TestChatScreenActivity.kt

To test:
1. Add to AndroidManifest.xml:
   <activity android:name=".TestChatScreenActivity"
             android:exported="true">
       <intent-filter>
           <action android:name="android.intent.action.MAIN" />
           <category android:name="android.intent.category.LAUNCHER" />
       </intent-filter>
   </activity>

2. Or manually integrate ChatScreenScreen into your MainActivity
```

**Compilation fails:**
```
❌ Generated code failed to compile

Error: {compiler_error}

Troubleshooting:
1. Check theme files exist in ui/theme/
2. Verify all imports are correct
3. Check data class properties match usage

Would you like me to:
1. Fix the compilation error
2. Show you the generated code for manual review
3. Regenerate with different approach
4. Abort workflow

What would you like to do? [1/2/3/4]:
```

---

## Section 4: preview-renderer Agent (NEW)

### Purpose

**Problem solved:** Current visual-validator can't render previews autonomously - has ralph-wiggum Skill tool but not mobile-mcp tools for device deployment.

**Solution:** Extract device operations into dedicated preview-renderer agent with full mobile-mcp toolset.

### Agent Specification

```yaml
---
name: preview-renderer
description: Renders Jetpack Compose components on Android devices/emulators by building APK, deploying, launching, and capturing screenshots for visual validation
model: sonnet
color: yellow
tools:
  - Read
  - Write
  - Bash
  - mcp__mobile-mcp__mobile_list_available_devices
  - mcp__mobile-mcp__mobile_install_app
  - mcp__mobile-mcp__mobile_launch_app
  - mcp__mobile-mcp__mobile_take_screenshot
  - mcp__mobile-mcp__mobile_save_screenshot
  - mcp__mobile-mcp__mobile_click_on_screen_at_coordinates
  - mcp__mobile-mcp__mobile_swipe_on_screen
  - mcp__mobile-mcp__mobile_type_keys
---
```

### Workflow

**Phase 0: Device Setup**
```
1. List available devices:
   devices = mobile_list_available_devices()

2. Select device (priority order):
   a. If config.testing.device_id is set → use that
   b. If multiple devices → ask user to select
   c. If no devices → error with setup instructions

3. Verify device responsive:
   mobile_take_screenshot(device_id) # Quick test
```

**Phase 1: Build and Deploy**
```
4. Build debug APK:
   cd {project_root}
   ./gradlew assembleDebug

5. Get APK path:
   apk_path = "app/build/outputs/apk/debug/app-debug.apk"

6. Install on device:
   mobile_install_app(
       device=device_id,
       path=apk_path
   )

7. Wait for installation (2-3 seconds)
```

**Phase 2: Launch and Capture**
```
8. Launch app:
   mobile_launch_app(
       device=device_id,
       packageName="{config.testing.test_activity_package}"
   )

9. Wait for render:
   sleep({config.validation.preview_screenshot_delay} seconds)

10. Capture screenshot:
    mobile_save_screenshot(
        device=device_id,
        saveTo="{temp_dir}/preview-iteration-{N}.png"
    )
```

**Phase 3: Return Results**
```
11. Report to caller:
    {
        "status": "success",
        "screenshot_path": "{temp_dir}/preview-iteration-{N}.png",
        "device_id": "{device_id}",
        "device_name": "{device_name}",
        "build_time_seconds": 2.1,
        "apk_size_mb": 7.7
    }
```

### Inputs (from caller)

```json
{
    "iteration": 3,
    "component_file": "app/src/main/java/.../ChatScreenScreen.kt",
    "temp_dir": "/tmp/compose-designer.v2aKn1",
    "config": {
        "testing": {
            "device_id": "emulator-5554",
            "test_activity_package": "com.test.composedesigner"
        },
        "validation": {
            "preview_screenshot_delay": 2
        }
    }
}
```

### Outputs

```
/tmp/compose-designer.v2aKn1/
├── preview-iteration-1.png  # Device screenshot at 1080x2400
├── preview-iteration-2.png
└── preview-iteration-3.png
```

### Error Handling

**No devices found:**
```
❌ No Android devices found

Connect a device:
  • Physical: Enable USB debugging in Developer Options
  • Emulator: Launch from Android Studio → AVD Manager

Verify: adb devices

Would you like to:
1. Wait and retry (I'll check again in 10s)
2. Skip device rendering (validation will fail)
3. Abort workflow
```

**Build fails:**
```
❌ APK build failed

Error: {gradle_error}

Troubleshooting:
1. Check component compiles: ./gradlew compileDebugKotlin
2. Verify Gradle daemon: ./gradlew --status
3. Check AndroidManifest.xml is valid

Retry after fixing? [Y/n]:
```

**Screenshot capture fails:**
```
⚠️  Screenshot capture failed (attempt {N}/3)

Possible causes:
- App crashed on launch
- Device disconnected
- Activity not launched

Retrying in 3 seconds...
```

### Graceful Degradation

**If mobile-mcp unavailable:**
```
⚠️  mobile-mcp plugin not found

Visual validation requires device screenshots.

Options:
1. Install mobile-mcp: https://github.com/anthropics/mobile-ui-testing
2. Skip validation (accept generated code as-is)
3. Manual validation (I'll guide you)

What would you like to do? [1/2/3]:
```

**If emulator slow:**
```
⏱  Build taking longer than expected ({elapsed}s)...

This is normal for:
- First build (Gradle downloads dependencies)
- Emulator startup (can take 30-60s)
- Large projects

Still working...
```

---

## Section 5: code-refiner Agent (NEW)

### Purpose

**Problem solved:** Current visual-validator tries to do both device operations AND code refinement, but lacks the right tools for device ops.

**Solution:** Extract code refinement logic into dedicated code-refiner agent that works with preview screenshots provided by preview-renderer.

### Agent Specification

```yaml
---
name: code-refiner
description: Iteratively refines Jetpack Compose code to match baseline design by analyzing visual diffs, identifying mismatches, and applying targeted code improvements within ralph-wiggum loop
model: sonnet
color: cyan
tools:
  - Read
  - Edit
  - Bash
  - Skill  # For ralph-wiggum loop control
---
```

**Key point:** NO mobile-mcp tools - this agent only edits code based on screenshots provided by preview-renderer.

### Workflow (Per Iteration)

**Phase 0: Load Context**
```
1. Read current code:
   component = Read("{component_file}")

2. Read baseline:
   baseline = Read("{baseline_preprocessed_path}")

3. Read latest preview:
   preview = Read("{temp_dir}/preview-iteration-{N}.png")

4. Read preprocessing report:
   report = Read("{temp_dir}/preprocessing-report.json")
   realistic_target = report.realistic_similarity_target
```

**Phase 1: Calculate Similarity**
```
5. Run SSIM comparison:
   python3 - <<'EOF'
   from skimage.metrics import structural_similarity as ssim
   from PIL import Image
   import numpy as np

   baseline = np.array(Image.open("{baseline_preprocessed_path}"))
   preview = np.array(Image.open("{preview_path}"))

   # Resize if dimensions differ
   if baseline.shape != preview.shape:
       preview_img = Image.fromarray(preview)
       preview_img = preview_img.resize(
           (baseline.shape[1], baseline.shape[0]),
           Image.Resampling.LANCZOS
       )
       preview = np.array(preview_img)

   # Calculate SSIM
   score = ssim(baseline, preview, channel_axis=2)
   print(f"{score:.4f}")
   EOF

6. Parse similarity:
   similarity = float(output.strip())
```

**Phase 2: Analyze Differences**
```
7. Generate visual diff:
   python3 - <<'EOF'
   from PIL import Image, ImageChops, ImageEnhance
   import numpy as np

   baseline = Image.open("{baseline_preprocessed_path}").convert("RGB")
   preview = Image.open("{preview_path}").convert("RGB")

   # Resize to match
   if baseline.size != preview.size:
       preview = preview.resize(baseline.size, Image.Resampling.LANCZOS)

   # Create difference image
   diff = ImageChops.difference(baseline, preview)

   # Enhance for visibility
   enhancer = ImageEnhance.Brightness(diff)
   diff = enhancer.enhance(3.0)

   diff.save("{temp_dir}/diff-iteration-{N}.png")
   EOF

8. Analyze diff visually:
   diff_img = Read("{temp_dir}/diff-iteration-{N}.png")

   # Identify major differences:
   # - Color mismatches (show as bright areas in diff)
   # - Layout shifts (shape differences)
   # - Missing/extra elements
```

**Phase 3: Identify Root Causes**
```
9. Map visual differences to code issues:

   If header color wrong:
       → TopAppBarDefaults.topAppBarColors(containerColor = ...)

   If message bubble color wrong:
       → Surface(color = MaterialTheme.colorScheme.X)

   If spacing too tight/loose:
       → Modifier.padding() or Arrangement.spacedBy()

   If element alignment wrong:
       → Arrangement.Start/End/Center
       → Alignment.Start/End/CenterHorizontally

   If typography wrong:
       → MaterialTheme.typography.X
```

**Phase 4: Apply Refinements**
```
10. Make targeted edits:

    Edit(
        file_path = "{component_file}",
        old_string = """
            TopAppBar(
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary
                )
            )
        """,
        new_string = """
            TopAppBar(
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        """
    )

11. Verify compilation:
    ./gradlew compileDebugKotlin
```

**Phase 5: Report Progress**
```
12. Output iteration summary:

    Iteration {N} Complete
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Similarity: {similarity:.2%} (target: {realistic_target:.2%})
    Change: {similarity - previous_similarity:+.2%}

    Refinements applied:
    • Changed TopAppBar containerColor to surface (was primary)
    • Adjusted message padding: 16dp → 12dp

    Status: {similarity >= realistic_target ? "✅ TARGET REACHED" : "🔄 CONTINUE"}

13. If target reached:
    Output: <promise>VALIDATION COMPLETE</promise>
    (This signals ralph-wiggum loop to exit)
```

### Integration with preview-renderer

**Coordination pattern:**
```
code-refiner (iteration N):
    1. Edit code based on diff analysis
    2. Signal: "Preview needed for iteration {N+1}"
    3. WAIT for preview-renderer

preview-renderer:
    1. Build APK
    2. Deploy to device
    3. Capture screenshot
    4. Signal: "Preview ready at {path}"

code-refiner (iteration N+1):
    1. Load new preview
    2. Calculate similarity
    3. Continue refinement...
```

**This is handled by parent workflow** (not by agents directly):
```bash
# In commands/create.md workflow:

for iteration in 1..max_iterations; do
    # Code refinement iteration
    Task(
        subagent_type: "compose-designer:code-refiner",
        prompt: "Refine iteration $iteration"
    )

    # If target not reached, render preview
    if [ "$similarity" -lt "$realistic_target" ]; then
        Task(
            subagent_type: "compose-designer:preview-renderer",
            prompt: "Render preview for iteration $((iteration + 1))"
        )
    fi
done
```

### Ralph-Wiggum Integration

**Using Skill tool for loop control:**
```
# Start loop (from parent workflow):
Skill(
    skill: "ralph-wiggum:ralph-loop",
    args: "Refine {ComponentName} to match baseline. Target: {realistic_target:.0%} similarity. Max iterations: {max_iterations}. Output <promise>VALIDATION COMPLETE</promise> when target reached."
)

# Inside code-refiner:
if similarity >= realistic_target:
    Output: <promise>VALIDATION COMPLETE</promise>
elif iteration >= max_iterations:
    Output: """
    ⚠️ Max iterations reached

    Final similarity: {similarity:.1%}
    Target: {realistic_target:.1%}
    Gap: {realistic_target - similarity:.1%}

    The generated code is {similarity:.0%} accurate. Remaining differences:
    • {list top 3 differences from diff analysis}

    <promise>VALIDATION COMPLETE</promise>
    """
```

### Success Criteria

**Target reached:**
- ✅ Similarity >= realistic_target
- ✅ All major visual elements match
- ✅ Colors accurate
- ✅ Layout structure correct

**Acceptable (not target but good):**
- ✅ Similarity within 5% of target
- ✅ Only minor spacing differences remain
- ✅ No structural mismatches

**Unacceptable:**
- ❌ Similarity < 60% (indicates fundamental misunderstanding)
- ❌ Wrong layout structure (Column vs Row)
- ❌ Hardcoded colors instead of theme

### Error Handling

**SSIM calculation fails:**
```
❌ Similarity calculation failed

Error: {python_error}

Troubleshooting:
1. Verify scikit-image: pip3 install scikit-image
2. Check image files exist and are readable
3. Verify images have compatible formats

Continuing without similarity score (manual review required)...
```

**Code refinement makes things worse:**
```
⚠️ Similarity decreased: {prev:.1%} → {current:.1%}

Iteration {N} changes:
• {list changes made}

This suggests wrong diagnosis. Reverting...

git restore {component_file}

Trying alternative approach...
```

**Stuck (no progress for 2+ iterations):**
```
⚠️ No progress in {stalled_iterations} iterations

Current: {similarity:.1%}
Target: {realistic_target:.1%}
Gap: {gap:.1%}

Possible causes:
• Remaining differences are device rendering artifacts
• Missing assets (images, fonts) that can't be replicated
• Device frame or status bar in baseline

Recommend accepting current quality or manual refinement.

Continue trying? [y/N]:
```

---

## Section 6: Success Criteria and Graceful Degradation

### Overall Workflow Success Criteria

**Phase 1: Code Generation SUCCESS**
- ✅ Component file generated and compiles
- ✅ Uses MaterialTheme colors/typography (no hardcoded values)
- ✅ Stateless with callbacks
- ✅ Integrated with MainActivity OR test activity created
- ✅ Preview function with mock data

**Phase 2: Visual Validation SUCCESS**
- ✅ Similarity >= realistic_target (from preprocessing)
- ✅ Major structural elements match (layout, components)
- ✅ Colors accurate to design
- ✅ Completed within max_iterations

**Phase 2: Visual Validation ACCEPTABLE** (warning, not failure)
- ⚠️ Similarity within 5% of realistic_target
- ⚠️ Minor spacing/padding differences only
- ⚠️ Reached max_iterations but improvements made

**Phase 3: Device Testing SUCCESS**
- ✅ APK builds and installs successfully
- ✅ App launches without crashes
- ✅ All interactive elements respond (buttons, inputs, etc.)
- ✅ Visual similarity on device >= 85% of baseline

### Similarity Target Calculation

**Base target:** 92%

**Adjustments (baseline-preprocessor calculates):**
```python
realistic_target = 0.92

# Device frame present
if has_device_frame:
    realistic_target -= 0.15  # Down to 77%

# Composite layout (multiple screens)
if is_composite:
    realistic_target -= 0.10  # Down to 82% (or 67% if also has frame)

# Missing assets (images, stickers, custom fonts)
missing_asset_penalty = detected_missing_assets * 0.05
realistic_target -= missing_asset_penalty

# Floor at 60% (below this indicates fundamental mismatch)
realistic_target = max(0.60, realistic_target)

# Ceiling at 95% (perfect match is unrealistic due to rendering differences)
realistic_target = min(0.95, realistic_target)
```

**Examples:**
- Clean screenshot, no device frame: 92%
- Screenshot with device frame: 77%
- Figma frame with missing image assets (2): 82%
- Composite layout + device frame: 67%
- Complex design with 3 missing assets: 77%

### Graceful Degradation

#### ralph-wiggum Plugin Unavailable

**Detection:**
```bash
claude --help | grep -q "ralph-loop" || {
    echo "⚠️  ralph-wiggum plugin not found"
    RALPH_AVAILABLE=false
}
```

**Fallback:**
```
⚠️  Ralph-wiggum plugin not found

Visual validation requires iterative refinement.

Options:
1. Install ralph-wiggum:
   https://github.com/anthropics/ralph-wiggum-plugin

2. Manual refinement mode:
   I'll generate code, you review preview, I'll make improvements
   (Interactive, no auto-loop)

3. Skip validation:
   Accept generated code as-is (code quality only, no visual check)

What would you like to do? [1/2/3]:
```

**If user chooses Option 2 (Manual refinement):**
```
Manual Refinement Mode
━━━━━━━━━━━━━━━━━━━━━━━━━━

I've generated the initial code. Let's refine it iteratively:

Step 1: Review preview
• Build and run the app on your device
• Or use Android Studio preview
• Take a screenshot if using device

Step 2: Identify differences
• Compare with baseline design
• Note color, spacing, or layout differences

Step 3: Request improvements
• Tell me what to fix (e.g., "header should be white not purple")
• I'll update the code

Step 4: Repeat
• Review updated preview
• Continue until satisfied

Ready? [Y/n]:
```

#### mobile-mcp Plugin Unavailable

**Detection:**
```bash
claude --help | grep -q "mobile_list_available_devices" || {
    echo "⚠️  mobile-mcp plugin not found"
    MOBILE_MCP_AVAILABLE=false
}
```

**Fallback:**
```
⚠️  Mobile-mcp plugin not found

Device testing and preview rendering require mobile-mcp.

Options:
1. Install mobile-mcp:
   https://github.com/anthropics/mobile-ui-testing

2. Manual preview mode:
   • I'll generate code with Android Studio preview
   • You build and review in Android Studio
   • No device automation, no screenshots

3. Skip device operations:
   • Generate code only
   • You handle all testing

What would you like to do? [1/2/3]:
```

**If user chooses Option 2 (Manual preview):**
```
Manual Preview Mode
━━━━━━━━━━━━━━━━━━━━━━━━━

Generated: {ComponentName}

To preview:
1. Open Android Studio
2. Navigate to: {component_file}
3. Click preview panel (right side)
4. View {ComponentName}Preview composable

The preview function includes mock data and should render the design.

Note: Without device screenshots, I can't calculate similarity scores.
You'll need to manually compare the preview with your baseline design.

Would you like me to:
• Explain the generated code
• Make manual refinements based on your feedback
• Create the final report

What next? [explain/refine/report]:
```

#### No Android Devices Available

**Detection:**
```bash
devices=$(mobile_list_available_devices 2>/dev/null)
device_count=$(echo "$devices" | jq -r '.devices | length' 2>/dev/null || echo "0")

if [ "$device_count" -eq 0 ]; then
    echo "⚠️  No Android devices found"
    DEVICE_AVAILABLE=false
fi
```

**Fallback:**
```
⚠️  No Android devices or emulators found

Device testing requires a connected device or running emulator.

To connect a device:

Physical Device:
1. Enable Developer Options:
   Settings → About Phone → Tap "Build Number" 7 times
2. Enable USB Debugging:
   Settings → Developer Options → USB Debugging
3. Connect via USB and authorize computer

Emulator:
1. Open Android Studio
2. Tools → AVD Manager
3. Create/Start an emulator
4. Wait for boot (30-60 seconds)

Verify: adb devices

Options:
1. Wait for device (I'll retry in 30s)
2. Skip device testing (validation only, no runtime checks)
3. Abort workflow

What would you like to do? [1/2/3]:
```

#### Python Dependencies Missing

**Detection:**
```bash
python3 -c "import skimage, PIL, numpy" 2>/dev/null || {
    echo "❌ Required Python packages missing"
    PYTHON_DEPS_AVAILABLE=false
}
```

**Fallback:**
```
❌ Required Python packages missing

Visual similarity calculation requires:
• scikit-image (SSIM algorithm)
• Pillow (image processing)
• numpy (array operations)

Install:
pip3 install scikit-image pillow numpy

Or using conda:
conda install scikit-image pillow numpy

Options:
1. Install now (I'll wait)
2. Skip similarity calculation (generate code only, no visual validation)
3. Abort workflow

What would you like to do? [1/2/3]:
```

#### Compilation Failures

**Detection:**
```bash
./gradlew compileDebugKotlin 2>&1 | tee compile.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "❌ Compilation failed"
    COMPILE_ERROR=$(cat compile.log)
fi
```

**Fallback:**
```
❌ Generated code failed to compile

Error:
{compiler_error}

Common causes:
1. Missing theme files:
   → I can generate default theme files

2. Incorrect imports:
   → I can fix import statements

3. Type mismatches:
   → I can adjust data class properties

Options:
1. Auto-fix (I'll attempt to resolve the error)
2. Show generated code (for manual review)
3. Regenerate with different approach
4. Abort workflow

What would you like to do? [1/2/3/4]:
```

### Partial Success Scenarios

#### Generated Code Works, Validation Fails

**Scenario:** Code compiles and runs, but visual validation can't reach target.

**Status:** ⚠️ PARTIAL SUCCESS

**Report:**
```
⚠️  Visual Validation Incomplete

Code Generation: ✅ SUCCESS
• Component: ChatScreenScreen.kt (292 lines)
• Compiles: ✅ Yes
• Integrated: ✅ MainActivity updated
• Theme usage: ✅ MaterialTheme colors

Visual Validation: ⚠️ BELOW TARGET
• Final similarity: 68.5%
• Target: 77%
• Gap: 8.5%
• Iterations: 10/10 (max reached)

The generated code is structurally correct and follows best practices.
Remaining visual differences are likely:
• Minor spacing/padding adjustments (2-3%)
• Device rendering differences (2-3%)
• Missing assets (sticker image) (3-4%)

Options:
1. Accept current quality (68.5% is functional)
2. Manual refinement (I'll help improve specific areas)
3. Lower target to 68% and mark as success
4. Regenerate with different baseline

What would you like to do? [1/2/3/4]:
```

#### Validation Works, Device Testing Fails

**Scenario:** Visual validation succeeded, but device deployment fails.

**Status:** ⚠️ PARTIAL SUCCESS

**Report:**
```
⚠️  Device Testing Failed

Code Generation: ✅ SUCCESS
Visual Validation: ✅ SUCCESS (similarity: 89.2%)

Device Testing: ❌ FAILED
• Build: ✅ Success (2.1s)
• Install: ❌ Failed
• Error: INSTALL_FAILED_INSUFFICIENT_STORAGE

The generated code is high quality and visually validated.
Device deployment failed due to environment issues, not code problems.

Your generated component is ready to use:
• File: app/src/main/java/.../ChatScreenScreen.kt
• Quality: 4.5/5 stars
• Visual accuracy: 89.2%

To test manually:
1. Free up device storage
2. Run: ./gradlew installDebug
3. Or use Android Studio: Run → 'app'

Mark as complete? [Y/n]:
```

---

## Section 7: Agent Handoff Workflows

### Workflow Overview

```
┌──────────────────────────────────────────────────────────────┐
│                  compose-designer:create                      │
│                  (Main orchestrator skill)                    │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ├─► Phase 1: Preprocessing
                   │   ┌────────────────────────────────┐
                   │   │ baseline-preprocessor agent    │
                   │   │ Input: baseline.png            │
                   │   │ Output: baseline-preprocessed  │
                   │   │         preprocessing-report   │
                   │   └────────────────────────────────┘
                   │
                   ├─► Phase 2: Code Generation
                   │   ┌────────────────────────────────┐
                   │   │ design-generator agent         │
                   │   │ Input: baseline-preprocessed   │
                   │   │        preprocessing-report    │
                   │   │ Output: Component.kt           │
                   │   │         MainActivity updated   │
                   │   └────────────────────────────────┘
                   │
                   ├─► Phase 3: Visual Validation (Loop)
                   │   ┌────────────────────────────────┐
                   │   │ Ralph-wiggum loop coordinator  │
                   │   │                                │
                   │   │  ┌──────────────────────────┐ │
                   │   │  │ code-refiner iteration   │ │
                   │   │  │ - Analyze diff           │ │
                   │   │  │ - Edit code              │ │
                   │   │  │ - Check similarity       │ │
                   │   │  └──────────┬───────────────┘ │
                   │   │             │                  │
                   │   │             ↓ If not done      │
                   │   │  ┌──────────────────────────┐ │
                   │   │  │ preview-renderer         │ │
                   │   │  │ - Build APK              │ │
                   │   │  │ - Deploy to device       │ │
                   │   │  │ - Capture screenshot     │ │
                   │   │  └──────────┬───────────────┘ │
                   │   │             │                  │
                   │   │             ↓ Loop back        │
                   │   └─────────────────────────────────┘
                   │
                   └─► Phase 4: Device Testing
                       ┌────────────────────────────────┐
                       │ device-tester agent            │
                       │ Input: Component.kt            │
                       │        baseline-preprocessed   │
                       │ Output: device-screenshot      │
                       │         interaction-results    │
                       └────────────────────────────────┘
```

### Handoff 1: create → baseline-preprocessor

**Trigger:** User runs `/compose-design create --input {path} --name {Name} --type {type}`

**Orchestrator creates:**
```bash
# Create temp directory
temp_dir=$(mktemp -d /tmp/compose-designer.XXXXXX)

# Copy/download baseline
cp {input_path} "$temp_dir/baseline.png"

# Invoke baseline-preprocessor
Task(
    subagent_type: "compose-designer:baseline-preprocessor",
    description: "Preprocess baseline image",
    prompt: """
    Preprocess the baseline image at $temp_dir/baseline.png.

    Tasks:
    1. Detect device frames and crop to content area
    2. Handle composite layouts (ask user which screen if multiple)
    3. Calculate realistic similarity target based on complexity
    4. Save preprocessed baseline and report

    Output:
    • $temp_dir/baseline-preprocessed.png
    • $temp_dir/preprocessing-report.json
    """
)
```

**Agent returns:**
```json
{
    "status": "success",
    "baseline_preprocessed_path": "/tmp/compose-designer.v2aKn1/baseline-preprocessed.png",
    "preprocessing_report_path": "/tmp/compose-designer.v2aKn1/preprocessing-report.json",
    "report": {
        "has_device_frame": true,
        "is_composite": true,
        "selected_screen": "middle",
        "detected_missing_assets": 1,
        "realistic_similarity_target": 0.67,
        "content_dimensions": [1080, 2160],
        "notes": "Cropped middle screen from 3-screen composite. Device frame removed. Sticker image detected but cannot be replicated (similarity penalty applied)."
    }
}
```

### Handoff 2: create → design-generator

**Trigger:** Preprocessing complete

**Orchestrator reads report and invokes:**
```bash
# Read preprocessing report
report=$(cat "$temp_dir/preprocessing-report.json")
realistic_target=$(echo "$report" | jq -r '.realistic_similarity_target')

# Invoke design-generator
Task(
    subagent_type: "compose-designer:design-generator",
    description: "Generate Compose code",
    prompt: """
    Generate Jetpack Compose code for {Name} ({type}).

    Inputs:
    • Baseline: $temp_dir/baseline-preprocessed.png
    • Report: $temp_dir/preprocessing-report.json
    • Config: .claude/compose-designer.yaml

    Requirements:
    1. Analyze design and extract structure
    2. Generate component with MaterialTheme integration
    3. Update MainActivity or create test activity
    4. Verify compilation

    Expected similarity target: ${realistic_target}%

    Output:
    • app/src/main/java/{package}/ui/screens/{Name}Screen.kt
    • MainActivity.kt (updated) OR Test{Name}Activity.kt
    """
)
```

**Agent returns:**
```json
{
    "status": "success",
    "component_file": "app/src/main/java/com/test/composedesigner/ui/screens/ChatScreenScreen.kt",
    "integration": "mainactivity_updated",
    "mainactivity_file": "app/src/main/java/com/test/composedesigner/MainActivity.kt",
    "data_classes": [
        "app/src/main/java/com/test/composedesigner/ui/model/ChatMessage.kt"
    ],
    "lines_of_code": 292,
    "compilation_successful": true,
    "notes": "Generated chat screen with message bubbles, input bar, and mock data. Integrated with MainActivity."
}
```

### Handoff 3: create → Ralph-wiggum Loop (code-refiner + preview-renderer)

**Trigger:** Code generation complete

**Orchestrator sets up loop:**
```bash
# Start ralph-wiggum loop
Skill(
    skill: "ralph-wiggum:ralph-loop",
    args: """
    Refine {ComponentName} to match baseline design.
    Target: ${realistic_target}% similarity.
    Max iterations: ${max_iterations}.

    Output <promise>VALIDATION COMPLETE</promise> when target reached.
    """
)

# Inside the loop (managed by ralph-wiggum):
iteration=1
while [ $iteration -le $max_iterations ]; do
    # Step 1: Code refinement
    Task(
        subagent_type: "compose-designer:code-refiner",
        description: "Refine code iteration $iteration",
        prompt: """
        Iteration $iteration: Refine code to match baseline.

        Inputs:
        • Component: {component_file}
        • Baseline: $temp_dir/baseline-preprocessed.png
        • Previous preview: $temp_dir/preview-iteration-$((iteration-1)).png
        • Target: ${realistic_target}%

        Tasks:
        1. Calculate similarity with baseline
        2. Analyze visual differences
        3. Identify code changes needed
        4. Apply targeted edits
        5. Report progress

        If similarity >= target:
            Output: <promise>VALIDATION COMPLETE</promise>
        """
    )

    # Get similarity from code-refiner
    similarity=$(cat "$temp_dir/similarity-iteration-$iteration.txt")

    # Check if target reached
    if (( $(echo "$similarity >= $realistic_target" | bc -l) )); then
        echo "✅ Target reached: ${similarity}%"
        break
    fi

    # Step 2: Render preview for next iteration
    if [ $iteration -lt $max_iterations ]; then
        Task(
            subagent_type: "compose-designer:preview-renderer",
            description: "Render preview iteration $((iteration+1))",
            prompt: """
            Render preview for iteration $((iteration+1)).

            Inputs:
            • Component: {component_file} (updated by code-refiner)
            • Config: .claude/compose-designer.yaml

            Tasks:
            1. Build debug APK
            2. Deploy to device: ${device_id}
            3. Launch app
            4. Capture screenshot

            Output:
            • $temp_dir/preview-iteration-$((iteration+1)).png
            """
        )
    fi

    iteration=$((iteration + 1))
done
```

**code-refiner returns (each iteration):**
```json
{
    "iteration": 3,
    "similarity": 0.7234,
    "similarity_change": 0.0312,
    "refinements_applied": [
        "Changed TopAppBar containerColor from primary to surface",
        "Adjusted message bubble padding: 16dp → 12dp",
        "Fixed timestamp alignment to End"
    ],
    "status": "continue",
    "notes": "Similarity improved by 3.1%. Header now white instead of purple. Still 4.7% from target."
}
```

**preview-renderer returns (each iteration):**
```json
{
    "iteration": 4,
    "screenshot_path": "/tmp/compose-designer.v2aKn1/preview-iteration-4.png",
    "device_id": "emulator-5554",
    "device_name": "Pixel 8 Pro API 34",
    "build_time_seconds": 2.3,
    "apk_size_mb": 7.7,
    "status": "success"
}
```

**Final code-refiner output (when target reached):**
```json
{
    "iteration": 5,
    "similarity": 0.7701,
    "similarity_change": 0.0467,
    "refinements_applied": [
        "Increased message bubble width constraint to 280dp"
    ],
    "status": "complete",
    "completion_promise": "<promise>VALIDATION COMPLETE</promise>",
    "notes": "Target reached! Similarity: 77.0% (target: 77.0%). Ralph loop will exit."
}
```

### Handoff 4: create → device-tester

**Trigger:** Visual validation complete (ralph-wiggum loop exited)

**Orchestrator invokes:**
```bash
# Invoke device-tester
Task(
    subagent_type: "compose-designer:device-tester",
    description: "Test on device",
    prompt: """
    Test {ComponentName} on Android device.

    Inputs:
    • Component: {component_file}
    • Baseline: $temp_dir/baseline-preprocessed.png
    • Device: ${device_id}
    • Config: .claude/compose-designer.yaml

    Tasks:
    1. Build and install final APK
    2. Launch and capture screenshot
    3. Test interactive elements:
       - Text input field
       - Send button
       - Scroll behavior
       - Icon buttons
    4. Compare device screenshot with baseline
    5. Report results

    Output:
    • $temp_dir/device-screenshot.png
    • $temp_dir/interaction-results.json
    """
)
```

**Agent returns:**
```json
{
    "status": "success",
    "device_screenshot_path": "/tmp/compose-designer.v2aKn1/device-screenshot.png",
    "device_similarity": 0.7645,
    "build_time_seconds": 2.1,
    "apk_size_mb": 7.7,
    "interactions_tested": [
        {
            "element": "message_input_field",
            "action": "type_text",
            "result": "pass",
            "notes": "Text input responsive, keyboard appeared"
        },
        {
            "element": "send_button",
            "action": "click",
            "result": "pass",
            "notes": "Button clicked, empty callback executed"
        },
        {
            "element": "message_list",
            "action": "scroll",
            "result": "warning",
            "notes": "List scrollable but too short to fully test"
        }
    ],
    "interactions_passed": 2,
    "interactions_total": 3,
    "notes": "Device testing successful. Minor warning on scroll test (list too short). Component functions correctly."
}
```

### Final Report Generation

**Orchestrator compiles all results:**
```bash
# Compile final report
cat > "$temp_dir/FINAL_REPORT.md" <<EOF
# Compose Designer Plugin - Execution Report

**Date:** $(date +%Y-%m-%d)
**Component:** {ComponentName}
**Status:** ✅ COMPLETED

## Phase 0: Baseline Preprocessing
$(cat "$temp_dir/preprocessing-report.json" | jq -r '.notes')
• Target similarity: ${realistic_target}%
• Baseline: $temp_dir/baseline-preprocessed.png

## Phase 1: Code Generation
• Component: {component_file}
• Lines of code: ${loc}
• Integration: ${integration_method}
• Compilation: ✅ Success

## Phase 2: Visual Validation
• Method: Ralph-wiggum iterative loop
• Iterations: ${iterations_completed}/${max_iterations}
• Final similarity: ${final_similarity}%
• Status: ${validation_status}

## Phase 3: Device Testing
• Device: ${device_name}
• Device similarity: ${device_similarity}%
• Interactions: ${passed}/${total} passed
• Status: ${device_status}

## Generated Files
• {component_file}
• {mainactivity_file}
• $temp_dir/baseline-preprocessed.png
• $temp_dir/preview-iteration-*.png
• $temp_dir/device-screenshot.png

## Next Steps
[ ] Review generated code
[ ] Integrate into feature module
[ ] Add ViewModel/state management
[ ] Connect callbacks to business logic
EOF

# Display report
cat "$temp_dir/FINAL_REPORT.md"
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
1. Create `agents/baseline-preprocessor.md` with full workflow
2. Update `.claude-plugin/plugin.json` to register 4 agents
3. Test preprocessing with various baseline types
4. Validate realistic similarity calculation

### Phase 2: Code Generation (Week 2)
1. Enhance `agents/design-generator.md` with MainActivity integration
2. Add Option A/B logic for test activity creation
3. Test with different project structures
4. Validate compilation and integration

### Phase 3: Visual Validation Split (Week 3)
1. Create `agents/preview-renderer.md` with mobile-mcp tools
2. Create `agents/code-refiner.md` with ralph-wiggum integration
3. Update `commands/create.md` to coordinate both agents
4. Test ralph-wiggum loop with realistic targets

### Phase 4: Device Testing (Week 4)
1. Update `agents/device-tester.md` to focus on testing only
2. Remove preview rendering from device-tester
3. Test end-to-end workflow with all 4 agents
4. Validate graceful degradation scenarios

### Phase 5: Documentation and Release (Week 5)
1. Update README.md with new architecture
2. Add troubleshooting guide
3. Create migration guide for v0.1.2 → v0.2.0 users
4. Release v0.2.0 to marketplace

---

## Appendix: Comparison

### v0.1.2 (Current)

**Agents:** 3
- design-generator (code only, no integration)
- visual-validator (can't render, wrong tools)
- device-tester (did visual-validator's job)

**Success rate:** ~60% (manual fixes required)
**Similarity targets:** 92% (unrealistic)
**Agent autonomy:** Low (manual steps needed)

### v0.2.0 (Proposed)

**Agents:** 4
- baseline-preprocessor (new)
- design-generator (enhanced, integrates with MainActivity)
- preview-renderer (new, mobile-mcp tools)
- code-refiner (new, ralph-wiggum loop)

**Success rate:** ~90% (fully autonomous)
**Similarity targets:** 60-95% (realistic, baseline-dependent)
**Agent autonomy:** High (graceful degradation when tools missing)

---

## Next Steps

1. **Review this design document** - Does the 4-agent architecture solve all critical issues?
2. **Begin implementation** - Start with baseline-preprocessor agent
3. **Test incrementally** - Validate each agent before moving to next
4. **Update marketplace** - Release v0.2.0 when complete

**Document Status:** READY FOR REVIEW
**Estimated Implementation Time:** 4-5 weeks
**Breaking Changes:** Yes (command interface unchanged, but internal workflow different)
