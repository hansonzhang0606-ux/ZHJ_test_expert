---
name: req-merger
description: 解析 Confluence 导出的 MIME 格式 .doc 需求文档，从 zip 包中提取图片，合并多版本需求为标准化 Markdown 文档。使用场景：用户提供从 Confluence 导出的 .doc 文件（非真正的 Word 文档），需要将历史需求按模块整理为 Markdown 格式，或需要将多版本（V1.0/V1.1/V1.3）需求合并为一个文档。当 .doc 文件无法被 python-docx 打开时，触发此 skill。
---

# 需求文档合并 Skill

## 目标

将 Confluence 导出的历史需求文档（MIME 格式 .doc）解析为结构化 HTML，从 zip 图片包中提取原型图并正确映射到需求文本，最终合并为标准化、图文并茂的 Markdown 需求文档。

## 输入输出

- **输入**：
  - Confluence 导出的 `.doc` 文件（MIME multipart 格式，非真正 Word .doc）
  - 图片 zip 包（Confluence 导出的附件图片压缩包）
  - 已有模块 Markdown 文件（可选，用于增量合并）
- **输出**：
  - `<模块名>.md` — 标准化 Markdown 需求文档
  - 图片文件放置到 `images/<模块>/` 目录

## ⚠️ 图片和附件解析要求

**图片正确放置是本次合并的核心要求！**

Confluence 导出的需求文档中，图片与文本的对应关系通过 HTML 表格结构确定：

| 表格列 | 内容类型 | 图片归属 |
|---------|---------|---------|
| **页面名称** | 功能/页面标题 | — |
| **原型** | 原型截图 | 放在 `**原型图**：` 下方，紧跟小标题之后 |
| **需求详细说明** | 文字描述 + 行内图片 | 行内图片紧跟在对应文字之后 |

### 图片引用机制

Confluence HTML 中 `<img>` 标签使用 CID 引用：

```html
<img class="confluence-embedded-image" src="8ee10a6c335090a752b5974ff78dd310"
     data-image-src="/download/attachments/85150393/image2025-8-20_17-33-32.png">
```

- `src`：CID（32位 MD5 哈希），不能直接匹配文件名
- `data-image-src`：原始文件名，**必须通过此属性建立 CID→文件名的映射**

### 图片命名规范

| 版本 | 前缀 | 示例 |
|------|------|------|
| V1.0（基础版） | `img_XXX_` | `img_001_image2025-6-23_11-14-58.png` |
| V1.1 | `img_v11_` | `img_v11_500_image2025-7-23_13-50-37.png` |
| V1.3+ | `img_v13_` | `img_v13_image2025-8-20_17-33-32.png` |

命名规则：`img_<版本前缀>_<三位序号>_<原始文件名>.png`

### CID→文件名映射步骤（必须执行）

1. **从 HTML 提取所有 `<img>` 标签**，获取 `src`（CID）和 `data-image-src`（原始文件名）
2. **从 `data-image-src` 提取文件名**：`/download/attachments/85150393/image2025-8-20_17-33-32.png` → `image2025-8-20_17-33-32`
3. **与 zip 提取的图片匹配**：提取的图片文件名为 `img_v13_XXX_image2025-8-20_17-33-32.png`，按原始文件名前缀匹配
4. **建立映射表**：`CID -> images/模块/img_v13_xxx.png`

### 模型不支持图片时的处理

如当前模型不支持图片输入，无法验证图片内容是否正确对应：

1. **明确提示用户**：
   ```
   ⚠️ 当前模型不支持图片输入，无法验证图片与文本的对应关系。
   建议更换为支持多模态的模型版本。
   ```
2. **列出引用的图片清单**：从 Markdown 中提取所有 `![]()` 引用
3. **建议更换模型**：提示用户切换到支持多模态的模型版本

## 文档结构识别

根据 Confluence 导出的 HTML 内容自动识别文档结构：

