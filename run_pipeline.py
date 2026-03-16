#!/usr/bin/env python3
"""
run_pipeline.py — Orchestrates the full art placement pipeline.

Usage:
    python run_pipeline.py
    python run_pipeline.py --apartment input/apartment --artwork input/artwork
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def check_dependencies():
    """Verify required packages and tools are installed."""
    errors = []

    try:
        import anthropic
    except ImportError:
        errors.append("anthropic  →  pip install anthropic")

    try:
        import cv2
    except ImportError:
        errors.append("opencv-python  →  pip install opencv-python")

    try:
        from PIL import Image
    except ImportError:
        errors.append("Pillow  →  pip install Pillow")

    try:
        import numpy
    except ImportError:
        errors.append("numpy  →  pip install numpy")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        errors.append("ANTHROPIC_API_KEY not set  →  export ANTHROPIC_API_KEY=your_key")

    if errors:
        print("\n❌ Missing dependencies:\n")
        for e in errors:
            print(f"   {e}")
        print()
        sys.exit(1)

    print("✓ All dependencies found")


def check_input_folders(apartment_dir: str, artwork_dir: str):
    """Check input folders exist and have images."""
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}

    for name, folder in [("Apartment", apartment_dir), ("Artwork", artwork_dir)]:
        path = Path(folder)
        if not path.exists():
            print(f"\n❌ {name} folder not found: {folder}")
            print(f"   Create it and add your images: mkdir -p {folder}")
            sys.exit(1)
        images = [f for f in path.iterdir() if f.suffix.lower() in valid_exts]
        if not images:
            print(f"\n❌ No images found in {folder}")
            print(f"   Add .jpg or .png files there.")
            sys.exit(1)
        print(f"✓ {name}: {len(images)} image(s) in {folder}")


def main():
    parser = argparse.ArgumentParser(description="Art Placement Pipeline")
    parser.add_argument("--apartment", default="input/apartment", help="Apartment photos folder")
    parser.add_argument("--artwork", default="input/artwork", help="Artwork photos folder")
    parser.add_argument("--output", default="results", help="Output folder for composited images")
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("  🎨  Art Placement Pipeline")
    print("=" * 55)

    print("\nChecking setup...")
    check_dependencies()
    check_input_folders(args.apartment, args.artwork)

    # ── Step 1: Analyze rooms ──────────────────────────────────
    from analyze_rooms import run as analyze_rooms
    analyze_rooms(input_dir=args.apartment, output_file="rooms_analysis.json")

    # ── Step 2: Analyze artwork ────────────────────────────────
    from analyze_art import run as analyze_art
    analyze_art(input_dir=args.artwork, output_file="artwork_analysis.json")

    # ── Step 3: Match & score ──────────────────────────────────
    from match_and_place import run as match_and_place
    placements = match_and_place(
        rooms_file="rooms_analysis.json",
        artwork_file="artwork_analysis.json",
        output_file="placement_plan.json",
    )

    if not placements:
        print("\n⚠️  No placements generated. Check your input images.")
        sys.exit(1)

    # ── Step 4: Composite ──────────────────────────────────────
    from composite import run as composite
    output_paths = composite(
        placement_file="placement_plan.json",
        output_dir=args.output,
        rooms_file="rooms_analysis.json",
    )

    # ── Step 5: Report ─────────────────────────────────────────
    from generate_report import run as generate_report
    report_path = generate_report(
        placement_file="placement_plan.json",
        output_file="placement_report.md",
    )

    # ── Done ───────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  ✅  Pipeline complete!")
    print("=" * 55)
    print(f"\n  📁 Composited images  →  /{args.output}/")
    print(f"  📄 Design report      →  placement_report.md")
    print(f"  📊 Raw analysis       →  rooms_analysis.json")
    print(f"                           artwork_analysis.json")
    print(f"                           placement_plan.json")
    print()


if __name__ == "__main__":
    main()
