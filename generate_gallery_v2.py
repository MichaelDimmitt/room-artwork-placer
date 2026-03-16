"""
Generate a gallery from extracted paintings, preserving relative real-world sizes.
Uses the size estimates from Claude Vision to scale artworks proportionally.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image


def load_extracted_artworks(detections_file: str) -> list[dict]:
    """Load extracted artwork metadata."""
    with open(detections_file) as f:
        data = json.load(f)
    return data.get("extracted_artworks", [])


def calculate_scale_factors(artworks: list[dict], pixels_per_inch: float = 10.0) -> list[dict]:
    """
    Calculate scaled dimensions based on estimated real-world sizes.

    Args:
        artworks: List of artwork metadata with size estimates
        pixels_per_inch: How many pixels per inch in the gallery output

    Returns:
        List of artworks with added 'gallery_width' and 'gallery_height'
    """
    for art in artworks:
        real_w = art.get("estimated_real_width_inches")
        real_h = art.get("estimated_real_height_inches")

        if real_w and real_h:
            # Use real-world size estimates
            art["gallery_width"] = int(real_w * pixels_per_inch)
            art["gallery_height"] = int(real_h * pixels_per_inch)
            art["scale_method"] = "real_world_estimate"
        else:
            # Fallback: use extracted pixel dimensions scaled down
            art["gallery_width"] = art["extracted_width_px"] // 4
            art["gallery_height"] = art["extracted_height_px"] // 4
            art["scale_method"] = "pixel_fallback"

    return artworks


def generate_gallery_v2(
    artworks: list[dict],
    padding: int = 30,
    background_color: tuple[int, int, int] = (250, 250, 248),
) -> Image.Image:
    """
    Arrange extracted artworks side by side using their relative real-world sizes.
    """
    if not artworks:
        raise ValueError("No artworks to arrange")

    # Calculate total dimensions
    total_width = sum(art["gallery_width"] for art in artworks) + padding * (len(artworks) + 1)
    max_height = max(art["gallery_height"] for art in artworks)
    total_height = max_height + padding * 2

    # Create canvas
    gallery = Image.new("RGB", (total_width, total_height), background_color)

    # Place each artwork
    x_offset = padding
    for art in artworks:
        try:
            img = Image.open(art["extracted_file"]).convert("RGB")

            # Resize to gallery dimensions (based on real-world size)
            resized = img.resize(
                (art["gallery_width"], art["gallery_height"]),
                Image.LANCZOS
            )

            # Center vertically
            y_offset = padding + (max_height - art["gallery_height"]) // 2
            gallery.paste(resized, (x_offset, y_offset))

            x_offset += art["gallery_width"] + padding

        except Exception as e:
            print(f"  Warning: Could not load {art['extracted_file']}: {e}")

    return gallery


def run(
    detections_file: str = "results/artwork_detections.json",
    output_file: str = "results/gallery_v3.jpg",
    pixels_per_inch: float = 10.0,
    padding: int = 30,
):
    """Generate v2 gallery from extracted artworks."""
    print(f"\n[Gallery V2] Loading extracted artworks...")

    artworks = load_extracted_artworks(detections_file)

    if not artworks:
        print("No extracted artworks found. Run extract_paintings.py first.")
        sys.exit(1)

    print(f"  Found {len(artworks)} extracted artwork(s)")

    # Calculate scaled sizes
    artworks = calculate_scale_factors(artworks, pixels_per_inch)

    print("\n  Size calculations:")
    for art in artworks:
        real_w = art.get("estimated_real_width_inches", "?")
        real_h = art.get("estimated_real_height_inches", "?")
        print(f"    {art['id']}: {real_w}\"x{real_h}\" -> {art['gallery_width']}x{art['gallery_height']}px ({art['scale_method']})")

    print(f"\n[Gallery V2] Generating gallery with relative sizes...")
    gallery = generate_gallery_v2(artworks, padding=padding)

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gallery.save(output_file, quality=95)
    print(f"\n  Gallery saved: {output_file}")
    print(f"  Dimensions: {gallery.width}x{gallery.height}")

    return output_file


def main():
    parser = argparse.ArgumentParser(description="Generate gallery from extracted paintings")
    parser.add_argument(
        "--detections", "-d",
        default="results/artwork_detections.json",
        help="Path to artwork detections JSON"
    )
    parser.add_argument(
        "--output", "-o",
        default="results/gallery_v3.jpg",
        help="Output path for gallery image"
    )
    parser.add_argument(
        "--ppi",
        type=float,
        default=10.0,
        help="Pixels per inch for gallery scaling (default: 10)"
    )
    parser.add_argument(
        "--padding", "-p",
        type=int,
        default=30,
        help="Pixels between artworks (default: 30)"
    )
    args = parser.parse_args()

    run(
        detections_file=args.detections,
        output_file=args.output,
        pixels_per_inch=args.ppi,
        padding=args.padding,
    )


if __name__ == "__main__":
    main()
