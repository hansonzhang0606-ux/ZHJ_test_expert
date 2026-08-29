#!/usr/bin/env python3
"""
Extract HTML content and embedded images from Confluence-exported MIME .doc files.

Confluence exports requirements as MIME multipart/related documents with
quoted-printable encoding, NOT real Word .doc files. python-docx cannot parse them.

Usage:
    python extract_confluence_doc.py --input <confluence-doc.doc> --output-dir <out-dir>
"""

import argparse
import email
import email.parser
import email.policy
import io
import os
import re
import sys
from pathlib import Path

# Fix Windows console encoding for Chinese text
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def parse_confluence_doc(doc_path: str, output_dir: str) -> dict:
    """
    Parse a Confluence MIME .doc file and extract HTML + embedded images.

    Returns dict with:
        - html_path: path to extracted HTML file
        - images: list of extracted image file paths
        - image_cids: dict mapping CID to image filename
    """
    doc_path = Path(doc_path)
    if not doc_path.exists():
        print(f"Error: File not found: {doc_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    img_dir = Path(output_dir) / "images"
    img_dir.mkdir(exist_ok=True)

    with open(doc_path, "rb") as f:
        raw = f.read()

    # Check if this is actually a MIME document
    if b"multipart/related" not in raw and b"MIME-Version" not in raw:
        print(f"Warning: {doc_path} does not appear to be a Confluence MIME export.")
        print("It may be a regular binary .doc file (requires antiword/olefile).")
        sys.exit(1)

    msg = email.parser.BytesParser(policy=email.policy.default).parsebytes(raw)

    result = {
        "html_path": None,
        "images": [],
        "image_cids": {},
    }

    def _walk(part, depth=0):
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition", "")
        content_id = part.get("Content-ID", "")
        content_location = part.get("Content-Location", "")

        # Clean up CID: strip < > if present
        if content_id:
            content_id = content_id.strip("<>")

        # Extract HTML content
        if content_type == "text/html":
            payload = part.get_payload(decode=True)
            if payload:
                # Try to detect encoding
                charset = part.get_content_charset() or "utf-8"
                try:
                    html_content = payload.decode(charset)
                except (UnicodeDecodeError, LookupError):
                    html_content = payload.decode("utf-8", errors="replace")

                html_path = Path(output_dir) / "main.html"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                result["html_path"] = str(html_path)
                print(f"  Extracted HTML: {html_path}")

        # Extract image attachments
        elif content_type.startswith("image/") or (
            "attachment" in content_disposition and content_type != "text/html"
        ):
            payload = part.get_payload(decode=True)
            if payload:
                # Determine filename
                filename = part.get_filename()
                if not filename:
                    if content_location:
                        filename = Path(content_location).name
                    elif content_id:
                        filename = f"cid_{content_id}.png"
                    else:
                        filename = f"image_{len(result['images'])}.bin"

                img_path = img_dir / filename
                with open(img_path, "wb") as f:
                    f.write(payload)
                result["images"].append(str(img_path))

                if content_id:
                    result["image_cids"][content_id] = filename
                print(f"  Extracted image: {img_path} (CID: {content_id or 'none'})")

        # Recurse into multipart
        if part.is_multipart():
            for subpart in part.get_payload():
                if isinstance(subpart, email.message.Message):
                    _walk(subpart, depth + 1)

    _walk(msg)

    if not result["html_path"]:
        print("Warning: No HTML content found in the MIME document.")

    return result


def extract_image_references(html_path: str) -> list:
    """
    Extract <img> references from HTML. Returns list of dicts with
    src, alt, and parent_context info.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Note: bs4 not installed. Skipping image reference extraction.")
        print("Install with: pip install beautifulsoup4")
        return []

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    images = []

    for img in soup.find_all("img"):
        ref = {
            "src": img.get("src", ""),
            "alt": img.get("alt", ""),
            "title": img.get("title", ""),
        }

        # Get parent context (table row or section info)
        parent = img.parent
        context_parts = []
        depth = 0
        while parent and depth < 5:
            tag_name = parent.name or ""
            if tag_name in ["td", "th", "div", "p", "tr"]:
                text = parent.get_text(strip=True)
                if text:
                    context_parts.append(text[:200])
                    if tag_name in ["tr", "p"]:
                        break
            parent = parent.parent
            depth += 1

        ref["context"] = " | ".join(context_parts[-3:]) if context_parts else ""
        images.append(ref)

    return images


def main():
    parser = argparse.ArgumentParser(
        description="Extract HTML and images from Confluence MIME .doc files"
    )
    parser.add_argument("--input", required=True, help="Path to Confluence .doc file")
    parser.add_argument(
        "--output-dir", required=True, help="Directory for extracted output"
    )
    parser.add_argument(
        "--extract-img-refs",
        action="store_true",
        help="Extract and list <img> references from HTML",
    )
    args = parser.parse_args()

    print(f"Parsing Confluence MIME document: {args.input}")
    result = parse_confluence_doc(args.input, args.output_dir)

    if result["html_path"] and args.extract_img_refs:
        print(f"\nExtracting image references from HTML...")
        refs = extract_image_references(result["html_path"])
        for i, ref in enumerate(refs):
            print(f"  [{i}] src={ref['src']} alt={ref['alt']}")
            if ref["context"]:
                print(f"      context: {ref['context'][:100]}")

    print(f"\nDone. {len(result['images'])} images, 1 HTML file extracted.")
    return result


if __name__ == "__main__":
    main()