| 结构部分 | 判断依据 | 处理方式 |
|---------|---------|---------|
| **业务说明** | 包含版本对比表格（V1.0/V1.3/后续迭代） | 作为基础文档保留 |
| **字段说明** | 包含字段定义表格 | 作为基础文档保留 |
| **页面逻辑** | 包含页面列表、筛选项、操作项等描述 | 作为基础文档保留 |
| **需求详述** | 包含表格结构：页面名称\|原型\|需求详细说明 | 按表格行提取，图片紧跟文字 |
| **需求分析** | 包含竞品方案对比、核心场景分析 | **不纳入输出文档** |
| **变更记录** | 包含改动日期/改动内容/改动人/产品经理分工 | **不纳入输出文档** |
| **数据埋点** | 包含事件ID/事件名称/采集时机等 | **不纳入输出文档** |
| **背景说明** | 包含背景/目标/功能定位等 | **不纳入输出文档** |
| **非功能需求** | 包含性能/成本等说明 | **不纳入输出文档** |
| **问题列表** | 包含待确认问题 | **不纳入输出文档** |

## 处理流程

### 步骤 1：解析 Confluence MIME 文档

Confluence 导出的 `.doc` 文件是 MIME multipart/related 格式，使用 `quoted-printable` 编码，**不能被 python-docx 解析**。

**执行脚本**：

```bash
py -3 <skill-path>/scripts/extract_confluence_doc.py \
  --input <confluence-doc路径> \
  --output-dir <临时输出目录>
```

脚本输出：
- `main.html` — HTML 内容文件
- `images/` — 如 MIME 中包含嵌入图片（通常为空，图片在单独 zip 包中）

### 步骤 2：从 zip 包提取图片

**执行脚本**：

```bash
py -3 <skill-path>/scripts/extract_images.py \
  --zip <zip路径> \
  --target-dir images/<模块>/ \
  --version-prefix <版本前缀，如 v13>
```

脚本输出：重命名后的图片文件，如 `img_v13_001_image2025-8-25_19-12-38.png`

### 步骤 3：检测并排除删除线内容 ⚠️

**此步骤极其重要！遗漏删除线内容是最常见的整理错误。**

Confluence HTML 中使用以下标签标记删除线内容：

| HTML 标签 | 说明 | 处理 |
|-----------|------|------|
| `<s>文字</s>` | Strikethrough — 最常见 | **必须排除** |
| `<del>文字</del>` | Deleted text | **必须排除** |
| `<strike>文字</strike>` | Strike-through | **必须排除** |
| `~~文字~~` | Markdown 删除线 | **必须排除** |

**检测脚本**（必须在整理前执行）：

```python
from bs4 import BeautifulSoup

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# 检测所有删除线内容
print('=== 删除线内容检测 ===')
for tag in soup.find_all(['s', 'del', 'strike']):
    txt = tag.get_text(strip=True)
    if txt:
        print(f'  <{tag.name}>: {txt[:200]}')

# 提取非删除线内容时，必须检查每个元素的父元素链
def is_in_strikethrough(elem):
    """检查元素是否在删除线标签内"""
    parent = elem.parent
    while parent:
        if parent.name in ('s', 'del', 'strike'):
            return True
        parent = parent.parent
    return False

# 提取非删除线文字和图片时使用
def flatten_content(elem):
    results = []
    def walk(e):
        from bs4 import NavigableString
        if e.name == 'img':
            if is_in_strikethrough(e):
                return  # 跳过删除线内的图片
            # ... 提取图片
        elif isinstance(e, NavigableString):
            if is_in_strikethrough(e):
                return  # 跳过删除线内的文字
            txt = str(e).strip()
            if txt:
                results.append(('text', txt))
        elif e.name:
            for child in e.children:
                walk(child)
    walk(elem)
    return results
```

### 步骤 4：提取完整文字和图片（不可压缩！）⚠️

**文字过度压缩/省略是第二常见的整理错误。必须保留完整的原始文字。**

提取规则：

