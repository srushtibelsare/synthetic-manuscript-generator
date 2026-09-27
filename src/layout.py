"""Layout Engine for Synthetic Manuscripts.
Handles varied historical manuscript formats (standard folio, palm-leaf pothi,
commentary bhasya, dual-column codex, marginalia, rubricated verse) with
strict automatic fitting and zero-overflow boundary enforcement.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PIL import ImageDraw, ImageFont


@dataclass
class TextBlock:
    """Represents a bounded text block within a manuscript folio."""
    text_lines: List[str]
    x: int
    y: int
    max_width: int
    max_height: int
    font_size: int
    line_spacing: float
    role: str = "body"  # 'body', 'commentary', 'header', 'margin_note', 'root_verse'
    color_role: str = "primary"  # 'primary', 'rubric', 'faded'
    align: str = "left"  # 'left', 'center', 'justify'


@dataclass
class LayoutPlan:
    """Complete layout plan for a manuscript folio."""
    style: str
    canvas_width: int
    canvas_height: int
    safe_margin: int
    blocks: List[TextBlock] = field(default_factory=list)
    bounding_box: Tuple[int, int, int, int] = (0, 0, 0, 0)
    all_rendered_text: str = ""


class ManuscriptLayoutEngine:
    """Calculates geometric layouts and ensures strict boundary fitting with no overflow."""

    def __init__(self):
        pass

    def compute_layout(
        self,
        raw_text_dict: Dict[str, List[str]],
        layout_style: str,
        script: str,
        canvas_width: int,
        canvas_height: int,
        font_path: str,
        base_font_size: int = 28,
        seed: int = 42,
    ) -> LayoutPlan:
        """Compute fitted layout for the specified manuscript style with zero overflow."""
        py_rng = random.Random(seed)

        # Safe margins (generous buffer preventing text from ever touching paper edges)
        margin_x = int(canvas_width * 0.09)
        margin_y = int(canvas_height * 0.10)
        content_w = canvas_width - 2 * margin_x
        content_h = canvas_height - 2 * margin_y

        blocks: List[TextBlock] = []

        if layout_style == "palm_leaf":
            # Palm leaf pothi: 3 to 5 wide horizontal lines with generous line spacing
            lines = raw_text_dict.get("body", [])
            line_sp = py_rng.uniform(1.85, 2.15)
            f_lines, f_size = self._fit_text_to_box(
                lines,
                max_w=content_w,
                max_h=int(content_h * 0.85),
                font_path=font_path,
                start_size=py_rng.randint(32, 40),
                min_size=18,
                line_spacing=line_sp,
            )
            total_h = int(len(f_lines) * f_size * line_sp)
            start_y = margin_y + max(0, int((content_h - total_h) * 0.48))

            blocks.append(
                TextBlock(
                    text_lines=f_lines,
                    x=margin_x,
                    y=start_y,
                    max_width=content_w,
                    max_height=content_h,
                    font_size=f_size,
                    line_spacing=line_sp,
                    role="body",
                    color_role="primary",
                )
            )

        elif layout_style == "dual_column":
            # Two side-by-side columns with central gutter
            gutter = int(canvas_width * 0.05)
            col_w = (content_w - gutter) // 2

            col1_lines = raw_text_dict.get("column1", raw_text_dict.get("body", []))
            col2_lines = raw_text_dict.get("column2", col1_lines)

            line_sp = py_rng.uniform(1.75, 2.0)
            max_col_h = int(content_h * 0.88)

            f_lines1, f_size1 = self._fit_text_to_box(
                col1_lines, max_w=col_w, max_h=max_col_h, font_path=font_path, start_size=py_rng.randint(26, 32), min_size=16, line_spacing=line_sp
            )
            f_lines2, f_size2 = self._fit_text_to_box(
                col2_lines, max_w=col_w, max_h=max_col_h, font_path=font_path, start_size=f_size1, min_size=16, line_spacing=line_sp
            )
            final_size = min(f_size1, f_size2)

            max_lines = max(len(f_lines1), len(f_lines2))
            total_h = int(max_lines * final_size * line_sp)
            start_y = margin_y + max(0, int((content_h - total_h) * 0.48))

            blocks.append(
                TextBlock(
                    text_lines=f_lines1,
                    x=margin_x,
                    y=start_y,
                    max_width=col_w,
                    max_height=content_h,
                    font_size=final_size,
                    line_spacing=line_sp,
                    role="body",
                    color_role="primary",
                )
            )
            blocks.append(
                TextBlock(
                    text_lines=f_lines2,
                    x=margin_x + col_w + gutter,
                    y=start_y,
                    max_width=col_w,
                    max_height=content_h,
                    font_size=final_size,
                    line_spacing=line_sp,
                    role="body",
                    color_role="primary",
                )
            )

        elif layout_style == "commentary_bhasya":
            # Root verse centered in upper box (grand size); commentary framed below
            root_lines = raw_text_dict.get("root_verse", [])
            comm_lines = raw_text_dict.get("commentary", raw_text_dict.get("body", []))

            root_sp = py_rng.uniform(1.85, 2.15)
            comm_sp = py_rng.uniform(1.7, 1.95)

            root_max_h = int(content_h * 0.30)
            comm_max_h = int(content_h * 0.52)

            f_root, f_root_size = self._fit_text_to_box(
                root_lines, max_w=int(content_w * 0.85), max_h=root_max_h, font_path=font_path, start_size=py_rng.randint(34, 42), min_size=22, line_spacing=root_sp
            )
            f_comm, f_comm_size = self._fit_text_to_box(
                comm_lines, max_w=content_w, max_h=comm_max_h, font_path=font_path, start_size=py_rng.randint(26, 32), min_size=16, line_spacing=comm_sp
            )

            root_x = margin_x + (content_w - int(content_w * 0.85)) // 2
            actual_root_h = int(len(f_root) * f_root_size * root_sp)
            actual_comm_h = int(len(f_comm) * f_comm_size * comm_sp)
            gap = int(content_h * 0.04)

            total_combined_h = actual_root_h + gap + actual_comm_h
            start_y = margin_y + max(0, int((content_h - total_combined_h) * 0.46))

            blocks.append(
                TextBlock(
                    text_lines=f_root,
                    x=root_x,
                    y=start_y,
                    max_width=int(content_w * 0.85),
                    max_height=root_max_h,
                    font_size=f_root_size,
                    line_spacing=root_sp,
                    role="root_verse",
                    color_role="rubric" if py_rng.random() > 0.4 else "primary",
                    align="center",
                )
            )

            comm_y = start_y + actual_root_h + gap
            blocks.append(
                TextBlock(
                    text_lines=f_comm,
                    x=margin_x,
                    y=comm_y,
                    max_width=content_w,
                    max_height=comm_max_h,
                    font_size=f_comm_size,
                    line_spacing=comm_sp,
                    role="commentary",
                    color_role="primary",
                )
            )

        elif layout_style == "marginalia_codex":
            # Main central text box with right margin commentary column
            margin_col_w = int(content_w * 0.25)
            main_col_w = content_w - margin_col_w - int(content_w * 0.04)

            main_lines = raw_text_dict.get("body", [])
            note_lines = raw_text_dict.get("marginal_note", [])

            main_sp = py_rng.uniform(1.8, 2.1)
            f_main, f_main_size = self._fit_text_to_box(
                main_lines, max_w=main_col_w, max_h=int(content_h * 0.85), font_path=font_path, start_size=py_rng.randint(30, 38), min_size=18, line_spacing=main_sp
            )
            f_note, f_note_size = self._fit_text_to_box(
                note_lines, max_w=margin_col_w, max_h=int(content_h * 0.65), font_path=font_path, start_size=int(f_main_size * 0.70), min_size=14, line_spacing=1.6
            )

            total_h = int(len(f_main) * f_main_size * main_sp)
            start_y = margin_y + max(0, int((content_h - total_h) * 0.48))

            blocks.append(
                TextBlock(
                    text_lines=f_main,
                    x=margin_x,
                    y=start_y,
                    max_width=main_col_w,
                    max_height=content_h,
                    font_size=f_main_size,
                    line_spacing=main_sp,
                    role="body",
                    color_role="primary",
                )
            )
            blocks.append(
                TextBlock(
                    text_lines=f_note,
                    x=margin_x + main_col_w + int(content_w * 0.04),
                    y=start_y + int(f_main_size * 0.5),
                    max_width=margin_col_w,
                    max_height=int(content_h * 0.65),
                    font_size=f_note_size,
                    line_spacing=1.6,
                    role="margin_note",
                    color_role="faded",
                )
            )

        else:
            # Standard folio & Rubricated verse: grand calligraphic manuscript text
            lines = raw_text_dict.get("body", [])
            target_start = py_rng.randint(32, 40)
            line_sp = py_rng.uniform(1.8, 2.15)
            f_lines, f_size = self._fit_text_to_box(
                lines, max_w=content_w, max_h=int(content_h * 0.86), font_path=font_path, start_size=target_start, min_size=18, line_spacing=line_sp
            )
            total_h = int(len(f_lines) * f_size * line_sp)
            start_y = margin_y + max(0, int((content_h - total_h) * 0.48))

            blocks.append(
                TextBlock(
                    text_lines=f_lines,
                    x=margin_x,
                    y=start_y,
                    max_width=content_w,
                    max_height=content_h,
                    font_size=f_size,
                    line_spacing=line_sp,
                    role="body",
                    color_role="rubric" if layout_style == "rubricated_verse" and py_rng.random() > 0.4 else "primary",
                )
            )

        # Collect exact ground-truth text rendered
        all_text_lines: List[str] = []
        min_bx, min_by, max_bx, max_by = canvas_width, canvas_height, 0, 0

        for block in blocks:
            for l in block.text_lines:
                if l.strip():
                    all_text_lines.append(l.strip())
            min_bx = min(min_bx, block.x)
            min_by = min(min_by, block.y)
            max_bx = max(max_bx, block.x + block.max_width)
            max_by = max(max_by, block.y + block.max_height)

        full_ground_truth = "\n".join(all_text_lines)

        return LayoutPlan(
            style=layout_style,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            safe_margin=margin_x,
            blocks=blocks,
            bounding_box=(min_bx, min_by, max_bx, max_by),
            all_rendered_text=full_ground_truth,
        )

    def _fit_text_to_box(
        self,
        raw_lines: List[str],
        max_w: int,
        max_h: int,
        font_path: str,
        start_size: int = 28,
        min_size: int = 14,
        line_spacing: float = 1.6,
    ) -> Tuple[List[str], int]:
        """Wrap and shrink text until all lines strictly fit inside (max_w, max_h)."""
        current_size = start_size

        while current_size >= min_size:
            try:
                font = ImageFont.truetype(font_path, current_size)
            except Exception:
                # Fallback to default if font load fails
                font = ImageFont.load_default()

            wrapped_lines: List[str] = []
            for raw_line in raw_lines:
                wrapped_lines.extend(self._wrap_indic_line(raw_line, font, max_w))

            line_height = int(current_size * line_spacing)
            total_height = len(wrapped_lines) * line_height

            if total_height <= max_h and len(wrapped_lines) > 0:
                return wrapped_lines, current_size

            # If it overflows, reduce font size
            current_size -= 2

        # If still doesn't fit at min_size, trim to max lines that fit
        font = ImageFont.truetype(font_path, min_size)
        wrapped_lines = []
        for raw_line in raw_lines:
            wrapped_lines.extend(self._wrap_indic_line(raw_line, font, max_w))

        line_height = int(min_size * line_spacing)
        max_possible_lines = max(1, max_h // line_height)
        return wrapped_lines[:max_possible_lines], min_size

    def _wrap_indic_line(self, line: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
        """Wrap words while keeping Indic syllables, compounds, and verse markers intact."""
        words = line.split()
        if not words:
            return []

        wrapped: List[str] = []
        cur_line = words[0]

        for w in words[1:]:
            test_line = cur_line + " " + w
            try:
                bbox = font.getbbox(test_line)
                line_w = bbox[2] - bbox[0]
            except Exception:
                line_w = len(test_line) * (font.size if hasattr(font, "size") else 15)

            if line_w <= max_width:
                cur_line = test_line
            else:
                wrapped.append(cur_line)
                cur_line = w

        if cur_line:
            wrapped.append(cur_line)

        return wrapped
