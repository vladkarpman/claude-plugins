#!/usr/bin/env python3
"""
Image similarity calculator for compose-designer plugin.
Uses SSIM (Structural Similarity Index) to compare images.

Usage:
  python3 image-similarity.py baseline.png preview.png [--output diff.png]

Returns:
  Similarity score (0.0 to 1.0) printed to stdout

Requirements:
  pip3 install scikit-image pillow numpy
"""

import sys
import argparse
import json
from pathlib import Path

try:
    from skimage.metrics import structural_similarity as ssim
    from PIL import Image
    import numpy as np
except ImportError as e:
    print(f"Error: Required package not installed: {e}", file=sys.stderr)
    print("Install with: pip3 install scikit-image pillow numpy", file=sys.stderr)
    sys.exit(1)


def calculate_similarity(baseline_path, preview_path, output_diff_path=None):
    """
    Calculate SSIM between two images.

    Args:
        baseline_path: Path to baseline/reference image
        preview_path: Path to preview/test image
        output_diff_path: Optional path to save difference image

    Returns:
        float: Similarity score (0.0 to 1.0)
    """
    try:
        # Load images
        baseline = Image.open(baseline_path)
        preview = Image.open(preview_path)

        # Convert to RGB if needed
        if baseline.mode != 'RGB':
            baseline = baseline.convert('RGB')
        if preview.mode != 'RGB':
            preview = preview.convert('RGB')

        # Resize preview to match baseline dimensions
        if baseline.size != preview.size:
            print(f"Resizing preview from {preview.size} to {baseline.size}", file=sys.stderr)
            preview = preview.resize(baseline.size, Image.Resampling.LANCZOS)

        # Convert to numpy arrays
        baseline_arr = np.array(baseline)
        preview_arr = np.array(preview)

        # Calculate SSIM
        score, diff_image = ssim(
            baseline_arr,
            preview_arr,
            multichannel=True,
            channel_axis=2,
            full=True
        )

        # Generate diff visualization if requested
        if output_diff_path:
            # Calculate absolute pixel difference
            abs_diff = np.abs(baseline_arr.astype(float) - preview_arr.astype(float))

            # Enhance differences for visibility (multiply by 3, cap at 255)
            enhanced_diff = (abs_diff * 3).clip(0, 255).astype(np.uint8)

            # Save diff image
            diff_img = Image.fromarray(enhanced_diff)
            diff_img.save(output_diff_path)
            print(f"Diff image saved: {output_diff_path}", file=sys.stderr)

        return score

    except FileNotFoundError as e:
        print(f"Error: Image file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error calculating similarity: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Calculate image similarity using SSIM algorithm',
        epilog='Example: python3 image-similarity.py baseline.png preview.png --output diff.png'
    )
    parser.add_argument('baseline', help='Path to baseline/reference image')
    parser.add_argument('preview', help='Path to preview/test image')
    parser.add_argument(
        '--output', '-o',
        help='Path to save difference visualization (optional)',
        default=None
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output result as JSON'
    )

    args = parser.parse_args()

    # Validate inputs
    baseline_path = Path(args.baseline)
    preview_path = Path(args.preview)

    if not baseline_path.exists():
        print(f"Error: Baseline image not found: {baseline_path}", file=sys.stderr)
        sys.exit(1)

    if not preview_path.exists():
        print(f"Error: Preview image not found: {preview_path}", file=sys.stderr)
        sys.exit(1)

    # Calculate similarity
    score = calculate_similarity(
        str(baseline_path),
        str(preview_path),
        args.output
    )

    # Output result
    if args.json:
        result = {
            "similarity": round(score, 4),
            "threshold_met": score >= 0.92,
            "baseline": args.baseline,
            "current": args.preview,
            "diff_image": args.output if args.output else None
        }
        print(json.dumps(result))
    else:
        # Print score to stdout (for parsing by bash scripts)
        print(f"{score:.4f}")

    # Exit with success
    sys.exit(0)


if __name__ == '__main__':
    main()
