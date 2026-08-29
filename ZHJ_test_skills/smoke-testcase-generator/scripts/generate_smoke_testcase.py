#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke Test Case Generator
=========================
Extract cases of a target priority (default P0) from a reviewed test-case XMind
and generate a smoke-test Excel following the DMP import template format.

Usage:
    python generate_smoke_testcase.py \
        --xmind <reviewed.xmind> \
        --version v1.6.1 \
        --template <DMP_template.xlsx> \
        --output-base <testcases/冒烟用例 parent> \
        [--priority P0] [--manager 詹惠英] \
        [--stories '{"关键词":"PRJ-xxx:故事名称",...}']

Requirements:
    - Python 3.8+ with openpyxl
    - Valid reviewed XMind (content.json with 前置条件/优先级 child nodes)
    - DMP Excel template (24-column format)
"""
import os
import re
import json
import zipfile
import shutil
import argparse
import openpyxl
from openpyxl.styles import Alignment, Border, Side


def get_children(node):
    cd = node.get("children", {})
    if isinstance(cd, dict):
        return cd.get("attached", [])
    if isinstance(cd, list):
        return cd
    return []


def extract_cases(xmind_path):
    """Extract all cases from a reviewed XMind file."""
    with zipfile.ZipFile(xmind_path, "r") as zf:
        content = json.loads(zf.read("content.json"))
    root = content[0]["rootTopic"]
    cases = []

    def walk(node, path):
        title = node.get("title", "")
        children = get_children(node)
        child_titles = [c.get("title", "") for c in children]
        is_case = any("前置条件" in t or "优先级" in t for t in child_titles)
        if is_case:
            case = {"name": title, "path": " > ".join(path[1:]) if len(path) > 1 else ""}
            for c in children:
                t = c.get("title", "")
                sub = [gc.get("title", "") for gc in get_children(c)]
                if "前置条件" in t:
                    case["precondition"] = "\n".join(sub)
                elif "测试步骤" in t:
                    case["steps"] = sub
                elif "预期结果" in t:
                    case["expected"] = sub
                elif "优先级" in t:
                    case["priority"] = t.replace("⚡ 优先级:", "").strip()
            cases.append(case)
        else:
            for c in children:
                walk(c, path + [title])

    walk(root, [root.get("title", "")])
    return cases


def clean_paren(text):
    """Remove example parentheses containing only numbers/arithmetic (e.g. （8）, （10-2=8）).
    Keep descriptive parentheses like （前置条件）."""
    if not text:
        return text
    return re.sub(r"[（(][\d\s\+\-\*/=]+[）)]", "", text)


def match_story(case, stories):
    """Match a case to a user-story group by keyword.
    stories: dict {keyword: "code:storyname"}.
    Returns (caseGroup_suffix, code, storyname) or (None, None, None).
    """
    text = case["path"] + " " + case["name"]
    for keyword, val in stories.items():
        if keyword in text:
            code, _, story = val.partition(":")
            return keyword, code.strip(), story.strip()
    return None, None, None


def generate(xmind_path, version, template_path, output_base, priority, manager, stories):
    # Step 1: extract + filter
    all_cases = extract_cases(xmind_path)
    target_cases = [c for c in all_cases if c.get("priority") == priority]
    print(f"总用例: {len(all_cases)} | {priority}用例: {len(target_cases)}")
    if not target_cases:
        print(f"WARNING: 未找到 {priority} 用例，检查 XMind 优先级标记")
        return None

    # Step 2: prepare output dir (零售版{version without leading v})
    ver_folder = version if not version.lower().startswith("v") else version
    out_dir = os.path.join(output_base, f"零售版{ver_folder}")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"零售版{ver_folder}冒烟用例.xlsx")

    # Step 3: copy template + fill
    shutil.copy2(template_path, out_file)
    wb = openpyxl.load_workbook(out_file)
    ws = wb["sheet1"]

    # delete template sample rows (row 5+)
    if ws.max_row >= 5:
        ws.delete_rows(5, ws.max_row - 4)

    thin = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")

    for i, c in enumerate(target_cases, start=5):
        row_num = i - 4
        # group + story
        kw, code, story = match_story(c, stories) if stories else (None, None, None)
        group = f"2026-零售版{ver_folder}-{kw}" if kw else f"2026-零售版{ver_folder}-其他"

        # clean example parentheses
        pre_text = clean_paren(c.get("precondition", ""))
        steps_text = "\n".join(f"{j+1}.{s}" for j, s in enumerate(c.get("steps", [])))
        steps_text = clean_paren(steps_text)
        expected_text = "\n".join(f"{j+1}.{e}" for j, e in enumerate(c.get("expected", [])))
        expected_text = clean_paren(expected_text)

        row_data = [
            "智慧记AI零售",                 # A team
            group,                          # B caseGroup
            row_num,                        # C number
            c["name"],                      # D name
            "",                             # E caseLabels
            pre_text,                       # F preCondition
            steps_text,                     # G input
            expected_text,                  # H output
            "零售",                         # I product
            "智慧记AI零售-AI零售",          # J modulePath
            version,                        # K version
            "功能测试",                     # L caseType
            "需求文档",                     # M source
            priority,                       # N caseLevel
            manager or "",                  # O manager
            "否",                           # P autoState
            code or "",                     # Q relateReqCode
            "",                             # R workload
            story or "",                    # S remarks
            "", "", "", "", "",             # T-X
        ]
        for col, val in enumerate(row_data, start=1):
            cell = ws.cell(i, col, val)
            cell.alignment = wrap
            cell.border = border

    # row heights + column widths
    for i in range(5, 5 + len(target_cases)):
        ws.row_dimensions[i].height = 80
    col_widths = {"A":14,"B":30,"C":6,"D":30,"E":12,"F":30,"G":40,"H":40,"I":8,"J":18,"K":10,"L":10,"M":10,"N":8,"O":10,"P":10,"Q":16,"S":30}
    for col, w in col_widths.items():
        ws.column_dimensions[col].width = w

    wb.save(out_file)
    print(f"\n生成冒烟用例excel: {out_file}")
    print(f"{priority}用例数: {len(target_cases)}")
    # report per-case
    for c in target_cases:
        kw, code, story = match_story(c, stories) if stories else (None, None, None)
        print(f"  - {c['name']} | 分组={kw or '其他'} | 编码={code or ''} | 故事={story or ''}")
    return out_file


def main():
    parser = argparse.ArgumentParser(description="Generate smoke-test Excel from reviewed XMind.")
    parser.add_argument("--xmind", required=True, help="path to reviewed XMind")
    parser.add_argument("--version", required=True, help="version label, e.g. v1.6.1")
    parser.add_argument("--template", required=True, help="path to DMP Excel template")
    parser.add_argument("--output-base", required=True, help="parent dir of 冒烟用例/")
    parser.add_argument("--priority", default="P0", help="priority to extract (default P0)")
    parser.add_argument("--manager", default="", help="responsible person (column O)")
    parser.add_argument("--stories", default="", help='JSON mapping {keyword:"code:storyname"}')
    args = parser.parse_args()

    stories = {}
    if args.stories:
        try:
            stories = json.loads(args.stories)
        except json.JSONDecodeError as e:
            print(f"ERROR: --stories JSON 解析失败: {e}")
            return 1

    out = generate(args.xmind, args.version, args.template, args.output_base,
                   args.priority, args.manager, stories)
    return 0 if out else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
