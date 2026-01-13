# Compose Designer Examples

Example design files for testing the compose-designer plugin.

## Test Designs

### Simple Button (`button-example.png`)

A basic button design for testing component generation.

**Usage:**
```bash
/compose-design create --input examples/button-example.png --name TestButton --type component
```

**Expected Output:**
- `TestButtonComponent.kt` with Button composable
- Simple mock data
- Preview function

### Profile Card (`card-example.png`)

A card layout with image, text, and button elements.

**Usage:**
```bash
/compose-design create --input examples/card-example.png --name ProfileCard --type component
```

**Expected Output:**
- `ProfileCardComponent.kt` with Card composable
- Row/Column layout
- Image, text, and button elements
- Realistic mock data

## Creating Your Own Test Designs

### Best Practices

1. **Clear Visual Hierarchy**
   - Well-defined layout structure
   - Clear spacing between elements
   - Obvious element types (buttons, text, etc.)

2. **Standard Colors**
   - Use Material Design colors when possible
   - Clear contrast between elements
   - Avoid overly complex gradients

3. **Readable Text**
   - Sufficient size for OCR
   - Clear font weights
   - No distorted or stylized fonts

4. **Proper Format**
   - PNG or JPG format
   - Minimum 400px width
   - Clear, non-blurry screenshot

### Figma Integration

For best results with Figma:

1. **Create Figma Frame**
   - Use Auto Layout for precise spacing
   - Define colors in Styles
   - Use Text Styles for typography

2. **Get Node URL**
   - Right-click frame → "Copy link to selection"
   - URL format: `https://www.figma.com/file/...?node-id=...`

3. **Set Up Token**
   ```bash
   export FIGMA_TOKEN="your-token-here"
   ```

4. **Generate**
   ```bash
   /compose-design create --input "figma-url" --name Component --type component
   ```

## Testing Workflow

### End-to-End Test

```bash
# 1. Initialize config
/compose-design config

# 2. Generate from example
/compose-design create --input examples/button-example.png --name TestButton --type component

# 3. Review generated code
cat app/src/main/java/.../TestButtonComponent.kt

# 4. Check validation artifacts
ls -la /tmp/compose-designer/*/

# 5. Test in app
# Add to your activity:
# TestButtonComponent(text = "Click Me", onClick = {})
```

### Batch Test

```bash
# Process all examples at once
/compose-design create --input examples/ --batch
```

## Adding New Examples

To contribute new example designs:

1. Create clear, focused design mockup
2. Save as PNG in `examples/`
3. Name descriptively: `{element}-{variant}.png`
4. Add description to this README
5. Test generation: `/compose-design create --input examples/your-design.png --name YourComponent --type component`

## Troubleshooting Examples

**Generated code doesn't match design:**
- Check if design is clear and unambiguous
- Verify colors are distinct
- Ensure text is readable
- Try adjusting similarity threshold in config

**Validation fails:**
- Design may be too complex for Compose
- Preview rendering might differ from screenshot
- Lower similarity threshold or accept manual refinement

**Device test fails:**
- Check theme is applied in test activity
- Verify resources exist (colors, icons)
- Test on different device/emulator