| 规则 | 说明 | 常见错误 |
|------|------|---------|
| **保留完整原文** | 逐字保留 HTML 中的所有非删除线文字 | ❌ 将多条规则压缩为要点列表 |
| **保留 toast 提示** | 所有 toast 提示文案必须完整保留 | ❌ 省略"toast提示'xxx'" |
| **保留校验规则** | 所有校验规则（必填/格式/范围/报错）必须完整保留 | ❌ 省略"若xx为空则报错'xx'" |
| **保留边界条件** | 数量限制/字符限制/格式要求必须保留 | ❌ 省略"最多5张""最多32个字" |
| **保留默认值** | 默认值/默认勾选/默认选中必须保留 | ❌ 省略"默认勾选""默认今日" |
| **保留交互细节** | 点击/弹窗/跳转/置灰等交互逻辑必须保留 | ❌ 省略"点击后弹窗展示""按钮置灰" |
| **保留图片引用** | 所有非删除线图片必须引用 | ❌ 遗漏原型图/行内图 |
| **不总结归纳** | 不要用"等""详见"等省略性表述代替原文 | ❌ "详见星火"代替完整描述 |

### 步骤 5：构建 CID→提取文件名映射并分析表格结构

**关键步骤！** 此步骤决定图片能否正确放置。

从 `main.html` 中提取所有非删除线 `<img>` 标签，建立 CID→文件名映射。

遍历 Confluence 表格的每一行，按阅读顺序提取文字和图片：

```python
def flatten_detail(cell):
    results = []
    def walk(elem):
        from bs4 import NavigableString
        if elem.name == 'img':
            if is_in_strikethrough(elem):
                return  # 跳过删除线图片
            src = elem.get('src', '')
            results.append(('img', cid_map.get(src, 'UNMAPPED')))
        elif isinstance(elem, NavigableString):
            if is_in_strikethrough(elem):
                return  # 跳过删除线文字
            txt = elem.strip()
            if txt:
                results.append(('text', txt))
        elif elem.name:
            for child in elem.children:
                walk(child)
    walk(cell)
    return results
```

### 步骤 6：合并到 Markdown 文档

### 合并规则

| 规则 | 说明 |
|------|------|
| **版本优先级** | 最新版本覆盖旧版本。V1.3 > V1.1 > V1.0 |
| **移除需求分析** | 不纳入需求分析/竞品方案对比/背景说明/变更记录/数据埋点/非功能需求/问题列表 |
| **移除删除线内容** | 删除所有 `<s>`、`<del>`、`<strike>`、`~~删除~~` 标记的内容 |
| **保留完整原文** | 不压缩、不省略、不归纳，逐字保留原始非删除线文字 |
| **图片引用格式** | `![文件名](images/模块/文件名.png)`，确保文件存在 |
| **不添加解释性文字** | 不要添加"以下按原需求文档表格结构整理..."等注释 |
| **不篡改原始需求** | 严格按照 HTML 中的图片-文字对应关系放置 |

### 图片放置规则 ⚠️

每行需求必须遵循表格行的格式：

```markdown
##### 1）页面名称

**原型图**：

![img_v13_xxx.png](images/模块/img_v13_xxx.png)

**需求详细说明**：

文字描述内容...
![img_v13_yyy.png](images/模块/img_v13_yyy.png)
更多文字描述...
```

| 规则 | 说明 | 错误示例 |
|------|------|---------|
| 原型图位置 | 放在 `**原型图**：` 下方，紧跟小标题 | 原型图被放到需求详细说明中 |
| 行内图片位置 | 紧跟在对应文字说明之后 | 所有图片被集中放在段落末尾 |
| 不重复图片 | 原型图只出现在 `**原型图**：` 下方 | 同一图片在原型图和需求详细说明中各出现一次 |
| 数量匹配 | 原型图数量与 HTML 中该行列数一致 | HTML 中只有1张图，输出中放了3张 |

### 步骤 7：校验与验证 ⚠️

**整理完成后必须执行以下3项校验，不可跳过！**

#### 7.1 删除线内容泄露检查

检查各模块 Markdown 文件中是否错误包含了 HTML 中的删除线内容：

```python
from bs4 import BeautifulSoup
import os

# 从HTML提取所有删除线文字
soup = BeautifulSoup(html, 'html.parser')
del_texts = set()
for tag in soup.find_all(['s', 'del', 'strike']):
    txt = tag.get_text(strip=True)
    if txt and len(txt) > 5:
        del_texts.add(txt)

# 检查模块文件
for fname in module_files:
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    for del_text in del_texts:
        check = del_text[:40]  # 取前40字符作为检查片段
        if check in content:
            # 进一步检查：该文字在HTML中是否同时有非删除线版本
            has_non_del = False
            for s in soup.find_all(string=lambda x: x and check in str(x)):
                parent = s.parent
                in_del = False
                while parent:
                    if parent.name in ('s', 'del', 'strike'):
                        in_del = True
                        break
                    parent = parent.parent
                if not in_del:
                    has_non_del = True
                    break
            if not has_non_del:
                print(f'  ❌ {fname}: 删除线内容被保留: {del_text[:80]}')
```

