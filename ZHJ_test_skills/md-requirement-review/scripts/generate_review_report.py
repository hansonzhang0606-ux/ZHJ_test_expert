#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
需求评审报告生成脚本
将 AI 评审生成的 JSON 数据转换为结构化的 Markdown 评审报告
"""

import json
import argparse
import os
from datetime import datetime


def generate_review_report(json_data, output_path):
    """
    将评审 JSON 数据转换为 Markdown 格式报告
    
    Args:
        json_data: 评审数据字典
        output_path: 输出文件路径
    """
    lines = []
    
    # 文档头部
    lines.append("# 📋 需求评审报告\n")
    lines.append(f"> 文档名称：{json_data.get('doc_title', '未知')}")
    lines.append(f"> 评审日期：{json_data.get('review_date', datetime.now().strftime('%Y-%m-%d'))}")
    lines.append(f"> 评审人：{json_data.get('reviewer', 'AI 评审助手')}\n")
    lines.append("---\n")
    
    # 评审概览
    summary = json_data.get('summary', {})
    lines.append("## 📊 评审概览\n")
    lines.append("| 指标 | 数量 |")
    lines.append("|------|------|")
    lines.append(f"| 问题总数 | {summary.get('total_issues', 0)} |")
    lines.append(f"| 🔴 严重 | {summary.get('critical', 0)} |")
    lines.append(f"| 🟡 重要 | {summary.get('major', 0)} |")
    lines.append(f"| 🟢 一般 | {summary.get('minor', 0)} |\n")
    lines.append("---\n")
    
    # 按严重程度分组输出问题
    severity_order = ['critical', 'major', 'minor']
    severity_titles = {
        'critical': '🔴 严重问题',
        'major': '🟡 重要问题',
        'minor': '🟢 一般问题'
    }
    
    for severity in severity_order:
        # 收集该严重程度的所有问题
        items_by_category = []
        for category in json_data.get('categories', []):
            cat_items = [item for item in category.get('items', []) 
                        if item.get('severity') == severity or 
                        (severity == 'critical' and not item.get('severity'))]
            if cat_items:
                items_by_category.append({
                    'category': category.get('name'),
                    'items': cat_items
                })
        
        if items_by_category:
            lines.append(f"## {severity_titles.get(severity, '问题')}\n")
            item_index = 1
            for cat_data in items_by_category:
                for item in cat_data['items']:
                    lines.append(f"### {item_index}. {cat_data['category']} - {get_item_title(item)}\n")
                    lines.append(f"- **位置**：{item.get('location', '未知')}")
                    lines.append(f"- **描述**：{item.get('description', '')}")
                    if item.get('suggestion'):
                        lines.append(f"- **建议**：{item['suggestion']}")
                    lines.append("")
                    item_index += 1
            lines.append("---\n")
    
    # 完整性检查结果
    completeness_items = get_completeness_items(json_data)
    if completeness_items:
        lines.append("## ✅ 完整性检查结果\n")
        lines.append("| 检查项 | 状态 | 说明 |")
        lines.append("|--------|------|------|")
        for item in completeness_items:
            status_icon = get_status_icon(item.get('status'))
            lines.append(f"| {item.get('name')} | {status_icon} {item.get('status', '未知')} | {item.get('description', '')} |")
        lines.append("")
        lines.append("---\n")
    
    # 总结建议
    lines.append("## 💡 总结建议\n")
    lines.append(generate_summary_suggestions(json_data))
    lines.append("")
    lines.append("---\n")
    lines.append("*本报告由 AI 评审助手自动生成，需人工审核确认*\n")
    
    # 写入文件
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ 评审报告已生成: {output_path}")
    print(f"   问题总数: {summary.get('total_issues', 0)}")
    print(f"   严重: {summary.get('critical', 0)}, 重要: {summary.get('major', 0)}, 一般: {summary.get('minor', 0)}")


def get_item_title(item):
    """从 item 中提取简短标题"""
    desc = item.get('description', '')
    # 取前30个字符作为标题
    if len(desc) > 30:
        return desc[:30] + "..."
    return desc


def get_completeness_items(json_data):
    """获取完整性检查项"""
    for category in json_data.get('categories', []):
        if category.get('name') == '完整性检查':
            return category.get('items', [])
    return []


def get_status_icon(status):
    """根据状态返回对应图标"""
    if status in ['有', '完整']:
        return '✅'
    elif status in ['缺失', '无']:
        return '❌'
    else:
        return '⚠️'


def generate_summary_suggestions(json_data):
    """生成总结建议"""
    suggestions = []
    
    # 按严重程度提取建议
    critical_items = []
    major_items = []
    minor_items = []
    
    for category in json_data.get('categories', []):
        for item in category.get('items', []):
            if item.get('severity') == 'critical':
                critical_items.append(item.get('suggestion', item.get('description', '')))
            elif item.get('severity') == 'major':
                major_items.append(item.get('suggestion', item.get('description', '')))
            else:
                minor_items.append(item.get('suggestion', item.get('description', '')))
    
    if critical_items:
        suggestions.append("1. **高优先级**：" + "、".join(critical_items[:3]))
    if major_items:
        suggestions.append("2. **中优先级**：" + "、".join(major_items[:3]))
    if minor_items:
        suggestions.append("3. **低优先级**：" + "、".join(minor_items[:3]))
    
    if not suggestions:
        suggestions.append("无特别建议，需求文档质量较好")
    
    return "\n".join(suggestions)


def main():
    parser = argparse.ArgumentParser(description='生成需求评审报告')
    parser.add_argument('--input', '-i', required=True, help='评审 JSON 文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出报告文件路径')
    
    args = parser.parse_args()
    
    # 读取 JSON 文件
    with open(args.input, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # 生成报告
    generate_review_report(json_data, args.output)


if __name__ == '__main__':
    main()
