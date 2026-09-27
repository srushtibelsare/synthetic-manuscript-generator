#!/usr/bin/env python3
"""Main Entry Point for Synthetic Manuscript Generator.

Usage:
    python generate.py                    # Generate full 300-image dataset (85 train, 10 val, 5 test per script)
    python generate.py --sample           # Generate 6 sample folios (2 per script)
    python generate.py --script devanagari # Generate only Devanagari
    python generate.py --script modi      # Generate only Modi
    python generate.py --script sharada   # Generate only Sharada
    python generate.py --count 10         # Generate custom count per script
    python generate.py --seed 42          # Set custom random seed
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
from src.generator import SyntheticManuscriptGenerator
from src.validator import ManuscriptDatasetValidator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Synthetic Manuscript Generator for Indic Historical Folios",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Generate a small sample set (2 Devanagari, 2 Modi, 2 Sharada = 6 total folios)",
    )
    parser.add_argument(
        "--script",
        type=str,
        choices=SUPPORTED_SCRIPTS + ["all"],
        default="all",
        help="Target script to generate (devanagari, modi, sharada, or all)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Custom total count per script (distributed proportionately across train/val/test)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Master random seed for reproducible generation",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory path for generated images and annotations (defaults to 'output_sample' with --sample, 'output' for full dataset)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of parallel worker threads for fast batch generation",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validator immediately after generation",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Determine target scripts
    if args.script == "all":
        target_scripts = SUPPORTED_SCRIPTS
    else:
        target_scripts = [args.script]

    # Determine split counts and output directory
    if args.sample:
        split_counts = SAMPLE_SPLIT_COUNTS
        output_path = Path(args.output_dir) if args.output_dir else SAMPLE_OUTPUT_DIR
    elif args.count is not None:
        # Proportionate 85/10/5 split
        n_train = max(1, int(round(args.count * 0.85)))
        n_val = max(1, int(round(args.count * 0.10)))
        n_test = max(1, args.count - n_train - n_val)
        split_counts = {"train": n_train, "validation": n_val, "test": n_test}
        output_path = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
    else:
        split_counts = DEFAULT_SPLIT_COUNTS
        output_path = Path(args.output_dir) if args.output_dir else OUTPUT_DIR

    generator = SyntheticManuscriptGenerator(output_dir=output_path, seed=args.seed)

    # Run generation
    records = generator.generate_dataset(
        scripts=target_scripts,
        split_counts=split_counts,
        sample_mode=args.sample,
        seed=args.seed,
        workers=args.workers,
    )

    print(f"\n[OK] Generation complete! Files saved to: {output_path.resolve()}")

    if args.validate or args.sample:
        print("\nRunning automated validation...")
        validator = ManuscriptDatasetValidator(output_dir=output_path)
        report = validator.validate(
            expected_splits=split_counts,
            target_scripts=target_scripts,
        )
        validator.print_report(report)
        if not report.passed:
            sys.exit(1)


if __name__ == "__main__":
    main()
