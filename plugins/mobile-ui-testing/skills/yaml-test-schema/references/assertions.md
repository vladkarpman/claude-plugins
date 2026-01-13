# YAML Test Assertions Reference

Complete reference for verification and assertion actions in YAML mobile tests.

## Screen Verification

### Basic Screen Verification
```yaml
- verify_screen: "Expected screen state description"
```
Takes a screenshot and uses AI to verify the screen matches the expectation.

### Verification with Options
```yaml
- verify_screen:
    expectation: "Home screen with user profile visible"
    strictness: strict  # strict, normal, or lenient
    timeout: 10s        # Optional: wait for condition
```

**Strictness levels:**
- `strict` - Exact match required, fails on minor differences
- `normal` (default) - Reasonable match, tolerates minor UI variations
- `lenient` - Loose match, only checks key elements mentioned

## Element Verification

### Verify Element Exists
```yaml
- verify_contains: "Element text"
- verify_contains: ["Element 1", "Element 2", "Element 3"]
```
Checks that element(s) with given text/description exist on screen.

### Verify Element Does Not Exist
```yaml
- verify_no_element: "Error message"
- verify_no_element: ["Error", "Warning", "Failed"]
```
Ensures specified element(s) are NOT present on screen.

### Verify Element State
```yaml
- verify_element:
    text: "Submit"
    enabled: true       # Check if clickable
    visible: true       # Check if visible
    selected: false     # Check if selected/checked
```

## Text Verification

### Verify Text Content
```yaml
- verify_text:
    element: "Price label"
    contains: "$"       # Text contains substring
```

```yaml
- verify_text:
    element: "Status"
    equals: "Complete"  # Exact text match
```

```yaml
- verify_text:
    element: "Count"
    matches: "\\d+ items"  # Regex pattern
```

## Count Verification

### Verify Element Count
```yaml
- verify_count:
    element: "List item"
    equals: 5           # Exactly 5 items
```

```yaml
- verify_count:
    element: "Card"
    min: 3              # At least 3
    max: 10             # At most 10
```

## Comparison Assertions

### Value Comparisons
```yaml
- verify_value:
    element: "Progress"
    greater_than: 50
    less_than: 100
```

## Mobile-MCP Tool Mapping

| YAML Assertion | mobile-mcp Tools |
|----------------|------------------|
| `verify_screen` | `mobile_take_screenshot` + AI analysis |
| `verify_contains` | `mobile_list_elements_on_screen` + check presence |
| `verify_no_element` | `mobile_list_elements_on_screen` + check absence |
| `verify_element` | `mobile_list_elements_on_screen` + property check |
| `verify_text` | `mobile_list_elements_on_screen` + text extraction |
| `verify_count` | `mobile_list_elements_on_screen` + count elements |

## Assertion Behavior

### On Failure
When an assertion fails:
1. Screenshot is captured automatically
2. Test is marked as FAILED
3. Error message includes expected vs actual
4. Subsequent steps in the test are skipped
5. Teardown still runs

### Timeouts
Default assertion timeout is 5 seconds. Override per assertion:
```yaml
- verify_contains:
    element: "Success"
    timeout: 30s
```

## Best Practices

1. **Use descriptive expectations** - "Home screen with tabs" vs "Home"
2. **Start with lenient strictness** - Tighten as needed
3. **Verify key elements** - Don't over-specify
4. **Add timeouts for async content** - API responses, animations
5. **Screenshot before complex verifications** - Helps debugging
