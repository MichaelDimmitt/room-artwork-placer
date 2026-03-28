#!/usr/bin/env python3
"""
Interactive tool to select artwork quadrilaterals by clicking 4 corners.

Usage:
    python interactive_picker.py

Instructions:
    1. Click on the TOP-LEFT corner of a painting
    2. Click on the TOP-RIGHT corner
    3. Click on the BOTTOM-RIGHT corner
    4. Click on the BOTTOM-LEFT corner
    5. A quadrilateral will be drawn - press 'y' to confirm, 'n' to redo
    6. Press 's' to save and move to next image
    7. Press 'q' to quit and save all progress
    8. Press 'u' to undo last selection
    9. Press 'r' to reset all selections for current image
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path

# Configuration
INPUT_DIR = "input/artwork"
OUTPUT_DIR = "results/extracted"
COORDS_FILE = "results/interactive_coords.json"

# Global state
clicks = []
current_boxes = []
current_image = None
display_image = None
help_panel = None
combined_display = None
window_name = "Artwork Picker - Click corners"


def update_display():
    """Update the combined display with image and help panel."""
    global display_image, help_panel, combined_display
    if help_panel is not None and display_image is not None:
        combined_display = np.hstack([display_image, help_panel])
        cv2.imshow(window_name, combined_display)


def mouse_callback(event, x, y, flags, param):
    """Handle mouse clicks to define quadrilaterals with 4 corners."""
    global clicks, current_boxes, display_image, current_image

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicks) < 4:
            clicks.append((x, y))

        # Draw click point
        display_image = current_image.copy()

        # Draw existing quads
        for quad in current_boxes:
            pts = np.array(quad, np.int32).reshape((-1, 1, 2))
            cv2.polylines(display_image, [pts], True, (0, 255, 0), 3)
            # Add quad number
            idx = current_boxes.index(quad) + 1
            cv2.putText(display_image, str(idx), (quad[0][0] + 5, quad[0][1] + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Draw current clicks with different colors for each corner
        corner_colors = [(255, 0, 0), (0, 165, 255), (0, 0, 255), (255, 0, 255)]  # Blue, Orange, Red, Magenta
        corner_labels = ["TL", "TR", "BR", "BL"]
        for i, click in enumerate(clicks):
            cv2.circle(display_image, click, 8, corner_colors[i], -1)
            cv2.putText(display_image, corner_labels[i], (click[0] + 10, click[1] + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, corner_colors[i], 2)

        # Draw lines between clicks
        if len(clicks) >= 2:
            for i in range(len(clicks) - 1):
                cv2.line(display_image, clicks[i], clicks[i + 1], (0, 255, 255), 2)

        # If we have 4 clicks, close the quadrilateral
        if len(clicks) == 4:
            pts = np.array(clicks, np.int32).reshape((-1, 1, 2))
            cv2.polylines(display_image, [pts], True, (0, 255, 255), 3)

        update_display()


def draw_boxes():
    """Redraw all confirmed quadrilaterals on the image."""
    global display_image, current_image, current_boxes

    display_image = current_image.copy()
    for i, quad in enumerate(current_boxes):
        pts = np.array(quad, np.int32).reshape((-1, 1, 2))
        cv2.polylines(display_image, [pts], True, (0, 255, 0), 3)
        cv2.putText(display_image, str(i + 1), (quad[0][0] + 5, quad[0][1] + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    update_display()


def resize_for_display(image, max_width=1100, max_height=900):
    """Resize image to fit on screen while maintaining aspect ratio."""
    h, w = image.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h)), scale
    return image.copy(), 1.0


def create_help_panel(height):
    """Create a help panel to display on the right side of the window."""
    panel_width = 320
    panel = np.zeros((height, panel_width, 3), dtype=np.uint8)
    panel[:] = (40, 40, 40)  # Dark gray background

    # Title
    cv2.putText(panel, "INSTRUCTIONS", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.line(panel, (20, 50), (300, 50), (100, 100, 100), 1)

    # Instructions
    instructions = [
        "",
        "1. Click TOP-LEFT corner",
        "2. Click TOP-RIGHT corner",
        "3. Click BOTTOM-RIGHT corner",
        "4. Click BOTTOM-LEFT corner",
        "",
        "5. Yellow quad appears:",
        "   Press 'y' to confirm",
        "   Press 'n' to redo",
        "",
        "6. Repeat for all paintings",
        "",
        "7. Press 's' to save and",
        "   go to next image",
        "",
        "8. Press 'q' to quit",
        "   (progress is saved)",
    ]

    y_pos = 80
    for line in instructions:
        cv2.putText(panel, line, (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)
        y_pos += 22

    # Controls section
    y_pos += 10
    cv2.line(panel, (20, y_pos), (300, y_pos), (100, 100, 100), 1)
    y_pos += 25
    cv2.putText(panel, "OTHER CONTROLS", (20, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    controls = [
        "",
        "'u' = Undo last box",
        "'r' = Reset all boxes",
        "'s' = Save & next image",
        "'q' = Quit & save all",
    ]

    y_pos += 10
    for line in controls:
        y_pos += 22
        cv2.putText(panel, line, (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 255, 180), 1)

    # Color legend
    y_pos += 40
    cv2.line(panel, (20, y_pos), (300, y_pos), (100, 100, 100), 1)
    y_pos += 25
    cv2.putText(panel, "COLOR LEGEND", (20, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    y_pos += 30
    cv2.circle(panel, (30, y_pos), 8, (255, 0, 0), -1)
    cv2.putText(panel, "TL = Top-left (1st)", (50, y_pos + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    y_pos += 25
    cv2.circle(panel, (30, y_pos), 8, (0, 165, 255), -1)
    cv2.putText(panel, "TR = Top-right (2nd)", (50, y_pos + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    y_pos += 25
    cv2.circle(panel, (30, y_pos), 8, (0, 0, 255), -1)
    cv2.putText(panel, "BR = Bottom-right (3rd)", (50, y_pos + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    y_pos += 25
    cv2.circle(panel, (30, y_pos), 8, (255, 0, 255), -1)
    cv2.putText(panel, "BL = Bottom-left (4th)", (50, y_pos + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    y_pos += 25
    pts = np.array([(22, y_pos - 6), (38, y_pos - 8), (40, y_pos + 6), (20, y_pos + 8)], np.int32)
    cv2.polylines(panel, [pts.reshape((-1, 1, 2))], True, (0, 255, 255), 2)
    cv2.putText(panel, "= Pending quad", (50, y_pos + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    y_pos += 25
    pts = np.array([(22, y_pos - 6), (38, y_pos - 8), (40, y_pos + 6), (20, y_pos + 8)], np.int32)
    cv2.polylines(panel, [pts.reshape((-1, 1, 2))], True, (0, 255, 0), 2)
    cv2.putText(panel, "= Confirmed quad", (50, y_pos + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    return panel


def process_image(image_path, existing_boxes=None):
    """Process a single image interactively."""
    global clicks, current_boxes, current_image, display_image, help_panel

    # Load image
    original = cv2.imread(str(image_path))
    if original is None:
        print(f"Error loading {image_path}")
        return None

    # Resize for display
    current_image, scale = resize_for_display(original)
    display_image = current_image.copy()

    # Create help panel matching image height
    help_panel = create_help_panel(current_image.shape[0])

    # Convert existing quads to display scale
    current_boxes = []
    if existing_boxes:
        for quad in existing_boxes:
            if len(quad) == 4:
                # 4-corner format
                scaled_quad = [(int(pt[0] * scale), int(pt[1] * scale)) for pt in quad]
                current_boxes.append(scaled_quad)
            elif len(quad) == 2:
                # Legacy 2-corner format - convert to 4 corners
                pt1, pt2 = quad
                tl = (int(pt1[0] * scale), int(pt1[1] * scale))
                tr = (int(pt2[0] * scale), int(pt1[1] * scale))
                br = (int(pt2[0] * scale), int(pt2[1] * scale))
                bl = (int(pt1[0] * scale), int(pt2[1] * scale))
                current_boxes.append([tl, tr, br, bl])

    clicks = []

    # Setup window
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(window_name, mouse_callback)

    print(f"\n  Processing: {image_path.name}")
    print(f"  Scale: {scale:.2f}x (original: {original.shape[1]}x{original.shape[0]})")
    print("  Controls:")
    print("    Click: Select 4 corners (TL -> TR -> BR -> BL)")
    print("    y: Confirm current quadrilateral")
    print("    n: Cancel current selection")
    print("    u: Undo last confirmed quad")
    print("    r: Reset all quads for this image")
    print("    s: Save and go to next image")
    print("    q: Quit and save all")

    draw_boxes()

    while True:
        key = cv2.waitKey(1) & 0xFF

        if key == ord('y') and len(clicks) == 4:
            # Confirm quadrilateral (store as list of 4 corner tuples)
            quad = [clicks[0], clicks[1], clicks[2], clicks[3]]
            current_boxes.append(quad)
            clicks = []
            print(f"    Quad {len(current_boxes)} confirmed: {quad}")
            draw_boxes()

        elif key == ord('n'):
            # Cancel current selection
            clicks = []
            draw_boxes()
            print("    Selection cancelled")

        elif key == ord('u') and current_boxes:
            # Undo last box
            current_boxes.pop()
            clicks = []
            draw_boxes()
            print(f"    Undone. {len(current_boxes)} boxes remaining")

        elif key == ord('r'):
            # Reset all
            current_boxes = []
            clicks = []
            draw_boxes()
            print("    All boxes reset")

        elif key == ord('s'):
            # Save and continue
            # Convert back to original scale
            original_boxes = []
            for quad in current_boxes:
                scaled_quad = [(int(pt[0] / scale), int(pt[1] / scale)) for pt in quad]
                original_boxes.append(scaled_quad)
            cv2.destroyAllWindows()
            return original_boxes

        elif key == ord('q'):
            # Quit
            cv2.destroyAllWindows()
            return None  # Signal to quit


def extract_artworks(coords_data):
    """Extract artwork images based on saved coordinates using perspective transform."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    extracted_artworks = []
    total = 0

    for filename, data in coords_data.items():
        image_path = Path(INPUT_DIR) / filename
        if not image_path.exists():
            print(f"  Warning: {filename} not found")
            continue

        image = cv2.imread(str(image_path))
        boxes = data.get('boxes', [])

        for i, box in enumerate(boxes):
            if len(box) == 4:
                # 4-corner format - use perspective transform
                src_pts = np.array(box, dtype=np.float32)

                # Calculate output dimensions from the quadrilateral
                width_top = np.linalg.norm(np.array(box[1]) - np.array(box[0]))
                width_bottom = np.linalg.norm(np.array(box[2]) - np.array(box[3]))
                height_left = np.linalg.norm(np.array(box[3]) - np.array(box[0]))
                height_right = np.linalg.norm(np.array(box[2]) - np.array(box[1]))

                out_width = int(max(width_top, width_bottom))
                out_height = int(max(height_left, height_right))

                # Destination points for a rectangle
                dst_pts = np.array([
                    [0, 0],
                    [out_width - 1, 0],
                    [out_width - 1, out_height - 1],
                    [0, out_height - 1]
                ], dtype=np.float32)

                # Compute perspective transform and apply
                matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                extracted = cv2.warpPerspective(image, matrix, (out_width, out_height))

            elif len(box) == 2:
                # Legacy 2-corner format - simple crop
                x1, y1 = box[0]
                x2, y2 = box[1]
                extracted = image[y1:y2, x1:x2]
                out_width = x2 - x1
                out_height = y2 - y1
            else:
                print(f"  Warning: Invalid box format for {filename}")
                continue

            # Save
            artwork_id = f"art_{i+1}"
            output_filename = f"{image_path.stem}_{artwork_id}.jpg"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            cv2.imwrite(output_path, extracted)

            print(f"    Extracted: {output_filename} ({extracted.shape[1]}x{extracted.shape[0]}px)")

            extracted_artworks.append({
                "id": f"{image_path.stem}_{artwork_id}",
                "source_image": filename,
                "extracted_file": output_path,
                "extracted_width_px": extracted.shape[1],
                "extracted_height_px": extracted.shape[0],
                "estimated_real_width_inches": None,
                "estimated_real_height_inches": None,
                "size_needs_analysis": True
            })
            total += 1

    return extracted_artworks, total


