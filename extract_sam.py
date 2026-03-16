#!/usr/bin/env python3
"""
Extract paintings from images using Segment Anything Model (SAM).
SAM automatically segments all objects, then we filter for rectangular artwork.
"""

import os
import json
import cv2
import numpy as np
import torch
from pathlib import Path
from PIL import Image
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

# Configuration
INPUT_DIR = "input/artwork"
OUTPUT_DIR = "results/extracted"
MODEL_PATH = "models/sam_vit_b_01ec64.pth"
MODEL_TYPE = "vit_b"

# Filter settings for artwork detection
MIN_AREA_RATIO = 0.01  # Minimum 1% of image area
MAX_AREA_RATIO = 0.8   # Maximum 80% of image area
MIN_ASPECT_RATIO = 0.3  # Minimum width/height ratio
MAX_ASPECT_RATIO = 3.0  # Maximum width/height ratio
MIN_SOLIDITY = 0.7      # How "filled in" the shape is (rectangle = high solidity)
MIN_RECTANGULARITY = 0.6  # How close to a rectangle


def is_artwork_candidate(mask, image_area):
    """
    Determine if a mask is likely to be a painting/artwork.
    Artworks tend to be:
    - Rectangular
    - Medium-sized relative to image
    - Have high solidity (filled in, not hollow)
    """
    area = mask['area']
    bbox = mask['bbox']  # x, y, width, height

    # Size check
    area_ratio = area / image_area
    if area_ratio < MIN_AREA_RATIO or area_ratio > MAX_AREA_RATIO:
        return False

    # Aspect ratio check
    width, height = bbox[2], bbox[3]
    if height == 0 or width == 0:
        return False
    aspect_ratio = width / height
    if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
        return False

    # Rectangularity check - how much of bounding box is filled
    bbox_area = width * height
    rectangularity = area / bbox_area if bbox_area > 0 else 0
    if rectangularity < MIN_RECTANGULARITY:
        return False

    # Solidity check (from stability score if available)
    if 'stability_score' in mask and mask['stability_score'] < 0.8:
        return False

    return True


def extract_artwork_from_mask(image, mask, padding=10):
    """
    Extract the artwork region from the image using the mask's bounding box.
    """
    bbox = mask['bbox']  # x, y, width, height
    x, y, w, h = bbox

    # Add padding
    img_h, img_w = image.shape[:2]
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(img_w, x + w + padding)
    y2 = min(img_h, y + h + padding)

    # Extract region
    extracted = image[int(y1):int(y2), int(x1):int(x2)]
    return extracted, (x1, y1, x2, y2)


def main():
    print("[SAM Extract] Initializing Segment Anything Model...")

    # Check for GPU (force CPU on Mac due to MPS float64 issues)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Using device: {device}")

    # Load SAM model
    sam = sam_model_registry[MODEL_TYPE](checkpoint=MODEL_PATH)
    sam.to(device=device)

    # Create mask generator with settings optimized for artwork (faster settings)
    mask_generator = SamAutomaticMaskGenerator(
        model=sam,
        points_per_side=16,           # Fewer points = faster
        pred_iou_thresh=0.88,         # Higher = more confident masks only
        stability_score_thresh=0.90,  # Higher = more stable masks
        crop_n_layers=0,              # No multi-scale (faster)
        min_mask_region_area=2000,    # Ignore tiny regions
    )

    # Setup directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get input images
    input_path = Path(INPUT_DIR)
    image_files = list(input_path.glob("*.jpg")) + list(input_path.glob("*.png")) + list(input_path.glob("*.jpeg"))

    all_detections = {}
    total_extracted = 0

    for img_path in sorted(image_files):
        print(f"\n  Processing: {img_path.name}")

        # Load image
        image = cv2.imread(str(img_path))
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_area = image.shape[0] * image.shape[1]

        # Generate masks
        print("    Generating masks...")
        masks = mask_generator.generate(image_rgb)
        print(f"    Found {len(masks)} segments")

        # Filter for artwork candidates
        artwork_masks = [m for m in masks if is_artwork_candidate(m, image_area)]
        print(f"    {len(artwork_masks)} artwork candidates")

        # Sort by area (largest first) and limit
        artwork_masks.sort(key=lambda x: x['area'], reverse=True)
        artwork_masks = artwork_masks[:15]  # Max 15 per image

        # Extract and save each artwork
        detections = []
        for i, mask in enumerate(artwork_masks):
            artwork_id = f"art_{i+1}"

            extracted, coords = extract_artwork_from_mask(image, mask)

            # Save extracted artwork
            output_filename = f"{img_path.stem}_{artwork_id}.jpg"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            cv2.imwrite(output_path, extracted)

            print(f"    Extracted: {artwork_id} ({extracted.shape[1]}x{extracted.shape[0]}px)")

            detections.append({
                "id": artwork_id,
                "description": f"Automatically detected artwork {i+1}",
                "top_left_px": [int(coords[0]), int(coords[1])],
                "bottom_right_px": [int(coords[2]), int(coords[3])],
                "area": mask['area'],
                "stability_score": float(mask.get('stability_score', 0)),
                "estimated_real_width_inches": 20,  # Default estimate
                "estimated_real_height_inches": 16,
                "confidence": "high" if mask.get('stability_score', 0) > 0.95 else "medium"
            })
            total_extracted += 1

        all_detections[img_path.name] = {
            "image_width": image.shape[1],
            "image_height": image.shape[0],
            "artworks": detections
        }

    # Save detections JSON
    detections_path = os.path.join("results", "artwork_detections.json")
    with open(detections_path, 'w') as f:
        json.dump(all_detections, f, indent=2)

    print(f"\n  Extracted {total_extracted} artwork(s) to {OUTPUT_DIR}/")
    print(f"  Detection data saved to {detections_path}")


if __name__ == "__main__":
    main()
