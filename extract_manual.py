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
    # Owl portrait - single framed print on white wall (4000x3000) - STRAIGHT ON
    # This one is correct already
    "owl_portrait_and_frame.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "owls_print",
                "description": "Framed print of owls on pine branches with brown/tan mat and gold frame",
                "top_left_px": [970, 440],
                "bottom_right_px": [2640, 2100],
                "estimated_real_width_inches": 16,
                "estimated_real_height_inches": 20,
                "size_reference": "Standard framed print with wide mat",
                "confidence": "high"
            }
        ]
    },
    # Wave painting - rotated 90 CCW (4000x3000)
    # Frame left edge ~880, right edge ~2780, top ~530, bottom ~2150
    "1painting_with_frame.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "wave_lines",
                "description": "Blue and white abstract with flowing contour lines - thin gold frame",
                "top_left_px": [880, 530],
                "bottom_right_px": [2780, 2150],
                "estimated_real_width_inches": 30,
                "estimated_real_height_inches": 24,
                "size_reference": "Large piece above desk",
                "confidence": "high"
            }
        ]
    },
    # 3 paintings - rotated 90 CCW (4000x3000)
    "3paintings_2_with_frames.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "wood_cityscape",
                "description": "Wood-burned cityscape panel with buildings and figures",
                "top_left_px": [50, 400],
                "bottom_right_px": [1400, 2450],
                "estimated_real_width_inches": 18,
                "estimated_real_height_inches": 24,
                "size_reference": "Wood panel, approximately 18x24 inches",
                "confidence": "high"
            },
            {
                "id": "colorful_chains",
                "description": "Interlocking circles/Olympic rings style on white canvas",
                "top_left_px": [1380, 1350],
                "bottom_right_px": [2850, 2450],
                "estimated_real_width_inches": 36,
                "estimated_real_height_inches": 12,
                "size_reference": "Wide horizontal canvas, about 36x12 inches",
                "confidence": "high"
            },
            {
                "id": "abstract_expressionist",
                "description": "Abstract expressionist painting - blues, yellows, grays in silver frame",
                "top_left_px": [2350, 200],
                "bottom_right_px": [3550, 1450],
                "estimated_real_width_inches": 14,
                "estimated_real_height_inches": 14,
                "size_reference": "Square format in frame, approximately 14x14 inches",
                "confidence": "high"
            }
        ]
    },
    # 4 paintings - rotated 90 CCW (4000x3000)
    "4paintings_with_frames.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "gray_doves",
                "description": "Abstract white doves/birds on gray background - thin gold frame - ON WALL",
                "top_left_px": [150, 1700],
                "bottom_right_px": [1450, 3000],
                "estimated_real_width_inches": 30,
                "estimated_real_height_inches": 24,
                "size_reference": "Large horizontal piece on wall, about 30x24 inches",
                "confidence": "high"
            },
            {
                "id": "woman_yellow_field",
                "description": "Woman in blue dress reclining in yellow flower field - gold frame - LEANING",
                "top_left_px": [2350, 1800],
                "bottom_right_px": [3450, 2950],
                "estimated_real_width_inches": 18,
                "estimated_real_height_inches": 14,
                "size_reference": "Medium painting in ornate gold frame",
                "confidence": "high"
            },
            {
                "id": "city_rooftops_print",
                "description": "Colorful city rooftops print - white mat, black frame - LEANING",
                "top_left_px": [2700, 1150],
                "bottom_right_px": [3700, 2000],
                "estimated_real_width_inches": 12,
                "estimated_real_height_inches": 10,
                "size_reference": "Small framed print with mat",
                "confidence": "high"
            },
            {
                "id": "blue_moonlit_scene",
                "description": "Blue moonlit night scene - small gold frame - ON WALL TOP",
                "top_left_px": [2900, 500],
                "bottom_right_px": [3800, 1200],
                "estimated_real_width_inches": 12,
                "estimated_real_height_inches": 8,
                "size_reference": "Small horizontal piece",
                "confidence": "high"
            }
        ]
    },
    # 8+ paintings stacked - STRAIGHT ON (2334x1556)
    "8_pantings_with_frame_and1paintings_without_frame.jpg": {
        "image_width": 2334,
        "image_height": 1556,
        "artworks": [
            {
                "id": "abstract_orange_black",
                "description": "Large abstract - orange, black, white expressionist canvas",
                "top_left_px": [200, 250],
                "bottom_right_px": [1030, 950],
                "estimated_real_width_inches": 40,
                "estimated_real_height_inches": 30,
                "size_reference": "Largest piece in photo",
                "confidence": "high"
            },
            {
                "id": "woman_portrait",
                "description": "Portrait of woman looking over shoulder - warm earth tones - FAR LEFT",
                "top_left_px": [0, 440],
                "bottom_right_px": [230, 1100],
                "estimated_real_width_inches": 12,
                "estimated_real_height_inches": 18,
                "size_reference": "Small portrait canvas",
                "confidence": "high"
            },
            {
                "id": "red_organic_shapes",
                "description": "Red/orange organic curved shapes on white background - TOP CENTER",
                "top_left_px": [950, 20],
                "bottom_right_px": [1220, 600],
                "estimated_real_width_inches": 14,
                "estimated_real_height_inches": 20,
                "size_reference": "Medium vertical canvas",
                "confidence": "high"
            },
            {
                "id": "geometric_sailboats",
                "description": "Geometric abstract with red triangles/sailboats - black frame",
                "top_left_px": [870, 680],
                "bottom_right_px": [1200, 1300],
                "estimated_real_width_inches": 16,
                "estimated_real_height_inches": 20,
                "size_reference": "Medium framed piece",
                "confidence": "high"
            },
            {
                "id": "blue_mountain_diptych",
                "description": "Blue mountain/waterfall Asian style - TWO PANELS",
                "top_left_px": [1430, 0],
                "bottom_right_px": [1920, 640],
                "estimated_real_width_inches": 24,
                "estimated_real_height_inches": 32,
                "size_reference": "Vertical diptych panels",
                "confidence": "high"
            },
            {
                "id": "horse_drawing",
                "description": "Horse sketch in black frame - CENTER",
                "top_left_px": [1160, 440],
                "bottom_right_px": [1420, 960],
                "estimated_real_width_inches": 10,
                "estimated_real_height_inches": 14,
                "size_reference": "Small framed sketch",
                "confidence": "medium"
            },
            {
                "id": "yellow_venice_scene",
                "description": "Yellow/ochre cityscape - Venice scene - RIGHT BOTTOM",
                "top_left_px": [1200, 660],
                "bottom_right_px": [1730, 1210],
                "estimated_real_width_inches": 18,
                "estimated_real_height_inches": 18,
                "size_reference": "Square format canvas",
                "confidence": "high"
            },
            {
                "id": "sunflower_simple",
                "description": "Simple line drawing of daisy/sunflower with hand",
                "top_left_px": [1340, 360],
                "bottom_right_px": [1600, 800],
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
