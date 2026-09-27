"""Physical page distortions for historical manuscript folios.
Implements realistic creases, folds, surface buckling/warping, uneven illumination,
and perspective distortion with high performance.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


class ManuscriptDistortionEngine:
    """Applies authentic physical and optical distortions to manuscript folios."""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed

    def apply_all_distortions(
        self,
        image: Image.Image,
        seed: int = 42,
        apply_folds: bool = True,
        apply_warp: bool = True,
        apply_lighting: bool = True,
        apply_perspective: bool = True,
    ) -> Image.Image:
        """Apply full suite of historical physical distortions with high performance."""
        rng = np.random.default_rng(seed)
        py_rng = random.Random(seed)

        # 1. Page folds and creases (drawn on PIL overlay)
        if apply_folds:
            image = self.add_creases_and_folds_pil(image, py_rng)

        # 2. Uneven illumination & lighting gradient (blended on PIL)
        if apply_lighting:
            image = self.apply_uneven_illumination_pil(image, py_rng)

        # 3. Surface mesh buckling & warping
        if apply_warp:
            image = self.apply_surface_mesh_warp(image, py_rng)

        # 4. Subtle 3D perspective tilt
        if apply_perspective:
            image = self.apply_subtle_perspective(image, py_rng)

        return image

    def add_creases_and_folds_pil(self, image: Image.Image, py_rng: random.Random) -> Image.Image:
        """Simulate physical page folds and storage creases using PIL layers."""
        w, h = image.size
        num_folds = py_rng.randint(1, 3)

        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for _ in range(num_folds):
            fold_type = py_rng.choice(["vertical", "horizontal", "diagonal"])

            if fold_type == "vertical":
                fx = py_rng.randint(int(w * 0.25), int(w * 0.75))
                # Shadow line
                draw.line([(fx - 1, 0), (fx - 1, h)], fill=(0, 0, 0, 45), width=2)
                # Highlight line
                draw.line([(fx + 2, 0), (fx + 2, h)], fill=(255, 255, 255, 35), width=2)

            elif fold_type == "horizontal":
                fy = py_rng.randint(int(h * 0.25), int(h * 0.75))
                draw.line([(0, fy - 1), (w, fy - 1)], fill=(0, 0, 0, 45), width=2)
                draw.line([(0, fy + 2), (w, fy + 2)], fill=(255, 255, 255, 35), width=2)

            else:
                p1 = (py_rng.randint(0, w), 0)
                p2 = (py_rng.randint(0, w), h)
                draw.line([p1, p2], fill=(0, 0, 0, 40), width=2)
                draw.line([(p1[0] + 2, p1[1]), (p2[0] + 2, p2[1])], fill=(255, 255, 255, 30), width=2)

        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1.5))
        image.paste(overlay, (0, 0), overlay)
        return image

    def apply_uneven_illumination_pil(self, image: Image.Image, py_rng: random.Random) -> Image.Image:
        """Simulate natural lighting gradients and archival spot illumination."""
        w, h = image.size
        # Create gradient mask
        grad_small = Image.new("L", (16, 16), 255)
        arr = np.ones((16, 16), dtype=np.float32)

        # Ambient lighting gradient
        lx = py_rng.uniform(-0.8, 0.8)
        ly = py_rng.uniform(-0.8, 0.8)
        x_norm = np.linspace(-1, 1, 16)
        y_norm = np.linspace(-1, 1, 16)
        xx, yy = np.meshgrid(x_norm, y_norm)

        dist_sq = ((xx - lx) ** 2 + (yy - ly) ** 2) / 4.0
        light = np.clip(1.08 - 0.22 * dist_sq, 0.75, 1.15)

        light_upscaled = Image.fromarray((light * 200).astype(np.uint8)).resize((w, h), resample=Image.BILINEAR)

        # Apply lighting modulation to RGB
        img_np = np.array(image, dtype=np.float32)
        light_factor = np.array(light_upscaled, dtype=np.float32)[:, :, np.newaxis] / 200.0
        mod_np = np.clip(img_np * light_factor, 0, 255).astype(np.uint8)

        return Image.fromarray(mod_np, mode="RGB")

    def apply_surface_mesh_warp(self, image: Image.Image, py_rng: random.Random) -> Image.Image:
        """Apply non-linear page curling / buckling using fast grid mesh transform."""
        w, h = image.size
        # 4x4 grid mesh transform
        grid_x = 4
        grid_y = 4
        dx = w / grid_x
        dy = h / grid_y

        mesh_data = []
        amp = py_rng.uniform(2.0, 5.0)

        for i in range(grid_x):
            for j in range(grid_y):
                # Target quad
                box = (int(i * dx), int(j * dy), int((i + 1) * dx), int((j + 1) * dy))
                # Source quad with slight sinusoidal displacement
                x1 = i * dx + math.sin(j * 0.8) * amp
                y1 = j * dy + math.cos(i * 0.8) * amp
                x2 = (i + 1) * dx + math.sin(j * 0.8) * amp
                y2 = j * dy + math.cos((i + 1) * 0.8) * amp
                x3 = (i + 1) * dx + math.sin((j + 1) * 0.8) * amp
                y3 = (j + 1) * dy + math.cos((i + 1) * 0.8) * amp
                x4 = i * dx + math.sin((j + 1) * 0.8) * amp
                y4 = (j + 1) * dy + math.cos(i * 0.8) * amp

                quad = (x1, y1, x4, y4, x3, y3, x2, y2)
                mesh_data.append((box, quad))

        try:
            return image.transform((w, h), Image.MESH, mesh_data, resample=Image.BILINEAR)
        except Exception:
            return image

    def apply_subtle_perspective(self, image: Image.Image, py_rng: random.Random) -> Image.Image:
        """Apply slight photographic / scanning perspective tilt."""
        w, h = image.size
        max_shift_x = w * 0.012
        max_shift_y = h * 0.012

        src_quad = (
            py_rng.uniform(-max_shift_x, max_shift_x),
            py_rng.uniform(-max_shift_y, max_shift_y),
            py_rng.uniform(-max_shift_x, max_shift_x),
            h + py_rng.uniform(-max_shift_y, max_shift_y),
            w + py_rng.uniform(-max_shift_x, max_shift_x),
            h + py_rng.uniform(-max_shift_y, max_shift_y),
            w + py_rng.uniform(-max_shift_x, max_shift_x),
            py_rng.uniform(-max_shift_y, max_shift_y),
        )

        transformed = image.transform(
            (w, h),
            Image.QUAD,
            src_quad,
            resample=Image.BICUBIC,
            fillcolor=(38, 34, 30),
        )

        return transformed
