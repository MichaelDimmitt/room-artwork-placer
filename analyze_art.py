"""
Step 2: Analyze artwork images using Claude Vision.
Outputs a JSON file describing each artwork's palette, style, size, and ideal placement.
"""

import anthropic
import base64
import json
import os
import sys
from pathlib import Path


def encode_image(image_path: str) -> tuple[str, str]:
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


ARTWORK_ANALYSIS_PROMPT = """
You are an expert art curator and interior designer analyzing an artwork image.

Analyze this artwork and return ONLY a valid JSON object (no markdown, no explanation):

{
  "title_guess": "Brief descriptive title if unknown",
  "medium": "oil painting | watercolor | photography | print | digital | mixed media | sculpture | other",
  "style": "abstract | figurative | landscape | portrait | geometric | expressionist | minimalist | maximalist | illustrative | other",
  "dominant_colors": ["#hexcolor1", "#hexcolor2", "#hexcolor3"],
  "color_temperature": "warm | cool | neutral | mixed",
  "mood": "calm | energetic | melancholic | joyful | dramatic | mysterious | romantic | playful",
  "visual_weight": "light | medium | heavy",
  "estimated_aspect_ratio": "portrait | landscape | square",
  "recommended_room_types": ["living room", "bedroom"],
  "recommended_wall_styles": ["modern", "minimalist"],
  "ideal_placement": "above sofa | above fireplace | focal wall | hallway | bedroom wall | dining room",
  "sizing_notes": "This piece needs breathing room - best as a solo statement piece",
  "pairs_well_with": "neutral walls, warm wood tones",
  "avoid_pairing_with": "busy wallpaper, cold blue tones",
  "matting_suggestion": "white mat | natural wood frame | no frame | floating frame | gallery wrap",
  "design_notes": "Concise curator notes on how to display this piece effectively"
}
"""


def analyze_artwork(image_path: str, client: anthropic.Anthropic) -> dict:
    print(f"  Analyzing artwork: {Path(image_path).name}")
    img_data, media_type = encode_image(image_path)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1200,
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
                    {"type": "text", "text": ARTWORK_ANALYSIS_PROMPT},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def run(input_dir: str = "input/artwork", output_file: str = "artwork_analysis.json"):
    client = anthropic.Anthropic()
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"ERROR: Input directory '{input_dir}' not found.")
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

    print(f"\n[Step 2] Analyzing {len(image_files)} artwork(s)...")
    results = {}

    for img_path in image_files:
        try:
            analysis = analyze_artwork(str(img_path), client)
            analysis["source_image"] = str(img_path)
            results[img_path.stem] = analysis
            print(f"    ✓ {img_path.name} → {analysis.get('style')} | mood: {analysis.get('mood')}")
        except Exception as e:
            print(f"    ✗ {img_path.name} → ERROR: {e}")

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  Saved artwork analysis → {output_file}")
    return results


if __name__ == "__main__":
    run()
