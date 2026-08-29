# 零售版 8 个 Skill 阶段映射表

> 参考图片格式，按工作流顺序排列

| # | 阶段 | 实现方式 | 主要输入 | 关键产物 |
|---|------|---------|---------|---------|
| 1 | ⓪ 导出需求 | 调用 skill `confluence-requirement-exporter`；脚本 `scripts/export_confluence.py --page-id --mode ORIGINAL\|LATEST`；账号密码 Basic Auth 认证（本机配置，永久免密） | Confluence 页面 URL（含 pageId） | 新需求：`最新需求/{标题}/{标题}.doc` + `images/`<br>旧需求：`原需求/{标题}.doc` + `原图片/{标题}.zip` |
| 2 | ① 转 MD | 调用 skill `markitdown-converter`；脚本 `scripts/convert_to_md.py`；.doc 先转 .docx 再转 MD | Word/PDF/PPT/Excel 单文件或目录 | 结构化 `.md` 文件 + `images/`（提取的图片） |
| 3 | ② 需求评审 | 调用 skill `md-requirement-review`；AI 读取知识库历史需求对比分析 | 需求 MD 文件 | `{文件名}_评审报告.md`（含疑问/模糊点/冲突/完整性/可测试性/风险） |
| — | ⏸️ 停止点 1 | 人工审核评审报告 | 评审报告 | 回复"确认"或提出修改意见 |
| 4 | ③ 生成测试用例 | 调用 skill `md-to-xmind-testcase`；AI 整合需求+评审报告+场景示例+知识库模式推导；脚本 `scripts/generate_xmind.py` 生成 XMind | 需求 MD（自动搜索同目录评审报告+场景示例） | `{文件名}_测试用例_详细版_v1.0-ai.json` + `.xmind`（含前置条件/测试步骤/预期结果/优先级） |
| — | ⏸️ 停止点 2 | 人工在 XMind 中评审用例（直接增删改，无需标记颜色） | AI 版 XMind | 保存为 `{文件名}_测试用例_详细版reviewed.xmind` |
| 5 | ④ 生成冒烟用例 | 调用 skill `smoke-testcase-generator`；脚本 `scripts/generate_smoke_testcase.py --xmind --version --template --priority P0`；从 reviewed 提取 P0 按 DMP 模板生成 Excel | reviewed XMind + DMP Excel 模板 + 用户故事映射（需求关键词→编码:故事名称）+ 责任人 | `testcases/冒烟用例/零售版{版本}/零售版{版本}冒烟用例.xlsx`（24列 DMP 导入格式） |
| — | ⏸️ 停止点 3 | 客户确认冒烟用例无误，同意入库 | 冒烟用例 Excel | 回复"确认入库" |
| 6 | ⑤ AI 对比入库 | 调用 skill `testcase-archive`；AI 自动对比 AI 版与 reviewed 版差异（按用例名+步骤+预期+优先级匹配）；合并入库+更新索引+进化日志 | `{文件名}_测试用例_详细版_v1.0-ai.xmind` + `{文件名}_测试用例_详细版reviewed.xmind` | `{文件名}_测试用例_对比差异报告.md`（新增/删除/修改/未变更）<br>`{文件名}_测试用例_质量分析报告.md`（覆盖率/准确率/遗漏率）<br>入库 `testcases/` + 更新 `INDEX.md` + `EVOLUTION_LOG.md` |
| 7 | ⑦ SVN 归档上传 | 调用 skill `svn-archive`；脚本 `scripts/svn_upload.py --version --files`；只用 `svn mkdir` + `svn import`，禁止 `svn delete`；AI 列出清单后直接执行，无需人工确认 | ai.xmind + reviewed.xmind + 评审报告.md | SVN `零售版/v{版本}/` 下 3 个文件 |
| 8 | ⑧ 需求归档 | 调用 skill `req-merger`；脚本 `extract_confluence_doc.py` 解析 MIME .doc + `extract_images.py` 提取图片；按模块拆分到 `原需求/<模块>/` | Confluence 导出的 `.doc` + 图片 zip | `原需求/<模块>/<模块>_V<版本>_最终需求.md` + `images/<模块>/` |

---

## 工作流全貌

```
⓪导出需求 → ①转MD → ②需求评审 → ⏸️停1 → ③生成测试用例 → ⏸️停2
→ ④生成冒烟用例 → ⏸️停3 → ⑤AI对比入库 → ⑦SVN归档上传 → ⑧需求归档
```

> 💡 非强制串行：可从任意节点插入执行后续步骤，前置停止点视为已通过

---

## 环境准备

| 依赖 | 用途 | 安装 |
|------|------|------|
| Python 3.8+ | 运行所有脚本 | python.org |
| markitdown[all] + pywin32 | ①转MD | `pip install markitdown[all] pywin32` |
| beautifulsoup4 | ⑧解析Confluence MIME .doc | `pip install beautifulsoup4` |
| openpyxl | ④冒烟用例Excel | `pip install openpyxl` |
| SlikSVN 64bit | ⑦SVN上传 | sliksvn.com |

**Confluence 配置**：对话输入 `配置confluence：账号=xxx, 密码=yyy`
**SVN 配置**：cmd 运行 `svn info http://192.168.204.100/svn/zhihuiji/ --username 账号 --password 密码`
