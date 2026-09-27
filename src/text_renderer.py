"""Text Renderer for Historical Calligraphic Manuscripts.
Renders Indic manuscript text with organic handwriting dynamics:
compound baseline waviness, scribal dip cycles, broad-nib calligraphic weight,
micro-rotations, stroke fading, and authentic rubrication.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

from src.layout import LayoutPlan, TextBlock


class ManuscriptTextRenderer:
    """Renders authentic handwritten manuscript calligraphy onto transparent layers."""

    def __init__(self):
        pass

    def render_layout(
        self,
        layout_plan: LayoutPlan,
        font_path: str,
        ink_palette: Dict,
        seed: int = 42,
    ) -> Tuple[Image.Image, str]:
        """Render all text blocks in the layout plan with calligraphic handwriting dynamics.

        Returns:
            (rendered_text_layer_rgba, exact_ground_truth_string)
        """
        py_rng = random.Random(seed)
        w, h = layout_plan.canvas_width, layout_plan.canvas_height

        # Create transparent RGBA canvas
        text_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        primary_ink = ink_palette.get("primary", (32, 28, 24))
        faded_ink = ink_palette.get("faded", (70, 62, 54))
        rubric_ink = ink_palette.get("rubric", (165, 42, 32))

        rendered_lines_log: List[str] = []

        # Subtle page-wide scribal hand drift
        page_slant_dy = py_rng.uniform(-0.007, 0.007)

        for block_idx, block in enumerate(layout_plan.blocks):
            try:
                font = ImageFont.truetype(font_path, block.font_size)
            except Exception:
                font = ImageFont.load_default()

            cur_y = block.y

            # Inking reservoir state (simulates dipping reed pen every 3-6 words)
            dip_cycle_len = py_rng.randint(3, 6)
            words_since_dip = 0

            for line_idx, line in enumerate(block.text_lines):
                if not line.strip():
                    cur_y += int(block.font_size * block.line_spacing)
                    continue

                rendered_lines_log.append(line.strip())

                # Determine line base color
                if block.color_role == "rubric" or (line_idx == 0 and block.role == "root_verse"):
                    base_color = rubric_ink
                elif block.color_role == "faded":
                    base_color = faded_ink
                else:
                    base_color = primary_ink

                # Organic line start margin offset (reduces rigid alignment)
                margin_jitter = py_rng.randint(-16, 20) if block.align != "center" else 0
                line_start_x = block.x + margin_jitter

                # Organic line-to-line leading jitter (+- 4px)
                leading_jitter = py_rng.randint(-3, 4)
                effective_y = cur_y + leading_jitter

                # Dynamic line spacing per line
                cur_line_spacing = block.line_spacing * py_rng.uniform(0.95, 1.08)

                # Render line word-by-word with handwriting dynamics
                words_since_dip = self._render_calligraphic_line(
                    target_image=text_layer,
                    line_text=line,
                    font=font,
                    font_size=block.font_size,
                    start_x=line_start_x,
                    start_y=effective_y,
                    max_width=block.max_width,
                    base_color=base_color,
                    align=block.align,
                    page_slant_dy=page_slant_dy,
                    words_since_dip=words_since_dip,
                    dip_cycle_len=dip_cycle_len,
                    py_rng=py_rng,
                )

                cur_y += int(block.font_size * cur_line_spacing)

        exact_ground_truth = "\n".join(rendered_lines_log)
        return text_layer, exact_ground_truth

    def _render_calligraphic_line(
        self,
        target_image: Image.Image,
        line_text: str,
        font: ImageFont.ImageFont,
        font_size: int,
        start_x: int,
        start_y: int,
        max_width: int,
        base_color: Tuple[int, int, int],
        align: str,
        page_slant_dy: float,
        words_since_dip: int,
        dip_cycle_len: int,
        py_rng: random.Random,
    ) -> int:
        """Render a single line with compound baseline waviness, micro-slant, calligraphic nib, and inking dynamics."""
        words = line_text.split()
        if not words:
            return words_since_dip

        # Measure line width for alignment
        try:
            bbox = font.getbbox(line_text)
            total_w = bbox[2] - bbox[0]
        except Exception:
            total_w = len(line_text) * (font.size if hasattr(font, "size") else 14)

        if align == "center":
            cur_x = start_x + max(0, (max_width - total_w) // 2)
        else:
            cur_x = start_x

        # 1. Global line arc / sag (natural hand curve across the page width)
        line_arc_amp = py_rng.uniform(-3.5, 3.5)

        # 2. Mid-frequency baseline wave
        wave_freq = py_rng.uniform(0.008, 0.022)
        wave_amp = py_rng.uniform(1.2, 2.6)
        wave_phase = py_rng.uniform(0, 2 * math.pi)

        # 3. Individual line slant
        line_slant = page_slant_dy + py_rng.uniform(-0.007, 0.007)

        space_w = font.getbbox(" ")[2] - font.getbbox(" ")[0] if hasattr(font, "getbbox") else 10

        cum_wobble_y = 0.0

        for word_idx, word in enumerate(words):
            words_since_dip += 1
            if words_since_dip > dip_cycle_len:
                words_since_dip = 0
                dip_cycle_len = py_rng.randint(3, 7)

            # Inking dip dynamics: fresh dip has rich dark pigment; depletes across words
            dip_progress = words_since_dip / max(1, dip_cycle_len)

            # Random stroke skip or dry-brush effect on occasional words
            is_dry_brush = py_rng.random() < 0.12
            if is_dry_brush:
                ink_fade_rgb = py_rng.randint(25, 45)
                ink_alpha = py_rng.randint(145, 185)
            else:
                ink_fade_rgb = int(dip_progress * py_rng.randint(12, 26))
                ink_alpha = int(255 - dip_progress * py_rng.randint(20, 50))

            # Rubrication for auspicious marks, invocations, and verse dandas
            is_rubric_word = any(c in word for c in ["॥", "𑇆", "।", "𑇅", "ॐ", "श्री", "𑘫𑘿𑘨𑘲", "𑙑", "𑙙"]) and (py_rng.random() > 0.35 or "॥" in word)
            if is_rubric_word:
                word_color = (175, 40, 28)  # Cinnabar red
            else:
                # Local organic ink color variation per word
                delta_rgb = py_rng.randint(-12, 14) + ink_fade_rgb
                word_color = (
                    max(10, min(245, base_color[0] + delta_rgb)),
                    max(10, min(245, base_color[1] + delta_rgb)),
                    max(10, min(245, base_color[2] + delta_rgb)),
                )

            # Compound baseline calculation
            x_rel = max(0, cur_x - start_x)
            line_progress = min(1.0, x_rel / max(200, max_width))
            arc_dy = line_arc_amp * math.sin(math.pi * line_progress)
            wavy_dy = wave_amp * math.sin(cur_x * wave_freq + wave_phase)
            slant_dy = x_rel * line_slant

            # Subtle random walk drift between words
            cum_wobble_y = np.clip(cum_wobble_y + py_rng.uniform(-0.8, 0.8), -2.5, 2.5)

            word_y = int(start_y + arc_dy + wavy_dy + slant_dy + cum_wobble_y)

            # Measure word dimensions
            try:
                w_bbox = font.getbbox(word)
                w_width = w_bbox[2] - w_bbox[0]
                w_height = w_bbox[3] - w_bbox[1] + 16
            except Exception:
                w_width = len(word) * 16
                w_height = 42

            pad = 16
            word_img = Image.new("RGBA", (w_width + pad * 2, w_height + pad * 2), (0, 0, 0, 0))
            word_draw = ImageDraw.Draw(word_img)

            # Calligraphic broad-nib effect:
            # Traditional reed pen creates broad downstrokes at ~40 degree angle.
            # When ink is rich, simulate broad nib with subtle directional offset pass
            if not is_dry_brush and dip_progress < 0.65 and py_rng.random() > 0.25:
                # Faint calligraphic shadow / nib spread
                shadow_alpha = int(ink_alpha * 0.45)
                word_draw.text((pad + 1, pad + 1), word, font=font, fill=(*word_color, shadow_alpha))

            # Primary sharp stroke
            word_draw.text((pad, pad), word, font=font, fill=(*word_color, ink_alpha))

            # Subtle organic slant / micro-rotation (-1.6 to +1.6 degrees)
            rot_angle = py_rng.uniform(-1.5, 1.5)
            if abs(rot_angle) > 0.12:
                word_img = word_img.rotate(rot_angle, resample=Image.BICUBIC, expand=False)

            # Paste word onto text layer
            target_image.paste(word_img, (int(cur_x - pad), int(word_y - pad)), word_img)

            # Advance x with natural kerning jitter
            spacing_jitter = py_rng.uniform(0.82, 1.32)
            cur_x += w_width + int(space_w * spacing_jitter)

        return words_since_dip
