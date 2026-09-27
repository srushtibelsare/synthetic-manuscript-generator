#!/usr/bin/env python3
"""Validation CLI for Synthetic Manuscript Generator.

Validates:
- Image counts
- Annotation counts
- 1:1 Image/Annotation matching
- Train / Validation / Test counts
- Image readability & corruption
- Annotation readability & UTF-8 integrity
- Empty annotations
- Script encoding verification
- Basic text boundary & overflow checks
"""

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import (
    DEFAULT_SPLIT_COUNTS,
    OUTPUT_DIR,
    SAMPLE_OUTPUT_DIR,
    SAMPLE_SPLIT_COUNTS,
    SUPPORTED_SCRIPTS,
)
from src.validator import ManuscriptDatasetValidator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validator for Synthetic Manuscript Dataset",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Path to output directory to validate (defaults to 'output_sample' with --sample, 'output' for full dataset)",
    )
    parser.add_argument(
        "--script",
        type=str,
        choices=SUPPORTED_SCRIPTS + ["all"],
        default="all",
        help="Target script to validate",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Validate against sample counts (2 train per script)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.sample:
        output_path = Path(args.output_dir) if args.output_dir else SAMPLE_OUTPUT_DIR
        expected_splits = SAMPLE_SPLIT_COUNTS
    else:
        output_path = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
        expected_splits = DEFAULT_SPLIT_COUNTS

    target_scripts = SUPPORTED_SCRIPTS if args.script == "all" else [args.script]

    validator = ManuscriptDatasetValidator(output_dir=output_path)
    report = validator.validate(
        expected_splits=expected_splits,
        target_scripts=target_scripts,
    )
    validator.print_report(report)

    if not report.passed:
        print("[FAIL] Validation failed! Review the errors above.")
        sys.exit(1)
    else:
        print("[SUCCESS] All validation checks passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
