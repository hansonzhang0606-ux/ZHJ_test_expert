#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""时间追踪步骤名称与编码的统一映射。"""


STEP_MAP = {
    "00": "导出需求",
    "01": "文档整理",
    "02": "需求评审",
    "04": "生成测试点",
    "05": "AI 对比入库",
    "06": "生成用例",
    "07": "入库知识库",
    "08": "SVN 归档上传",
}

STEP_NAME_ALIASES = {
    "用例细化": "生成用例",
    "知识入库": "入库知识库",
}

STEP_COLUMN_COMMENT = "步骤名称(" + "、".join(
    f"{name}（{code}）" for code, name in STEP_MAP.items()
) + ")"


def normalize_step(step: str, step_code: str) -> tuple[str, str]:
    """以已知 step_code 为准，返回规范的 (step, step_code)。"""
    code = str(step_code or "").strip()
    name = STEP_NAME_ALIASES.get(str(step or "").strip(), str(step or "").strip())
    if code in STEP_MAP:
        return STEP_MAP[code], code
    if not code:
        for known_code, known_name in STEP_MAP.items():
            if name == known_name:
                return known_name, known_code
    return name or code, code
