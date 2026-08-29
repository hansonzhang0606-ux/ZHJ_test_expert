# markitdown-converter

多格式文档转 Markdown 工具，基于 [markitdown](https://github.com/microsoft/markitdown) 库实现。支持 Word、PDF、PPT、Excel、HTML 等多种格式，自动提取文档中的图片和附件，并生成结构化的 Markdown 文件。

## 功能概述

### 核心能力

- **多格式支持**: 转换 Word (.doc/.docx)、PDF、PowerPoint (.ppt/.pptx)、Excel (.xls/.xlsx)、HTML、CSV、JSON、XML、TXT 等格式
- **旧版格式兼容**: 自动将旧版 Office 格式（.doc、.ppt、.xls）转换为新格式后再处理
- **图片提取**: 从 Word 和 PowerPoint 文档中提取嵌入的图片资源
- **附件提取**: 从 Word 文档中提取嵌入的 OLE 附件（如 Excel 表格、其他文档等）
- **批量处理**: 支持单文件转换和目录批量转换，可选递归子目录
- **智能后处理**: 对生成的 Markdown 进行优化，包括标题层级调整、图片引用替换等

### Markdown 后处理规则

1. **文档头部**: 自动添加文档标题和转换来源说明
2. **标题层级**: 
   - 跳过原文档的第一个标题（避免与自动添加的文档标题重复）
   - 所有标题层级下调一级（`#` → `##`，`##` → `###`，以此类推）
   - 防止标题层级跳跃过大（最多跳一级）
   - 最高限制到 5 级标题
3. **图片处理**: 将 base64 内嵌图片替换为本地图片引用
4. **列表格式**: 规范化列表符号（将 `*` 开头统一为 `-`）
5. **分页标记**: 将分页符转换为 Markdown 注释标记 `<!-- 分页 -->`
6. **附件链接**: 在文档末尾添加附件列表（如有附件）

## 使用方法

### 基本语法

```bash
python scripts/convert_to_md.py <文件或目录> [-r|--recursive]
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `<文件或目录>` | 要转换的文件路径或目录路径 |
| `-r`, `--recursive` | 递归处理子目录（仅目录模式有效） |

### 使用示例

```bash
# 转换单个 Word 文档
python scripts/convert_to_md.py report.docx

# 转换单个 PDF 文件
python scripts/convert_to_md.py presentation.pdf

# 转换目录下所有支持的文件
python scripts/convert_to_md.py ./documents/

# 递归转换目录及子目录中的所有文件
python scripts/convert_to_md.py ./documents/ -r
```

### 批量转换行为

- 扫描目录下所有支持格式的文件
- **自动跳过**: 已存在对应 `.md` 文件的文档（避免重复转换）
- 按文件名排序依次处理
- 显示处理进度和统计结果

## 输出结构

转换完成后，在源文件所在目录生成以下内容：

```
<源文件目录>/
├── <文件名>.md          # 转换后的 Markdown 文件
├── images/              # 提取的图片目录（如有）
│   ├── <文件名>_001.png
│   ├── <文件名>_002.jpg
│   └── ...
└── attachments/         # 提取的附件目录（如有）
    ├── 附件1.xlsx
    └── ...
```

### 生成的 Markdown 文件格式

```markdown
# 文档标题

> 本文档由 Word 文档自动转换生成

## 一级标题

正文内容...

## 二级标题

### 三级标题

内容...

![图片1](images/文档名_001.png)

---

<!-- 分页 -->

## 📎 附件

> 📎 附件1: [数据表.xlsx](attachments/数据表.xlsx)
```

## 系统要求

### Python 版本

- Python >= 3.10

### 依赖安装

```bash
# 核心依赖（必需）
pip install markitdown[all]

# Office 旧格式支持（转换 .doc/.ppt/.xls 需要）
pip install pywin32

# 完整安装
pip install markitdown[all] pywin32
```

### 依赖说明

| 依赖 | 用途 | 必要性 |
|------|------|--------|
| `markitdown[all]` | 核心转换引擎 | 必需 |
| `pywin32` | 调用 Office COM 接口转换旧格式 | 仅处理 .doc/.ppt/.xls 时需要 |

### 平台限制

- **Windows**: 完整支持所有格式，包括旧版 Office 格式转换
- **Linux/macOS**: 支持除 .doc/.ppt/.xls 之外的所有格式

## 注意事项

### Office 格式转换

- 转换旧版 Office 格式（.doc、.ppt、.xls）需要安装 Microsoft Office
- 转换过程会启动 Office 应用程序后台进程
- 脚本会自动清理残留的 Office 进程（WINWORD.EXE、POWERPNT.EXE、EXCEL.EXE）
- 建议在转换大批量文件时关闭其他 Office 应用

### 图片提取

- 从 .docx 文件提取图片时，会自动识别图片格式（PNG、JPEG、GIF、BMP）
- 无法识别格式的图片默认保存为 PNG
- 图片按文档内出现顺序命名（`<文档名>_001.png`、`<文档名>_002.jpg` 等）

### 附件提取

- 仅支持 Word 文档（.docx）中的 OLE 嵌入对象
- 支持提取的附件类型包括：Excel 表格、Word 文档、PDF 等嵌入对象
- 附件会保留原始文件名

### 批量转换

- 批量转换时会自动跳过已存在 `.md` 文件的文档
- 如需重新转换，请先删除对应的 `.md` 文件
- 单个文件转换失败不会影响其他文件的处理

## 故障排除

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `需要安装: pip install markitdown[all]` | 未安装核心依赖 | 执行 `pip install markitdown[all]` |
| `需要安装: pip install pywin32` | 转换旧格式但缺少 pywin32 | 执行 `pip install pywin32` 或使用新格式文件 |
| `Word 转换失败` | Office 未安装或文件损坏 | 确认已安装 Microsoft Word，检查文件是否正常 |
| `转换失败` | 文件格式不支持或文件损坏 | 确认文件格式在支持列表中，尝试用对应软件打开验证 |

### 调试建议

1. 确认文件能在对应 Office 软件中正常打开
2. 尝试用对应软件另存为新文件后重新转换
3. 检查文件路径是否包含特殊字符
4. 确保有足够的磁盘空间存放提取的图片和附件

## 技术实现

### 转换流程

```
输入文件
    ↓
格式判断 ─→ 旧格式? ─→ Office COM 转换 ─→ 新格式
    ↓                                    ↓
markitdown 解析 ←─────────────────────────┘
    ↓
图片/附件提取
    ↓
Markdown 后处理
    ↓
输出 .md 文件
```

### 关键技术

- **markitdown**: Microsoft 开源的多格式文档解析库
- **Office COM 接口**: 通过 pywin32 调用 Office 应用程序进行格式转换
- **ZIP 解压**: 直接解压 .docx/.pptx 文件提取嵌入资源
- **XML 解析**: 解析 Office 文档的 XML 结构获取附件元数据

## 更新日志

### v1.0.0

- 初始版本
- 支持多格式文件转 Markdown
- 支持图片和附件提取

## 时间追踪

交付后按 `../time-tracking-skill/references/zhj-eight-stage-workflow.md` 立即记录“文档整理（01）”；完成记录前不得进入下一步。
- 支持批量转换
