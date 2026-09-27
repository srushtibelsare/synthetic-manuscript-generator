# Synthetic Manuscript Generator (Indic Historical Folio Pipeline)

An end-to-end, high-performance Python pipeline that generates hyper-realistic synthetic historical manuscript folios with synchronized, character-exact ground-truth annotations across three classical Indic scripts: **Devanagari**, **Modi**, and **Sharada**.

Designed for document image analysis (DIA), historical Optical Character Recognition (OCR), Handwritten Text Recognition (HTR), and layout analysis benchmarks.

---

## Table of Contents

- [Objective](#objective)
- [Architecture & Pipeline Overview](#architecture--pipeline-overview)
- [Supported Scripts](#supported-scripts)
- [Input Manuscript Sources](#input-manuscript-sources)
- [Visual Realism & Manuscript Effects](#visual-realism--manuscript-effects)
- [Layout Varietals & Auto-Fitting](#layout-varietals--auto-fitting)
- [Installation & Dependencies](#installation--dependencies)
- [Typography & Fonts](#typography--fonts)
- [Usage Guide](#usage-guide)
  - [Sample Generation (6 Images)](#sample-generation-6-images)
  - [Full Dataset Generation (300 Images)](#full-dataset-generation-300-images)
  - [Custom / Single Script Generation](#custom--single-script-generation)
  - [Dataset Validation](#dataset-validation)
- [Dataset Structure & 85/10/5 Split](#dataset-structure--85105-split)
- [Hugging Face Dataset Preparation](#hugging-face-dataset-preparation)
- [Reproducibility](#reproducibility)
- [Limitations & Future Scope](#limitations--future-scope)

---

## Objective

Historical Indic manuscripts present immense challenges for automated preservation: centuries-old physical deterioration, fiber textures, ink bleeds, non-standard layouts, scribal hand variations, and scarce annotated ground truth.

This system bridges the data gap by synthetically rendering authentic, highly varied historical manuscript folios directly from authentic text corpora with:
1. **100% exact synchronized ground-truth transcription** (no OCR misalignment errors).
2. **Realistic physical aging physics**: fiber grain, aging stains, foxing, water tide lines, edge grime, binding apertures, creases, surface warping, uneven illumination, and perspective distortion.
3. **Organic handwriting & calligraphy dynamics**: baseline waviness, micro-slant jitter, imperfect kerning, varying ink darkness, and cinnabar red rubrication.
4. **Guaranteed zero text-overflow**: automatic layout fitting and boundary enforcement.

---

## Architecture & Pipeline Overview

```
                          ┌──────────────────────────┐
                          │   Original .md Corpora   │
                          │ (Devanagari/Modi/Sharada)│
                          └─────────────┬────────────┘
                                        │ (Byte-Offset Streaming)
                                        ▼
                          ┌──────────────────────────┐
                          │    Text Loader Engine    │
                          │  (src/text_loader.py)    │
                          └─────────────┬────────────┘
                                        │
                                        ▼
                          ┌──────────────────────────┐
                          │   Layout & Auto-Fitter   │
                          │    (src/layout.py)       │
                          └─────────────┬────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
       ┌────────────────────────┐              ┌────────────────────────┐
       │   Calligraphic Text    │              │ Background & Texture   │
       │  (src/text_renderer.py)│              │  (src/background.py)   │
       └────────────┬───────────┘              └────────────┬───────────┘
                    │                                       │
                    ▼                                       │
       ┌────────────────────────┐                           │
       │   Ink Physics Engine   │                           │
       │ (src/manuscript_effects│                           │
       └────────────┬───────────┘                           │
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        │ (Layer Composite)
                                        ▼
                          ┌──────────────────────────┐
                          │   Physical Distortions   │
                          │   (src/distortions.py)   │
                          └─────────────┬────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
       ┌────────────────────────┐              ┌────────────────────────┐
       │   PNG Folio Image      │              │ Matching Ground-Truth  │
       │   (image_xxx.png)      │              │  Markdown Annotation   │
       │                        │              │   (image_xxx.md)       │
       └────────────────────────┘              └────────────────────────┘
```

---

## Supported Scripts

| Script | Unicode Range | Historical Context & Sources |
|---|---|---|
| **Devanagari** | `U+0900 – U+097F` | Classical Sanskrit treatises, Ayurveda, philosophical texts |
| **Modi** | `U+11600 – U+1165F` | Historical Marathi administrative, legal, and literary archives |
| **Sharada** | `U+11180 – U+111DF` | Historical Kashmiri manuscripts, astronomy, and Vedic literature |

---

## Input Manuscript Sources

The pipeline processes raw, high-volume manuscript markdown files using **memory-safe byte-offset streaming**:
- `devanagari_md.md` (~22.3 MB, 78,550+ lines)
- `Modi_md.md` (~2.9 MB, 6,312+ lines)
- `sharada_md.md` (~29.4 MB, 78,550+ lines)

*Note: The generator does not load entire files into RAM. It builds a lightweight byte-offset index upon initialization, enabling sub-millisecond random seeking and deterministic passage extraction.*

---

## Visual Realism & Manuscript Effects

Each generated folio incorporates multi-layered physical and optical artifacts:

1. **Aged Paper & Substrate Synthesis**:
   - Multi-octave organic grain simulation (Perlin-like smooth noise).
   - Microscopic fibers (directional fibers for palm leaf; omnidirectional for rag paper).
   - Natural color palettes: Aged handmade paper, Golden palm-leaf, Weathered parchment, Bhurjapatra birch bark, Antique ochre.
   - Foxing spots & moisture pools with capillary tide-line rings.
   - Edge patina, corner grime, and handling darkening.
   - Binding cord apertures (punch holes) for palm-leaf pothi formats.

2. **Calligraphic & Scribal Dynamics**:
   - Organic baseline waviness (sinusoidal + random vertical drift per word).
   - Micro-slant jitter (-1.2° to +1.2° word rotation).
   - Imperfect spacing and kerning variation.
   - Natural stroke variations and dry-brush skips across rough fibers.
   - Rubrication: Cinnabar red (`#A52A20`) accents on opening invocations, mantras, and verse numbers (`॥`, `𑇆`, `।`, `𑇅`).
   - Yellow Haritala (orpiment) highlight wash behind key citations.
   - Traditional vertical margin ruling lines and column dividers.

3. **Physical Page Distortions**:
   - Storage creases and folding lines (highlight and shadow ridges).
   - 2D surface buckling / undulating mesh warp.
   - Uneven lighting gradients (archival desk lamp and natural illumination).
   - 3D perspective quad distortion.

---

## Layout Varietals & Auto-Fitting

The pipeline supports six manuscript formats with zero text clipping:
- **`standard_folio`**: Classic horizontal manuscript page with margins and line guides.
- **`palm_leaf`**: Elongated pothi leaf format (1600x560) with central cord apertures.
- **`commentary_bhasya`**: Large centered root verse (*mula*) framed by dense commentary (*tika*).
- **`dual_column`**: Two-column codex with central decorative separator.
- **`marginalia_codex`**: Central body block accompanied by glosses in the right margin.
- **`rubricated_verse`**: Cinnabar red section headers and highlighted verse markers.

---

## Installation & Dependencies

### Prerequisites
- Python 3.9+ (Python 3.10 - 3.13 supported)

### Install Requirements
```bash
pip install -r requirements.txt
```

### Dependencies
- `Pillow>=10.0.0` (Image processing, drawing, text rasterization)
- `numpy>=1.24.0` (Vectorized noise, gradients, fiber arrays)
- `scipy>=1.10.0` (Gaussian filters, multi-scale image processing)
- `tqdm>=4.65.0` (Progress bars)
- `matplotlib>=3.7.0` (Plotting and color utilities)

---

## Typography & Fonts

All fonts are stored in the local `fonts/` directory:

| Script | Configured Fonts |
|---|---|
| **Devanagari** | `NotoSansDevanagari-Regular.ttf`, `NotoSerifDevanagari-Regular.ttf`, `YatraOne-Regular.ttf` (Calligraphy), `Kalam-Regular.ttf` (Handwriting), `RozhaOne-Regular.ttf`, `Sahitya-Regular.ttf`, `Halant-Regular.ttf`, `Kurale-Regular.ttf`, `Amita-Regular.ttf`, `Gotu-Regular.ttf` |
| **Modi** | `NotoSansModi-Regular.ttf` |
| **Sharada** | `NotoSansSharada-Regular.ttf` |

---

## Usage Guide

### Sample Generation (6 Images)
Generates 2 sample folios per script (6 total) in `output_sample/` and runs automated validation immediately:
```bash
python generate.py --sample
```

### Full Dataset Generation (300 Images)
Generates the complete 300-image dataset (85 train, 10 val, 5 test per script) into `output/` with 8 parallel worker threads:
```bash
python generate.py --workers 8 --validate
```

### Custom / Single Script Generation
```bash
# Generate only Devanagari folios
python generate.py --script devanagari --count 50

# Generate with custom random seed
python generate.py --seed 12345

# Specify custom output directory
python generate.py --output-dir custom_output
```

### Dataset Validation
Run independent automated validation:
```bash
# Validate full 300-image dataset in output/
python validate.py

# Validate sample dataset in output_sample/
python validate.py --sample

# Validate a specific script
python validate.py --script modi
```

---

## Dataset Structure & 85/10/5 Split

The generated dataset follows the standard machine learning partitioned structure:

```
output/
├── devanagari/
│   ├── train/
│   │   ├── images/         # 85 PNG images (image_001.png ... image_085.png)
│   │   └── annotations/    # 85 MD files   (image_001.md ... image_085.md)
│   ├── validation/
│   │   ├── images/         # 10 PNG images (image_086.png ... image_095.png)
│   │   └── annotations/    # 10 MD files   (image_086.md ... image_095.md)
│   └── test/
│       ├── images/         # 5 PNG images  (image_096.png ... image_100.png)
│       └── annotations/    # 5 MD files    (image_096.md ... image_100.md)
│
├── modi/
│   ├── train/              # 85 images + 85 annotations
│   ├── validation/         # 10 images + 10 annotations
│   └── test/               # 5 images + 5 annotations
│
└── sharada/
    ├── train/              # 85 images + 85 annotations
    ├── validation/         # 10 images + 10 annotations
    └── test/               # 5 images + 5 annotations
```

### Summary of Counts

| Script | Train | Validation | Test | Total |
|---|:---:|:---:|:---:|:---:|
| **Devanagari** | 85 | 10 | 5 | **100** |
| **Modi** | 85 | 10 | 5 | **100** |
| **Sharada** | 85 | 10 | 5 | **100** |
| **Total** | **255** | **30** | **15** | **300** |

---

## Synchronized Annotation Schema

Each `.md` annotation file contains structured YAML frontmatter and exact UTF-8 transcription:

```markdown
---
image_file: "image_001.png"
script: "devanagari"
split: "train"
layout_style: "rubricated_verse"
font_name: "NotoSerifDevanagari-Regular.ttf"
width: 1400
height: 900
seed: 42
line_count: 5
word_count: 59
character_count: 428
---

# Manuscript Ground-Truth Annotation

**Script**: Devanagari  
**Image Reference**: `image_001.png`  
**Layout Format**: rubricated_verse  
**Line Count**: 5  

---

## Transcription

शृणु विस्तरतो लक्ष्मि भविष्यत् कथयामि तत् । द्वारकां वसमानस्य पुत्रदारसुतैः सह ॥ ७ ॥
प्रदक्षिणक्रमात् सार्धं पूर्ववद्गणिकादिभिः । क्षिपेयुर्द्वारबाह्ये वा बाह्यद्वारस्य बाह्यतः ॥ ॥
ततः किमभवत्तात कथ्यतां शशिमौलिनः । सत्याश्च चरितं दिव्यं सर्वाघौघविनाशनम् ॥ २ ॥
कृष्णस्य भवनं तत्र समायान्नारदो मुनिः । यथायोग्यं स्वागतं श्रीकृष्णस्तस्याऽकरोन्मुदा ॥ ८ ॥
अथवा विनियुक्तानि तानि संगृह्य योषितः । सुस्नाता धौतवसना द्विजातिभावितात्मनः ॥ ॥

---
```

---

## Hugging Face Dataset Preparation

The directory layout directly matches Hugging Face `datasets` folder structure. To load as an image-text dataset in Python:

```python
from datasets import load_dataset

# Load Devanagari subset
dataset = load_dataset(
    "imagefolder",
    data_dir="output/devanagari",
)

# Inspect train/validation/test splits
print(dataset)
```

---

## Reproducibility

- **Deterministic Seeding**: Every folio generation is tied to a composite mathematical seed: `master_seed * 10007 + global_index * 997 + 31`.
- Identical outputs are guaranteed on repeat runs with the same seed.
- Memory consumption remains strictly bounded (< 150 MB RAM) throughout 300-image batch runs.

---

## Limitations & Future Scope

### Current Limitations
1. Modi and Sharada currently have a single primary Unicode standard font available in open-source registries (`Noto Sans Modi` and `Noto Sans Sharada`).
2. Script ligatures in older rendering pipelines depend on FreeType HarfBuzz shaping support.

### Future Scope
- **Neural Style Transfer Augmentation**: Condition synthetic layouts on authentic historical GAN/Diffusion texture checkpoints.
- **Character Bounding Box & Polygon Ground Truth**: Export COCO/YOLO segmentation masks for word-level and character-level HTR.
- **Additional Scripts**: Extend pipeline to Grantha, Tigalari, Newari, and Nandinagari historical scripts.

- 
## Hugging Face Dataset

**Dataset Name:** `srushtibelsare/synthetic-manuscript-dataset`

**Dataset Link:** https://huggingface.co/datasets/srushtibelsare/synthetic-manuscript-dataset

The dataset contains 300 synthetic manuscript images with corresponding Markdown annotations across Devanagari, Modi, and Sharada scripts. It is organized into training, validation, and test splits.
