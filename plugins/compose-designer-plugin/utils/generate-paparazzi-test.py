#!/usr/bin/env python3
"""
Paparazzi test generator for compose-designer plugin.
Generates Kotlin test files for Paparazzi snapshot testing.

Usage:
  python3 generate-paparazzi-test.py \\
    --component JetNewsCardComponent \\
    --preview JetNewsCardComponentPreview \\
    --output test-harness/src/test/kotlin/generated \\
    --device-config PIXEL_5

Note:
  The generated test assumes the component is copied to the test harness
  with package "generated", so no import is needed for the preview function.

Returns:
  Path to generated test file printed to stdout

Requirements:
  Python 3.7+
"""

import sys
import argparse
import re
from pathlib import Path

# Valid Paparazzi DeviceConfig values
VALID_DEVICE_CONFIGS = [
    "NEXUS_4",
    "NEXUS_5",
    "NEXUS_5_LAND",
    "NEXUS_7",
    "NEXUS_7_2012",
    "NEXUS_9",
    "NEXUS_10",
    "PIXEL",
    "PIXEL_XL",
    "PIXEL_2",
    "PIXEL_2_XL",
    "PIXEL_3",
    "PIXEL_3_XL",
    "PIXEL_3A",
    "PIXEL_3A_XL",
    "PIXEL_4",
    "PIXEL_4_XL",
    "PIXEL_4A",
    "PIXEL_5",
    "PIXEL_6",
    "PIXEL_6_PRO",
    "PIXEL_C",
]

# Template for the generated test file
# Note: Component is copied to test-harness/src/main/kotlin/generated/ with package "generated"
# Both test and component are in the same package, so no import needed for preview function
TEST_TEMPLATE = '''package generated

import app.cash.paparazzi.DeviceConfig
import app.cash.paparazzi.Paparazzi
import org.junit.Rule
import org.junit.Test

class {component_name}Test {{
    @get:Rule
    val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.{device_config}
    )

    @Test
    fun snapshot() {{
        paparazzi.snapshot {{
            {preview_function}()
        }}
    }}
}}
'''


def is_valid_kotlin_identifier(name: str) -> bool:
    """
    Check if a string is a valid Kotlin identifier.

    Rules:
    - Must start with a letter or underscore
    - Can contain letters, digits, and underscores
    - Cannot be a Kotlin keyword (simplified check)
    """
    if not name:
        return False

    # Check for spaces
    if ' ' in name:
        return False

    # Must start with letter or underscore
    if not re.match(r'^[a-zA-Z_]', name):
        return False

    # Can only contain letters, digits, underscores
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return False

    # Common Kotlin keywords (simplified list)
    kotlin_keywords = {
        'as', 'break', 'class', 'continue', 'do', 'else', 'false', 'for',
        'fun', 'if', 'in', 'interface', 'is', 'null', 'object', 'package',
        'return', 'super', 'this', 'throw', 'true', 'try', 'typealias',
        'typeof', 'val', 'var', 'when', 'while'
    }
    if name.lower() in kotlin_keywords:
        return False

    return True


def generate_test_file(
    component_name: str,
    preview_function: str,
    output_dir: Path,
    device_config: str
) -> Path:
    """
    Generate a Paparazzi test file.

    Args:
        component_name: Name of the component (e.g., "JetNewsCardComponent")
        preview_function: Name of the @Preview function
        output_dir: Output directory for the test file
        device_config: Paparazzi device configuration

    Returns:
        Path to the generated test file

    Note:
        The generated test assumes the component is copied to the test harness
        with package "generated", so both test and component share the same package.
    """
    # Generate the test content
    content = TEST_TEMPLATE.format(
        component_name=component_name,
        preview_function=preview_function,
        device_config=device_config
    )

    # Create output file path
    output_file = output_dir / f"{component_name}Test.kt"

    # Write the file
    try:
        output_file.write_text(content)
        return output_file
    except IOError as e:
        print(f"Error: Failed to write test file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Generate Paparazzi snapshot test files for Compose components',
        epilog='Example: python3 generate-paparazzi-test.py --component MyButton --preview MyButtonPreview'
    )
    parser.add_argument(
        '--component',
        required=True,
        help='Name of the component (e.g., JetNewsCardComponent)'
    )
    parser.add_argument(
        '--preview',
        required=True,
        help='Name of the @Preview function (e.g., JetNewsCardComponentPreview)'
    )
    parser.add_argument(
        '--output',
        default='test-harness/src/test/kotlin/generated',
        help='Output directory for the test file (default: test-harness/src/test/kotlin/generated)'
    )
    parser.add_argument(
        '--device-config',
        default='PIXEL_5',
        help='Paparazzi device config (default: PIXEL_5)'
    )

    args = parser.parse_args()

    # Validate component name
    if not is_valid_kotlin_identifier(args.component):
        print(f"Error: Invalid component name: '{args.component}'", file=sys.stderr)
        print("Component name must be a valid Kotlin identifier (no spaces, starts with letter or underscore)", file=sys.stderr)
        sys.exit(1)

    # Validate preview function name
    if not is_valid_kotlin_identifier(args.preview):
        print(f"Error: Invalid preview function name: '{args.preview}'", file=sys.stderr)
        print("Preview function name must be a valid Kotlin identifier", file=sys.stderr)
        sys.exit(1)

    # Validate device config
    if args.device_config not in VALID_DEVICE_CONFIGS:
        print(f"Error: Invalid device config: '{args.device_config}'", file=sys.stderr)
        print(f"Valid options: {', '.join(VALID_DEVICE_CONFIGS)}", file=sys.stderr)
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error: Failed to create output directory: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate the test file
    output_path = generate_test_file(
        component_name=args.component,
        preview_function=args.preview,
        output_dir=output_dir,
        device_config=args.device_config
    )

    # Print success message
    print(f"Generated: {output_path}")

    sys.exit(0)


if __name__ == '__main__':
    main()
