#!/usr/bin/env python3
"""
Image similarity calculator for compose-designer plugin.
Uses SSIM (Structural Similarity Index) to compare images.

Supports masked comparison for illustration-aware validation:
- Layout SSIM: Compares only non-illustration regions (used for threshold)
- Full SSIM: Compares entire image (reported for awareness)

Usage:
  python3 image-similarity.py baseline.png preview.png [--output diff.png]
  python3 image-similarity.py baseline.png preview.png --mask mask.png --json

Returns:
  Similarity score (0.0 to 1.0) printed to stdout
  With --json: Full report including layout_ssim, full_ssim, illustration_coverage

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


def load_and_prepare_image(path, target_size=None):
    """Load image, convert to RGB, optionally resize."""
    img = Image.open(path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    if target_size and img.size != target_size:
        img = img.resize(target_size, Image.Resampling.LANCZOS)
    return np.array(img)


def load_mask(mask_path, target_size):
    """
    Load mask image and convert to binary mask.
    White (255) = include in comparison
    Black (0) = exclude from comparison (illustration regions)
    """
    mask = Image.open(mask_path)
    if mask.mode != 'L':
        mask = mask.convert('L')
    if mask.size != target_size:
        mask = mask.resize(target_size, Image.Resampling.NEAREST)

    mask_arr = np.array(mask)
    # Normalize to 0-1 range
    binary_mask = (mask_arr > 127).astype(np.float32)
    return binary_mask


def calculate_masked_ssim(baseline_arr, preview_arr, mask):
    """
    Calculate SSIM only on masked (white) regions.

    Args:
        baseline_arr: Baseline image as numpy array
        preview_arr: Preview image as numpy array
        mask: Binary mask (1 = include, 0 = exclude)

    Returns:
        float: SSIM score for masked regions
    """
    # Expand mask to 3 channels
    mask_3ch = np.stack([mask] * 3, axis=2)

    # Apply mask - set excluded regions to same value in both images
    # This way they contribute 1.0 to SSIM (perfect match)
    neutral_value = 128
    masked_baseline = np.where(mask_3ch > 0.5, baseline_arr, neutral_value)
    masked_preview = np.where(mask_3ch > 0.5, preview_arr, neutral_value)

    # Calculate SSIM on masked images
    score, _ = ssim(
        masked_baseline.astype(np.uint8),
        masked_preview.astype(np.uint8),
        multichannel=True,
        channel_axis=2,
        full=True
    )

    return score


def calculate_similarity(baseline_path, preview_path, mask_path=None, output_diff_path=None):
    """
    Calculate SSIM between two images, optionally with mask.

    Args:
        baseline_path: Path to baseline/reference image
        preview_path: Path to preview/test image
        mask_path: Optional path to mask image (white=include, black=exclude)
        output_diff_path: Optional path to save difference image

    Returns:
        dict: {
            'layout_ssim': float (masked SSIM if mask provided, else full SSIM),
            'full_ssim': float,
            'illustration_coverage': float (0.0-1.0, percentage of masked area),
            'has_mask': bool
        }
    """
    try:
        # Load baseline to get target size
        baseline = Image.open(baseline_path)
        target_size = baseline.size

        # Load and prepare both images
        baseline_arr = load_and_prepare_image(baseline_path)

        preview = Image.open(preview_path)
        if preview.size != target_size:
            print(f"Resizing preview from {preview.size} to {target_size}", file=sys.stderr)
        preview_arr = load_and_prepare_image(preview_path, target_size)

        # Calculate full SSIM
        full_score, diff_image = ssim(
            baseline_arr,
            preview_arr,
            multichannel=True,
            channel_axis=2,
            full=True
        )

        # Calculate masked SSIM if mask provided
        layout_score = full_score
        illustration_coverage = 0.0
        has_mask = False

        if mask_path and Path(mask_path).exists():
            has_mask = True
            mask = load_mask(mask_path, target_size)

            # Calculate coverage (percentage of black/excluded pixels)
            illustration_coverage = 1.0 - np.mean(mask)

            # Calculate layout-only SSIM
            layout_score = calculate_masked_ssim(baseline_arr, preview_arr, mask)

            print(f"Mask applied: {illustration_coverage*100:.1f}% illustration coverage", file=sys.stderr)

        # Generate diff visualization if requested
        if output_diff_path:
            # Calculate absolute pixel difference
            abs_diff = np.abs(baseline_arr.astype(float) - preview_arr.astype(float))

            # If mask exists, highlight illustration regions differently
            if has_mask:
                mask_3ch = np.stack([mask] * 3, axis=2)
                # Illustration regions in blue tint
                illustration_highlight = np.zeros_like(abs_diff)
                illustration_highlight[:, :, 2] = 100  # Blue channel
                abs_diff = np.where(mask_3ch > 0.5, abs_diff, illustration_highlight)

            # Enhance differences for visibility (multiply by 3, cap at 255)
            enhanced_diff = (abs_diff * 3).clip(0, 255).astype(np.uint8)

            # Save diff image
            diff_img = Image.fromarray(enhanced_diff)
            diff_img.save(output_diff_path)
            print(f"Diff image saved: {output_diff_path}", file=sys.stderr)

        return {
            'layout_ssim': float(layout_score),
            'full_ssim': float(full_score),
            'illustration_coverage': float(illustration_coverage),
            'has_mask': has_mask
        }

    except FileNotFoundError as e:
        print(f"Error: Image file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error calculating similarity: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Calculate image similarity using SSIM algorithm',
        epilog='''
Examples:
  # Basic comparison
  python3 image-similarity.py baseline.png preview.png --output diff.png

  # Masked comparison (illustration-aware)
  python3 image-similarity.py baseline.png preview.png --mask mask.png --json

  # The mask should have:
  #   White (255) = layout regions (include in SSIM)
  #   Black (0) = illustration regions (exclude from SSIM)
'''
    )
    parser.add_argument('baseline', help='Path to baseline/reference image')
    parser.add_argument('preview', help='Path to preview/test image')
    parser.add_argument(
        '--output', '-o',
        help='Path to save difference visualization (optional)',
        default=None
    )
    parser.add_argument(
        '--mask', '-m',
        help='Path to mask image for illustration-aware comparison (white=include, black=exclude)',
        default=None
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output result as JSON with full details'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.92,
        help='SSIM threshold for pass/fail (default: 0.92)'
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
    result = calculate_similarity(
        str(baseline_path),
        str(preview_path),
        args.mask,
        args.output
    )

    # Output result
    if args.json:
        output = {
            "layout_ssim": round(result['layout_ssim'], 4),
            "full_ssim": round(result['full_ssim'], 4),
            "illustration_coverage": round(result['illustration_coverage'], 4),
            "has_mask": result['has_mask'],
            "threshold": args.threshold,
            "threshold_met": result['layout_ssim'] >= args.threshold,
            "baseline": args.baseline,
            "preview": args.preview,
            "mask": args.mask,
            "diff_image": args.output
        }
        print(json.dumps(output, indent=2))
    else:
        # Print layout_ssim to stdout (for parsing by bash scripts)
        # This is the score that should be used for threshold comparison
        print(f"{result['layout_ssim']:.4f}")

    # Exit with success
    sys.exit(0)


if __name__ == '__main__':
    main()
