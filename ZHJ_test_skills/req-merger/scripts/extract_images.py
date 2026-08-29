#!/usr/bin/env python3
"""
Extract images from zip file and rename with version prefix for requirement docs.

Usage:
    python extract_images.py --zip images.zip --target-dir images/商品/ --version-prefix v13

This extracts all images from the zip, renames them with the version prefix
(e.g., img_v13_image2025-8-20_17-33-32.png), and places them in the target directory.
"""

import argparse
import os
import re
import sys
import zipfile
from pathlib import Path


def extract_images(
    zip_path: str,
    target_dir: str,
    version_prefix: str,
    rename_pattern: str = None,
) -> dict:
    """
    Extract images from zip and rename with version prefix.

    Args:
        zip_path: Path to the zip file
        target_dir: Directory to place extracted images
        version_prefix: Version prefix like 'v11', 'v13'
        rename_pattern: Optional regex pattern to match source filenames

    Returns:
        dict mapping original filename -> new filename
    """
    zip_path = Path(zip_path)
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if not zip_path.exists():
        print(f"Error: Zip file not found: {zip_path}")
        sys.exit(1)

    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
    mapping = {}
    sequence = 1

    with zipfile.ZipFile(zip_path, "r") as zf:
        for entry in zf.namelist():
            # Skip directories and non-image files
            if entry.endswith("/") or "__MACOSX" in entry:
                continue

            ext = Path(entry).suffix.lower()
            if ext not in image_extensions:
                continue

            filename = Path(entry).name

            # Skip thumbnails or preview images
            if "thumb" in filename.lower() or "preview" in filename.lower():
                continue

            # Generate new filename
            if rename_pattern:
                # Apply custom pattern
                match = re.search(rename_pattern, filename)
                if match:
                    new_name = match.group(1)
                else:
                    new_name = filename
            else:
                # Default: prefix the original filename
                # Remove any existing version prefix to avoid double-prefixing
                clean_name = re.sub(r"^img_v\d+_", "", filename)
                clean_name = re.sub(r"^img_\d+_", "", clean_name)
                new_name = clean_name

            # Apply version prefix with sequence number
            # Format: img_v13_XXX_originalname.png
            new_filename = f"img_{version_prefix}_{sequence:03d}_{new_name}"
            target_path = target_dir / new_filename

            # Handle duplicate filenames
            if target_path.exists():
                sequence += 1
                new_filename = f"img_{version_prefix}_{sequence:03d}_{new_name}"
                target_path = target_dir / new_filename

            with zf.open(entry) as src, open(target_path, "wb") as dst:
                dst.write(src.read())

            mapping[filename] = new_filename
            print(f"  {filename} -> {new_filename}")
            sequence += 1

    return mapping


def map_html_images(
    html_refs: list,
    image_mapping: dict,
    existing_images: list = None,
) -> dict:
    """
    Map HTML <img> references to extracted image files.

    Args:
        html_refs: List of image references from HTML (src, alt, context)
        image_mapping: Dict from extract_images() (original -> new name)
        existing_images: List of already-existing image files in target dir

    Returns:
        dict mapping HTML src -> local filename
    """
    result = {}

    # Build a lookup: original filename (without path) -> new filename
    filename_lookup = {}
    for orig, new in image_mapping.items():
        filename_lookup[orig] = new
        # Also index by stem (without extension) for partial matching
        filename_lookup[Path(orig).stem] = new

    # If we have existing images, index them too
    if existing_images:
        for img_path in existing_images:
            filename_lookup[Path(img_path).name] = img_path
            filename_lookup[Path(img_path).stem] = img_path

    for ref in html_refs:
        src = ref["src"]

        # Direct match in mapping
        if src in filename_lookup:
            result[src] = filename_lookup[src]
            continue

        # Try matching by extracting filename from src (CID, URL, etc.)
        # Handle CID references: cid:xxx
        cid_match = re.match(r"cid:(.+)", src)
        if cid_match:
            cid = cid_match.group(1)
            if cid in filename_lookup:
                result[src] = filename_lookup[cid]
                continue

        # Handle filename-only references
        src_name = src.split("/")[-1] if "/" in src else src
        src_name = src_name.split("?")[0]  # Remove query params
        if src_name in filename_lookup:
            result[src] = filename_lookup[src_name]
            continue

        # Partial match: check if any key contains this src
        matched = False
        for key, value in filename_lookup.items():
            if src in key or key in src:
                result[src] = value
                matched = True
                break

        if not matched:
            print(f"  Warning: Could not map image reference: {src}")
            if ref.get("context"):
                print(f"    Context: {ref['context'][:100]}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Extract images from zip for requirement docs"
    )
    parser.add_argument("--zip", required=True, help="Path to image zip file")
    parser.add_argument(
        "--target-dir", required=True, help="Target directory for images"
    )
    parser.add_argument(
        "--version-prefix",
        required=True,
        help="Version prefix (e.g., v10, v11, v13)",
    )
    parser.add_argument(
        "--rename-pattern",
        help="Regex pattern to extract base name from filename",
    )
    args = parser.parse_args()

    print(f"Extracting images from: {args.zip}")
    print(f"Target directory: {args.target_dir}")
    print(f"Version prefix: {args.version_prefix}")
    print()

    mapping = extract_images(
        args.zip,
        args.target_dir,
        args.version_prefix,
        args.rename_pattern,
    )

    print(f"\nDone. {len(mapping)} images extracted.")
    return mapping


if __name__ == "__main__":
    main()
