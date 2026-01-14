# Visual Validation Redesign

**Date:** 2026-01-14
**Status:** Design Complete

## Problem

Current visual validation approach has issues:
- Preview rendering via Gradle is complex and unreliable
- SSIM alone doesn't provide actionable feedback
- Figma MCP not fully utilized for precise token extraction

## Solution: Device-Centric Validation with Dual Comparison

### Architecture

```
Input (Screenshot OR Figma URL)
         │
         ▼
┌─────────────────────────────────┐
│  Figma Path: Extract tokens    │  ← Figma MCP advantage
│  via get_design_context,       │
│  get_variable_defs             │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Code Generation               │
│  • Figma: precise values       │
│  • Screenshot: LLM interprets  │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Device Validation Loop        │
│  • Build APK → deploy          │
│  • mobile-mcp screenshot       │
│  • SSIM score (threshold)      │
│  • LLM vision (what to fix)    │
│  • Refine until ≥92%           │
└─────────────────────────────────┘
```

### Key Decisions

1. **Device-centric validation** - Skip preview rendering, go straight to device
2. **Dual comparison** - SSIM for threshold check, LLM vision for semantic feedback
3. **Figma MCP integration** - Extract precise tokens when Figma URL provided
4. **Merged phases** - Combine visual validation + device testing into single loop

## Input Flows

### Screenshot Input

1. **Preprocess**: Detect device frame, crop to content area
2. **Generate**: LLM vision interprets colors/spacing (~60-70% accuracy)
3. **Validate**: Deploy to same device type, SSIM + LLM vision loop

### Figma Input

1. **Extract via Figma MCP**:
   - `get_design_context` → component tree
   - `get_variable_defs` → exact color/spacing tokens
   - `get_screenshot` → visual baseline
2. **Generate**: Use EXACT values from tokens (~80-85% accuracy)
3. **Validate**: Fewer iterations needed due to precise starting point

## Validation Loop

```
iteration = 0
max_iterations = 8

while iteration < max_iterations:
    # Build and deploy
    build_apk()
    install_and_launch()

    # Screenshot device
    current = mobile_take_screenshot()

    # Dual comparison
    score = ssim_compare(baseline, current)
    feedback = llm_vision_compare(baseline, current)

    if score >= 0.92:
        return SUCCESS

    # Detect stuck (no progress)
    if no_progress_for_3_iterations:
        return STUCK  # Ask user

    # Apply targeted fixes
    apply_fixes(feedback)
    iteration += 1
```

## LLM Vision Feedback Format

```json
{
  "differences": [
    {"element": "title", "issue": "font size", "current": "18sp", "expected": "20sp"},
    {"element": "card", "issue": "corner radius", "current": "8dp", "expected": "12dp"},
    {"element": "button", "issue": "padding", "current": "12dp", "expected": "16dp"}
  ]
}
```

## Error Handling

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| No device | Empty device list | Prompt user (already implemented) |
| Build fails | Gradle exit ≠ 0 | Show error, ask to fix |
| SSIM stuck | 3+ iterations no progress | Stop, show diff, ask user |
| Figma token invalid | API 403 | Fallback to screenshot mode |
| Device disconnected | mobile-mcp error | Retry connection |

## Implementation Changes

### Files to Modify

1. **`agents/visual-validator.md`** - Major rewrite
   - Remove preview rendering
   - Add device deployment via mobile-mcp
   - Add SSIM + LLM vision dual comparison
   - Add targeted fix application

2. **`agents/design-generator.md`** - Enhancement
   - Add Figma MCP calls when URL provided
   - Extract tokens before generation
   - Use precise values in code

3. **`commands/create.md`** - Flow update
   - Merge Phase 2 & 3 into single device validation loop
   - Simplify workflow

### New Components

1. **LLM Vision Comparison**
   - Compare two images semantically
   - Output structured differences
   - Provide actionable fix suggestions

2. **Figma Token Extraction**
   - Call Figma MCP tools
   - Parse response into usable values
   - Pass to code generation

## Already Working

- Device selection via mobile-mcp
- Device screenshots
- APK install/launch
- Figma URL parsing (fixed 2026-01-14)
- Figma token authentication
- SSIM calculation via image-similarity.py

## Success Criteria

- Screenshots: Achieve 92%+ SSIM within 8 iterations
- Figma: Achieve 92%+ SSIM within 4-5 iterations (due to precise tokens)
- Clear feedback when stuck, actionable user intervention points
