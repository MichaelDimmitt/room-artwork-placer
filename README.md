# Art Placement Pipeline

Digitally composite artwork onto apartment photos using Claude Vision + OpenCV + ImageMagick.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design documentation.

## Setup

```bash
pip install opencv-python anthropic numpy Pillow requests
brew install imagemagick   # macOS
# OR: sudo apt-get install imagemagick  # Linux
```

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Project Structure

```
room-artwork-placer/
├── input/
│   ├── apartment/     # Room photos go here
│   └── artwork/       # Artwork photos go here
├── results/           # Generated composites and gallery
├── docs/
│   ├── ARCHITECTURE.md
│   └── REQUIREMENTS.md
└── *.py               # Pipeline modules
```

## Usage

```bash
# 1. Add your photos to the input folders
#    input/apartment/  - room photos
#    input/artwork/    - artwork photos

# 2. Generate a gallery preview of your artwork collection
python generate_gallery.py

# 3. Run the full placement pipeline
python run_pipeline.py

# 4. View results in /results folder + placement_report.md
```

## Modules

| Module | Description |
|--------|-------------|
| `generate_gallery.py` | Create side-by-side gallery of artwork (true to size) |
| `analyze_rooms.py` | Claude Vision extracts wall zones from room photos |
| `analyze_art.py` | Claude Vision analyzes artwork style/color/mood |
| `match_and_place.py` | Score and match artworks to walls |
| `composite.py` | OpenCV warps + blends artwork onto walls |
| `generate_report.py` | Generate Markdown placement report |
| `run_pipeline.py` | Orchestrate full pipeline end-to-end |
