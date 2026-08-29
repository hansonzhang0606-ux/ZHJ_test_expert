# 8 个 Skill 简单操作说明

> 零售版需求分析与测试用例设计平台
> 按工作流顺序排列，每个 skill 说明用途、操作方式、输入输出

> **工时追踪**：首次会话按 `time-tracking-skill/references/zhj-eight-stage-workflow.md` 验证姓名并选择本次业务线。8 个阶段完成后均立即收集节省时间并直接保存；③与④累计到同一条“生成用例（06）”记录，不再二次确认。

---

## 1. confluence-requirement-exporter（⓪ 导出需求）

**用途**：从 Confluence 导出需求页面为 Word + 全部附件图片

**操作方式（对话输入，推荐）**：

首次配置账号密码（一次性，永久免密）：
```
配置confluence：账号=你的账号, 密码=你的密码
```

日常导出（直接发 URL）：
```
新需求：https://finkms.kingdee.com/pages/viewpage.action?pageId=100658642
```
```
旧需求：https://finkms.kingdee.com/pages/viewpage.action?pageId=89883854
```

**输入**：Confluence URL + 账号密码（本机配置文件）
**输出**：
- 新需求 → `最新需求/{标题}/{标题}.doc` + `images/`
- 旧需求 → `原需求/{标题}.doc` + `原图片/{标题}.zip`

**注意**：
- `新需求`/`最新需求` → LATEST 模式（文件夹+images）
- `旧需求`/`原需求`/`历史需求` → ORIGINAL 模式（doc+zip）
- 账号密码 base64 密文本机存储，不走 cookie，不过期
- 脚本只导出不删除（只读）

---

## 2. markitdown-converter（① 转 MD）

**用途**：Word/PDF/PPT/Excel 转结构化 Markdown，自动提取图片

**操作方式（命令行）**：
```bash
# 单文件
python .qwen/skills/markitdown-converter/scripts/convert_to_md.py "最新需求/xxx/xxx.doc"

# 批量（目录）
python .qwen/skills/markitdown-converter/scripts/convert_to_md.py "最新需求/xxx/" -r
```

**输入**：Word/PDF/PPT/Excel 单文件或目录
**输出**：结构化 `.md` + `images/`（提取的图片）

**注意**：
- 支持 .doc/.docx/.pdf/.ppt/.xls 等
- .doc 会先转 .docx 再转 MD（需 pywin32）
- 无附件时自动清理空 attachments 目录

---

## 3. md-requirement-review（② 需求评审）

**用途**：对需求 MD 进行专业评审，生成评审报告

**操作方式（对话输入）**：
```
评审需求：最新需求/智慧记零售版本 V1.6.1/智慧记零售版本 V1.6.1.md
```
或直接说"评审 xxx 需求"

**输入**：需求 MD 文件
**输出**：`{文件名}_评审报告.md`（含疑问/模糊点/冲突/完整性/可测试性/风险维度）

**注意**：
- 评审前读取知识库历史文档对比
- 评审后 ⏸停止点1，等人工确认

---

## 4. md-to-xmind-testcase（③ 生成测试用例）

**用途**：整合需求+评审报告，生成详细测试用例 JSON + XMind

**操作方式（对话输入）**：
```
生成测试用例：最新需求/智慧记零售版本 V1.6.1/智慧记零售版本 V1.6.1.md
```
或直接说"生成 xxx 的测试用例"

**输入**：需求 MD（自动搜索同目录评审报告）
**输出**：
- `{文件名}_测试用例_详细版_v1.0-ai.json`
- `{文件名}_测试用例_详细版_v1.0-ai.xmind`

**注意**：
- 生成前读取知识库历史用例/测试模式库自我评审
- 参考历史 Bug 预防清单补充遗漏
- 用例含前置条件/步骤/预期/优先级
- 评审方式：XMind 直接增删改，无需标记颜色
- 保存为 `{文件名}_测试用例_详细版reviewed.xmind`
- 评审后 ⏸停止点2

---

## 5. smoke-testcase-generator（④ 生成冒烟用例）

**用途**：从 reviewed XMind 提取 P0 用例，生成 DMP 导入格式 Excel

**操作方式（命令行）**：
```bash
python .qwen/skills/smoke-testcase-generator/scripts/generate_smoke_testcase.py \
  --xmind "最新需求/xxx/xxx_测试用例_详细版reviewed.xmind" \
  --version v1.6.1 \
  --template ".qwen/knowledge-base/testcases/冒烟用例/模板：用户故事名称(便于DMP查找).xlsx" \
  --output-base ".qwen/knowledge-base/testcases/冒烟用例" \
  --priority P0 \
  --manager 詹惠英 \
  --stories '{"退款单作废":"PRJ-00762593:【AI零售 1.6.1】退款单支持作废功能","蓝牙打印机":"PRJ-00762596:故事名"}'
```

