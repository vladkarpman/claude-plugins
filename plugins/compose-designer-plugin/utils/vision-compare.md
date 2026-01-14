# Vision Compare Utility

Compare two UI images and return structured differences.

## Usage

Called by visual-validator agent with two image paths.

## Prompt Template

You are comparing a baseline design image against a current device screenshot.

Analyze both images and identify specific differences in:
- Colors (hex values if possible)
- Spacing/padding (in dp)
- Font sizes (in sp)
- Corner radius (in dp)
- Layout alignment
- Missing or extra elements

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
      "fix": "specific code change suggestion"
    }
  ],
  "priority_fixes": ["list of most impactful fixes to try first"]
}
```

Be specific. Instead of "colors are different", say "button background is #FFFFFF in baseline but #F5F5F5 in current".
