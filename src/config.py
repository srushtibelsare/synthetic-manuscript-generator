"""Configuration module for Synthetic Manuscript Generator.
Defines paths, fonts, layout styles, color palettes, and dataset split configurations.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_ROOT / "fonts"
OUTPUT_DIR = PROJECT_ROOT / "output"
SAMPLE_OUTPUT_DIR = PROJECT_ROOT / "output_sample"

# Source text files
INPUT_FILES = {
    "devanagari": PROJECT_ROOT / "devanagari_md.md",
    "modi": PROJECT_ROOT / "Modi_md.md",
    "sharada": PROJECT_ROOT / "sharada_md.md",
}

# Fonts mapped per script
SCRIPT_FONTS = {
    "devanagari": [
        FONTS_DIR / "NotoSansDevanagari-Regular.ttf",
        FONTS_DIR / "NotoSerifDevanagari-Regular.ttf",
        FONTS_DIR / "YatraOne-Regular.ttf",
        FONTS_DIR / "Kalam-Regular.ttf",
        FONTS_DIR / "RozhaOne-Regular.ttf",
        FONTS_DIR / "Sahitya-Regular.ttf",
        FONTS_DIR / "Halant-Regular.ttf",
        FONTS_DIR / "Kurale-Regular.ttf",
        FONTS_DIR / "Amita-Regular.ttf",
        FONTS_DIR / "Gotu-Regular.ttf",
    ],
    "modi": [
        FONTS_DIR / "NotoSansModi-Regular.ttf",
    ],
    "sharada": [
        FONTS_DIR / "NotoSansSharada-Regular.ttf",
    ],
}

# Supported scripts
SUPPORTED_SCRIPTS = ["devanagari", "modi", "sharada"]

# Target dataset counts per script
DEFAULT_SPLIT_COUNTS = {
    "train": 85,
    "validation": 10,
    "test": 5,
}

SAMPLE_SPLIT_COUNTS = {
    "train": 2,
    "validation": 0,
    "test": 0,
}

# Layout style templates
LAYOUT_STYLES = [
    "standard_folio",      # Standard horizontal manuscript page with margins & line guides
    "palm_leaf",          # Elongated pothi leaf with string apertures
    "commentary_bhasya",  # Central root verse framed by side commentary
    "dual_column",        # Two column text with central decorative separator
    "marginalia_codex",   # Main text body with marginal glosses/commentary
    "rubricated_verse",   # Red cinnabar invocations/dividers with highlighted verses
]

# Paper background palette presets (RGB base, texture variations)
PAPER_PALETTES = [
    {
        "name": "aged_handmade_paper",
        "base_color": (234, 220, 188),
        "fiber_color": (195, 175, 140),
        "stain_color": (160, 130, 90),
        "edge_darkness": 0.35,
        "fiber_density": 0.08,
    },
    {
        "name": "palm_leaf_golden",
        "base_color": (222, 196, 142),
        "fiber_color": (175, 145, 95),
        "stain_color": (140, 105, 60),
        "edge_darkness": 0.45,
        "fiber_density": 0.12,
    },
    {
        "name": "weathered_parchment",
        "base_color": (240, 228, 202),
        "fiber_color": (205, 188, 155),
        "stain_color": (170, 145, 110),
        "edge_darkness": 0.30,
        "fiber_density": 0.06,
    },
    {
        "name": "bhurjapatra_birch_bark",
        "base_color": (218, 198, 168),
        "fiber_color": (165, 138, 108),
        "stain_color": (130, 95, 65),
        "edge_darkness": 0.50,
        "fiber_density": 0.15,
    },
    {
        "name": "antique_ochre_folio",
        "base_color": (228, 208, 165),
        "fiber_color": (185, 158, 115),
        "stain_color": (150, 120, 75),
        "edge_darkness": 0.40,
        "fiber_density": 0.10,
    },
]

# Ink color presets
INK_PALETTES = [
    {
        "name": "carbon_lampblack",
        "primary": (32, 28, 24),
        "faded": (70, 62, 54),
        "rubric": (165, 42, 32),   # Cinnabar red
    },
    {
        "name": "aged_iron_gall",
        "primary": (48, 38, 30),
        "faded": (92, 78, 65),
        "rubric": (150, 36, 28),
    },
    {
        "name": "sepia_natural",
        "primary": (52, 40, 28),
        "faded": (105, 88, 70),
        "rubric": (175, 48, 35),
    },
]


@dataclass
class GenerationConfig:
    """Master generation configuration parameters."""
    script: str = "devanagari"
    split: str = "train"
    image_index: int = 1
    seed: int = 42
    output_dir: Path = OUTPUT_DIR
    width: int = 1400
    height: int = 900
    font_path: Path = field(default_factory=lambda: FONTS_DIR / "NotoSansDevanagari-Regular.ttf")
    font_size: int = 30
    line_spacing: float = 1.6
    layout_style: str = "standard_folio"
    palette_name: str = "aged_handmade_paper"
    ink_name: str = "carbon_lampblack"
    apply_distortions: bool = True
    apply_ink_effects: bool = True
    apply_aging_stains: bool = True
