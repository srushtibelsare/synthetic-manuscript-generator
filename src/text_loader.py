"""Text Loader module for Synthetic Manuscript Generator.
Efficiently loads, indexes, and extracts passages from large manuscript Markdown files
using byte-offset indexing and memory-safe streaming without reading entire files into RAM.
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ManuscriptTextLoader:
    """Memory-efficient streaming loader and passage extractor for large manuscript files."""

    def __init__(self, file_paths: Dict[str, Path]):
        self.file_paths = {k: Path(v) for k, v in file_paths.items()}
        self._line_offsets: Dict[str, List[int]] = {}
        self._total_lines: Dict[str, int] = {}
        self._initialize_indices()

    def _initialize_indices(self) -> None:
        """Build byte offset index for each manuscript file quickly and memory-efficiently."""
        for script, path in self.file_paths.items():
            if not path.exists():
                raise FileNotFoundError(f"Manuscript file for script '{script}' not found at: {path}")

            offsets: List[int] = []
            with open(path, "rb") as f:
                offset = 0
                for line in f:
                    # Only index lines that contain actual text content
                    stripped = line.strip()
                    if stripped and not stripped.startswith(b"#"):
                        offsets.append(offset)
                    offset += len(line)

            self._line_offsets[script] = offsets
            self._total_lines[script] = len(offsets)

    def get_line_count(self, script: str) -> int:
        """Return total valid lines available for the given script."""
        return self._total_lines.get(script, 0)

    def read_line_at_offset(self, script: str, offset: int) -> str:
        """Read a single line from the given byte offset."""
        path = self.file_paths[script]
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            line = f.readline()
            return line.strip()

    def get_passage(
        self,
        script: str,
        index: int,
        target_lines: int = 6,
        seed: int = 42,
    ) -> List[str]:
        """Extract a coherent passage of lines for a specific manuscript image.

        Uses deterministic pseudo-random sampling seeded with (seed, index) to ensure
        reproducibility across runs while guaranteeing distinct passages per folio.
        """
        offsets = self._line_offsets.get(script)
        if not offsets:
            raise ValueError(f"No line offsets indexed for script '{script}'")

        total = len(offsets)
        rng = random.Random(seed * 10007 + index * 997 + 13)

        # Pick a starting point that allows reading consecutive lines
        max_start = max(0, total - target_lines - 1)
        start_idx = rng.randint(0, max_start) if max_start > 0 else 0

        passage_lines: List[str] = []
        path = self.file_paths[script]
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for i in range(start_idx, min(start_idx + target_lines + 5, total)):
                f.seek(offsets[i])
                line = f.readline().strip()
                # Clean any markdown formatting artifacts if present
                clean_line = self._clean_manuscript_line(line)
                if clean_line:
                    passage_lines.append(clean_line)
                if len(passage_lines) >= target_lines:
                    break

        if not passage_lines:
            # Fallback to reading first available line
            passage_lines = [self.read_line_at_offset(script, offsets[0])]

        return passage_lines

    def get_structured_layout_text(
        self,
        script: str,
        index: int,
        layout_style: str,
        seed: int = 42,
    ) -> Dict[str, List[str]]:
        """Extract multi-part text structured for complex manuscript layouts.

        Returns a dictionary with keys such as 'header', 'body', 'margin_left',
        'margin_right', 'footer', 'commentary', or 'column1', 'column2'.
        """
        rng = random.Random(seed * 10007 + index * 997 + 53)

        if layout_style == "palm_leaf":
            # Palm leaf pothi: 3 to 5 long horizontal lines
            body = self.get_passage(script, index, target_lines=rng.randint(3, 5), seed=seed)
            return {"body": body}

        elif layout_style == "dual_column":
            # Two balanced columns (6 to 9 lines each)
            n_lines = rng.randint(6, 9)
            lines1 = self.get_passage(script, index * 3, target_lines=n_lines, seed=seed)
            lines2 = self.get_passage(script, index * 3 + 1, target_lines=n_lines, seed=seed + 1)
            return {"column1": lines1, "column2": lines2}

        elif layout_style == "commentary_bhasya":
            # Root verse (2-3 lines) with surrounding commentary (4-7 lines)
            root = self.get_passage(script, index, target_lines=rng.randint(2, 3), seed=seed)
            comm = self.get_passage(script, index + 350, target_lines=rng.randint(4, 7), seed=seed + 2)
            return {"root_verse": root, "commentary": comm}

        elif layout_style == "marginalia_codex":
            # Main central text (6-9 lines) with side marginal notes (2-4 lines)
            main_text = self.get_passage(script, index, target_lines=rng.randint(6, 9), seed=seed)
            margin_note = self.get_passage(script, index + 200, target_lines=rng.randint(2, 4), seed=seed + 5)
            return {"body": main_text, "marginal_note": margin_note}

        elif layout_style == "rubricated_verse":
            # Large calligraphic verse folio (5 to 8 lines)
            body = self.get_passage(script, index, target_lines=rng.randint(5, 8), seed=seed)
            return {"body": body}

        else:
            # Standard folio: varied between 5 and 10 lines
            body = self.get_passage(script, index, target_lines=rng.randint(5, 10), seed=seed)
            return {"body": body}

    @staticmethod
    def _clean_manuscript_line(line: str) -> str:
        """Clean markdown markers while preserving authentic script characters and Indic punctuation."""
        # Strip leading markdown header markers (#, ##, etc.)
        line = line.lstrip("#").strip()
        # Remove bold/italic markdown formatting asterisks or underscores
        line = line.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
        # Remove backticks
        line = line.replace("`", "")
        # Normalize multiple spaces
        line = " ".join(line.split())
        return line
