#!/usr/bin/env python3
"""
Extract paintings from images using OpenCV edge detection and contour finding.
Fast alternative to SAM that looks for rectangular shapes.
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path


# Configuration
INPUT_DIR = "input/artwork"
OUTPUT_DIR = "results/extracted"

# Detection settings
MIN_AREA_RATIO = 0.02   # Minimum 2% of image area
MAX_AREA_RATIO = 0.7    # Maximum 70% of image area
MIN_ASPECT_RATIO = 0.25 # Minimum width/height ratio
MAX_ASPECT_RATIO = 4.0  # Maximum width/height ratio


def find_rectangles(image):
    """
    Find rectangular regions in image using edge detection and contour finding.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise while keeping edges
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)

    # Edge detection with multiple thresholds
    edges1 = cv2.Canny(blurred, 30, 100)
    edges2 = cv2.Canny(blurred, 50, 150)
    edges = cv2.bitwise_or(edges1, edges2)

    # Dilate to connect nearby edges
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    image_area = image.shape[0] * image.shape[1]

    for contour in contours:
        # Approximate contour to polygon
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h

        # Filter by size
        area_ratio = area / image_area
        if area_ratio < MIN_AREA_RATIO or area_ratio > MAX_AREA_RATIO:
            continue

        # Filter by aspect ratio
        aspect = w / h if h > 0 else 0
        if aspect < MIN_ASPECT_RATIO or aspect > MAX_ASPECT_RATIO:
            continue

        # Calculate how rectangular the contour is
        contour_area = cv2.contourArea(contour)
        rectangularity = contour_area / area if area > 0 else 0

        # Only keep reasonably rectangular shapes
        if rectangularity < 0.4:
            continue

        rectangles.append({
            'bbox': (x, y, w, h),
            'area': area,
            'rectangularity': rectangularity,
            'vertices': len(approx)
        })

    return rectangles


def find_color_regions(image):
    """
    Find regions with distinct colors that might be artwork frames.
    """
    # Convert to HSV for better color segmentation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    regions = []
    image_area = image.shape[0] * image.shape[1]

    # Look for common frame colors: gold/brown, black, white
    color_ranges = [
        # Gold/brown frames
        ((10, 50, 50), (30, 255, 200)),
        # Black frames
        ((0, 0, 0), (180, 50, 50)),
        # White/light frames
        ((0, 0, 200), (180, 30, 255)),
    ]

    for lower, upper in color_ranges:
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))

        # Morphological operations to clean up mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Find contours in mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            area_ratio = area / image_area
            if area_ratio < MIN_AREA_RATIO or area_ratio > MAX_AREA_RATIO:
                continue

            aspect = w / h if h > 0 else 0
            if aspect < MIN_ASPECT_RATIO or aspect > MAX_ASPECT_RATIO:
                continue

            regions.append({
                'bbox': (x, y, w, h),
                'area': area,
                'type': 'color_region'
            })

    return regions


def merge_overlapping_boxes(boxes, overlap_thresh=0.3):
    """
    Merge boxes that significantly overlap.
    """
    if len(boxes) == 0:
        return []

    # Sort by area (largest first)
    boxes = sorted(boxes, key=lambda x: x['area'], reverse=True)

    merged = []
    used = set()

    for i, box1 in enumerate(boxes):
        if i in used:
            continue

        x1, y1, w1, h1 = box1['bbox']

        # Check overlap with all other boxes
        for j, box2 in enumerate(boxes):
            if j <= i or j in used:
                continue

            x2, y2, w2, h2 = box2['bbox']

            # Calculate overlap
            ix1 = max(x1, x2)
            iy1 = max(y1, y2)
            ix2 = min(x1 + w1, x2 + w2)
            iy2 = min(y1 + h1, y2 + h2)

            if ix2 > ix1 and iy2 > iy1:
                intersection = (ix2 - ix1) * (iy2 - iy1)
                smaller_area = min(box1['area'], box2['area'])
                overlap = intersection / smaller_area if smaller_area > 0 else 0

                if overlap > overlap_thresh:
                    # Merge: take the larger box
                    used.add(j)

        merged.append(box1)
        used.add(i)

    return merged


def extract_paintings(image_path, output_dir):
    """
    Extract paintings from a single image.
    """
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"    Error loading {image_path}")
        return []

    # Find rectangles using edge detection
    rectangles = find_rectangles(image)

    # Find color-based regions
    color_regions = find_color_regions(image)

    # Combine and merge
    all_boxes = rectangles + color_regions
    merged_boxes = merge_overlapping_boxes(all_boxes)

    # Sort by area
    merged_boxes.sort(key=lambda x: x['area'], reverse=True)

    # Limit to top candidates
    merged_boxes = merged_boxes[:12]

    detections = []

    for i, box in enumerate(merged_boxes):
        x, y, w, h = box['bbox']

        # Add small padding
        padding = 5
        img_h, img_w = image.shape[:2]
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(img_w, x + w + padding)
        y2 = min(img_h, y + h + padding)

        # Extract region
        extracted = image[y1:y2, x1:x2]

        # Save
        artwork_id = f"art_{i+1}"
        output_filename = f"{image_path.stem}_{artwork_id}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        cv2.imwrite(output_path, extracted)

        print(f"    Extracted: {artwork_id} ({extracted.shape[1]}x{extracted.shape[0]}px)")

        detections.append({
            "id": artwork_id,
            "description": f"Detected artwork {i+1}",
            "top_left_px": [int(x1), int(y1)],
            "bottom_right_px": [int(x2), int(y2)],
            "estimated_real_width_inches": 18,
            "estimated_real_height_inches": 14,
            "confidence": "medium"
        })

    return detections


def main():
    print("[OpenCV Extract] Finding artwork using edge detection...")

    # Setup directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get input images
    input_path = Path(INPUT_DIR)
    image_files = list(input_path.glob("*.jpg")) + list(input_path.glob("*.png")) + list(input_path.glob("*.jpeg"))

    all_detections = {}
    total_extracted = 0

    for img_path in sorted(image_files):
        print(f"\n  Processing: {img_path.name}")

        # Load image to get dimensions
        image = cv2.imread(str(img_path))

        detections = extract_paintings(img_path, OUTPUT_DIR)

        all_detections[img_path.name] = {
            "image_width": image.shape[1],
            "image_height": image.shape[0],
            "artworks": detections
        }

        total_extracted += len(detections)

    # Build extracted_artworks list for gallery generation
    extracted_artworks = []
    for source_file, data in all_detections.items():
        for art in data['artworks']:
            output_filename = f"{Path(source_file).stem}_{art['id']}.jpg"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            # Get actual extracted dimensions
            if os.path.exists(output_path):
                img = cv2.imread(output_path)
                if img is not None:
                    extracted_artworks.append({
                        "id": f"{Path(source_file).stem}_{art['id']}",
                        "source_image": source_file,
                        "extracted_file": output_path,
                        "extracted_width_px": img.shape[1],
                        "extracted_height_px": img.shape[0],
                        "estimated_real_width_inches": art.get("estimated_real_width_inches", 18),
                        "estimated_real_height_inches": art.get("estimated_real_height_inches", 14),
                        "confidence": art.get("confidence", "medium")
                    })

    # Save detections JSON in format expected by gallery generator
    detections_path = os.path.join("results", "artwork_detections.json")
    output_data = {
        "source_detections": all_detections,
        "extracted_artworks": extracted_artworks
    }
    with open(detections_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n  Extracted {total_extracted} artwork(s) to {OUTPUT_DIR}/")
    print(f"  Detection data saved to {detections_path}")


if __name__ == "__main__":
    main()
