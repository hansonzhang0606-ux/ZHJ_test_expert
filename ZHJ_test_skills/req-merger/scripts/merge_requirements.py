#!/usr/bin/env python3
"""
Merge new requirements from Confluence HTML into an existing Markdown document.

Handles:
- Version conflict resolution (newer version wins)
- Strikethrough content removal
- Image reference updates
- Structure consistency (业务说明 → 字段说明 → 页面逻辑 → 版本差异)

Usage:
    python merge_requirements.py --base 03_商品.md --new-html extracted.html \
        --version v13 --images-dir images/商品 --output 03_商品.md
"""

import argparse
import os
import re
import sys
from pathlib import Path


def strip_deleted_content(text: str) -> str:
    """Remove strikethrough content from text."""
    # Remove ~~text~~ patterns
    text = re.sub(r"~~[^~]*~~", "", text)
    # Remove <del>...</del> patterns
    text = re.sub(r"<del[^>]*>.*?</del>", "", text, flags=re.DOTALL)
    return text


def extract_html_sections(html_path: str) -> dict:
    """
    Extract structured sections from Confluence HTML.

    Returns dict with section names and their content.
    Typical sections: 业务说明, 字段说明, 页面逻辑
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Error: bs4 (beautifulsoup4) is required. Install with: pip install beautifulsoup4")
        sys.exit(1)

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    sections = {}
    current_section = None
    current_content = []

    # Walk through all elements to find section headings and their content
    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "table", "div", "p"]):
        if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            # Save previous section
            if current_section:
                sections[current_section] = "".join(current_content)

            # Start new section
            heading_text = element.get_text(strip=True)
            current_section = heading_text
            current_content = []
        elif element.name == "table":
            current_content.append(str(element))
        elif element.name in ["div", "p"]:
            text = element.get_text(strip=True)
            if text:
                current_content.append(str(element))

    # Save last section
    if current_section:
        sections[current_section] = "".join(current_content)

    return sections


def html_table_to_markdown(html_table) -> str:
    """Convert an HTML table to Markdown table format."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return str(html_table)

    soup = BeautifulSoup(str(html_table), "html.parser")
    rows = soup.find_all("tr")
    if not rows:
        return ""

    lines = []

    for i, row in enumerate(rows):
        cells = row.find_all(["td", "th"])
        cell_texts = []
        for cell in cells:
            text = cell.get_text(strip=True)
            text = strip_deleted_content(text)

            # Handle <img> tags - extract src
            for img in cell.find_all("img"):
                src = img.get("src", "")
                alt = img.get("alt", "")
                # Keep image reference as a placeholder for later mapping
                img_tag = f"![{alt}]({src})"
                text = text + f" {img_tag}" if text else img_tag

            cell_texts.append(text)

        if i == 0:
            # Header row
            lines.append("| " + " | ".join(cell_texts) + " |")
            lines.append("| " + " | ".join(["---"] * len(cell_texts)) + " |")
        else:
            lines.append("| " + " | ".join(cell_texts) + " |")

    return "\n".join(lines)


