"""Ink physics and historical manuscript decorative effects.
Simulates ink bleeding into fibers, broken/faded strokes, subtle ink feathering,
rubrication (cinnabar red accents), and auspicious manuscript rulings.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter


class ManuscriptInkEffects:
    """Simulates realistic ink aging, bleeding, fading, and calligraphic physics."""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed

    def process_ink_layer(
        self,
        text_layer_rgba: Image.Image,
        paper_noise: Optional[np.ndarray],
        ink_palette: Dict,
        seed: int = 42,
        bleed_amount: float = 0.4,
        fade_amount: float = 0.25,
    ) -> Image.Image:
        """Process rendered raw text image with realistic ink physical properties."""
        rng = np.random.default_rng(seed)
        py_rng = random.Random(seed)

        # Extract RGB and Alpha channels
        r, g, b, a = text_layer_rgba.split()
        alpha_np = np.array(a, dtype=np.float32) / 255.0

        if alpha_np.max() == 0:
            return text_layer_rgba

        h, w = alpha_np.shape

        # 1. Subtle capillary ink bleeding (sharp core + microscopic bleed halo)
        dilated = gaussian_filter(alpha_np, sigma=bleed_amount)
        bleed_alpha = np.maximum(alpha_np * 0.92, dilated * 0.28)

        # 2. Stroke Breakages & Fading (Worn ink / fiber resistance)
        if paper_noise is not None and paper_noise.shape == (h, w):
            fiber_skip = np.clip(1.0 - (paper_noise - 0.5) * fade_amount * 1.2, 0.55, 1.0)
            bleed_alpha = bleed_alpha * fiber_skip

        # Organic micro stroke noise
        stroke_noise = gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma=1.2)
        bleed_alpha = np.clip(bleed_alpha * (1.0 + stroke_noise * 0.10), 0, 1.0)

        # 3. Micro Ink Poolings at stroke junctures
        num_smudges = py_rng.randint(1, 3)
        for _ in range(num_smudges):
            text_ys, text_xs = np.where(alpha_np > 0.6)
            if len(text_xs) > 0:
                idx = py_rng.randint(0, len(text_xs) - 1)
                sx, sy = text_xs[idx], text_ys[idx]
                s_rad = py_rng.uniform(2.5, 5.5)

                y_grid, x_grid = np.ogrid[-sy : h - sy, -sx : w - sx]
                smudge = np.exp(-(x_grid**2 + y_grid**2) / (2 * s_rad**2)) * py_rng.uniform(0.08, 0.18)
                bleed_alpha = np.maximum(bleed_alpha, smudge)

        # 4. Color modulation (subtle top-to-bottom ink flow gradient)
        rgb_np = np.array(Image.merge("RGB", (r, g, b)), dtype=np.float32)
        y_norm = np.linspace(0.95, 1.05, h)[:, np.newaxis, np.newaxis]
        rgb_np = np.clip(rgb_np * y_norm, 0, 255)

        # Reconstruct RGBA Image
        final_alpha = (bleed_alpha * 255).astype(np.uint8)
        final_rgb = rgb_np.astype(np.uint8)

        processed = Image.merge(
            "RGBA",
            (
                Image.fromarray(final_rgb[:, :, 0]),
                Image.fromarray(final_rgb[:, :, 1]),
                Image.fromarray(final_rgb[:, :, 2]),
                Image.fromarray(final_alpha),
            ),
        )

        return processed

    def draw_manuscript_decorations(
        self,
        canvas_image: Image.Image,
        bbox_limits: Tuple[int, int, int, int],
        layout_style: str,
        script: str,
        rubric_color: Tuple[int, int, int] = (165, 42, 32),
        seed: int = 42,
    ) -> Image.Image:
        """Draw historical decorative elements: margin ruling lines, cinnabar borders, yellow highlights."""
        py_rng = random.Random(seed + 99)
        draw = ImageDraw.Draw(canvas_image)
        min_x, min_y, max_x, max_y = bbox_limits

        # 1. Margin ruling lines (optional - only appear on ~25% of folios)
        has_margin_rules = py_rng.random() < 0.28
        if has_margin_rules and layout_style in ["standard_folio", "dual_column", "rubricated_verse"]:
            # Vary between faint lead pencil score, sepia ink, or cinnabar red
            rule_kind = py_rng.choice(["faint_lead", "sepia", "rubric"])
            if rule_kind == "rubric":
                line_color = rubric_color
            elif rule_kind == "sepia":
                line_color = (75, 60, 45)
            else:
                line_color = (130, 115, 95)  # Faint dry-point / graphite score line

            line_width = 1

            # Left vertical margin rule (often single line, rarely double)
            is_double = py_rng.random() < 0.35
            rule_x1 = max(18, min_x - py_rng.randint(22, 38))
            draw.line([(rule_x1, max(10, min_y - 20)), (rule_x1, min(canvas_image.height - 10, max_y + 20))], fill=line_color, width=line_width)
            if is_double:
                rule_x2 = rule_x1 + py_rng.randint(4, 6)
                draw.line([(rule_x2, max(10, min_y - 20)), (rule_x2, min(canvas_image.height - 10, max_y + 20))], fill=line_color, width=1)

            # Right vertical margin rule
            rule_rx1 = min(canvas_image.width - 18, max_x + py_rng.randint(22, 38))
            draw.line([(rule_rx1, max(10, min_y - 20)), (rule_rx1, min(canvas_image.height - 10, max_y + 20))], fill=line_color, width=line_width)
            if is_double:
                rule_rx2 = rule_rx1 - py_rng.randint(4, 6)
                draw.line([(rule_rx2, max(10, min_y - 20)), (rule_rx2, min(canvas_image.height - 10, max_y + 20))], fill=line_color, width=1)

        # 2. Center column divider for dual-column format (optional)
        if layout_style == "dual_column" and py_rng.random() < 0.6:
            mid_x = (min_x + max_x) // 2
            div_color = (80, 65, 50) if py_rng.random() > 0.3 else rubric_color
            draw.line([(mid_x, max(10, min_y - 12)), (mid_x, min(canvas_image.height - 10, max_y + 12))], fill=div_color, width=1)

        # 3. Yellow orpiment (haritala) highlight wash behind a central key phrase (optional ~20%)
        if layout_style in ["commentary_bhasya", "rubricated_verse"] and py_rng.random() < 0.22:
            hl_layer = Image.new("RGBA", canvas_image.size, (0, 0, 0, 0))
            hl_draw = ImageDraw.Draw(hl_layer)

            box_y1 = min_y + py_rng.randint(8, 20)
            box_y2 = box_y1 + py_rng.randint(30, 45)
            box_x1 = min_x + py_rng.randint(15, 50)
            box_x2 = min(max_x - 15, box_x1 + py_rng.randint(160, 320))

            hl_draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(240, 205, 75, 60))
            hl_layer = hl_layer.filter(ImageFilter.GaussianBlur(radius=2.0))
            canvas_image.paste(hl_layer, (0, 0), hl_layer)

        return canvas_image
