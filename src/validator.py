"""Validator module for Synthetic Manuscript Generator.
Performs comprehensive integrity checks across all generated folios:
image counts, annotation counts, 1:1 file matching, train/val/test splits,
image corruption, annotation validity, empty checks, and script encoding integrity.
"""

import os
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from src.config import DEFAULT_SPLIT_COUNTS, OUTPUT_DIR, SUPPORTED_SCRIPTS


@dataclass
class ValidationReport:
    """Stores detailed validation results and metrics."""
    total_images: int = 0
    total_annotations: int = 0
    matched_pairs: int = 0
    unmatched_images: List[str] = field(default_factory=list)
    unmatched_annotations: List[str] = field(default_factory=list)
    corrupted_images: List[str] = field(default_factory=list)
    empty_annotations: List[str] = field(default_factory=list)
    invalid_script_annotations: List[str] = field(default_factory=list)
    split_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ManuscriptDatasetValidator:
    """Validates full synthetic manuscript dataset structure and file contents."""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = Path(output_dir)

    def validate(
        self,
        expected_splits: Optional[Dict[str, int]] = None,
        target_scripts: Optional[List[str]] = None,
    ) -> ValidationReport:
        """Run complete test and verification suite on the output directory."""
        report = ValidationReport()
        scripts = target_scripts or SUPPORTED_SCRIPTS

        if not self.output_dir.exists():
            report.passed = False
            report.errors.append(f"Output directory does not exist: {self.output_dir}")
            return report

        for script in scripts:
            report.split_counts[script] = {}
            script_dir = self.output_dir / script
            if not script_dir.exists():
                report.errors.append(f"Missing script folder: {script_dir}")
                continue

            for split_name in ["train", "validation", "test"]:
                split_dir = script_dir / split_name
                img_dir = split_dir / "images"
                ann_dir = split_dir / "annotations"

                if not img_dir.exists():
                    report.split_counts[script][split_name] = 0
                    continue

                img_files = sorted(list(img_dir.glob("*.png")))
                ann_files = sorted(list(ann_dir.glob("*.md"))) if ann_dir.exists() else []

                count = len(img_files)
                report.split_counts[script][split_name] = count
                report.total_images += count
                report.total_annotations += len(ann_files)

                # Check 1:1 image and annotation mapping
                img_stems = {f.stem: f for f in img_files}
                ann_stems = {f.stem: f for f in ann_files}

                for stem, img_path in img_stems.items():
                    if stem not in ann_stems:
                        report.unmatched_images.append(str(img_path))
                    else:
                        report.matched_pairs += 1

                for stem, ann_path in ann_stems.items():
                    if stem not in img_stems:
                        report.unmatched_annotations.append(str(ann_path))

                # Check image integrity
                for img_path in img_files:
                    try:
                        with Image.open(img_path) as img:
                            img.verify()
                        # Re-open to check mode & dimensions
                        with Image.open(img_path) as img:
                            w, h = img.size
                            if w < 200 or h < 100:
                                report.corrupted_images.append(f"{img_path} (abnormal size {w}x{h})")
                    except Exception as e:
                        report.corrupted_images.append(f"{img_path} ({e})")

                # Check annotation validity and script encoding
                for ann_path in ann_files:
                    try:
                        with open(ann_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        if not content.strip():
                            report.empty_annotations.append(str(ann_path))
                            continue

                        # Check if transcription section exists and is non-empty
                        if "## Transcription" in content:
                            parts = content.split("## Transcription")
                            transcription = parts[1].split("---")[0].strip()
                        else:
                            transcription = content.strip()

                        if not transcription:
                            report.empty_annotations.append(f"{ann_path} (empty transcription)")
                            continue

                        # Verify correct script characters are present
                        char_scripts = self._detect_scripts_in_text(transcription)
                        expected_block = script.upper()
                        if expected_block == "MODI":
                            expected_block = "MODI"
                        elif expected_block == "SHARADA":
                            expected_block = "SHARADA"
                        else:
                            expected_block = "DEVANAGARI"

                        if not any(expected_block in s for s in char_scripts):
                            report.invalid_script_annotations.append(
                                f"{ann_path} (missing {expected_block} characters, found: {char_scripts})"
                            )

                    except Exception as e:
                        report.empty_annotations.append(f"{ann_path} (read error: {e})")

        # Verify against expected split counts if provided
        if expected_splits:
            for script in scripts:
                for split_name, expected_num in expected_splits.items():
                    actual_num = report.split_counts.get(script, {}).get(split_name, 0)
                    if actual_num != expected_num:
                        report.warnings.append(
                            f"Split count mismatch for {script}/{split_name}: expected {expected_num}, got {actual_num}"
                        )

        # Determine overall pass/fail
        has_critical_failures = (
            len(report.corrupted_images) > 0
            or len(report.empty_annotations) > 0
            or len(report.unmatched_images) > 0
            or len(report.unmatched_annotations) > 0
            or len(report.invalid_script_annotations) > 0
            or len(report.errors) > 0
        )
        report.passed = not has_critical_failures

        return report

    @staticmethod
    def _detect_scripts_in_text(text: str) -> List[str]:
        """Detect Unicode script names present in text."""
        detected = set()
        for char in text:
            if ord(char) > 127:
                try:
                    name = unicodedata.name(char)
                    script_part = name.split()[0]
                    detected.add(script_part)
                except Exception:
                    pass
        return list(detected)

    def print_report(self, report: ValidationReport) -> None:
        """Print formatted CLI report of validation results."""
        print("\n" + "=" * 60)
        print("SYNTHETIC MANUSCRIPT DATASET VALIDATION REPORT")
        print("=" * 60)
        print(f"Overall Status: {'PASSED [OK]' if report.passed else 'FAILED [ERROR]'}")
        print(f"Total Images: {report.total_images}")
        print(f"Total Annotations: {report.total_annotations}")
        print(f"Matched (Image <-> Annotation) Pairs: {report.matched_pairs}")

        print("\n--- Split Breakdown by Script ---")
        for script, splits in report.split_counts.items():
            split_str = ", ".join(f"{k}: {v}" for k, v in splits.items())
            total_script = sum(splits.values())
            print(f"  * {script.capitalize():<12}: {split_str} (Total: {total_script})")

        if report.corrupted_images:
            print(f"\n[!] Corrupted Images ({len(report.corrupted_images)}):")
            for c in report.corrupted_images[:5]:
                print(f"    - {c}")

        if report.empty_annotations:
            print(f"\n[!] Empty Annotations ({len(report.empty_annotations)}):")
            for e in report.empty_annotations[:5]:
                print(f"    - {e}")

        if report.unmatched_images:
            print(f"\n[!] Unmatched Images ({len(report.unmatched_images)}):")
            for u in report.unmatched_images[:5]:
                print(f"    - {u}")

        if report.invalid_script_annotations:
            print(f"\n[!] Invalid Script Annotations ({len(report.invalid_script_annotations)}):")
            for i in report.invalid_script_annotations[:5]:
                print(f"    - {i}")

        if report.warnings:
            print(f"\n[i] Warnings ({len(report.warnings)}):")
            for w in report.warnings:
                print(f"    - {w}")

        if report.errors:
            print(f"\n[!] Errors ({len(report.errors)}):")
            for err in report.errors:
                print(f"    - {err}")

        print("=" * 60 + "\n")
