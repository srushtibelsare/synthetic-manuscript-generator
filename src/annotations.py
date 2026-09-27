"""Annotations generator for Synthetic Manuscripts.
Produces synchronized ground-truth Markdown (.md) annotation files for every
generated manuscript image with full metadata and exact rendered transcription.
"""

from pathlib import Path
from typing import Dict, Optional


class ManuscriptAnnotationWriter:
    """Writes standardized ground-truth Markdown annotations matching manuscript folios."""

    @staticmethod
    def write_annotation(
        output_path: Path,
        image_filename: str,
        script: str,
        split: str,
        exact_text: str,
        layout_style: str,
        font_name: str,
        dimensions: tuple,
        seed: int,
        extra_meta: Optional[Dict] = None,
    ) -> Path:
        """Write a complete, structured Markdown annotation file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = exact_text.strip().split("\n") if exact_text.strip() else []
        line_count = len(lines)
        char_count = sum(len(l) for l in lines)
        word_count = sum(len(l.split()) for l in lines)

        md_content = f"""---
image_file: "{image_filename}"
script: "{script}"
split: "{split}"
layout_style: "{layout_style}"
font_name: "{font_name}"
width: {dimensions[0]}
height: {dimensions[1]}
seed: {seed}
line_count: {line_count}
word_count: {word_count}
character_count: {char_count}
---

# Manuscript Ground-Truth Annotation

**Script**: {script.capitalize()}  
**Image Reference**: `{image_filename}`  
**Layout Format**: {layout_style}  
**Line Count**: {line_count}  

---

## Transcription

{exact_text}

---
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return output_path
