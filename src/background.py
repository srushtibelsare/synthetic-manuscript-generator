"""Background Generator for Synthetic Manuscripts.
Creates authentic aged paper, palm leaf, birch bark (bhurjapatra), and weathered parchment
textures complete with multi-scale fiber noise, foxing stains, moisture tide lines,
and edge grime with high-performance vectorized rendering.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter


class ManuscriptBackgroundGenerator:
    """Generates hyper-realistic historical manuscript surfaces with high-performance algorithms."""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed

    def generate_folio_background(
        self,
        width: int,
        height: int,
        palette_config: Dict,
        layout_style: str = "standard_folio",
        seed: int = 42,
    ) -> Tuple[Image.Image, np.ndarray, Dict]:
        """Generate a complete manuscript page background with paper mask and metadata."""
        rng = np.random.default_rng(seed)
        py_rng = random.Random(seed)

        base_color = np.array(palette_config.get("base_color", (234, 220, 188)), dtype=np.float32)
        fiber_color = np.array(palette_config.get("fiber_color", (195, 175, 140)), dtype=np.float32)
        stain_color = np.array(palette_config.get("stain_color", (160, 130, 90)), dtype=np.float32)

        # 1. Base gradient & broad tonal variation
        canvas = self._create_base_tone_layer(width, height, base_color, rng)

        # 2. Fast multi-scale organic paper texture
        texture_noise = self._generate_fast_multiscale_noise(width, height, rng)
        noise_factor = (texture_noise - 0.5) * 26.0
        canvas = np.clip(canvas + noise_factor[:, :, np.newaxis], 0, 255)

        # 3. Microscopic paper / palm leaf fibers
        is_palm_leaf = (layout_style == "palm_leaf")
        canvas = self._add_paper_fibers_fast(
            canvas,
            fiber_color,
            density=palette_config.get("fiber_density", 0.08),
            is_directional=is_palm_leaf,
            rng=rng,
            py_rng=py_rng,
        )

        # 4. Aging stains, foxing spots, and moisture pools
        canvas = self._add_fast_stains_and_foxing(canvas, stain_color, is_palm_leaf, rng, py_rng)

        # 5. Edge grime and vignette
        canvas = self._add_fast_edge_grime(
            canvas,
            edge_darkness=palette_config.get("edge_darkness", 0.35),
            rng=rng,
        )

        # 6. Realistic irregular paper boundary mask & outer shadow
        paper_mask, bg_image = self._create_paper_boundary_and_shadow(canvas, width, height, rng, is_palm_leaf)

        # 7. Add palm-leaf cord apertures if palm leaf
        if is_palm_leaf:
            bg_image = self._add_palm_leaf_apertures(bg_image, width, height, py_rng)

        meta = {
            "palette": palette_config.get("name", "custom"),
            "layout_style": layout_style,
            "is_palm_leaf": is_palm_leaf,
            "width": width,
            "height": height,
        }

        return bg_image, paper_mask, meta

    def _create_base_tone_layer(
        self, width: int, height: int, base_color: np.ndarray, rng: np.random.Generator
    ) -> np.ndarray:
        """Create base tonal gradient across the manuscript canvas."""
        x_grad = np.linspace(-1, 1, width, dtype=np.float32)
        y_grad = np.linspace(-1, 1, height, dtype=np.float32)
        xx, yy = np.meshgrid(x_grad, y_grad)

        angle = rng.uniform(0, 2 * math.pi)
        grad_shift = (xx * math.cos(angle) + yy * math.sin(angle)) * rng.uniform(6.0, 14.0)

        layer = np.zeros((height, width, 3), dtype=np.float32)
        for c in range(3):
            shift = grad_shift * (1.0 - c * 0.15)
            layer[:, :, c] = np.clip(base_color[c] + shift, 0, 255)

        return layer

    def _generate_fast_multiscale_noise(
        self, width: int, height: int, rng: np.random.Generator
    ) -> np.ndarray:
        """Fast multi-scale smooth noise using downsampled low-res filters upsampled via bicubic."""
        combined_noise = np.zeros((height, width), dtype=np.float32)

        # Large scale (coarse clouds)
        scale_down = 8
        h_small, w_small = max(16, height // scale_down), max(16, width // scale_down)
        noise_coarse = rng.standard_normal((h_small, w_small)).astype(np.float32)
        noise_coarse = gaussian_filter(noise_coarse, sigma=4.0)
        c_min, c_max = noise_coarse.min(), noise_coarse.max()
        if c_max > c_min:
            noise_coarse = (noise_coarse - c_min) / (c_max - c_min)
        coarse_pil = Image.fromarray(noise_coarse).resize((width, height), resample=Image.BICUBIC)
        combined_noise += np.array(coarse_pil) * 0.55

        # Medium scale
        scale_med = 4
        h_med, w_med = max(32, height // scale_med), max(32, width // scale_med)
        noise_med = rng.standard_normal((h_med, w_med)).astype(np.float32)
        noise_med = gaussian_filter(noise_med, sigma=2.0)
        m_min, m_max = noise_med.min(), noise_med.max()
        if m_max > m_min:
            noise_med = (noise_med - m_min) / (m_max - m_min)
        med_pil = Image.fromarray(noise_med).resize((width, height), resample=Image.BILINEAR)
        combined_noise += np.array(med_pil) * 0.30

        # Fine grain
        fine_noise = rng.uniform(0.0, 1.0, (height, width)).astype(np.float32)
        combined_noise += fine_noise * 0.15

        return combined_noise

    def _add_paper_fibers_fast(
        self,
        canvas: np.ndarray,
        fiber_color: np.ndarray,
        density: float,
        is_directional: bool,
        rng: np.random.Generator,
        py_rng: random.Random,
    ) -> np.ndarray:
        """Render realistic fibers directly using PIL line drawing."""
        h, w, _ = canvas.shape
        num_fibers = int(w * h * density * 0.001)

        fiber_img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(fiber_img)

        xs = rng.integers(0, w, size=num_fibers)
        ys = rng.integers(0, h, size=num_fibers)

        if is_directional:
            lengths = rng.integers(30, 140, size=num_fibers)
            angles = rng.normal(0.0, 0.04, size=num_fibers)
        else:
            lengths = rng.integers(10, 40, size=num_fibers)
            angles = rng.uniform(0, 2 * math.pi, size=num_fibers)

        for x, y, length, ang in zip(xs, ys, lengths, angles):
            x2 = int(x + length * math.cos(ang))
            y2 = int(y + length * math.sin(ang))
            val = py_rng.randint(40, 110)
            draw.line([(x, y), (x2, y2)], fill=val, width=1)

        fiber_arr = np.array(fiber_img, dtype=np.float32) / 255.0

        for c in range(3):
            canvas[:, :, c] = canvas[:, :, c] * (1.0 - fiber_arr) + fiber_color[c] * fiber_arr

        return canvas

    def _add_fast_stains_and_foxing(
        self,
        canvas: np.ndarray,
        stain_color: np.ndarray,
        is_palm_leaf: bool,
        rng: np.random.Generator,
        py_rng: random.Random,
    ) -> np.ndarray:
        """Subtle and organic aging stains, capillary tide lines, and foxing spots."""
        h, w, _ = canvas.shape
        stain_img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(stain_img)

        # 1. Subtle foxing specks
        num_foxing = py_rng.randint(10, 25)
        for _ in range(num_foxing):
            cx = py_rng.randint(30, w - 30)
            cy = py_rng.randint(30, h - 30)
            r = py_rng.randint(2, 8)
            opacity = py_rng.randint(30, 85)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=opacity)

        # 2. Organic water tide lines & moisture pools
        num_pools = py_rng.randint(2, 5)
        for _ in range(num_pools):
            cx = py_rng.randint(0, w)
            cy = py_rng.randint(0, h)
            rx = py_rng.randint(60, 180)
            ry = int(rx * py_rng.uniform(0.7, 1.3))
            # Outer diffuse pool
            draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=py_rng.randint(20, 50))
            # Subtle capillary tide line ring
            if py_rng.random() > 0.4:
                ring_r = int(rx * 0.9)
                ring_ry = int(ry * 0.9)
                draw.ellipse([cx - ring_r, cy - ring_ry, cx + ring_r, cy + ring_ry], outline=py_rng.randint(35, 70), width=py_rng.randint(2, 4))

        # Blur stain layer smoothly
        stain_img = stain_img.filter(ImageFilter.GaussianBlur(radius=6.0))
        stain_arr = np.array(stain_img, dtype=np.float32) / 255.0 * 0.45

        for c in range(3):
            canvas[:, :, c] = canvas[:, :, c] * (1.0 - stain_arr) + stain_color[c] * stain_arr

        return canvas

    def _add_fast_edge_grime(
        self, canvas: np.ndarray, edge_darkness: float, rng: np.random.Generator
    ) -> np.ndarray:
        """Asymmetric, organic edge patina and archival handling wear."""
        h, w, _ = canvas.shape

        # Distances to the 4 edges
        d_left = np.arange(w)[np.newaxis, :]
        d_right = (w - 1 - np.arange(w))[np.newaxis, :]
        d_top = np.arange(h)[:, np.newaxis]
        d_bottom = (h - 1 - np.arange(h))[:, np.newaxis]

        # Weight the edges asymmetrically (e.g. bottom and outer edges receive more handling)
        w_left = rng.uniform(0.7, 1.2)
        w_right = rng.uniform(0.9, 1.4)
        w_top = rng.uniform(0.6, 1.1)
        w_bottom = rng.uniform(1.0, 1.5)

        weighted_dist = np.minimum(
            np.minimum(d_left / w_left, d_right / w_right),
            np.minimum(d_top / w_top, d_bottom / w_bottom),
        ).astype(np.float32)

        # Add organic low-frequency modulation to the boundary distance
        scale_mod = max(16, min(w, h) // 16)
        noise_small = rng.standard_normal((h // scale_mod, w // scale_mod)).astype(np.float32)
        noise_mod = gaussian_filter(noise_small, sigma=2.0)
        noise_mod = Image.fromarray(noise_mod).resize((w, h), resample=Image.BICUBIC)
        noise_arr = np.array(noise_mod, dtype=np.float32) * 18.0

        border_w = min(w, h) * 0.12
        effective_dist = np.maximum(0, weighted_dist + noise_arr)
        edge_factor = np.clip(1.0 - (effective_dist / border_w), 0, 1)
        edge_factor = (edge_factor**2.0) * (edge_darkness * 0.70)

        grime_color = np.array([62, 46, 32], dtype=np.float32)
        for c in range(3):
            canvas[:, :, c] = canvas[:, :, c] * (1.0 - edge_factor) + grime_color[c] * edge_factor

        return canvas

    def _create_paper_boundary_and_shadow(
        self,
        canvas: np.ndarray,
        width: int,
        height: int,
        rng: np.random.Generator,
        is_palm_leaf: bool,
    ) -> Tuple[np.ndarray, Image.Image]:
        """Create paper edge boundary and desk shadow."""
        margin = int(min(width, height) * 0.025)
        paper_mask = np.zeros((height, width), dtype=np.uint8)
        paper_mask[margin : height - margin, margin : width - margin] = 255

        mask_pil = Image.fromarray(paper_mask, mode="L").filter(ImageFilter.GaussianBlur(radius=1.2))

        # Background archival board
        bg_pil = Image.new("RGB", (width, height), color=(38, 34, 30))

        # Soft drop shadow
        shadow_pil = Image.new("L", (width, height), 0)
        shadow_draw = ImageDraw.Draw(shadow_pil)
        s_off = int(margin * 0.4)
        shadow_draw.rectangle(
            [margin + s_off, margin + s_off, width - margin + s_off, height - margin + s_off],
            fill=180,
        )
        shadow_pil = shadow_pil.filter(ImageFilter.GaussianBlur(radius=margin * 0.6))

        shadow_colored = Image.new("RGB", (width, height), color=(18, 15, 12))
        bg_pil.paste(shadow_colored, (0, 0), shadow_pil)

        paper_pil = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), mode="RGB")
        bg_pil.paste(paper_pil, (0, 0), mask_pil)

        return np.array(mask_pil), bg_pil

    def _add_palm_leaf_apertures(
        self, img: Image.Image, width: int, height: int, py_rng: random.Random
    ) -> Image.Image:
        """Add binding cord apertures for palm leaf manuscripts."""
        draw = ImageDraw.Draw(img)
        hole_rad = py_rng.randint(9, 14)
        h_center = height // 2

        hole_x1 = int(width * 0.22)
        hole_x2 = int(width * 0.78)

        for hx in [hole_x1, hole_x2]:
            wear_rad = hole_rad + py_rng.randint(6, 12)
            draw.ellipse(
                [hx - wear_rad, h_center - wear_rad, hx + wear_rad, h_center + wear_rad],
                fill=(120, 90, 50),
                outline=(90, 65, 35),
            )
            draw.ellipse(
                [hx - hole_rad, h_center - hole_rad, hx + hole_rad, h_center + hole_rad],
                fill=(28, 24, 20),
                outline=(20, 16, 12),
            )

        return img
