"""
Generate a gallery composite showing all artwork pieces side by side.
Can scale to real-world dimensions using Claude Vision size estimates.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image


def load_artworks(input_dir: str, size_data: dict = None, ppi: int = 10) -> list[tuple[str, Image.Image, dict]]:
    """Load all artwork images from directory with optional size metadata."""
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

            # Get size metadata if available
            meta = {}
            if size_data:
                # Try to find matching entry by stem
                stem = img_path.stem
                if stem in size_data:
                    meta = size_data[stem]
                else:
                    # Try partial match
                    for key in size_data:
                        if stem in key or key in stem:
                            meta = size_data[key]
                            break

            artworks.append((img_path.name, img, meta))

            if meta.get('estimated_width_inches'):
                print(f"  Loaded: {img_path.name} ({img.width}x{img.height}) → {meta['estimated_width_inches']}x{meta['estimated_height_inches']}\"")
            else:
                print(f"  Loaded: {img_path.name} ({img.width}x{img.height})")
        except Exception as e:
            print(f"  Skipped: {img_path.name} - {e}")

    return artworks


def generate_gallery(
    artworks: list[tuple[str, Image.Image, dict]],
    padding: int = 40,
    background_color: tuple[int, int, int] = (245, 245, 245),
    use_real_size: bool = False,
    ppi: int = 10,
) -> Image.Image:
    """
    Arrange artworks side by side in a single row.

    Args:
        artworks: List of (filename, PIL.Image, metadata) tuples
        padding: Pixels between each artwork
        background_color: RGB tuple for gallery background
        use_real_size: If True, scale images to real-world proportions
        ppi: Pixels per inch for real-size rendering

    Returns:
        Composite gallery image
    """
    if not artworks:
        raise ValueError("No artworks to arrange")

    # Process images - scale to real size if requested
    processed = []
    for name, img, meta in artworks:
        if use_real_size and meta.get('estimated_width_inches') and meta.get('estimated_height_inches'):
            # Scale to real-world size
            target_width = int(meta['estimated_width_inches'] * ppi)
            target_height = int(meta['estimated_height_inches'] * ppi)
            scaled_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            processed.append((name, scaled_img))
        else:
            processed.append((name, img))

    # Calculate total dimensions
    total_width = sum(img.width for _, img in processed) + padding * (len(processed) + 1)
    max_height = max(img.height for _, img in processed)
    total_height = max_height + padding * 2

    # Create canvas
    gallery = Image.new("RGB", (total_width, total_height), background_color)

    # Place each artwork (vertically centered, aligned at bottom for real-size mode)
    x_offset = padding
    for name, img in processed:
        if use_real_size:
            # Bottom-align for real-size (like hanging on a wall)
            y_offset = padding + (max_height - img.height)
        else:
            # Center vertically
            y_offset = padding + (max_height - img.height) // 2
        gallery.paste(img, (x_offset, y_offset))
        x_offset += img.width + padding

    return gallery


def run(
    input_dir: str = "input/artwork",
    output_file: str = "results/gallery.jpg",
    padding: int = 40,
    size_file: str = None,
    use_real_size: bool = False,
    ppi: int = 10,
):
    """Generate gallery composite from artwork images."""
    # Load size data if available
    size_data = {}
    if size_file and Path(size_file).exists():
        with open(size_file) as f:
            size_data = json.load(f)
        print(f"  Loaded size data from {size_file}")

    print(f"\n[Gallery] Loading artwork from {input_dir}...")
    artworks = load_artworks(input_dir, size_data=size_data, ppi=ppi)

    mode = "real-world scale" if use_real_size else "pixel size"
    print(f"\n[Gallery] Arranging {len(artworks)} piece(s) side by side ({mode})...")
    gallery = generate_gallery(artworks, padding=padding, use_real_size=use_real_size, ppi=ppi)

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gallery.save(output_file, quality=95)
    print(f"\n  Gallery saved: {output_file}")
    print(f"  Dimensions: {gallery.width}x{gallery.height}")
    if use_real_size:
        print(f"  Scale: {ppi} pixels per inch")

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
    parser.add_argument(
        "--sizes", "-s",
        default=None,
        help="JSON file with size estimates (from artwork_analysis.json)"
    )
    parser.add_argument(
        "--real-size", "-r",
        action="store_true",
        help="Scale images to real-world proportions"
    )
    parser.add_argument(
        "--ppi",
        type=int,
        default=10,
        help="Pixels per inch for real-size rendering (default: 10)"
    )
    args = parser.parse_args()

    run(
        input_dir=args.input,
        output_file=args.output,
        padding=args.padding,
        size_file=args.sizes,
        use_real_size=args.real_size,
        ppi=args.ppi,
    )


if __name__ == "__main__":
    main()