**输入**：reviewed XMind + DMP 模板 + 用户故事映射
**输出**：`testcases/冒烟用例/零售版{版本}/零售版{版本}冒烟用例.xlsx`

**注意**：
- 自动提取 P0 + 按需求关键词分组
- 去掉预期里多余的举例括号（如"（8）"）
- 填责任人（O列）、用户故事编码（Q列）、故事名称（S列）
- 一条命令生成完整 Excel，可直接导入 DMP
- ⏸停止点3：客户确认入库

---

## 6. testcase-archive（⑤ AI 对比入库）

**用途**：对比 AI 版与 reviewed 版 XMind 差异，合并入库，维护索引和进化日志

**操作方式（对话输入）**：
```
已评审，请对比入库
```
或直接说"对比入库 xxx"

**输入**：
- `{文件名}_测试用例_详细版_v1.0-ai.xmind`（AI 生成版）
- `{文件名}_测试用例_详细版reviewed.xmind`（人工评审版）

**输出**：
- `{文件名}_测试用例_对比差异报告.md`（新增/删除/修改/未变更）
- `{文件名}_测试用例_质量分析报告.md`（覆盖率/准确率/遗漏率等）
- 入库 `testcases/{文件名}_测试用例_详细版reviewed.xmind`
- 更新 `INDEX.md` + `EVOLUTION_LOG.md`（去重替换）

**注意**：
- 直接内容对比（按用例名+步骤+预期+优先级），无需颜色标记
- EVOLUTION_LOG 去重：同标题记录替换，不重复追加
- ⏸停止点3 客户确认后才执行

---

## 7. svn-archive（⑦ SVN 归档上传）

**用途**：上传测试用例和评审报告到 SVN 归档

**操作方式（对话输入）**：
```
上传SVN归档
```
AI 列出待上传文件清单 + 目标路径后直接执行上传，无需人工确认。

**命令行**：
```bash
python .qwen/skills/svn-archive/scripts/svn_upload.py \
  --version v1.6.1 \
  --files "ai.xmind" "reviewed.xmind" "评审报告.md"
```

**输入**：ai.xmind + reviewed.xmind + 评审报告.md
**输出**：SVN `零售版/v{版本}/` 下 3 个文件

**安全规则**：
- 只用 `svn mkdir` + `svn import`，**禁止 svn delete**
- AI 列出清单后直接执行上传，无需用户回复确认
- 文件已存在则跳过（不删除重传）
- 凭据 svn auth 缓存（免密），不存明文密码
- 前置：装 SlikSVN + `svn info URL --username xxx --password yyy` 缓存凭据

---

## 8. req-merger（⑧ 需求归档）

**用途**：解析 Confluence MIME .doc，按模块拆分归档最终需求

**操作方式（命令行）**：
```bash
# 解析 MIME 文档
python .qwen/skills/req-merger/scripts/extract_confluence_doc.py \
  --input "原需求/xxx.doc" --output-dir "临时目录"

# 提取图片
python .qwen/skills/req-merger/scripts/extract_images.py \
  --zip "原图片/xxx.zip" --target-dir "images/模块名/"
```

**输入**：Confluence .doc + 图片 zip
**输出**：`原需求/<模块>/<模块>_V<版本>_最终需求.md` + `images/`

**注意**：
- 项目结束时按模块归档最终需求
- 空闲期可人工发起整理历史需求（见 QWEN.md "空闲期补充任务"）
- 按章节识别模块，同模块同版本覆盖更新

---

## 完整工作流顺序

```
⓪导出 → ①转MD → ②评审 → ⏸停1 → ③测试用例 → ⏸停2
→ ④冒烟用例 → ⏸停3 → ⑤对比入库 → ⑥完整性检查
→ ⑦SVN归档上传(⏸️确认) → ⑧需求归档
```

> 💡 非强制串行：可从任意节点插入执行后续步骤，前置停止点视为已通过

---

## 环境准备（首次使用）

| 依赖 | 用途 | 安装 |
|------|------|------|
| Python 3.8+ | 运行脚本 | python.org |
| markitdown[all] + pywin32 | ①转MD | `pip install markitdown[all] pywin32` |
| openpyxl | ④冒烟用例Excel | `pip install openpyxl` |
| SlikSVN 64bit | ⑦SVN上传 | sliksvn.com |

**Confluence 配置**：对话输入 `配置confluence：账号=xxx, 密码=yyy`
**SVN 配置**：cmd 运行 `svn info http://192.168.204.100/svn/zhihuiji/ --username 账号 --password 密码`

---

*文档更新：2026-07-23*
