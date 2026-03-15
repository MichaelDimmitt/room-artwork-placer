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

## Usage

```bash
# 1. Drop your photos into the right folders
mkdir -p input/apartment input/artwork results

# 2. Run the full pipeline
python run_pipeline.py

# 3. View results in /results folder + placement_report.md
```

## Pipeline Steps
1. `analyze_rooms.py`   — Claude Vision reads each room, outputs wall zones as JSON
2. `analyze_art.py`     — Claude Vision reads each artwork, outputs style/color/size JSON  
3. `match_and_place.py` — Scores and matches artworks to walls
4. `composite.py`       — OpenCV warps + ImageMagick blends artwork onto walls
5. `run_pipeline.py`    — Orchestrates all steps end-to-end
