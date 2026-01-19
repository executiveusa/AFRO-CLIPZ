#!/usr/bin/env python3
"""
Asset Organizer for AfroMations

This script processes assets uploaded to /incoming and organizes them
into the /assets directory with proper categorization and manifest tracking.

Usage:
    python tools/organize_assets.py --input ./incoming --output ./assets --manifest ./assets/manifest.json

Features:
- Content-addressable storage (SHA-256 hashing)
- Automatic categorization by file type
- Image dimension extraction
- Deduplication
- Manifest generation for asset tracking
"""

import argparse
import hashlib
import json
import mimetypes
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Asset category mappings
CATEGORY_MAPPINGS = {
    # Images
    ".gif": "hero",  # GIFs default to hero (animation)
    ".png": "images",
    ".jpg": "images",
    ".jpeg": "images",
    ".webp": "images",
    ".svg": "icons",
    ".ico": "icons",
    # Videos
    ".mp4": "video",
    ".mov": "video",
    ".avi": "video",
    ".webm": "video",
    ".mkv": "video",
    # Audio
    ".mp3": "audio",
    ".wav": "audio",
    ".m4a": "audio",
    ".ogg": "audio",
    # Documents
    ".pdf": "documents",
    ".txt": "documents",
    ".md": "documents",
    # Fonts
    ".ttf": "fonts",
    ".otf": "fonts",
    ".woff": "fonts",
    ".woff2": "fonts",
    # Design files
    ".psd": "design",
    ".ai": "design",
    ".sketch": "design",
    ".fig": "design",
}

# Special filename mappings (override category based on name)
SPECIAL_FILES = {
    "afromations_flag_pick.gif": "hero",
    "logo": "brand",
    "favicon": "brand",
}


def compute_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_image_dimensions(file_path: Path) -> Optional[Dict[str, int]]:
    """Get image dimensions if PIL is available."""
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            return {"width": img.width, "height": img.height}
    except ImportError:
        return None
    except Exception:
        return None


def get_category(file_path: Path) -> str:
    """Determine the category for an asset based on extension and name."""
    filename = file_path.name.lower()
    extension = file_path.suffix.lower()

    # Check special filename mappings first
    for pattern, category in SPECIAL_FILES.items():
        if pattern in filename:
            return category

    # Fall back to extension mapping
    return CATEGORY_MAPPINGS.get(extension, "misc")


def get_mime_type(file_path: Path) -> str:
    """Get MIME type for a file."""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load existing manifest or create new one."""
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            return json.load(f)
    return {
        "version": "1.0",
        "generated_at": None,
        "assets": {}
    }


def save_manifest(manifest_path: Path, manifest: Dict[str, Any]) -> None:
    """Save manifest to disk."""
    manifest["generated_at"] = datetime.utcnow().isoformat() + "Z"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def organize_asset(
    file_path: Path,
    output_dir: Path,
    manifest: Dict[str, Any],
    dry_run: bool = False
) -> Optional[str]:
    """
    Organize a single asset file.

    Returns the relative path in assets directory, or None if skipped.
    """
    if file_path.name.startswith(".") or file_path.name in ["README.md", ".gitkeep"]:
        print(f"  Skipping: {file_path.name} (system file)")
        return None

    # Compute content hash
    content_hash = compute_hash(file_path)

    # Check for duplicates
    for asset_path, asset_info in manifest.get("assets", {}).items():
        if asset_info.get("content_hash") == f"sha256:{content_hash}":
            print(f"  Skipping: {file_path.name} (duplicate of {asset_path})")
            return None

    # Determine category and destination
    category = get_category(file_path)
    dest_dir = output_dir / category
    dest_path = dest_dir / file_path.name
    relative_path = f"{category}/{file_path.name}"

    # Handle name collisions
    counter = 1
    while dest_path.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        new_name = f"{stem}_{counter}{suffix}"
        dest_path = dest_dir / new_name
        relative_path = f"{category}/{new_name}"
        counter += 1

    if dry_run:
        print(f"  Would move: {file_path.name} -> {relative_path}")
        return relative_path

    # Create directory and move file
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(file_path), str(dest_path))
    print(f"  Moved: {file_path.name} -> {relative_path}")

    # Build asset metadata
    asset_info = {
        "original_name": file_path.name,
        "content_hash": f"sha256:{content_hash}",
        "size_bytes": dest_path.stat().st_size,
        "mime_type": get_mime_type(dest_path),
        "category": category,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
    }

    # Add dimensions for images
    dimensions = get_image_dimensions(dest_path)
    if dimensions:
        asset_info["dimensions"] = dimensions

    # Update manifest
    manifest["assets"][relative_path] = asset_info

    return relative_path


def main():
    parser = argparse.ArgumentParser(
        description="Organize uploaded assets into the assets directory"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("./incoming"),
        help="Input directory containing uploaded assets"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("./assets"),
        help="Output directory for organized assets"
    )
    parser.add_argument(
        "--manifest", "-m",
        type=Path,
        default=Path("./assets/manifest.json"),
        help="Path to asset manifest file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Validate input directory
    if not args.input.exists():
        print(f"Error: Input directory does not exist: {args.input}")
        sys.exit(1)

    if not args.input.is_dir():
        print(f"Error: Input path is not a directory: {args.input}")
        sys.exit(1)

    # Load or create manifest
    manifest = load_manifest(args.manifest)

    # Find all files in input directory
    files = [f for f in args.input.iterdir() if f.is_file()]

    if not files:
        print("No files found in input directory.")
        return

    print(f"Found {len(files)} file(s) to process")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Manifest: {args.manifest}")
    if args.dry_run:
        print("DRY RUN - no changes will be made")
    print()

    # Process each file
    organized = 0
    skipped = 0

    for file_path in sorted(files):
        result = organize_asset(file_path, args.output, manifest, args.dry_run)
        if result:
            organized += 1
        else:
            skipped += 1

    print()
    print(f"Summary: {organized} organized, {skipped} skipped")

    # Save manifest (unless dry run)
    if not args.dry_run and organized > 0:
        save_manifest(args.manifest, manifest)
        print(f"Manifest updated: {args.manifest}")

    # Report any pending required assets
    print()
    print("=" * 50)
    print("PENDING REQUIRED ASSETS")
    print("=" * 50)

    required_assets = [
        ("afromations_flag_pick.gif", "Hero section background media"),
    ]

    for asset_name, purpose in required_assets:
        found = any(asset_name in path for path in manifest.get("assets", {}).keys())
        status = "FOUND" if found else "MISSING"
        print(f"  [{status}] {asset_name} - {purpose}")

    print()
    print("To upload missing assets:")
    print("  1. Copy files to ./incoming/")
    print("  2. Run this script again")
    print()


if __name__ == "__main__":
    main()
