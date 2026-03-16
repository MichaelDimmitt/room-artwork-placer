"""
Manual extraction script - extracts artwork regions based on pre-analyzed coordinates.
Run this after coordinates have been determined by visual analysis.
"""

import json
from pathlib import Path
from PIL import Image

# Detections from visual analysis of the 5 input photos
# Coordinates are [x, y] for top_left and bottom_right
# All photos are 4000x3000 except photo1.jpg which is 2334x1556

# Precise frame boundary coordinates
# Images are 4000x3000 except photo1.jpg (2334x1556)
# Coordinates are [x, y] for top_left and bottom_right of the FRAME edges
# x increases left to right, y increases top to bottom

DETECTIONS = {
    # Photo 1: Single framed owl print on white wall (shot straight on, slight angle)
    "20260315_152038.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "owls_print",
                "description": "Framed print of owls on pine branches with brown/tan mat and gold frame",
                "top_left_px": [1005, 475],
                "bottom_right_px": [2595, 2045],
                "estimated_real_width_inches": 16,
                "estimated_real_height_inches": 20,
                "size_reference": "Standard framed print with wide mat",
                "confidence": "high"
            }
        ]
    },
    # Photo 2: Three pieces - rotated 90 degrees CCW (wood panel left, chains bottom, expressionist right)
    # When viewing: wood panel is on left side, chains canvas horizontal in middle-bottom, framed piece upper right
    "20260315_152052.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "wood_cityscape",
                "description": "Wood-burned cityscape panel with buildings and figures",
                "top_left_px": [85, 620],
                "bottom_right_px": [1320, 2180],
                "estimated_real_width_inches": 18,
                "estimated_real_height_inches": 24,
                "size_reference": "Wood panel, approximately 18x24 inches",
                "confidence": "high"
            },
            {
                "id": "colorful_chains",
                "description": "Interlocking circles/Olympic rings style on white canvas",
                "top_left_px": [1320, 1520],
                "bottom_right_px": [2620, 2180],
                "estimated_real_width_inches": 36,
                "estimated_real_height_inches": 12,
                "size_reference": "Wide horizontal canvas, about 36x12 inches",
                "confidence": "high"
            },
            {
                "id": "abstract_expressionist",
                "description": "Abstract expressionist painting - blues, yellows, grays in silver frame",
                "top_left_px": [2420, 420],
                "bottom_right_px": [3350, 1350],
                "estimated_real_width_inches": 14,
                "estimated_real_height_inches": 14,
                "size_reference": "Square format in frame, approximately 14x14 inches",
                "confidence": "high"
            }
        ]
    },
    # Photo 3: Four pieces - image is 4000x3000
    # As displayed: gray doves bottom-left, woman in yellow bottom-right, city print middle-right, blue moon top-right
    "20260315_152101.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "gray_doves",
                "description": "Abstract white doves/birds on gray background - thin gold frame - ON WALL",
                "top_left_px": [318, 1948],
                "bottom_right_px": [1328, 2878],
                "estimated_real_width_inches": 30,
                "estimated_real_height_inches": 24,
                "size_reference": "Large horizontal piece on wall, about 30x24 inches",
                "confidence": "high"
            },
            {
                "id": "woman_yellow_field",
                "description": "Woman in blue dress reclining in yellow flower field - gold frame - LEANING",
                "top_left_px": [2555, 2048],
                "bottom_right_px": [3325, 2820],
                "estimated_real_width_inches": 18,
                "estimated_real_height_inches": 14,
                "size_reference": "Medium painting in ornate gold frame",
                "confidence": "high"
            },
            {
                "id": "city_rooftops_print",
                "description": "Colorful city rooftops print - white mat, black frame - LEANING",
                "top_left_px": [2908, 1468],
                "bottom_right_px": [3508, 2028],
                "estimated_real_width_inches": 12,
                "estimated_real_height_inches": 10,
                "size_reference": "Small framed print with mat",
                "confidence": "high"
            },
            {
                "id": "blue_moonlit_scene",
                "description": "Blue moonlit night scene - small gold frame - ON WALL TOP",
                "top_left_px": [3048, 688],
                "bottom_right_px": [3648, 1048],
                "estimated_real_width_inches": 12,
                "estimated_real_height_inches": 8,
                "size_reference": "Small horizontal piece",
                "confidence": "high"
            }
        ]
    },
    # Photo 4: Single wave lines painting - rotated 90 degrees CCW
    "20260315_152108.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "wave_lines",
                "description": "Blue and white abstract with flowing contour lines - thin gold frame",
                "top_left_px": [1020, 580],
                "bottom_right_px": [2600, 2020],
                "estimated_real_width_inches": 30,
                "estimated_real_height_inches": 24,
                "size_reference": "Large piece, compared to desk chair about 30x24 inches",
                "confidence": "high"
            }
        ]
    },
    # Photo 5: Multiple stacked paintings - shot straight on (2334x1556)
    "photo1.jpg": {
        "image_width": 2334,
        "image_height": 1556,
        "artworks": [
            {
                "id": "abstract_orange_black",
                "description": "Large abstract - orange, black, white expressionist canvas - LEFT CENTER",
                "top_left_px": [285, 510],
                "bottom_right_px": [978, 855],
                "estimated_real_width_inches": 40,
                "estimated_real_height_inches": 24,
                "size_reference": "Largest piece in photo, approximately 40x24 inches",
                "confidence": "high"
            },
            {
                "id": "woman_portrait",
                "description": "Portrait of woman looking over shoulder - warm earth tones - FAR LEFT BOTTOM",
                "top_left_px": [0, 555],
                "bottom_right_px": [175, 1020],
                "estimated_real_width_inches": 12,
                "estimated_real_height_inches": 18,
                "size_reference": "Small portrait canvas",
                "confidence": "high"
            },
            {
                "id": "red_organic_shapes",
                "description": "Red/orange organic curved shapes on white background - TOP CENTER",
                "top_left_px": [958, 82],
                "bottom_right_px": [1195, 545],
                "estimated_real_width_inches": 14,
                "estimated_real_height_inches": 20,
                "size_reference": "Medium vertical canvas",
                "confidence": "high"
            },
            {
                "id": "geometric_sailboats",
                "description": "Geometric abstract with red triangles/sailboats - black frame - leaning in front",
                "top_left_px": [918, 758],
                "bottom_right_px": [1168, 1205],
                "estimated_real_width_inches": 16,
                "estimated_real_height_inches": 20,
                "size_reference": "Medium framed piece",
                "confidence": "high"
            },
            {
                "id": "blue_mountain_landscape",
                "description": "Blue mountain/waterfall Asian style landscape - two panels - FAR RIGHT TOP",
                "top_left_px": [1452, 42],
                "bottom_right_px": [1875, 605],
                "estimated_real_width_inches": 24,
                "estimated_real_height_inches": 32,
                "size_reference": "Vertical diptych panels",
                "confidence": "high"
            },
            {
                "id": "horse_drawing",
                "description": "Horse sketch in black frame - CENTER",
                "top_left_px": [1182, 515],
                "bottom_right_px": [1382, 902],
                "estimated_real_width_inches": 10,
                "estimated_real_height_inches": 14,
                "size_reference": "Small framed sketch",
                "confidence": "medium"
            },
            {
                "id": "yellow_venice_scene",
                "description": "Yellow/ochre cityscape - Venice scene - RIGHT BOTTOM",
                "top_left_px": [1275, 715],
                "bottom_right_px": [1672, 1152],
                "estimated_real_width_inches": 18,
                "estimated_real_height_inches": 18,
                "size_reference": "Square format canvas",
                "confidence": "high"
            },
            {
                "id": "sunflower_simple",
                "description": "Simple line drawing of daisy/sunflower - CENTER RIGHT",
                "top_left_px": [1372, 422],
                "bottom_right_px": [1545, 732],
                "estimated_real_width_inches": 8,
                "estimated_real_height_inches": 12,
                "size_reference": "Small framed print",
                "confidence": "medium"
            }
        ]
    }
}


