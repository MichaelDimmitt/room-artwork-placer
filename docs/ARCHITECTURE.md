# Architecture

This document describes the design and data flow of the Art Placement Pipeline.

## Overview

The pipeline uses Claude Vision to analyze room photos and artwork images, then applies computer vision techniques to composite artwork onto walls with realistic perspective and lighting.

```
┌─────────────────┐     ┌─────────────────┐
│  Room Photos    │     │  Artwork Images │
│  (input/apt)    │     │  (input/art)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ analyze_rooms   │     │  analyze_art    │
│ (Claude Vision) │     │ (Claude Vision) │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ rooms_analysis  │     │ artwork_analysis│
│    .json        │     │    .json        │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
            ┌─────────────────┐
            │ match_and_place │
            │  (scoring algo) │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ placement_plan  │
            │     .json       │
            └────────┬────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   composite     │     │ generate_report │
│ (OpenCV + PIL)  │     │   (Markdown)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ results/*.jpg   │     │ placement_report│
│ (composited)    │     │     .md         │
└─────────────────┘     └─────────────────┘
```

## Modules

### 0. generate_gallery.py

**Purpose:** Create a side-by-side gallery composite of all artwork pieces.

**Input:** Directory of artwork images (`input/artwork/`)

**Output:** `results/gallery.jpg`

**Key features:**
- **True to size**: No scaling or resizing of artwork
- Each piece maintains original dimensions
- Vertically centered on a neutral background
- Configurable padding between pieces

**CLI usage:**
```bash
python generate_gallery.py
python generate_gallery.py --input input/artwork --output results/gallery.jpg --padding 40
```

---

### 1. analyze_rooms.py

**Purpose:** Extract wall zones and room characteristics from apartment photos.

**Input:** Directory of room images (JPG, PNG, WebP)

**Output:** `rooms_analysis.json`

**Claude Vision prompt extracts:**
- Room type (living room, bedroom, hallway, etc.)
- Design style (modern, minimalist, bohemian, etc.)
- Dominant colors (hex values)
- Lighting conditions
- Wall zones with pixel coordinates (`top_left_px`, `bottom_right_px`)
- Best candidate wall for artwork
- Obstructions (windows, doors, shelving)

**Design decisions:**
- Pixel coordinates are relative to the source image dimensions
- Multiple walls can be identified, but only `is_best_candidate: true` walls are used for matching
- JSON parsing strips markdown fences if Claude returns them

### 2. analyze_art.py

**Purpose:** Analyze artwork characteristics for matching and display recommendations.

**Input:** Directory of artwork images

**Output:** `artwork_analysis.json`

**Claude Vision prompt extracts:**
- Medium (oil, watercolor, photography, digital, etc.)
- Style (abstract, figurative, minimalist, etc.)
- Color palette with hex values
- Color temperature (warm, cool, neutral)
- Mood (calm, energetic, dramatic, etc.)
- Visual weight
- Aspect ratio
- Room type recommendations
- Framing/matting suggestions
- Pairing advice (what to pair with, what to avoid)

**Design decisions:**
- Curator perspective for actionable recommendations
- Framing suggestions feed into the compositing step

### 3. match_and_place.py

**Purpose:** Score and match artworks to room walls using weighted criteria.

**Input:** `rooms_analysis.json`, `artwork_analysis.json`

**Output:** `placement_plan.json`

**Scoring algorithm (weights):**
| Factor | Weight | Description |
|--------|--------|-------------|
| Color harmony | 35% | RGB distance with sweet spot for contrast |
| Style compatibility | 25% | Room style to art style affinities |
| Room type match | 25% | Art's recommended rooms vs actual room |
| Mood match | 15% | Compatible mood pairings |
| Obstruction penalty | -20% | Deduction if wall has obstructions |

**Color harmony scoring:**
- Computes Euclidean distance in RGB space
- Ideal contrast: normalized distance 0.3-0.65 (not too similar, not clashing)
- Too similar (< 0.3): reduced score
- Too different (> 0.65): reduced score

**Assignment algorithm:**
- Greedy: sort all candidates by score descending
- Each artwork used once, each wall used once
- First valid match wins