**注意**：同一文字可能同时存在删除线和非删除线版本（删除线是旧版，非删除线是新版）。只有**仅有删除线版本**的文字才需要移除。

#### 7.2 图片引用完整性检查

检查所有非删除线图片是否都被引用：

```python
import re, os

# 从HTML提取所有非删除线图片
non_del_imgs = set()
for img in soup.find_all('img'):
    if not is_in_strikethrough(img):
        # ... 提取文件名并匹配
        non_del_imgs.add(matched_filename)

# 从模块文件提取已引用的图片
refs = set(re.findall(r'!\[.*?\]\(images/[^/]+/([^)]+)\)', content))

# 找出缺失
missing = non_del_imgs - refs
if missing:
    print(f'缺失 {len(missing)} 张图片')
```

#### 7.3 文字完整性检查

提取 HTML 中各模块的非删除线关键文字（含 toast/报错/校验/不可/必须/默认/不支持/隐藏/展示/限制/超过/最多/至少 等关键词的句子），检查是否在模块文件中存在：

```python
keywords = ['toast', '报错', '校验', '不可', '必须', '默认', '不支持', 
            '隐藏', '展示', '限制', '超过', '最多', '至少', '禁止', '需']

# 提取含关键词的非删除线文字
for elem in soup.find_all(['p', 'td', 'th']):
    if is_in_strikethrough(elem):
        continue
    txt = elem.get_text(strip=True)
    if txt and len(txt) > 5 and any(kw in txt for kw in keywords):
        check = txt[:40]
        if check not in existing_content:
            print(f'  [TXT] 缺失: {txt[:100]}')
```

### 版本覆盖检查

确认新版本需求正确覆盖了旧版本中已被删除/修改的功能描述，删除线内容已被移除。

## 输出文件命名

```
<模块名>.md

示例：
商品模块 → 03_商品.md
订单模块 → 04_订单.md
```

图片目录：

```
images/<模块>/
├── img_001_*.png          # V1.0 图片
├── img_v11_*.png          # V1.1 图片
└── img_v13_*.png          # V1.3+ 图片
```

## 输出文档格式

```markdown
## 模块名

### 1、业务说明

|  | V1.0 | V1.3 | 后续迭代 |
| --- | --- | --- | --- |
| 功能A | ~~旧描述~~ | 新描述 | 未来计划 |
| 功能B | 保留 | 更新 | — |

### 2、字段说明

| 字段名 | 预设值 | 交互组件 | 默认值 | 是否必填 | 前端是否展示 | 更多说明 |
| --- | --- | --- | --- | --- | --- | --- |
| 商品名称 | | | | 是 | 是 | |

### 3、页面逻辑

#### 1）商品列表页

原型图：
![img_005_xxx.png](images/模块/img_005_xxx.png)

功能描述：
列表页功能描述...

### V1.1 移动端差异说明

移动端与 PC 端的差异说明...

---

## V1.3 新增需求

### 一、模块-功能名称

#### 需求详述

##### 1）页面名称

**原型图**：

![img_v13_xxx.png](images/模块/img_v13_xxx.png)

**需求详细说明**：

文字描述...
![img_v13_yyy.png](images/模块/img_v13_yyy.png)

更多文字描述...

##### 2）另一个页面名称

**原型图**：

![img_v13_zzz.png](images/模块/img_v13_zzz.png)

**需求详细说明**：

文字描述...
```

## 使用方法

### 基础用法（单模块需求合并）

```
用户：将零售版/V1.3+多单位_赊账等.doc 和图片包合并到商品需求文档
```

