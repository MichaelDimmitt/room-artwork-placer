"""
Generate a gallery composite showing all artwork pieces side by side.
Preserves true-to-size dimensions - no scaling to match other pieces.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image


def load_artworks(input_dir: str) -> list[tuple[str, Image.Image]]:
    """Load all artwork images from directory."""
    input_path = Path(input_dir)
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}

    if not input_path.exists():
        print(f"ERROR: Input directory '{input_dir}' not found.")
        sys.exit(1)

    image_files = sorted(
        f for f in input_path.iterdir()
        if f.suffix.lower() in valid_exts
    )

    if not image_files:
        print(f"No images found in {input_dir}")
        sys.exit(1)

    artworks = []
    for img_path in image_files:
        try:
            img = Image.open(img_path).convert("RGB")
            artworks.append((img_path.name, img))
            print(f"  Loaded: {img_path.name} ({img.width}x{img.height})")
        except Exception as e:
            print(f"  Skipped: {img_path.name} - {e}")

    return artworks


def generate_gallery(
    artworks: list[tuple[str, Image.Image]],
    padding: int = 40,
    background_color: tuple[int, int, int] = (245, 245, 245),
) -> Image.Image:
    """
    Arrange artworks side by side in a single row, preserving original sizes.

    Args:
        artworks: List of (filename, PIL.Image) tuples
        padding: Pixels between each artwork
        background_color: RGB tuple for gallery background

    Returns:
        Composite gallery image
    """
    if not artworks:
        raise ValueError("No artworks to arrange")

    # Calculate total dimensions
    total_width = sum(img.width for _, img in artworks) + padding * (len(artworks) + 1)
    max_height = max(img.height for _, img in artworks)
    total_height = max_height + padding * 2

    # Create canvas
    gallery = Image.new("RGB", (total_width, total_height), background_color)

    # Place each artwork (vertically centered)
    x_offset = padding
    for name, img in artworks:
        y_offset = padding + (max_height - img.height) // 2
        gallery.paste(img, (x_offset, y_offset))
        x_offset += img.width + padding

    return gallery


def run(
    input_dir: str = "input/artwork",
    output_file: str = "results/gallery.jpg",
    padding: int = 40,
):
    """Generate gallery composite from artwork images."""
    print(f"\n[Gallery] Loading artwork from {input_dir}...")
    artworks = load_artworks(input_dir)

    print(f"\n[Gallery] Arranging {len(artworks)} piece(s) side by side...")
    gallery = generate_gallery(artworks, padding=padding)

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gallery.save(output_file, quality=95)
    print(f"\n  Gallery saved: {output_file}")
    print(f"  Dimensions: {gallery.width}x{gallery.height}")

    return output_file


def main():
    parser = argparse.ArgumentParser(description="Generate artwork gallery composite")
    parser.add_argument(
        "--input", "-i",
        default="input/artwork",
        help="Directory containing artwork images"
    )
    parser.add_argument(
        "--output", "-o",
        default="results/gallery.jpg",
        help="Output path for gallery image"
    )
    parser.add_argument(
        "--padding", "-p",
        type=int,
        default=40,
        help="Pixels between artworks (default: 40)"
    )
    args = parser.parse_args()

    run(input_dir=args.input, output_file=args.output, padding=args.padding)


if __name__ == "__main__":
    main()
