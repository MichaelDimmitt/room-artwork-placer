"""
Extract paintings from room/scene photos using Claude Vision.
Detects artwork boundaries, extracts them, and preserves relative size information.
"""

import anthropic
import base64
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

load_dotenv()


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


EXTRACTION_PROMPT = """
Analyze this image and identify ALL paintings, artwork, framed pictures, or canvases visible.

CRITICAL INSTRUCTIONS:
- The image may be ROTATED 90 degrees. Look at the entire image carefully.
- Include the FULL FRAME/BORDER of each artwork in your bounding box - do NOT crop tight to just the painted area.
- For framed pieces: the bounding box should include the outer edge of the frame.
- For unframed canvases: include the full canvas edge.
- Count EVERY piece of art, even if partially obscured or stacked.
- Some images have 8+ artworks - make sure you find them ALL.

For EACH piece of artwork found, provide bounding box coordinates as [x, y] where:
- x is pixels from LEFT edge of image
- y is pixels from TOP edge of image
- top_left_px must have SMALLER x and y values than bottom_right_px

Return ONLY a valid JSON object (no markdown, no explanation):

{
  "image_width": 4000,
  "image_height": 3000,
  "artworks": [
    {
      "id": "art_1",
      "description": "Brief description of the artwork",
      "top_left_px": [x, y],
      "bottom_right_px": [x, y],
      "estimated_real_width_inches": 24,
      "estimated_real_height_inches": 18,
      "size_reference": "Compared to the door frame, this appears to be about 24 inches wide",
      "confidence": "high | medium | low"
    }
  ]
}

Be VERY precise with pixel coordinates. Double-check that top_left has smaller values than bottom_right.
"""


def detect_artworks(image_path: str, client: anthropic.Anthropic) -> dict:
    """Use Claude Vision to detect artwork in an image."""
    print(f"  Analyzing: {Path(image_path).name}")

    img = Image.open(image_path)
    img_width, img_height = img.size

    img_data, media_type = encode_image(image_path)

    message = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=2000,
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
                    {"type": "text", "text": EXTRACTION_PROMPT},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw.strip())
    result["image_width"] = img_width
    result["image_height"] = img_height
    result["source_image"] = str(image_path)

    return result


def extract_artwork_region(
    image_path: str,
    top_left: list[int],
    bottom_right: list[int],
    padding: int = 10
) -> Image.Image:
    """Extract a region from an image with optional padding."""
    img = Image.open(image_path)

    # Apply padding and clamp to image bounds
    x1 = max(0, top_left[0] - padding)
    y1 = max(0, top_left[1] - padding)
    x2 = min(img.width, bottom_right[0] + padding)
    y2 = min(img.height, bottom_right[1] + padding)

    return img.crop((x1, y1, x2, y2))


def run(
    input_dir: str = "input/artwork",
    output_dir: str = "results/extracted",
    detections_file: str = "results/artwork_detections.json",
):
    """Detect and extract paintings from all images in input directory."""
    print("\n[Extract] Detecting paintings in images...")

    client = anthropic.Anthropic()
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    image_files = sorted(
        f for f in input_path.iterdir()
        if f.suffix.lower() in valid_exts
    )

    if not image_files:
        print(f"No images found in {input_dir}")
        sys.exit(1)

    all_detections = []
    extracted_artworks = []

    for img_path in image_files:
        try:
            detection = detect_artworks(str(img_path), client)
            all_detections.append(detection)

            artworks = detection.get("artworks", [])
            print(f"    Found {len(artworks)} artwork(s)")

            for i, art in enumerate(artworks):
                art_id = f"{img_path.stem}_{art.get('id', f'art_{i}')}"

                try:
                    extracted = extract_artwork_region(
                        str(img_path),
                        art["top_left_px"],
                        art["bottom_right_px"],
                        padding=5
                    )

                    output_file = output_path / f"{art_id}.jpg"
                    extracted.save(output_file, quality=95)

                    extracted_artworks.append({
                        "id": art_id,
                        "source_image": str(img_path),
                        "extracted_file": str(output_file),
                        "extracted_width_px": extracted.width,
                        "extracted_height_px": extracted.height,
                        "estimated_real_width_inches": art.get("estimated_real_width_inches"),
                        "estimated_real_height_inches": art.get("estimated_real_height_inches"),
                        "size_reference": art.get("size_reference"),
                        "description": art.get("description"),
                        "confidence": art.get("confidence"),
                    })

                    print(f"      Extracted: {art_id} ({extracted.width}x{extracted.height}px)")

                except Exception as e:
                    print(f"      Failed to extract {art_id}: {e}")

        except Exception as e:
            print(f"    ERROR analyzing {img_path.name}: {e}")

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
