#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MarkItDown 多格式文件转 Markdown 工具
支持 Word (.doc, .docx)、PDF、PPT、Excel、HTML 等多种格式
支持单文件转换和批量目录转换
"""

import os
import sys
import re
import shutil
import zipfile
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

# 检查依赖
try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False

try:
    from markitdown import MarkItDown
    HAS_MARKITDOWN = True
except ImportError:
    HAS_MARKITDOWN = False

# 支持的文件扩展名（排除 .md，因为不需要转换 md 文件）
SUPPORTED_EXTENSIONS = [
    '.doc', '.docx',      # Word
    '.pdf',               # PDF
    '.ppt', '.pptx',      # PowerPoint
    '.xls', '.xlsx',      # Excel
    '.html', '.htm',      # HTML
    '.csv', '.json', '.xml', '.txt'  # 其他
]


# ==================== 格式转换 ====================

def kill_office_processes():
    """强制清理残留的 Office 进程"""
    import subprocess
    try:
        subprocess.run('taskkill /f /im WINWORD.EXE 2>nul', shell=True, capture_output=True)
        subprocess.run('taskkill /f /im POWERPNT.EXE 2>nul', shell=True, capture_output=True)
        subprocess.run('taskkill /f /im EXCEL.EXE 2>nul', shell=True, capture_output=True)
    except: pass


def doc_to_docx(doc_path, docx_path):
    """使用 Word 将 .doc 转为 .docx"""
    word = None
    doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")  # 使用 DispatchEx 创建独立进程
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(str(Path(doc_path).resolve()))
        doc.SaveAs(str(Path(docx_path).resolve()), FileFormat=16)
        doc.Close(SaveChanges=False)
        print(f"✅ Word 转换: {Path(doc_path).name}")
        return True
    except Exception as e:
        print(f"❌ Word 转换失败: {e}")
        return False
    finally:
        if doc:
            try: doc.Close(SaveChanges=False)
            except: pass
        if word:
            try: word.Quit()
            except: pass
        # 强制清理并等待
        time.sleep(1)
        kill_office_processes()


def ppt_to_pptx(ppt_path, pptx_path):
    """使用 PowerPoint 将 .ppt 转为 .pptx"""
    ppt = None
    pres = None
    try:
        ppt = win32com.client.DispatchEx("PowerPoint.Application")
        ppt.Visible = False
        pres = ppt.Presentations.Open(str(Path(ppt_path).resolve()))
        pres.SaveAs(str(Path(pptx_path).resolve()), FileFormat=24)
        pres.Close()
        print(f"✅ PPT 转换: {Path(ppt_path).name}")
        return True
    except Exception as e:
        print(f"❌ PPT 转换失败: {e}")
        return False
    finally:
        if pres:
            try: pres.Close()
            except: pass
        if ppt:
            try: ppt.Quit()
            except: pass
        time.sleep(1)
        kill_office_processes()


def xls_to_xlsx(xls_path, xlsx_path):
    """使用 Excel 将 .xls 转为 .xlsx"""
    excel = None
    wb = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(str(Path(xls_path).resolve()))
        wb.SaveAs(str(Path(xlsx_path).resolve()), FileFormat=51)
        wb.Close(SaveChanges=False)
        print(f"✅ Excel 转换: {Path(xls_path).name}")
        return True
    except Exception as e:
        print(f"❌ Excel 转换失败: {e}")
        return False
    finally:
        if wb:
            try: wb.Close(SaveChanges=False)
            except: pass
        if excel:
            try: excel.Quit()
            except: pass
        time.sleep(1)
        kill_office_processes()


# ==================== 图片提取 ====================

def extract_images_from_docx(docx_path, images_dir, doc_prefix):
    images_dir = Path(images_dir)
    images_dir.mkdir(exist_ok=True)
    image_names = []

    with zipfile.ZipFile(docx_path, 'r') as zf:
        if 'word/_rels/document.xml.rels' not in zf.namelist():
            return images_dir, 0, []
        media_files = sorted([f for f in zf.namelist() if f.startswith('word/media/')])
        for i, media_file in enumerate(media_files, 1):
            with zf.open(media_file) as src:
                content = src.read()
            ext = Path(media_file).suffix.lower()
            actual_ext = ext
            if ext in ['.tmp', '.bin', ''] or ext not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                if content[:8] == b'\x89PNG\r\n\x1a\n': actual_ext = '.png'
                elif content[:2] == b'\xff\xd8': actual_ext = '.jpg'
                elif content[:6] in [b'GIF87a', b'GIF89a']: actual_ext = '.gif'
                elif content[:2] == b'BM': actual_ext = '.bmp'
                else: actual_ext = '.png'
            image_name = f"{doc_prefix}_{i:03d}{actual_ext}"
            with open(images_dir / image_name, 'wb') as dst:
                dst.write(content)
            image_names.append(image_name)

    if image_names:
        print(f"✅ 提取图片: {len(image_names)} 张")
    return images_dir, len(image_names), image_names


def extract_images_from_pptx(pptx_path, images_dir, doc_prefix):
    images_dir = Path(images_dir)
    images_dir.mkdir(exist_ok=True)
    image_names = []

    with zipfile.ZipFile(pptx_path, 'r') as zf:
        media_files = sorted([f for f in zf.namelist() if 'media/' in f])
        for i, media_file in enumerate(media_files, 1):
            ext = Path(media_file).suffix.lower()
            if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                continue
            with zf.open(media_file) as src:
                content = src.read()
            image_name = f"{doc_prefix}_{i:03d}{ext}"
            with open(images_dir / image_name, 'wb') as dst:
                dst.write(content)
            image_names.append(image_name)

    if image_names:
        print(f"✅ 提取图片: {len(image_names)} 张")
    return images_dir, len(image_names), image_names


# ==================== 附件提取 ====================

def extract_attachments_from_docx(docx_path, attachments_dir):
    attachments_dir = Path(attachments_dir)
    attachments_dir.mkdir(exist_ok=True)
    attach_names = []

    with zipfile.ZipFile(docx_path, 'r') as zf:
        ole_files = [f for f in zf.namelist() if f.startswith('word/embeddings/')]
        for ole_file in ole_files:
            rels_file = ole_file.replace('.bin', '.xml.rels').replace('embeddings/', '_rels/embeddings/')
            orig_name = Path(ole_file).stem
            if rels_file in zf.namelist():
                try:
                    rels_xml = zf.read(rels_file).decode('utf-8')
                    rels_root = ET.fromstring(rels_xml)
                    ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
                    for rel in rels_root.findall('r:Relationship', ns):
                        target = rel.get('Target')
                        if target:
                            orig_name = Path(target).name
                            break
                except: pass
            with zf.open(ole_file) as src:
                with open(attachments_dir / orig_name, 'wb') as dst:
                    dst.write(src.read())
            attach_names.append(orig_name)

    if attach_names:
        print(f"✅ 提取附件: {len(attach_names)} 个")
    return attachments_dir, len(attach_names), attach_names


# ==================== 后处理 ====================

def post_process_markdown(md_content, doc_name, images_dir, image_names, attachments_dir, attach_names, file_type):
    lines = md_content.split('\n')
    processed_lines = []

    header_lines = [f"# {doc_name}", "", f"> 本文档由 {file_type} 自动转换生成", ""]
    img_counter = 0
    images_rel_dir = Path(images_dir).name if images_dir else 'images'
    prev_level = 1
    first_header_skipped = False

    for line in lines:
        if re.match(r'!\[\]\(data:image/[^;]+;base64[^)]*\)', line):
            img_counter += 1
            if img_counter <= len(image_names):
                img_name = image_names[img_counter - 1]
                processed_lines.append(f"\n![图片{img_counter}]({images_rel_dir}/{img_name})\n")
            else:
                processed_lines.append(f"\n![图片{img_counter}]\n")
            continue

        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if header_match:
            original_level = len(header_match.group(1))
            title_text = header_match.group(2)
            if not first_header_skipped:
                first_header_skipped = True
                continue
            level = original_level + 1
            if level > prev_level + 1:
                level = prev_level + 1
            level = min(level, 5)
            prev_level = level
            processed_lines.append(f"{'#' * level} {title_text}")
            processed_lines.append("")
            continue

        if re.match(r'^\*+\s', line):
            line = re.sub(r'^\*+\s', '- ', line)

        if '---' in line and len(line.strip()) <= 10:
            processed_lines.append("\n---\n\n<!-- 分页 -->\n")
            continue

        processed_lines.append(line)

    md_content = '\n'.join(header_lines + processed_lines)
    md_content = re.sub(r'\n{4,}', '\n\n\n', md_content)

    if attach_names:
        attachments_rel_dir = Path(attachments_dir).name
        md_content += "\n\n---\n\n## 📎 附件\n\n"
        for i, name in enumerate(attach_names, 1):
            md_content += f"> 📎 附件{i}: [{name}]({attachments_rel_dir}/{name})\n"

    return md_content


# ==================== 辅助函数 ====================

def get_file_type(file_path):
    ext = Path(file_path).suffix.lower()
    type_map = {
        '.doc': 'Word 文档（旧格式）', '.docx': 'Word 文档',
        '.pdf': 'PDF 文档', '.ppt': 'PPT（旧格式）', '.pptx': 'PPT',
        '.xls': 'Excel（旧格式）', '.xlsx': 'Excel',
        '.html': 'HTML', '.htm': 'HTML', '.csv': 'CSV',
        '.json': 'JSON', '.xml': 'XML', '.txt': '文本',
    }
    return type_map.get(ext, f'{ext} 文件')


def needs_office_conversion(file_path):
    return Path(file_path).suffix.lower() in ['.doc', '.ppt', '.xls']


# ==================== 单文件转换 ====================

def convert_file_to_md(file_path):
    file_path = Path(file_path).resolve()
    output_dir = file_path.parent
    temp_dir = tempfile.mkdtemp(prefix="markitdown_")

    file_type = get_file_type(file_path)
    doc_name = file_path.stem
    doc_prefix = re.sub(r'[^\w\u4e00-\u9fff]', '_', doc_name)[:20]

    print(f"\n{'='*50}")
    print(f"输入: {file_path.name} ({file_type})")

    if not HAS_MARKITDOWN:
        print("❌ 需安装: pip install markitdown[all]")
        return None

    try:
        working_file = file_path
        if needs_office_conversion(file_path):
            ext = file_path.suffix.lower()
            new_ext = ext + 'x'
            converted_path = Path(temp_dir) / f"{doc_name}_temp{new_ext}"
            print(f"转换格式: {ext} -> {new_ext}")
            if not HAS_WIN32COM:
                print("❌ 需安装: pip install pywin32")
                return None
            if ext == '.doc' and not doc_to_docx(file_path, converted_path): return None
            elif ext == '.ppt' and not ppt_to_pptx(file_path, converted_path): return None
            elif ext == '.xls' and not xls_to_xlsx(file_path, converted_path): return None
            working_file = converted_path

        images_dir = output_dir / 'images'
        attachments_dir = output_dir / 'attachments'
        image_names, attach_names = [], []

        ext = working_file.suffix.lower()
        if ext == '.docx':
            _, _, image_names = extract_images_from_docx(working_file, images_dir, doc_prefix)
            _, _, attach_names = extract_attachments_from_docx(working_file, attachments_dir)
        elif ext == '.pptx':
            _, _, image_names = extract_images_from_pptx(working_file, images_dir, doc_prefix)

        md = MarkItDown()
        result = md.convert(str(working_file))
        md_content = result.text_content

        md_content = post_process_markdown(md_content, doc_name, images_dir, image_names, attachments_dir, attach_names, file_type)

        md_path = output_dir / f"{doc_name}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"✅ 输出: {md_path.name}")
        if image_names: print(f"   图片: {len(image_names)} 张")
        if attach_names: print(f"   附件: {len(attach_names)} 个")
        # 清理空的 attachments 目录（无附件时自动删除，避免遗留空目录）
        if attachments_dir.exists() and not any(attachments_dir.iterdir()):
            shutil.rmtree(attachments_dir, ignore_errors=True)
        return md_path

    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ==================== 批量转换 ====================

def convert_batch(input_path, recursive=False):
    input_path = Path(input_path)
    files_to_convert = []

    if input_path.is_dir():
        print(f"\n扫描目录: {input_path}")
        if recursive:
            for ext in SUPPORTED_EXTENSIONS:
                files_to_convert.extend(input_path.rglob(f'*{ext}'))
        else:
            for ext in SUPPORTED_EXTENSIONS:
                files_to_convert.extend(input_path.glob(f'*{ext}'))

        # 排除已存在 .md 的文件（避免重复转换）
        files_to_convert = [f for f in files_to_convert if not (f.parent / f.stem).with_suffix('.md').exists()]
        files_to_convert = sorted(files_to_convert, key=lambda x: x.name)
        print(f"找到 {len(files_to_convert)} 个待转换文件")

    elif input_path.is_file():
        files_to_convert = [input_path]
    else:
        print(f"❌ 路径不存在: {input_path}")
        return []

    if not files_to_convert:
        return []

    print("\n待转换文件:")
    for i, f in enumerate(files_to_convert, 1):
        print(f"  {i}. {f.name}")

    results, success, fail = [], 0, 0
    for i, f in enumerate(files_to_convert, 1):
        print(f"\n[{i}/{len(files_to_convert)}]")
        result = convert_file_to_md(f)
        if result:
            results.append(result)
            success += 1
        else:
            fail += 1

    print(f"\n{'='*50}")
    print(f"批量转换完成: 成功 {success}, 失败 {fail}")
    return results


# ==================== 主函数 ====================

def main():
    if len(sys.argv) < 2:
        print("="*50)
        print("MarkItDown 多格式文件转 Markdown")
        print("="*50)
        print("\n支持: .doc/.docx, .pdf, .ppt/.pptx, .xls/.xlsx, .html, .csv/.json/.xml/.txt")
        print("\n用法:")
        print("  单文件: python convert_to_md.py <文件>")
        print("  批量:   python convert_to_md.py <目录>")
        print("  递归:   python convert_to_md.py <目录> -r")
        print("\n依赖: Python>=3.10, markitdown[all], pywin32(.doc/.ppt/.xls)")
        sys.exit(1)

    input_path = sys.argv[1]
    recursive = '-r' in sys.argv or '--recursive' in sys.argv

    path = Path(input_path)
    if path.is_dir():
        convert_batch(input_path, recursive=recursive)
    else:
        convert_file_to_md(input_path)


if __name__ == '__main__':
    main()