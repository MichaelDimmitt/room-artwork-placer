"""
Step 1: Analyze apartment room photos using Claude Vision.
Outputs a JSON file describing wall zones, colors, lighting, and style per room.
"""

import anthropic
import base64
import json
import os
import sys
from pathlib import Path


def encode_image(image_path: str) -> tuple[str, str]:
    """Base64-encode an image and detect its media type."""
    ext = Path(image_path).suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


ROOM_ANALYSIS_PROMPT = """
You are an expert interior designer analyzing a room photo to identify where artwork can be placed.

Analyze this room image and return ONLY a valid JSON object (no markdown, no explanation) with this structure:

{
  "room_type": "living room | bedroom | hallway | dining room | office | other",
  "style": "modern | traditional | minimalist | industrial | bohemian | scandinavian | other",
  "dominant_colors": ["#hexcolor1", "#hexcolor2", "#hexcolor3"],
  "lighting": "bright natural | dim natural | warm artificial | cool artificial | mixed",
  "walls": [
    {
      "id": "wall_A",
      "position": "left | right | back | above_sofa | above_fireplace | hallway",
      "approximate_width_px": 800,
      "approximate_height_px": 600,
      "top_left_px": [100, 50],
      "bottom_right_px": [900, 650],
      "color": "#hexcolor",
      "is_best_candidate": true,
      "obstructions": "none | window | door | shelving | light_switch",
      "notes": "Large unobstructed wall, great for a statement piece"
    }
  ],
  "best_wall_id": "wall_A",
  "recommended_art_size": "small (under 24in) | medium (24-36in) | large (36-60in) | oversized (60in+)",
  "mood": "calm | energetic | cozy | formal | playful | dramatic",
  "general_notes": "Brief design observations about the space"
}

Be precise with pixel coordinates based on what you see in the image.
"""


def analyze_room(image_path: str, client: anthropic.Anthropic) -> dict:
    """Send a room image to Claude Vision and get structured analysis back."""
    print(f"  Analyzing room: {Path(image_path).name}")
    img_data, media_type = encode_image(image_path)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data,
                        },
                    },
                    {"type": "text", "text": ROOM_ANALYSIS_PROMPT},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def run(input_dir: str = "input/apartment", output_file: str = "rooms_analysis.json"):
    client = anthropic.Anthropic()
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"ERROR: Input directory '{input_dir}' not found.")
        print("Create it and add your apartment photos.")
        sys.exit(1)

    image_files = sorted(
        [
            f
            for f in input_path.iterdir()
            if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ]
    )

    if not image_files:
        print(f"No images found in {input_dir}")
        sys.exit(1)

    print(f"\n[Step 1] Analyzing {len(image_files)} room photo(s)...")
    results = {}

    for img_path in image_files:
        try:
            analysis = analyze_room(str(img_path), client)
            analysis["source_image"] = str(img_path)
            results[img_path.stem] = analysis
            print(f"    ✓ {img_path.name} → {analysis.get('room_type', 'unknown')} | best wall: {analysis.get('best_wall_id')}")
        except Exception as e:
            print(f"    ✗ {img_path.name} → ERROR: {e}")

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  Saved room analysis → {output_file}")
    return results


if __name__ == "__main__":
    run()
