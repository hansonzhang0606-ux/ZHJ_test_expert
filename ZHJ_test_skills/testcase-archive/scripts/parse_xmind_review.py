#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XMind 评审标记解析脚本
解析评审后的 XMind 文件，提取标签颜色标记（蓝色=新增、橙色=修改、灰色=删除）
支持模块级标记继承（父节点标记，子节点默认继承）

用法:
    python parse_xmind_review.py <xmind_file> [--output json]

示例:
    python parse_xmind_review.py "额度测算_测试点_v1.0-reviewed.xmind"
    python parse_xmind_review.py "额度测算_测试点_v1.0-reviewed.xmind" --output json
"""

import zipfile
import json
import sys
import argparse

def parse_marker(marker):
    """解析标记，返回状态"""
    marker_id = marker.get('markerId', '') if isinstance(marker, dict) else str(marker)
    
    # XMind 标签颜色映射
    if 'tag-blue' in marker_id:  # 蓝色 = 新增
        return 'added'
    elif 'tag-orange' in marker_id:  # 橙色 = 修改
        return 'modified'
    elif 'tag-grey' in marker_id:  # 灰色 = 删除
        return 'deleted'
    elif 'tag-green' in marker_id:  # 绿色 = 确认
        return 'confirmed'
    return None

def get_children(node):
    """获取子节点列表"""
    children_data = node.get('children', {})
    if isinstance(children_data, dict):
        return children_data.get('attached', [])
    elif isinstance(children_data, list):
        return children_data
    return []

def collect_nodes(node, parent_status='confirmed', path=[]):
    """收集所有节点及其状态
    
    Args:
        node: 当前节点
        parent_status: 父节点状态（用于继承）
        path: 节点路径（从根到当前节点的标题列表）
    
    Returns:
        list: 所有叶子节点（测试点）及其状态
    """
    title = node.get('title', '')
    markers = node.get('markers', [])
    current_path = path + [title]
    
    # 解析标记，子节点继承父节点标记
    status = parent_status
    for marker in markers:
        marker_status = parse_marker(marker)
        if marker_status:
            status = marker_status
            break
    
    children = get_children(node)
    
    if not children:  # 叶子节点 = 测试点
        return [{
            'title': title,
            'status': status,
            'path': current_path
        }]
    
    # 递归收集子节点
    result = []
    for child in children:
        result.extend(collect_nodes(child, status, current_path))
    return result

def parse_xmind(xmind_path):
    """解析 XMind 文件
    
    Args:
        xmind_path: XMind 文件路径
    
    Returns:
        dict: 包含根节点标题、统计、所有节点列表
    """
    with zipfile.ZipFile(xmind_path) as z:
        data = z.read('content.json')
        content = json.loads(data)
        
        # XMind 8 格式 - content 是列表
        sheet = content[0]
        root = sheet.get('rootTopic', {})
        root_title = root.get('title', '')
        
        # 收集所有节点
        all_nodes = collect_nodes(root)
        
        # 统计各状态数量
        stats = {'confirmed': 0, 'added': 0, 'modified': 0, 'deleted': 0}
        for node in all_nodes:
            stats[node['status']] = stats.get(node['status'], 0) + 1
        
        return {
            'root_title': root_title,
            'statistics': stats,
            'total': len(all_nodes),
            'nodes': all_nodes
        }

def print_review_result(result):
    """打印评审结果"""
    print("=" * 60)
    print("评审标记解析结果")
    print("=" * 60)
    print(f"根节点: {result['root_title']}")
    print()
    
    # 打印有标记的节点
    status_icons = {'confirmed': '✅', 'added': '➕', 'modified': '🔄', 'deleted': '❌'}
    
    for node in result['nodes']:
        status = node['status']
        if status != 'confirmed':  # 只显示非确认的节点
            icon = status_icons.get(status, '?')
            path_str = ' → '.join(node['path'][-3:])  # 显示最后3层路径
            print(f"{icon} {path_str}")
    
    print()
    print("=" * 60)
    print("统计")
    print("=" * 60)
    print(f"✅ 确认: {result['statistics']['confirmed']}")
    print(f"➕ 新增: {result['statistics']['added']}")
    print(f"🔄 修改: {result['statistics']['modified']}")
    print(f"❌ 删除: {result['statistics']['deleted']}")
    print(f"总计: {result['total']}")

def main():
    parser = argparse.ArgumentParser(description='解析 XMind 评审标记')
    parser.add_argument('xmind_file', help='XMind 文件路径')
    parser.add_argument('--output', choices=['json', 'text'], default='text', 
                        help='输出格式 (json/text)')
    parser.add_argument('--filter', choices=['confirmed', 'added', 'modified', 'deleted', 'all'],
                        default='all', help='只输出指定状态的节点')
    
    args = parser.parse_args()
    
    result = parse_xmind(args.xmind_file)
    
    if args.output == 'json':
        # 过滤节点
        if args.filter != 'all':
            result['nodes'] = [n for n in result['nodes'] if n['status'] == args.filter]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_review_result(result)

if __name__ == '__main__':
    main()