# Visual Validation Task

Compare the device screenshot against the design baseline to determine if the implementation matches the design intent.

## Images
- **Design Baseline**: {baseline_image}
- **Device Screenshot**: {screenshot_image}
- **Component Name**: {component_name}

## Evaluation Criteria

### 1. Layout Structure (Critical)
- Are elements positioned correctly relative to each other?
- Is the visual hierarchy preserved?
- Are nested containers structured properly?

### 2. Typography (Important)
- Are font sizes approximately correct?
- Is font weight (bold/regular) correct?
- Is text alignment correct?

### 3. Colors & Theming (Important)
- Do colors match or align with Material theme conventions?
- Are accent colors in the right places?
- Is contrast appropriate?

### 4. Spacing (Moderate)
- Are margins and padding approximately correct?
- Is element spacing consistent?
- Minor pixel differences are acceptable.

### 5. Content Completeness (Critical)
- Is all visible content from the design present?
- Are icons/images in correct positions?
- Is text content accurate?

## Acceptable Differences
- Minor pixel variations (±5px)
- Platform-specific rendering (antialiasing, shadows)
- Material theme color adaptation
- System font substitution
- Status bar / navigation bar differences

## Response Format

Respond with EXACTLY this JSON structure:

```json
{
  "status": "PASS | ITERATE | STUCK",
  "confidence": "HIGH | MEDIUM | LOW",
  "summary": "One sentence overall assessment",
  "issues": [
    {
      "severity": "critical | important | minor",
      "category": "layout | typography | colors | spacing | content",
      "description": "Specific issue description",
      "fix": "Exact code change to make"
    }
  ],
  "reasoning": "If STUCK, explain why this cannot be fixed with code changes"
}
```

### Status Definitions
- **PASS**: Implementation matches design intent. Minor acceptable differences only.
- **ITERATE**: Fixable issues found. Apply suggested fixes and re-validate.
- **STUCK**: Fundamental mismatch that cannot be resolved with code changes (e.g., missing assets, wrong design reference).

### Confidence Levels
- **HIGH**: Clear assessment, obvious match or mismatch
- **MEDIUM**: Some ambiguity, but reasonable judgment made
- **LOW**: Difficult to assess, may need human review