AI 执行步骤：
1. 运行 `extract_confluence_doc.py` 解析 .doc 文件为 HTML
2. 运行 `extract_images.py` 从 zip 包提取图片
3. **检测所有删除线内容**（步骤3）
4. 构建 CID→文件名映射表
5. 分析 HTML 表格结构，提取非删除线图片-文字对应关系
6. **逐字保留完整原文**，不压缩不省略（步骤4）
7. 按规则生成 Markdown 内容
8. **执行3项校验**：删除线泄露检查、图片完整性检查、文字完整性检查（步骤7）

### 增量合并（已有文档基础上更新）

```
用户：把 V1.4 的新需求合并到 03_商品.md 中
```

AI 执行步骤：
1. 解析 V1.4 的 .doc 文件为 HTML
2. 提取 V1.4 图片包
3. **检测 V1.4 的删除线内容**
4. 读取现有 03_商品.md
5. 将 V1.4 非删除线需求追加/覆盖到对应位置
6. **校验：删除线泄露、图片完整性、文字完整性**

### 多版本合并

```
用户：把 V1.0、V1.1、V1.3 的所有需求合并为一个商品.md
```

AI 执行步骤：
1. 依次解析各版本 .doc 文件
2. 提取各版本图片包，按版本前缀命名
3. **检测各版本的删除线内容**
4. 以最新版本为基础，合并历史版本中未被覆盖的非删除线内容
5. 移除删除线内容和需求分析章节
6. **逐版本校验：删除线泄露、图片完整性、文字完整性**
7. 生成最终合并文档

## 注意事项

1. **不篡改原始需求**：严格按照 HTML 中的图片-文字对应关系放置图片，不要凭感觉添加或删除
2. **删除线内容必须删除**：所有 `<s>`、`<del>`、`<strike>`、`~~删除~~` 标记的内容不应出现在输出中。**特别注意 `<s>` 标签，这是 Confluence 最常用的删除线标签，容易被遗漏**
3. **删除线检测必须检查父元素链**：删除线标签可能嵌套在任意层级（td/p/div/span 等），必须递归检查每个元素的父元素链是否包含删除线标签
4. **同一文字可能同时存在删除线和非删除线版本**：删除线是旧版/废弃版，非删除线是新版/生效版。只有**仅有删除线版本**的文字才需要移除；同时存在两个版本的，保留非删除线版本
5. **保留完整原始文字**：不压缩、不省略、不归纳、不用"等""详见"代替原文。所有 toast 提示、校验规则、边界条件、默认值、交互细节必须逐字保留
6. **需求分析/竞品对比不纳入**：需求分析/竞品方案对比/背景说明/变更记录/数据埋点/非功能需求/问题列表不纳入输出文档
7. **解释性注释不添加**：不要在输出中添加"以下按原需求文档表格结构整理"等解释性文字
8. **图片文件必须存在**：所有引用的图片文件必须在磁盘上存在
9. **图片完整性**：所有非删除线图片必须引用，不可遗漏。整理后必须执行图片完整性校验
10. **文字完整性**：整理后必须执行文字完整性校验，检查含关键词（toast/报错/校验/必须/默认/不支持等）的句子是否被保留
11. **Windows 路径编码**：在 Windows 上执行脚本时，使用 `py -3` 而非 `python3`
12. **依赖库**：需要安装 `beautifulsoup4`，如未安装需执行 `pip install beautifulsoup4`
13. **评审结果需人工审核**：合并后的文档需人工确认图片与文本对应关系是否正确

## 常见错误及预防

| 错误类型 | 描述 | 预防措施 |
|---------|------|---------|
| **删除线泄露** | `<s>` 标签内容被保留在输出中 | 步骤3检测删除线，步骤7.1校验泄露 |
| **文字压缩** | 多条规则被压缩为要点列表，丢失 toast/校验/边界条件 | 步骤4逐字保留原文，步骤7.3文字完整性校验 |
| **图片遗漏** | 非删除线图片未被引用 | 步骤7.2图片完整性校验 |
| **误纳入需求分析** | 竞品对比/核心场景/变更记录被纳入 | 步骤6合并规则明确排除 |
| **格式差异误报** | 直引号vs弯引号、表格分隔符等导致误报缺失 | 校验时做格式归一化（去除空格、统一引号）后再匹配 |

## 时间追踪

需求归档完成后按 `../time-tracking-skill/references/zhj-eight-stage-workflow.md` 立即记录“入库知识库（07）”；完成记录前不得结束流程。