def extract_artwork(image_path: str, artwork: dict, output_dir: Path) -> dict:
    """Extract a single artwork region from an image - precise frame boundaries, no padding."""
    img = Image.open(image_path)

    tl = artwork["top_left_px"]
    br = artwork["bottom_right_px"]

    # Exact frame boundaries - no padding
    x1 = max(0, tl[0])
    y1 = max(0, tl[1])
    x2 = min(img.width, br[0])
    y2 = min(img.height, br[1])

    cropped = img.crop((x1, y1, x2, y2))

    output_file = output_dir / f"{artwork['id']}.jpg"
    cropped.save(output_file, quality=95)

    return {
        "id": artwork["id"],
        "source_image": image_path,
        "extracted_file": str(output_file),
        "extracted_width_px": cropped.width,
        "extracted_height_px": cropped.height,
        "estimated_real_width_inches": artwork.get("estimated_real_width_inches"),
        "estimated_real_height_inches": artwork.get("estimated_real_height_inches"),
        "size_reference": artwork.get("size_reference"),
        "description": artwork.get("description"),
        "confidence": artwork.get("confidence"),
    }


def run(
    input_dir: str = "input/artwork",
    output_dir: str = "results/extracted",
    detections_file: str = "results/artwork_detections.json",
):
    """Extract all artworks based on pre-analyzed coordinates."""
    print("\n[Extract] Extracting paintings from images...")

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_detections = []
    extracted_artworks = []

    for filename, detection in DETECTIONS.items():
        image_path = input_path / filename
        if not image_path.exists():
            print(f"  Skipping {filename} - not found")
            continue

        print(f"  Processing: {filename}")
        detection["source_image"] = str(image_path)
        all_detections.append(detection)

        for artwork in detection.get("artworks", []):
            try:
                extracted = extract_artwork(str(image_path), artwork, output_path)
                extracted_artworks.append(extracted)
                print(f"    Extracted: {artwork['id']} ({extracted['extracted_width_px']}x{extracted['extracted_height_px']}px)")
            except Exception as e:
                print(f"    Failed: {artwork['id']} - {e}")

    # Save detection results
    results = {
        "detections": all_detections,
        "extracted_artworks": extracted_artworks,
    }

    with open(detections_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  Extracted {len(extracted_artworks)} artwork(s) to {output_dir}/")
    print(f"  Detection data saved to {detections_file}")

    return results


if __name__ == "__main__":
    run()
