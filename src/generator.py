"""Pipeline Orchestrator for Synthetic Manuscript Generation.
Coordinates text loading, layout computation, calligraphic rendering, ink physics,
paper aging, physical distortions, and synchronized ground-truth annotation output.
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image
from tqdm import tqdm

from src.annotations import ManuscriptAnnotationWriter
from src.background import ManuscriptBackgroundGenerator
from src.config import (
    DEFAULT_SPLIT_COUNTS,
    INK_PALETTES,
    INPUT_FILES,
    LAYOUT_STYLES,
    OUTPUT_DIR,
    PAPER_PALETTES,
    SAMPLE_SPLIT_COUNTS,
    SCRIPT_FONTS,
    SUPPORTED_SCRIPTS,
    GenerationConfig,
)
from src.distortions import ManuscriptDistortionEngine
from src.layout import ManuscriptLayoutEngine
from src.manuscript_effects import ManuscriptInkEffects
from src.text_loader import ManuscriptTextLoader
from src.text_renderer import ManuscriptTextRenderer


class SyntheticManuscriptGenerator:
    """End-to-end generator for realistic historical manuscript folios."""

    def __init__(
        self,
        output_dir: Path = OUTPUT_DIR,
        seed: int = 42,
    ):
        self.output_dir = Path(output_dir)
        self.seed = seed
        self.text_loader = ManuscriptTextLoader(INPUT_FILES)
        self.bg_generator = ManuscriptBackgroundGenerator(seed)
        self.layout_engine = ManuscriptLayoutEngine()
        self.text_renderer = ManuscriptTextRenderer()
        self.ink_effects = ManuscriptInkEffects(seed)
        self.distortions = ManuscriptDistortionEngine(seed)
        self.annotation_writer = ManuscriptAnnotationWriter()

    def generate_single_folio(
        self,
        script: str,
        split: str,
        image_index: int,
        seed: int,
    ) -> Tuple[Path, Path, Dict]:
        """Generate a single manuscript folio image and matching annotation file."""
        py_rng = random.Random(seed)

        # 1. Select layout style and canvas dimensions
        layout_style = py_rng.choice(LAYOUT_STYLES)
        if layout_style == "palm_leaf":
            canvas_w, canvas_h = 1600, 560
        elif layout_style == "dual_column":
            canvas_w, canvas_h = 1400, 950
        elif layout_style == "commentary_bhasya":
            canvas_w, canvas_h = 1350, 880
        elif layout_style == "marginalia_codex":
            canvas_w, canvas_h = 1300, 920
        else:
            canvas_w, canvas_h = 1400, 900

        # 2. Select font for script
        available_fonts = SCRIPT_FONTS.get(script, [])
        if not available_fonts:
            raise ValueError(f"No fonts configured for script '{script}'")

        # Pick font deterministically
        font_path = available_fonts[py_rng.randint(0, len(available_fonts) - 1)]
        if not font_path.exists():
            font_path = available_fonts[0]

        # 3. Select paper & ink palettes
        # If palm_leaf layout, prioritize palm_leaf / birch bark palette
        if layout_style == "palm_leaf":
            palette_candidates = [p for p in PAPER_PALETTES if "palm_leaf" in p["name"] or "bhurja" in p["name"]]
            paper_palette = py_rng.choice(palette_candidates) if palette_candidates else PAPER_PALETTES[0]
        else:
            paper_palette = py_rng.choice(PAPER_PALETTES)

        ink_palette = py_rng.choice(INK_PALETTES)

        # 4. Extract structured text from source manuscript file
        raw_text_dict = self.text_loader.get_structured_layout_text(
            script=script,
            index=image_index,
            layout_style=layout_style,
            seed=seed,
        )

        # 5. Compute fitted layout with zero overflow
        base_font_size = py_rng.randint(34, 44)
        layout_plan = self.layout_engine.compute_layout(
            raw_text_dict=raw_text_dict,
            layout_style=layout_style,
            script=script,
            canvas_width=canvas_w,
            canvas_height=canvas_h,
            font_path=str(font_path),
            base_font_size=base_font_size,
            seed=seed,
        )

        # 6. Generate authentic manuscript background
        bg_image, paper_mask, bg_meta = self.bg_generator.generate_folio_background(
            width=canvas_w,
            height=canvas_h,
            palette_config=paper_palette,
            layout_style=layout_style,
            seed=seed,
        )

        # 7. Render calligraphic text layer
        text_layer_rgba, exact_ground_truth = self.text_renderer.render_layout(
            layout_plan=layout_plan,
            font_path=str(font_path),
            ink_palette=ink_palette,
            seed=seed,
        )

        # 8. Apply ink physics (bleeding, fiber absorption, stroke fading)
        processed_text_layer = self.ink_effects.process_ink_layer(
            text_layer_rgba=text_layer_rgba,
            paper_noise=paper_mask.astype(float) / 255.0,
            ink_palette=ink_palette,
            seed=seed,
        )

        # 9. Composite text onto background
        composite = bg_image.copy()
        composite.paste(processed_text_layer, (0, 0), processed_text_layer)

        # 10. Draw historical manuscript margin rulings / decorative accents
        composite = self.ink_effects.draw_manuscript_decorations(
            canvas_image=composite,
            bbox_limits=layout_plan.bounding_box,
            layout_style=layout_style,
            script=script,
            rubric_color=ink_palette.get("rubric", (165, 42, 32)),
            seed=seed,
        )

        # 11. Apply physical distortions (folds, surface warp, uneven illumination, perspective)
        final_image = self.distortions.apply_all_distortions(
            image=composite,
            seed=seed,
            apply_folds=True,
            apply_warp=True,
            apply_lighting=True,
            apply_perspective=True,
        )

        # 12. Determine file paths
        filename_base = f"image_{image_index:03d}"
        img_dir = self.output_dir / script / split / "images"
        ann_dir = self.output_dir / script / split / "annotations"
        img_dir.mkdir(parents=True, exist_ok=True)
        ann_dir.mkdir(parents=True, exist_ok=True)

        image_path = img_dir / f"{filename_base}.png"
        annotation_path = ann_dir / f"{filename_base}.md"

        # Save image as high-quality PNG
        final_image.save(image_path, format="PNG", compress_level=3)

        # Save synchronized Markdown annotation
        self.annotation_writer.write_annotation(
            output_path=annotation_path,
            image_filename=f"{filename_base}.png",
            script=script,
            split=split,
            exact_text=exact_ground_truth,
            layout_style=layout_style,
            font_name=font_path.name,
            dimensions=(canvas_w, canvas_h),
            seed=seed,
        )

        meta = {
            "image_path": str(image_path),
            "annotation_path": str(annotation_path),
            "script": script,
            "split": split,
            "index": image_index,
            "layout_style": layout_style,
            "font": font_path.name,
        }

        return image_path, annotation_path, meta

    def generate_dataset(
        self,
        scripts: Optional[List[str]] = None,
        split_counts: Optional[Dict[str, int]] = None,
        sample_mode: bool = False,
        seed: Optional[int] = None,
        workers: int = 8,
    ) -> List[Dict]:
        """Generate complete dataset or sample set for specified scripts and splits in parallel."""
        import concurrent.futures

        if seed is None:
            seed = self.seed

        target_scripts = scripts or SUPPORTED_SCRIPTS
        counts = split_counts or (SAMPLE_SPLIT_COUNTS if sample_mode else DEFAULT_SPLIT_COUNTS)

        total_items = sum(counts.values()) * len(target_scripts)
        print(f"\n=======================================================")
        print(f"Starting Manuscript Generation (Total Target: {total_items})")
        print(f"Scripts: {target_scripts}")
        print(f"Split counts per script: {counts}")
        print(f"Base seed: {seed} | Parallel workers: {workers}")
        print(f"=======================================================\n")

        task_list = []
        global_idx = 1
        for script in target_scripts:
            folio_index_for_script = 1
            for split_name, count in counts.items():
                for _ in range(count):
                    item_seed = seed * 10007 + global_idx * 997 + 31
                    task_list.append((script, split_name, folio_index_for_script, item_seed))
                    folio_index_for_script += 1
                    global_idx += 1

        generated_records: List[Dict] = []
        with tqdm(total=total_items, desc="Generating Folios") as pbar:
            if workers > 1 and len(task_list) > 1:
                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                    future_to_task = {
                        executor.submit(
                            self.generate_single_folio,
                            script=t[0],
                            split=t[1],
                            image_index=t[2],
                            seed=t[3],
                        ): t
                        for t in task_list
                    }
                    for future in concurrent.futures.as_completed(future_to_task):
                        img_path, ann_path, meta = future.result()
                        generated_records.append(meta)
                        pbar.update(1)
            else:
                for t in task_list:
                    img_path, ann_path, meta = self.generate_single_folio(
                        script=t[0],
                        split=t[1],
                        image_index=t[2],
                        seed=t[3],
                    )
                    generated_records.append(meta)
                    pbar.update(1)

        print(f"\nSuccessfully generated {len(generated_records)} folios across {len(target_scripts)} scripts.")
        return generated_records
