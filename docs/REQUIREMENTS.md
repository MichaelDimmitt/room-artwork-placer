# Requirements

## REQ-001: Artwork Gallery Generation

**Status:** Implemented (`generate_gallery.py`)

**Description:**
Generate a gallery composite image showing all artwork pieces side by side for visual reference before wall placement.

**Inputs:**
- Raw artwork photos in `input/artwork/`

**Outputs:**
- Gallery composite image showing all pieces arranged together

**Constraints:**
- Raw photos must be preserved as-is (no modifications to originals)
- **True to size**: Each artwork maintains its original dimensions
- No resizing or scaling to match other pieces (no uniform height/width)
- Simple side-by-side layout for analysis

**Purpose:**
Provide a visual overview of the full collection as it would appear in reality, useful for:
- Seeing how pieces relate to each other at actual scale
- Planning which pieces work together
- Reference before placement onto walls

---

## REQ-002: Gitignore for Photos

**Status:** Implemented (`.gitignore`)

**Description:**
Add `.gitignore` rules to prevent image files from being committed to the repository.

**Files to ignore:**
- Input photos (`input/` directory)
- Generated results (`results/` directory)
- Common image formats: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.bmp`, `.tiff`

**Purpose:**
- Keep repository size small
- Prevent accidental upload of personal photos
- Only track code and documentation
