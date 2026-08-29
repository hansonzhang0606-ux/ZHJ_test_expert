#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confluence Requirement Exporter
================================
Export a Confluence page as a Word document and download all attachments.

Supports two export modes:
  - ORIGINAL: Word doc to 原需求/, attachments zipped to 原图片/
  - LATEST:   Folder per title under 最新需求/, doc in folder, raw images in images/

Two ways to run:

  Option A (chat input, recommended):
    python export_confluence.py --page-id 91076209 --cookie "JSESSIONID=...; seraph.confluence=..." --mode ORIGINAL

  Option B (edit config below, then run):
    python export_confluence.py

Cookie expires frequently. Passing it via --cookie in chat is the simplest.

Requirements:
    - Python 3.8+ (standard library only, no external dependencies)
    - Valid Confluence cookie (JSESSIONID + seraph.confluence)
"""

import os
import sys
import json
import argparse
import zipfile
import urllib.request
import base64

# ============================================================
# PROJECT CONFIGURATION - Paths specific to this workspace
# (cookie/pageId/mode are passed via CLI, not edited here)
# ============================================================

BASE_URL = "https://finkms.kingdee.com"  # Confluence base URL

# Output directories (relative to project root)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Mode 1 (ORIGINAL) output directories
WORD_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, ".qwen", "knowledge-base", "requirements", "原需求")
ATTACHMENT_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, ".qwen", "knowledge-base", "requirements", "原图片")

# Mode 2 (LATEST) base directory (script auto-creates {title}/ and {title}/images/)
LATEST_REQ_BASE = os.path.join(_PROJECT_ROOT, "最新需求")

# Filename separator replacement (Windows does not allow / in filenames)
SLASH_REPLACEMENT = "_"

# Fallback values (used only when CLI args are not provided)
DEFAULT_PAGE_ID = ""
DEFAULT_COOKIE_STR = ""
DEFAULT_MODE = "ORIGINAL"  # "ORIGINAL" or "LATEST"

# ============================================================
# END OF CONFIGURATION
# ============================================================


HEADERS = {
    "Cookie": "",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def sanitize_filename(name):
    """Replace characters not allowed in Windows filenames.

    Windows forbidden chars: \\ / : * ? " < > |
    """
    forbidden = '\\/:*?"<>|'
    for ch in forbidden:
        name = name.replace(ch, SLASH_REPLACEMENT)
    return name


def make_request(url, method="GET", data=None):
    """Make an HTTP request with cookie authentication."""
    req = urllib.request.Request(url, data=data, method=method)
    for key, val in HEADERS.items():
        if val:
            req.add_header(key, val)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return resp
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        try:
            body = e.read().decode("utf-8", errors="replace")
            if len(body) > 500:
                body = body[:500] + "..."
            print(f"  Body: {body}")
        except Exception:
            pass
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def get_page_title(page_id):
    """Get the page title via Confluence REST API."""
    api_url = f"{BASE_URL}/rest/api/content/{page_id}?expand=title"
    print(f"  Getting page title from: {api_url}")

    resp = make_request(api_url)
    if resp is not None:
        try:
            data = json.loads(resp.read().decode("utf-8"))
            title = data.get("title", "")
            print(f"  Page title: {title}")
            return title
        except Exception as e:
            print(f"  Error parsing API response: {e}")

    print("  WARNING: Could not get page title from API")
    return None


def export_to_word(page_id, title, output_dir):
    """Export the Confluence page as a Word document.

    Confluence's /exportword endpoint returns MHTML format
    (Content-Type: application/vnd.ms-word;charset=UTF-8).
    This is a valid Word document despite being HTML-based.
    """
    export_url = f"{BASE_URL}/exportword?pageId={page_id}"
    print(f"  Exporting Word from: {export_url}")

    resp = make_request(export_url)
    if resp is None:
        print("  FAILED: Could not export to Word")
        return False

    content = resp.read()
    content_type = resp.headers.get("Content-Type", "")

    print(f"  Content-Type: {content_type}")
    print(f"  Size: {len(content)} bytes ({len(content) / 1024 / 1024:.2f} MB)")

    # Verify it's a valid Word export (MHTML format starts with MIME headers)
    # Do NOT treat MHTML as login page just because it contains <html>
    is_valid_word = (
        b"MIME-Version" in content[:500]
        or b"multipart/related" in content[:500]
        or content[:4] == b"PK\x03\x04"  # docx (ZIP)
        or content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # doc (OLE2)
    )

    if not is_valid_word and b"<html" in content[:500].lower():
        text = content.decode("utf-8", errors="replace")[:1000]
        if "login" in text.lower() or "password" in text.lower():
            print("  FAILED: Got login page - cookie may be expired")
            return False

    # Determine file extension
    if content[:4] == b"PK\x03\x04":
        ext = ".docx"
    elif content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        ext = ".doc"
    else:
        ext = ".doc"  # MHTML format uses .doc extension

    safe_title = sanitize_filename(title or page_id)
    output_path = os.path.join(output_dir, f"{safe_title}{ext}")

    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(content)

    print(f"  SUCCESS: Saved Word file to: {output_path}")
    return True


def get_attachments(page_id):
    """Get list of attachments via Confluence REST API.

    Returns list of dicts with: title, download_link, media_type, file_size
    """
    all_attachments = []
    start = 0
    limit = 200

    while True:
        api_url = (
            f"{BASE_URL}/rest/api/content/{page_id}/child/attachment"
            f"?limit={limit}&start={start}"
        )
        print(f"  Fetching attachments (start={start}): {api_url}")

        resp = make_request(api_url)
        if resp is None:
            break

        try:
            data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  Error parsing attachment API response: {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        for att in results:
            att_info = {
                "title": att.get("title", ""),
                "filename": att.get("title", ""),
                "download_link": att.get("_links", {}).get("download", ""),
                "media_type": att.get("metadata", {}).get("mediaType", ""),
                "file_size": att.get("extensions", {}).get("fileSize", "0"),
            }
            all_attachments.append(att_info)

        # Check if there are more results
        links = data.get("_links", {})
        if "next" not in links:
            break

        start += limit

    print(f"  Found {len(all_attachments)} attachments total")
    return all_attachments


def download_attachment(att):
    """Download a single attachment. Returns (filename, content_bytes) or (filename, None)."""
    filename = att["filename"]
    download_link = att["download_link"]

    if download_link.startswith("http"):
        full_url = download_link
    elif download_link.startswith("/"):
        full_url = BASE_URL + download_link
    else:
        full_url = BASE_URL + "/" + download_link

    resp = make_request(full_url)
    if resp is not None:
        content = resp.read()
        # Verify it's a file, not an HTML error page
        if b"<html" in content[:500].lower():
            return filename, None
        return filename, content
    return filename, None


def create_attachment_zip(attachments, title, output_dir):
    """Mode 1 (ORIGINAL): Download all attachments and package into a zip file.

    Preserves original filenames inside the zip.
    """
    print(f"\n  Downloading {len(attachments)} attachments...")

    downloaded = []
    failed = []

    for i, att in enumerate(attachments, 1):
        filename, content = download_attachment(att)
        if content:
            downloaded.append((filename, content))
            print(f"  [{i}/{len(attachments)}] {filename}: {len(content)} bytes")
        else:
            failed.append(filename)
            print(f"  [{i}/{len(attachments)}] {filename}: FAILED")

    print(f"\n  Downloaded: {len(downloaded)}/{len(attachments)}")
    if failed:
        print(f"  Failed: {len(failed)}")
        for f in failed:
            print(f"    - {f}")

    # Create zip file
    safe_title = sanitize_filename(title or PAGE_ID)
    zip_filename = f"{safe_title}.zip"
    zip_path = os.path.join(output_dir, zip_filename)

    os.makedirs(output_dir, exist_ok=True)

    # Remove old zip if exists
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in downloaded:
            zf.writestr(filename, content)

    zip_size = os.path.getsize(zip_path)
    print(f"\n  Zip file created: {zip_path}")
    print(f"  Zip size: {zip_size / 1024 / 1024:.2f} MB ({zip_size} bytes)")
    print(f"  Files in zip: {len(downloaded)}")

    return zip_path


def download_attachments_raw(attachments, images_dir):
    """Mode 2 (LATEST): Download all attachments as raw files into images_dir.

    Preserves original filenames. No zip packaging.
    """
    print(f"\n  Downloading {len(attachments)} attachments to {images_dir}...")

    os.makedirs(images_dir, exist_ok=True)

    success_count = 0
    fail_count = 0

    for i, att in enumerate(attachments, 1):
        filename, content = download_attachment(att)
        if content:
            output_path = os.path.join(images_dir, filename)
            with open(output_path, "wb") as f:
                f.write(content)
            success_count += 1
            if i <= 5 or i % 20 == 0 or i == len(attachments):
                print(f"  [{i}/{len(attachments)}] {filename}: {len(content)} bytes")
        else:
            fail_count += 1
            print(f"  [{i}/{len(attachments)}] {filename}: FAILED")

    print(f"\n  Downloaded: {success_count}/{len(attachments)}, Failed: {fail_count}")
    return success_count


def main():
    global BASE_URL, HEADERS
    parser = argparse.ArgumentParser(
        description="Export a Confluence page to Word + attachments."
    )
    parser.add_argument("--page-id", help="Confluence pageId (e.g. 91076209)")
    parser.add_argument("--cookie", help="Confluence cookie string (JSESSIONID=...; seraph.confluence=...)")
    parser.add_argument("--username", help="Confluence username (HTTP Basic Auth, alternative to cookie)")
    parser.add_argument("--password", help="Confluence password (HTTP Basic Auth)")
    parser.add_argument("--mode", choices=["ORIGINAL", "LATEST"],
                        default=DEFAULT_MODE, help="ORIGINAL or LATEST")
    parser.add_argument("--base-url", default=BASE_URL, help="Confluence base URL")
    args = parser.parse_args()

    page_id = args.page_id or DEFAULT_PAGE_ID
    cookie = args.cookie or DEFAULT_COOKIE_STR
    mode = args.mode or DEFAULT_MODE
    base_url = args.base_url or BASE_URL

    if not page_id:
        print("ERROR: pageId is required. Pass via --page-id or set DEFAULT_PAGE_ID.")
        sys.exit(1)

    # 读取本机配置文件（账号密码，密码 base64 编码 = 密文存储，不依赖 cookie）
    auth_file = os.path.join(os.path.expanduser("~"), ".workbuddy", "confluence_auth.json")
    config_user = config_pass = None
    if os.path.exists(auth_file):
        try:
            with open(auth_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            config_user = cfg.get("username")
            config_pass = base64.b64decode(cfg.get("password_base64", "")).decode("utf-8")
        except Exception:
            pass

    # 认证优先级：--username/--password > 配置文件 > --cookie
    username = args.username or config_user
    password = args.password or config_pass

    BASE_URL = base_url
    auth_mode = ""
    if username and password:
        creds = base64.b64encode(f"{username}:{password}".encode()).decode()
        HEADERS["Authorization"] = f"Basic {creds}"
        HEADERS["Cookie"] = ""
        auth_mode = "Basic Auth (账号密码)"
    elif cookie:
        HEADERS["Cookie"] = cookie
        auth_mode = "Cookie"
    else:
        print("ERROR: 需要 --username/--password 或 --cookie，或配置文件 ~/.workbuddy/confluence_auth.json")
        sys.exit(1)

    print("=" * 60)
    print(f"Confluence Requirement Exporter (Mode: {mode})")
    print("=" * 60)
    print(f"  Page ID: {page_id}")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Export mode: {mode}")
    print(f"  Auth: {auth_mode}")

    # Step 1: Get page title
    print("\n" + "-" * 40)
    print("Step 1: Get page title")
    print("-" * 40)
    title = get_page_title(page_id)
    if not title:
        print("  ERROR: Could not get page title. Check cookie and page ID.")
        sys.exit(1)

    safe_title = sanitize_filename(title)
    print(f"  Safe title: {safe_title}")

    if mode == "LATEST":
        # Mode 2: Latest requirement - create folder structure
        title_dir = os.path.join(LATEST_REQ_BASE, safe_title)
        images_dir = os.path.join(title_dir, "images")
        word_output_dir = title_dir
        print(f"\n  Directory structure:")
        print(f"    {LATEST_REQ_BASE}/")
        print(f"    └── {safe_title}/")
        print(f"        ├── {safe_title}.doc")
        print(f"        └── images/")
    else:
        # Mode 1: Original requirement - use configured directories
        word_output_dir = WORD_OUTPUT_DIR
        print(f"  Word output: {WORD_OUTPUT_DIR}")
        print(f"  Attachment output: {ATTACHMENT_OUTPUT_DIR}")

    # Step 2: Export as Word
    print("\n" + "-" * 40)
    print("Step 2: Export page as Word")
    print("-" * 40)
    word_ok = export_to_word(page_id, title, word_output_dir)

    # Step 3: Get attachments
    print("\n" + "-" * 40)
    print("Step 3: Get attachment list")
    print("-" * 40)
    attachments = get_attachments(page_id)

    if not attachments:
        print("  No attachments found.")
    else:
        # Step 4: Download attachments (mode-dependent)
        print("\n" + "-" * 40)
        if mode == "LATEST":
            print("Step 4: Download attachments to images/ (raw files)")
            print("-" * 40)
            os.makedirs(images_dir, exist_ok=True)
            success_count = download_attachments_raw(attachments, images_dir)
        else:
            print("Step 4: Download attachments and create zip")
            print("-" * 40)
            zip_path = create_attachment_zip(attachments, title, ATTACHMENT_OUTPUT_DIR)

    # Summary
    print("\n" + "=" * 60)
    print("ALL DONE")
    print("=" * 60)
    print(f"  Page title: {title}")
    print(f"  Export mode: {mode}")
    print(f"  Word export: {'SUCCESS' if word_ok else 'FAILED'}")

    if mode == "LATEST":
        print(f"  Word file: {os.path.join(title_dir, safe_title + '.doc')}")
        if attachments:
            print(f"  Attachments: {len(attachments)} found, {success_count} downloaded")
            print(f"  Images dir: {images_dir}")
    else:
        print(f"  Word file: {os.path.join(WORD_OUTPUT_DIR, safe_title + '.doc')}")
        if attachments:
            print(f"  Attachments: {len(attachments)} found")
            print(f"  Zip file: {os.path.join(ATTACHMENT_OUTPUT_DIR, safe_title + '.zip')}")


if __name__ == "__main__":
    main()
