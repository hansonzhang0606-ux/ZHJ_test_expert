#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVN Archive Upload Script
=========================
Upload test-case files to SVN for project archival.
- Creates v{version}/ folder if not exists (svn mkdir)
- Imports files via svn import
- UPLOAD-ONLY: never delete
- Credentials rely on svn auth cache (passwordless after first cache)

Usage:
    python svn_upload.py --version v1.6.1 --files <file1> <file2> ...
"""
import os
import sys
import argparse
import subprocess

SVN_EXE = r"C:\Program Files\SlikSVN\bin\svn.exe"
DEFAULT_BASE_URL = "http://192.168.204.100/svn/zhihuiji/trunk/doc/05%e6%b5%8b%e8%af%95%e6%96%87%e6%a1%a3/%e6%b5%8b%e8%af%95%e7%94%a8%e4%be%8b/%e9%9b%b6%e5%94%ae%e7%89%88"


def run_svn(args, desc=""):
    """Run svn command, return (success, output)."""
    cmd = [SVN_EXE] + args + ["--non-interactive"]
    print(f"  >> {' '.join(args[:3])}... {desc}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            return True, r.stdout
        else:
            return False, r.stderr or r.stdout
    except Exception as e:
        return False, str(e)


def folder_exists(url):
    """Check if SVN folder exists."""
    ok, out = run_svn(["info", url], "检查目录")
    return ok, out


def mkdir(url, version):
    """Create SVN folder."""
    ok, out = run_svn(["mkdir", url, "-m", f"创建 v{version} 归档目录"], "创建目录")
    return ok, out


def import_file(local_path, target_url, version, filename):
    """Import a file to SVN."""
    ok, out = run_svn(["import", local_path, target_url, "-m", f"归档 v{version}: {filename}"], f"上传 {filename}")
    return ok, out


def file_exists(file_url):
    """Check if a file already exists in SVN (for dedup)."""
    ok, out = run_svn(["info", file_url], "检查文件是否存在")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Upload files to SVN (upload-only, no delete).")
    parser.add_argument("--version", required=True, help="version label, e.g. v1.6.1")
    parser.add_argument("--files", required=True, nargs="+", help="local file paths to upload")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="SVN base URL")
    args = parser.parse_args()

    version = args.version.strip()
    base_url = args.base_url.rstrip("/")
    target_url = f"{base_url}/{version}"

    print("=" * 60)
    print(f"SVN 归档上传 (版本: {version})")
    print("=" * 60)
    print(f"  目标: {target_url}")
    print(f"  文件数: {len(args.files)}")

    # verify local files
    print("\n[1] 本地文件检查")
    valid_files = []
    for f in args.files:
        if os.path.exists(f):
            size = os.path.getsize(f) / 1024
            print(f"  ✅ {os.path.basename(f)} ({size:.1f} KB) — {f}")
            valid_files.append(f)
        else:
            print(f"  ❌ 不存在: {f}")
    if not valid_files:
        print("  错误: 无有效文件可上传")
        return 1

    # check target folder
    print(f"\n[2] 检查 SVN 目标目录 {version}/")
    exists, out = folder_exists(target_url)
    if exists:
        print(f"  ✅ 目录已存在，直接上传")
    else:
        print(f"  ℹ️  目录不存在，创建中...")
        ok, out = mkdir(target_url, version)
        if ok:
            print(f"  ✅ 目录创建成功")
        else:
            # maybe already exists (race) or auth issue
            if "already exists" in out or "File exists" in out:
                print(f"  ✅ 目录已存在（创建时反馈）")
            else:
                print(f"  ❌ 目录创建失败: {out[:200]}")
                return 1

    # import files (with dedup: skip if already exists)
    print(f"\n[3] 上传文件到 {version}/（去重：已存在则跳过）")
    success = 0
    skipped = 0
    failed = 0
    for f in valid_files:
        fname = os.path.basename(f)
        file_url = f"{target_url}/{fname}"
        # 去重：上传前检查文件是否已存在于 SVN
        if file_exists(file_url):
            print(f"  ⏭️ {fname} 已存在于 SVN，跳过（去重）")
            skipped += 1
            continue
        ok, out = import_file(f, file_url, version, fname)
        if ok:
            print(f"  ✅ {fname} 上传成功")
            success += 1
        else:
            print(f"  ❌ {fname} 上传失败: {out[:200]}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"完成: 成功 {success}/{len(valid_files)}, 跳过(去重) {skipped}, 失败 {failed}")
    print(f"{'='*60}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
