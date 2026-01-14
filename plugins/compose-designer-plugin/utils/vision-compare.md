# Vision Compare Utility

Compare two UI images and return structured differences.

## Usage

Called by visual-validator agent with two image paths.

## Prompt Template

You are comparing a baseline design image against a current device screenshot.

Analyze both images and identify specific differences in:
- Colors (hex values if possible)
- Spacing/padding (use dp units)
- Font sizes (use sp units)
- Corner radius (use dp units)
- Layout alignment
- Missing or extra elements

**Similarity Assessment Criteria:**
- **high**: Minor refinements needed (< 2% visual difference)
- **medium**: 2-3 fixes needed (2-8% visual difference)
- **low**: Major rework required (> 8% visual difference)

**Output Limit:** List up to 10 most impactful differences, ordered by visual impact.

Return a JSON object:

```json
{
  "similarity_assessment": "high|medium|low",
  "differences": [
    {
      "element": "element name or description",
      "property": "color|spacing|fontSize|cornerRadius|alignment|other",
      "baseline": "value in baseline",
      "current": "value in current screenshot",
      "fix": "specific Kotlin code change suggestion"
    }
  ],
  "priority_fixes": ["list of most impactful fixes to try first"]
}
```

**Error Response:** If images cannot be compared (missing, corrupted, or incompatible formats):

```json
{
  "error": true,
  "message": "Description of why comparison failed",
  "similarity_assessment": null,
  "differences": [],
  "priority_fixes": []
}
```

Be specific. Instead of "colors are different", say "button background is #FFFFFF in baseline but #F5F5F5 in current".

## Example Output

```json
{
  "similarity_assessment": "medium",
  "differences": [
    {
      "element": "Primary button",
      "property": "color",
      "baseline": "#6200EE",
      "current": "#3700B3",
      "fix": "Change `containerColor = Color(0xFF3700B3)` to `containerColor = Color(0xFF6200EE)`"
    },
    {
      "element": "Card title",
      "property": "fontSize",
      "baseline": "18sp",
      "current": "16sp",
      "fix": "Change `fontSize = 16.sp` to `fontSize = 18.sp`"
    },
    {
      "element": "Content padding",
      "property": "spacing",
      "baseline": "16dp",
      "current": "12dp",
      "fix": "Change `padding = 12.dp` to `padding = 16.dp`"
    },
    {
      "element": "Avatar image",
      "property": "cornerRadius",
      "baseline": "50% (circular)",
      "current": "8dp",
      "fix": "Change `RoundedCornerShape(8.dp)` to `CircleShape`"
    }
  ],
  "priority_fixes": [
    "Fix button color mismatch - most visually prominent",
    "Correct content padding for proper layout spacing",
    "Update card title font size for typography consistency"
  ]
}
```
