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

DETECTIONS = {
    "20260315_152038.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "owls_print",
                "description": "Framed print of owls on pine branches with brown/tan mat",
                "top_left_px": [920, 430],
                "bottom_right_px": [2680, 2150],
                "estimated_real_width_inches": 18,
                "estimated_real_height_inches": 14,
                "size_reference": "Standard framed print size based on wall proportion",
                "confidence": "high"
            }
        ]
    },
    "20260315_152052.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "wood_cityscape",
                "description": "Wood-burned cityscape with buildings and figures",
                "top_left_px": [150, 650],
                "bottom_right_px": [1350, 2100],
                "estimated_real_width_inches": 20,
                "estimated_real_height_inches": 24,
                "size_reference": "Compared to shelf height, approximately 20x24 inches",
                "confidence": "medium"
            },
            {
                "id": "colorful_chains",
                "description": "Horizontal artwork with interlocking circles/chains in red, blue, green, orange",
                "top_left_px": [1150, 1650],
                "bottom_right_px": [2650, 2150],
                "estimated_real_width_inches": 30,
                "estimated_real_height_inches": 10,
                "size_reference": "Wide horizontal piece, about 30x10 inches",
                "confidence": "medium"
            },
            {
                "id": "abstract_expressionist",
                "description": "Abstract expressionist painting with blues, yellows, grays - framed",
                "top_left_px": [2400, 450],
                "bottom_right_px": [3350, 1350],
                "estimated_real_width_inches": 16,
                "estimated_real_height_inches": 16,
                "size_reference": "Square format, approximately 16x16 inches",
                "confidence": "medium"
            }
        ]
    },
    "20260315_152101.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "gray_doves",
                "description": "Abstract painting of white doves/birds on gray background - gold frame",
                "top_left_px": [100, 1550],
                "bottom_right_px": [1150, 2650],
                "estimated_real_width_inches": 30,
                "estimated_real_height_inches": 24,
                "size_reference": "Large piece compared to door frame, about 30x24 inches",
                "confidence": "high"
            },
            {
                "id": "woman_yellow_field",
                "description": "Woman reclining in yellow flower field - gold frame",
                "top_left_px": [2300, 1800],
                "bottom_right_px": [3200, 2650],
                "estimated_real_width_inches": 20,
                "estimated_real_height_inches": 16,
                "size_reference": "Medium sized painting, about 20x16 inches",
                "confidence": "medium"
            },
            {
                "id": "city_print",
                "description": "Colorful city/rooftops print - black frame",
                "top_left_px": [2700, 1250],
                "bottom_right_px": [3450, 1900],
                "estimated_real_width_inches": 14,
                "estimated_real_height_inches": 11,
                "size_reference": "Smaller framed print, about 14x11 inches",
                "confidence": "medium"
            },
            {
                "id": "blue_moon_scene",
                "description": "Blue moonlit/night scene - small gold frame",
                "top_left_px": [2950, 550],
                "bottom_right_px": [3550, 950],
                "estimated_real_width_inches": 10,
                "estimated_real_height_inches": 8,
                "size_reference": "Small framed piece, about 10x8 inches",
                "confidence": "medium"
            }
        ]
    },
    "20260315_152108.jpg": {
        "image_width": 4000,
        "image_height": 3000,
        "artworks": [
            {
                "id": "wave_lines",
                "description": "Blue and white abstract with flowing wave/contour lines - thin gold frame",
                "top_left_px": [950, 550],
                "bottom_right_px": [2650, 2050],
                "estimated_real_width_inches": 30,
                "estimated_real_height_inches": 24,
                "size_reference": "Large piece above desk, compared to chair approximately 30x24 inches",
                "confidence": "high"
            }
        ]
    },
    "photo1.jpg": {
        "image_width": 2334,
        "image_height": 1556,
        "artworks": [
            {
                "id": "abstract_orange_black",
                "description": "Large abstract with orange, black, white - expressionist style",
                "top_left_px": [380, 280],
                "bottom_right_px": [980, 780],
                "estimated_real_width_inches": 36,
                "estimated_real_height_inches": 30,
                "size_reference": "Large canvas, approximately 36x30 inches",
                "confidence": "medium"
            },
            {
                "id": "woman_portrait",
                "description": "Portrait of woman looking over shoulder - warm tones",
                "top_left_px": [50, 620],
                "bottom_right_px": [280, 950],
                "estimated_real_width_inches": 16,
                "estimated_real_height_inches": 20,
                "size_reference": "Medium portrait, about 16x20 inches",
                "confidence": "medium"
            },
            {
                "id": "red_shapes_white",
                "description": "Red/orange organic shapes on white background",
                "top_left_px": [950, 150],
                "bottom_right_px": [1200, 500],
                "estimated_real_width_inches": 16,
                "estimated_real_height_inches": 20,
                "size_reference": "Medium canvas, about 16x20 inches",
                "confidence": "medium"
            },
            {
                "id": "geometric_red_brown",
                "description": "Geometric abstract with red triangles and brown tones - black frame",
                "top_left_px": [600, 750],
                "bottom_right_px": [950, 1100],
                "estimated_real_width_inches": 18,
                "estimated_real_height_inches": 18,
                "size_reference": "Square format, approximately 18x18 inches",
                "confidence": "medium"
            },
            {
                "id": "blue_mountain_diptych",
                "description": "Blue mountain landscape - Asian style diptych/triptych",
                "top_left_px": [1450, 100],
                "bottom_right_px": [1850, 550],
                "estimated_real_width_inches": 24,
                "estimated_real_height_inches": 36,
                "size_reference": "Tall vertical diptych, about 24x36 inches total",
                "confidence": "medium"
            },
            {
                "id": "horse_sketch",
                "description": "Horse or animal sketch/drawing - black frame",
                "top_left_px": [1200, 550],
                "bottom_right_px": [1380, 850],
                "estimated_real_width_inches": 11,
                "estimated_real_height_inches": 14,
                "size_reference": "Small framed sketch, about 11x14 inches",
                "confidence": "medium"
            },
            {
                "id": "yellow_cityscape",
                "description": "Yellow/warm toned cityscape or street scene",
                "top_left_px": [1300, 750],
                "bottom_right_px": [1650, 1100],
                "estimated_real_width_inches": 18,
                "estimated_real_height_inches": 18,
                "size_reference": "Medium square canvas, about 18x18 inches",
                "confidence": "medium"
            },
            {
                "id": "sunflower_line",
                "description": "Simple line drawing of sunflower/daisy",
                "top_left_px": [1380, 450],
                "bottom_right_px": [1550, 700],
                "estimated_real_width_inches": 10,
                "estimated_real_height_inches": 14,
                "size_reference": "Small framed print, about 10x14 inches",
                "confidence": "low"
            }
        ]
    }
}


def extract_artwork(image_path: str, artwork: dict, output_dir: Path) -> dict:
    """Extract a single artwork region from an image."""
    img = Image.open(image_path)

    tl = artwork["top_left_px"]
    br = artwork["bottom_right_px"]

    # Clamp to image bounds with small padding
    padding = 5
    x1 = max(0, tl[0] - padding)
    y1 = max(0, tl[1] - padding)
    x2 = min(img.width, br[0] + padding)
    y2 = min(img.height, br[1] + padding)

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
