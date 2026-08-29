#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XMind 测试点生成器
接收AI分析生成的测试点JSON数据，转换为XMind文件

使用方式：
1. AI分析需求文档，生成测试点JSON
2. 调用此脚本将JSON转换为XMind文件

python generate_xmind.py --input <测试点JSON文件> --output <XMind文件路径>
或
python generate_xmind.py --data '{"title":"xxx","modules":[]}'
"""

import os
import sys
import json
import zipfile
import uuid
import argparse
from pathlib import Path


def gen_id():
    """生成唯一ID"""
    return uuid.uuid4().hex


def build_topic(title, children=None):
    """构建XMind topic节点"""
    topic = {
        "id": gen_id(),
        "title": title,
        "structureClass": "org.xmind.ui.map.unbalanced"
    }
    if children:
        topic["children"] = {
            "attached": children
        }
    return topic


def build_sub_modules(sub_modules):
    """递归构建子模块"""
    children = []
    for sub in sub_modules:
        name = sub["name"]
        child_topics = []
        
        # 如果有更深层的 sub_modules，递归
        if "sub_modules" in sub:
            child_topics = build_sub_modules(sub["sub_modules"])
        # 如果有 testpoints，构建叶子节点
        elif "testpoints" in sub:
            child_topics = [build_topic(tp) for tp in sub["testpoints"]]
        
        children.append(build_topic(name, child_topics))
    return children


def generate_xmind(testpoint_data, output_path):
    """
    将测试点数据生成XMind文件
    
    testpoint_data格式（支持嵌套sub_modules）:
    {
        "title": "额度测算测试点",
        "modules": [
            {
                "name": "2.3 额度测算结果展示",
                "sub_modules": [
                    {
                        "name": "状态展示-正常流转",
                        "sub_modules": [
                            {
                                "name": "状态",
                                "testpoints": ["0-初始...", "10-待签署..."]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """
    
    # 构建根节点
    root_title = testpoint_data.get("title", "测试点")
    root_children = []
    
    for module in testpoint_data.get("modules", []):
        module_children = []
        
        # 子模块（递归处理）
        if "sub_modules" in module:
            module_children = build_sub_modules(module["sub_modules"])
        
        # 直接测试点
        for tp in module.get("testpoints", []):
            module_children.append(build_topic(tp))
        
        root_children.append(build_topic(module["name"], module_children))
    
    root_topic = build_topic(root_title, root_children)
    
    # content.json
    content_json = [{
        "id": gen_id(),
        "title": root_title,
        "rootTopic": root_topic
    }]
    
    # manifest.json
    manifest_json = {
        "file-entries": {
            "content.json": {},
            "metadata.json": {},
            "Revisions/": {}
        }
    }
    
    # metadata.json
    metadata_json = {
        "creator": {
            "name": "XMind",
            "version": "3.7.0"
        },
        "createdDate": "2026-04-16"
    }
    
    # 打包成xmind
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr('content.json', json.dumps(content_json, ensure_ascii=False, indent=2))
        zf.writestr('manifest.json', json.dumps(manifest_json, ensure_ascii=False))
        zf.writestr('metadata.json', json.dumps(metadata_json, ensure_ascii=False))
        zf.writestr('Revisions/', '')
    
    print(f"生成XMind: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='将测试点JSON数据转换为XMind文件')
    parser.add_argument('--input', '-i', help='测试点JSON文件路径')
    parser.add_argument('--data', '-d', help='直接传入JSON数据字符串')
    parser.add_argument('--output', '-o', help='XMind输出路径（可选，默认与输入同目录）')
    
    args = parser.parse_args()
    
    if args.input:
        # 从文件读取
        input_path = Path(args.input).resolve()
        with open(input_path, 'r', encoding='utf-8') as f:
            testpoint_data = json.load(f)
        
        # 输出路径
        if args.output:
            output_path = args.output
        else:
            output_path = str(input_path.parent / (input_path.stem + '.xmind'))
    
    elif args.data:
        # 直接解析JSON字符串
        testpoint_data = json.loads(args.data)
        
        if args.output:
            output_path = args.output
        else:
            # 默认输出到当前目录
            title = testpoint_data.get("title", "测试点")
            output_path = f"{title}.xmind"
    
    else:
        print("用法:")
        print("  python generate_xmind.py --input 测试点.json --output 输出.xmind")
        print("  python generate_xmind.py --data '{\"title\":\"xxx\",\"modules\":[]}'")
        sys.exit(1)
    
    print(f"输入数据: {testpoint_data.get('title', '未知')}")
    print(f"功能模块: {len(testpoint_data.get('modules', []))} 个")
    print("-" * 50)
    
    generate_xmind(testpoint_data, output_path)
    
    print("-" * 50)
    print("生成完成!")


if __name__ == '__main__':
    main()