### 4. composite.py

**Purpose:** Render artwork onto room walls with realistic perspective and effects.

**Input:** `placement_plan.json`, `rooms_analysis.json`, source images

**Output:** Composited images in `results/`

**Processing steps:**
1. Load room image (OpenCV) and artwork image (PIL)
2. Extract wall corners from analysis data
3. Resize artwork to fit wall zone (with 12% padding)
4. Adjust brightness/color for room lighting
5. Add frame/mat based on artwork recommendations
6. Add drop shadow
7. Compute perspective transform matrix
8. Warp artwork onto room canvas
9. Blend using mask

**Lighting adjustments:**
| Lighting Type | Brightness | Color Saturation |
|---------------|------------|------------------|
| Bright natural | +5% | unchanged |
| Dim/warm artificial | -12% | -8% |
| Cool artificial | unchanged | +5% |

**Frame styles:**
- White mat: 5% border, off-white color
- Wood frame: 4% border, warm brown
- No frame: thin 3px edge
- Default: 3% dark frame

### 5. generate_report.py

**Purpose:** Create human-readable placement recommendations.

**Input:** `placement_plan.json`

**Output:** `placement_report.md`

**Report includes:**
- Score breakdown with visual bars
- Design rationale (style, mood, framing)
- Embedded preview images
- Installation tips (hanging height, spacing)

### 6. run_pipeline.py

**Purpose:** Orchestrate the full workflow with validation.

**Steps:**
1. Check dependencies (anthropic, cv2, PIL, numpy, API key)
2. Validate input directories have images
3. Run analyze_rooms
4. Run analyze_art
5. Run match_and_place
6. Run composite
7. Run generate_report

**CLI arguments:**
- `--apartment`: Room photos directory (default: `input/apartment`)
- `--artwork`: Artwork directory (default: `input/artwork`)
- `--output`: Results directory (default: `results`)

## Data Formats

### rooms_analysis.json

```json
{
  "room_001": {
    "source_image": "input/apartment/living.jpg",
    "room_type": "living room",
    "style": "modern",
    "dominant_colors": ["#E8E4E0", "#8B7355", "#2F4F4F"],
    "lighting": "bright natural",
    "walls": [
      {
        "id": "wall_A",
        "position": "above_sofa",
        "top_left_px": [120, 80],
        "bottom_right_px": [850, 520],
        "is_best_candidate": true,
        "obstructions": "none"
      }
    ],
    "best_wall_id": "wall_A",
    "mood": "calm"
  }
}
```

### artwork_analysis.json

```json
{
  "art_001": {
    "source_image": "input/artwork/abstract.jpg",
    "title_guess": "Blue Horizon",
    "medium": "oil painting",
    "style": "abstract",
    "dominant_colors": ["#1E3A5F", "#E8DCC4", "#C4A484"],
    "color_temperature": "cool",
    "mood": "calm",
    "recommended_room_types": ["living room", "office"],
    "matting_suggestion": "natural wood frame"
  }
}
```

### placement_plan.json

```json
[
  {
    "room_id": "room_001",
    "wall_id": "wall_A",
    "art_id": "art_001",
    "room_image": "input/apartment/living.jpg",
    "art_image": "input/artwork/abstract.jpg",
    "score": 0.847,
    "score_breakdown": {
      "color_harmony": 0.92,
      "style_compatibility": 0.85,
      "room_type_match": 1.0,
      "mood_match": 0.6
    },
    "output_image": "results/result_01_room_001_art_001.jpg"
  }
]
```

## Dependencies

| Package | Purpose |
|---------|---------|
| anthropic | Claude API client for Vision analysis |
| opencv-python | Perspective transformation, image I/O |
| Pillow | Image manipulation, frame effects |
| numpy | Array operations for OpenCV |
| ImageMagick | (optional) Advanced blending via CLI |

## Limitations

- Wall coordinates from Claude are estimates; complex room geometries may need manual adjustment
- Single artwork per wall; no gallery wall layouts
- Perspective warp is simplified (planar assumption)
- No occlusion handling for furniture in front of walls