def main():
    print("[Interactive Picker] Select artwork bounding boxes")
    print("=" * 50)

    # Load existing coordinates if any
    coords_data = {}
    if os.path.exists(COORDS_FILE):
        with open(COORDS_FILE) as f:
            coords_data = json.load(f)
        print(f"  Loaded existing coordinates for {len(coords_data)} images")

    # Get input images
    input_path = Path(INPUT_DIR)
    image_files = sorted(
        list(input_path.glob("*.jpg")) +
        list(input_path.glob("*.png")) +
        list(input_path.glob("*.jpeg"))
    )

    print(f"  Found {len(image_files)} images to process")

    # Process each image
    for img_path in image_files:
        filename = img_path.name
        existing = coords_data.get(filename, {}).get('boxes', [])

        # Convert existing format if needed
        existing_boxes = []
        for box in existing:
            if isinstance(box, (list, tuple)):
                if len(box) == 4:
                    # 4-corner format
                    existing_boxes.append([tuple(pt) for pt in box])
                elif len(box) == 2:
                    # Legacy 2-corner format
                    existing_boxes.append([tuple(box[0]), tuple(box[1])])

        result = process_image(img_path, existing_boxes)

        if result is None:
            # User quit
            print("\n  Quitting...")
            break

        # Save coordinates
        coords_data[filename] = {
            'boxes': [list(map(list, box)) for box in result],
            'image_width': cv2.imread(str(img_path)).shape[1],
            'image_height': cv2.imread(str(img_path)).shape[0]
        }

        # Save progress after each image
        with open(COORDS_FILE, 'w') as f:
            json.dump(coords_data, f, indent=2)
        print(f"    Saved {len(result)} boxes for {filename}")

    # Final save
    with open(COORDS_FILE, 'w') as f:
        json.dump(coords_data, f, indent=2)

    print("\n" + "=" * 50)
    print(f"  Coordinates saved to: {COORDS_FILE}")

    # Extract artworks
    print("\n[Extracting Artworks]")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Clear old extractions
    for f in Path(OUTPUT_DIR).glob("*.jpg"):
        f.unlink()

    extracted_artworks, total = extract_artworks(coords_data)

    # Save detections JSON for gallery generator
    detections_path = os.path.join("results", "artwork_detections.json")
    output_data = {
        "source_detections": coords_data,
        "extracted_artworks": extracted_artworks
    }
    with open(detections_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n  Total extracted: {total} artworks")
    print(f"  Detection data saved to: {detections_path}")
    print("\n  Run 'python generate_gallery_v2.py' to create the gallery")


if __name__ == "__main__":
    main()
