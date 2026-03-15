"""
Step 4: Composite artwork onto room walls.
Uses OpenCV for perspective warping and PIL/ImageMagick for blending.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def load_image_cv(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Could not load image: {path}")
    return img


def load_image_pil(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def detect_wall_region(room_img: np.ndarray, wall_data: dict) -> tuple:
    """
    Extract the wall bounding box from Claude's analysis.
    Returns (top_left, top_right, bottom_right, bottom_left) as (x,y) pairs.
    """
    tl = wall_data.get("top_left_px", [50, 50])
    br = wall_data.get("bottom_right_px", [room_img.shape[1] - 50, room_img.shape[0] - 50])

    # Clamp to image dimensions
    h, w = room_img.shape[:2]
    x1, y1 = max(0, tl[0]), max(0, tl[1])
    x2, y2 = min(w, br[0]), min(h, br[1])

    # Return 4 corners: TL, TR, BR, BL
    return np.float32([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])


def resize_artwork_to_fit_wall(art_img: Image.Image, wall_corners: np.ndarray, padding: float = 0.15) -> Image.Image:
    """Resize artwork so it fits within the wall zone with padding."""
    x_coords = wall_corners[:, 0]
    y_coords = wall_corners[:, 1]
    wall_w = int(x_coords.max() - x_coords.min())
    wall_h = int(y_coords.max() - y_coords.min())

    # Target size with padding
    target_w = int(wall_w * (1 - padding * 2))
    target_h = int(wall_h * (1 - padding * 2))

    # Maintain aspect ratio
    art_w, art_h = art_img.size
    scale = min(target_w / art_w, target_h / art_h)
    new_w = int(art_w * scale)
    new_h = int(art_h * scale)

    return art_img.resize((new_w, new_h), Image.LANCZOS)


def adjust_artwork_to_room_lighting(art_img: Image.Image, lighting: str) -> Image.Image:
    """Shift artwork brightness/warmth to match room lighting."""
    if lighting in ("bright natural",):
        art_img = ImageEnhance.Brightness(art_img).enhance(1.05)
    elif lighting in ("dim natural", "warm artificial"):
        art_img = ImageEnhance.Brightness(art_img).enhance(0.88)
        art_img = ImageEnhance.Color(art_img).enhance(0.92)
    elif lighting in ("cool artificial",):
        art_img = ImageEnhance.Color(art_img).enhance(1.05)
    return art_img


def add_frame_and_shadow(art_pil: Image.Image, matting: str) -> Image.Image:
    """Add a simple frame/mat effect around the artwork."""
    art_w, art_h = art_pil.size

    if "white mat" in (matting or "").lower():
        border = max(12, int(min(art_w, art_h) * 0.05))
        color = (245, 245, 240)
    elif "wood" in (matting or "").lower():
        border = max(10, int(min(art_w, art_h) * 0.04))
        color = (139, 115, 85)
    elif "no frame" in (matting or "").lower():
        border = 3
        color = (200, 200, 200)
    else:  # default: thin dark frame
        border = max(8, int(min(art_w, art_h) * 0.03))
        color = (40, 35, 30)

    framed = Image.new("RGB", (art_w + border * 2, art_h + border * 2), color)
    framed.paste(art_pil, (border, border))

    # Soft drop shadow
    shadow_offset = max(4, border // 2)
    shadow_size = (framed.width + shadow_offset * 2, framed.height + shadow_offset * 2)
    shadow = Image.new("RGBA", shadow_size, (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", framed.size, (0, 0, 0, 90))
    shadow.paste(shadow_layer, (shadow_offset, shadow_offset))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_offset))

    composite = Image.new("RGBA", shadow_size, (0, 0, 0, 0))
    composite.paste(shadow, (0, 0))
    composite.paste(framed.convert("RGBA"), (0, 0))

    return composite.convert("RGB")


def composite_artwork_onto_room(
    room_path: str,
    art_path: str,
    wall_data: dict,
    lighting: str,
    matting: str,
    output_path: str,
):
    """Main compositing function: warp and blend artwork onto room wall."""
    room_cv = load_image_cv(room_path)
    room_pil = load_image_pil(room_path)
    art_pil = load_image_pil(art_path)

    # Get wall corners from Claude's analysis
    wall_corners = detect_wall_region(room_cv, wall_data)

    # Size artwork to fit
    art_pil = resize_artwork_to_fit_wall(art_pil, wall_corners, padding=0.12)

    # Adjust for room lighting
    art_pil = adjust_artwork_to_room_lighting(art_pil, lighting)

    # Add frame + shadow
    art_pil = add_frame_and_shadow(art_pil, matting)

    art_w, art_h = art_pil.size

    # Compute centered placement within wall zone
    wall_cx = int((wall_corners[0][0] + wall_corners[2][0]) / 2)
    wall_cy = int((wall_corners[0][1] + wall_corners[2][1]) / 2)

    x_offset = wall_cx - art_w // 2
    y_offset = wall_cy - art_h // 2

    # Convert artwork to RGBA for alpha compositing
    art_rgba = art_pil.convert("RGBA")

    # --- Perspective warp using OpenCV ---
    # Source points: corners of artwork
    src_pts = np.float32([[0, 0], [art_w, 0], [art_w, art_h], [0, art_h]])

    # Destination points: placed on wall (slight perspective nudge if wall has angle)
    x1, y1 = int(wall_corners[0][0]), int(wall_corners[0][1])
    x2, y2 = int(wall_corners[3][0]), int(wall_corners[3][1])
    wall_h_px = y2 - y1

    # Slight keystone effect based on wall position
    skew = int(wall_h_px * 0.01)  # very subtle
    dst_pts = np.float32([
        [x_offset + skew, y_offset],
        [x_offset + art_w - skew, y_offset],
        [x_offset + art_w, y_offset + art_h],
        [x_offset, y_offset + art_h],
    ])

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # Warp artwork onto blank canvas same size as room
    art_cv = cv2.cvtColor(np.array(art_pil), cv2.COLOR_RGB2BGR)
    warped = cv2.warpPerspective(art_cv, M, (room_cv.shape[1], room_cv.shape[0]))

    # Create mask for warped region
    mask_src = np.ones((art_h, art_w), dtype=np.uint8) * 255
    warped_mask = cv2.warpPerspective(mask_src, M, (room_cv.shape[1], room_cv.shape[0]))
    warped_mask_3ch = cv2.merge([warped_mask, warped_mask, warped_mask])

    # Blend: paste warped artwork onto room using mask
    result = room_cv.copy()
    result = np.where(warped_mask_3ch > 0, warped, result)

    # Save
    cv2.imwrite(output_path, result)
    print(f"    ✓ Composited → {output_path}")
    return output_path


def run(
    placement_file: str = "placement_plan.json",
    output_dir: str = "results",
    rooms_file: str = "rooms_analysis.json",
):
    print("\n[Step 4] Compositing artwork onto walls...")

    os.makedirs(output_dir, exist_ok=True)

    with open(placement_file) as f:
        placements = json.load(f)

    with open(rooms_file) as f:
        rooms = json.load(f)

    output_paths = []
    for i, placement in enumerate(placements):
        room_id = placement["room_id"]
        wall_id = placement["wall_id"]
        art_id = placement["art_id"]

        room_data = rooms.get(room_id, {})
        wall_data = next(
            (w for w in room_data.get("walls", []) if w["id"] == wall_id), {}
        )
        lighting = room_data.get("lighting", "bright natural")
        matting = placement.get("matting", "thin dark frame")

        output_path = os.path.join(
            output_dir, f"result_{i+1:02d}_{room_id}_{art_id}.jpg"
        )

        try:
            composite_artwork_onto_room(
                room_path=placement["room_image"],
                art_path=placement["art_image"],
                wall_data=wall_data,
                lighting=lighting,
                matting=matting,
                output_path=output_path,
            )
            placement["output_image"] = output_path
            output_paths.append(output_path)
        except Exception as e:
            print(f"    ✗ {room_id} + {art_id} → ERROR: {e}")

    # Update placement plan with output paths
    with open(placement_file, "w") as f:
        json.dump(placements, f, indent=2)

    print(f"\n  {len(output_paths)} composited image(s) saved to /{output_dir}/")
    return output_paths


if __name__ == "__main__":
    run()