def extract_prototype_images_from_html(html_path: str, version_prefix: str, images_dir: str) -> dict:
    """
    Extract prototype image references from Confluence HTML tables.

    The HTML typically has tables like:
    | 页面名称 | 原型 | 需求详细说明 |

    This maps each page name to its prototype images.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Error: bs4 (beautifulsoup4) is required.")
        sys.exit(1)

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    images_dir = Path(images_dir)

    # Get list of available images in the target directory
    available_images = set()
    if images_dir.exists():
        for f in images_dir.iterdir():
            if f.is_file() and version_prefix in f.name:
                available_images.add(f.name)

    # Find all tables and extract page-image mappings
    page_images = {}
    current_page = None

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                # Check if this is a header row
                header_text = cells[0].get_text(strip=True)
                if "页面" in header_text or "页面名称" in header_text:
                    continue  # Skip header row

                # First cell might be the page name
                page_name = cells[0].get_text(strip=True)
                if page_name and len(page_name) > 2:
                    current_page = page_name

                # Look for images in other cells
                for cell in cells[1:]:
                    for img in cell.find_all("img"):
                        src = img.get("src", "")
                        alt = img.get("alt", "")

                        # Match to available images
                        matched = None
                        for avail_img in available_images:
                            if alt and alt in avail_img:
                                matched = avail_img
                                break
                            if src and Path(src).name in avail_img:
                                matched = avail_img
                                break

                        if matched:
                            if current_page not in page_images:
                                page_images[current_page] = []
                            page_images[current_page].append(matched)

    return page_images


def merge_sections(base_md: str, new_sections: dict, version: str) -> str:
    """
    Merge new sections into existing Markdown content.

    Rules:
    1. If a section with the same name exists, merge/replace content
    2. New sections are appended at the end
    3. Strikethrough content is removed
    """
    lines = base_md.split("\n")
    output_lines = []
    in_section = False
    section_header = None

    for line in lines:
        # Check for section headers
        header_match = re.match(r"^(#{1,3})\s+(.+)", line)
        if header_match:
            section_header = header_match.group(2).strip()
            in_section = section_header in new_sections

        if in_section and section_header in new_sections:
            # Replace with new content
            if f"### {section_header}" in line or f"## {section_header}" in line:
                output_lines.append(line)
                output_lines.append(new_sections[section_header])
                # Skip until next section header
                in_section = "REPLACING"
                continue
            if in_section == "REPLACING":
                # Check if we've hit the next section
                if header_match:
                    in_section = section_header in new_sections
                    output_lines.append(line)
                continue

        # Remove strikethrough content
        line = strip_deleted_content(line)
        output_lines.append(line)

    # Append any sections not in base
    for section_name, section_content in new_sections.items():
        if section_name not in base_md:
            output_lines.append("")
            output_lines.append(f"### {section_name}")
            output_lines.append("")
            output_lines.append(section_content)

    return "\n".join(output_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Merge requirements from HTML into Markdown document"
    )
    parser.add_argument("--base", required=True, help="Path to existing Markdown file")
    parser.add_argument(
        "--new-html", required=True, help="Path to extracted HTML from Confluence doc"
    )
    parser.add_argument(
        "--version", required=True, help="Version tag (e.g., v10, v11, v13)"
    )
    parser.add_argument(
        "--images-dir", required=True, help="Directory containing version images"
    )
    parser.add_argument(
        "--output", required=True, help="Path to output Markdown file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be merged without writing output",
    )
    args = parser.parse_args()

    base_path = Path(args.base)
    if not base_path.exists():
        print(f"Error: Base Markdown file not found: {base_path}")
        sys.exit(1)

    html_path = Path(args.new_html)
    if not html_path.exists():
        print(f"Error: HTML file not found: {html_path}")
        sys.exit(1)

    # Read base Markdown
    with open(base_path, "r", encoding="utf-8") as f:
        base_md = f.read()

    # Extract sections from HTML
    print(f"Extracting sections from: {html_path}")
    sections = extract_html_sections(str(html_path))
    print(f"  Found {len(sections)} sections: {list(sections.keys())}")

    # Extract prototype image mappings
    print(f"Mapping prototype images from: {args.images_dir}")
    page_images = extract_prototype_images_from_html(
        str(html_path), args.version, args.images_dir
    )
    print(f"  Found {len(page_images)} page-to-image mappings")

    # Merge
    print(f"\nMerging {args.version} requirements into: {args.output}")
    merged = merge_sections(base_md, sections, args.version)

    if args.dry_run:
        print("\n--- DRY RUN: Would write the following ---")
        print(merged[:2000])
        print("... (truncated)")
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(merged)
        print(f"  Written to: {args.output}")

    return merged


if __name__ == "__main__":
    main()
