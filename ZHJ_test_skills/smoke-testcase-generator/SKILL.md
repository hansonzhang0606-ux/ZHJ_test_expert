---
name: smoke-testcase-generator
description: From a reviewed test-case XMind file, extract cases of a specified priority (default P0) and generate a smoke-test Excel in the DMP import template format (24 columns), saved under testcases/冒烟用例/零售版{版本号}/. This skill should be used when the user needs to generate smoke test cases, export P0 cases to Excel, create 冒烟用例, or prepare test cases for DMP import. Triggers include "生成冒烟用例", "冒烟测试用例", "P0用例导出excel", "导出冒烟用例", "smoke testcase".
agent_created: true
---

# Smoke Test Case Generator

## Overview

Extract cases of a specified priority (default P0) from a **reviewed** test-case XMind file (`*_测试用例_详细版reviewed.xmind`) and generate a smoke-test Excel following the DMP import template format (24 columns). Output is saved under `testcases/冒烟用例/零售版{版本号}/`.

## When to Use

- User asks to generate smoke test cases / 冒烟用例 from reviewed test cases
- User needs to export P0 (or other priority) cases to Excel for DMP import
- User mentions "生成冒烟用例", "冒烟测试用例", "P0用例导出", "导出冒烟用例"
- After the reviewed XMind is finalized and the user requests stage ④

## Prerequisites

1. **Reviewed XMind exists**: `最新需求/{标题}/{标题}_测试用例_详细版reviewed.xmind` (produced by stop-point 2)
2. **DMP Excel template exists**: `testcases/冒烟用例/模板：用户故事名称(便于DMP查找).xlsx`
3. **openpyxl installed**: run `pip install openpyxl` if not yet installed
4. User provides (optional but recommended):
   - Version number (e.g. `v1.6.1`) — derived from the requirement title if omitted
   - Manager / responsible person (责任人)
   - User-story mapping: requirement keyword → `编码:故事名称` (e.g. `退款单作废 → PRJ-00762593:【AI零售 1.6.1】退款单支持作废功能`)

## Workflow

### Step 1: Locate the reviewed XMind and DMP template

- Reviewed XMind: search `最新需求/{标题}/` for `*_测试用例_详细版reviewed.xmind`
- DMP template: `testcases/冒烟用例/模板：用户故事名称(便于DMP查找).xlsx`
- If either is missing, stop and tell the user.

### Step 2: Determine version, manager, and user-story mapping

Ask the user (or infer) for:
- **Version**: from the requirement title (e.g. "智慧记零售版本 V1.6.1" → `v1.6.1`). Output folder = `零售版{version去掉v}` (e.g. `零售版v1.6.1`).
- **Manager (责任人)**: the person responsible for the smoke cases (filled into column O).
- **User-story mapping**: for each requirement in the XMind, the user-story code (PRJ-xxx, column Q) and story name (column S remarks). Format per requirement: `关键词 → "PRJ-xxx:故事名称"`.

### Step 3: Extract target-priority cases from the reviewed XMind

Parse the XMind `content.json`, recursively walk the topic tree, and collect case nodes (nodes whose children contain "前置条件" or "测试步骤" or "预期结果"). For each case extract: name, precondition, steps, expected, path.

**优先级识别**：优先级标记在节点标题中（如 `P0: PC端退款单作废-正常流程`），脚本通过检查 `title.startswith('P0:')` 来筛选。
**注意**：当前脚本 `generate_smoke_testcase.py` 通过 `⚡ 优先级: P0` 子节点提取优先级，但 XMind 的优先级在父节点标题中。因此建议直接编写 Python 脚本从 XMind 中提取 P0 用例并生成 Excel，而非依赖脚本的优先级提取逻辑。

### Step 4: Group cases by requirement

Map each case to a `caseGroup` (column B) and user-story via the keyword mapping:
- If case name/path contains a mapping keyword (e.g. "退款单作废"), assign that group + story.
- `caseGroup` format: `2026-零售版{version}-{需求简称}` (e.g. `2026-零售版v1.6.1-退款单作废`).
- Cases not matching any keyword go to `2026-零售版{version}-其他` with empty story code.

### Step 5: Generate the Excel from the DMP template

1. Copy the DMP template to `testcases/冒烟用例/零售版{version}/零售版{version}冒烟用例.xlsx`
2. Load with openpyxl, delete template sample rows (row 5+)
3. Fill each P0 case as a row (starting row 5), 24 columns:
   - A team = `智慧记AI零售`
   - B caseGroup = group from step 4
   - C number = 1,2,3…
   - D name = case name
   - E caseLabels = `李刚`（负责测试的开发人员姓名，由用户提供）
   - F preCondition = precondition text
   - G input = steps, each step on a separate line. **必须在单元格内用 Alt+Enter (chr(10)) 换行！** (`1.xxx\n2.yyy`)
   - H output = expected, each result on a separate line. **必须在单元格内用 Alt+Enter (chr(10)) 换行！** (`1.xxx\n2.yyy`)
   - I product = `零售`
   - J modulePath = `智慧记AI零售-AI零售`
   - K version = `{version}`
   - L caseType = `功能测试`
   - M source = `需求文档`
   - N caseLevel = target priority (e.g. `P0`)
   - O manager = from user
   - P autoState = `否`
   - Q relateReqCode = user-story code from mapping
   - R workload = (empty)
   - S remarks = user-story name from mapping
   - T-X = (empty)
4. **换行处理**：使用 `chr(10)` 而不是 `\n` 字符串来分隔步骤和预期结果，确保 Excel 中正确显示为 Alt+Enter 换行效果
5. **自动换行设置**：对列 G 和列 H 的单元格设置 `alignment = Alignment(wrap_text=True, vertical='top')`，确保换行符在 Excel 中可见
6. Clean expected/steps text: remove example parentheses containing only numbers/arithmetic (e.g. `（8）`, `（10-2=8）`) — these are illustrative and should not appear in the final Excel.
7. Set borders for data rows.

### Step 6: Verify and report

- Verify row count = number of extracted cases
- Report the output path, case count, and per-case group/manager/story
- Present the file to the user

## Using the Script

The script `scripts/generate_smoke_testcase.py` automates the entire workflow.

```bash
PYTHON="py -3"
SCRIPT=".qwen/skills/smoke-testcase-generator/scripts/generate_smoke_testcase.py"

$PYTHON "$SCRIPT" \
  --xmind "最新需求/智慧记零售版本 V1.6.1/智慧记零售版本 V1.6.1_测试用例_详细版reviewed.xmind" \
  --version v1.6.1 \
  --template ".qwen/knowledge-base/testcases/冒烟用例/模板：用户故事名称(便于DMP查找).xlsx" \
  --output-base ".qwen/knowledge-base/testcases/冒烟用例" \
  --priority P0 \
  --manager 詹惠英 \
  --stories '{"退款单作废":"PRJ-00762593:【AI零售 1.6.1】退款单支持作废功能","蓝牙打印机":"PRJ-00762596:【AI零售 1.6.1】支持同时连接蓝牙小票打印机和标签打印机来打印"}'
```

Arguments:
- `--xmind` (required): path to the reviewed XMind
- `--version` (required): version label, e.g. `v1.6.1` (output folder = `零售版v1.6.1`)
- `--template` (required): path to the DMP Excel template
- `--output-base` (required): parent dir of `冒烟用例/` (script creates `零售版{version}/` inside)
- `--priority` (default `P0`): which priority to extract
- `--manager` (optional): responsible person (column O)
- `--stories` (optional): JSON mapping `需求关键词 → "编码:故事名称"`. Cases whose name/path contains the keyword get that code (column Q) and story name (column S).

> The `--stories` value is a single JSON string. Quote it and use double quotes inside. If omitted, columns Q and S are left empty for manual fill.

## Output

```
testcases/冒烟用例/零售版{version}/零售版{version}冒烟用例.xlsx
```

Excel structure (24 columns, rows 1-4 are the DMP template header, rows 5+ are cases). See `references/dmp_template_format.md` for the full column spec.

## Relationship to Other Skills

| Skill | Relationship | Order |
|-------|-------------|-------|
| md-to-xmind-testcase | Predecessor | Produces the AI XMind (③) |
| testcase-archive | Related | AI comparison and knowledge-base import is stage ⑤ |
| **smoke-testcase-generator** | **Current** | Extracts P0 → DMP Excel in stage ④ |

## Notes

- Always extract from the **reviewed** XMind (post stop-point 2), not the AI version — human review may have adjusted priorities.
- The DMP template has 3 sheets (`sheet1`, `dropdown_items_sheet`, `basedata_items_sheet`); only `sheet1` is modified, the other two are preserved from the template copy.
- Example parentheses in expected results (like `（8）`) are cleaned automatically; keep descriptive parentheses (like `（前置条件）`).
- **步骤和预期结果必须在单元格内用 Alt+Enter (chr(10)) 换行输入**，而不是用 `\n` 字符串。在 Python 中使用 `chr(10).join()` 或 `'\n'.join()` 均可，但必须确保输出到 Excel 的是真正的换行符。
- **必须设置 `wrap_text=True`**：对列 G 和列 H 的单元格设置 `Alignment(wrap_text=True, vertical='top')`，否则换行符在 Excel 中不可见。
- **用例标签列 (E列)**：填写负责测试的开发人员姓名（如"李刚"），由用户提供。
- **产品/模块路径**：列 I 产品固定为 `零售`，列 J 模块路径固定为 `智慧记AI零售-AI零售`。
- **优先级识别**：XMind 中的优先级标记在节点标题中（如 `P0: xxx`），而非独立的子节点。脚本应通过 `title.startswith('P0:')` 来筛选，而不是查找 `⚡ 优先级: P0` 子节点。
- **直接生成 Excel**：由于脚本的优先级提取逻辑与 XMind 格式不匹配，建议直接编写 Python 脚本从 XMind 提取 P0 用例并生成 Excel，而非依赖 `generate_smoke_testcase.py` 脚本。

## 时间追踪

进入④、开始生成冒烟用例前，按 `../time-tracking-skill/references/zhj-eight-stage-workflow.md` 处理会话标识：若当前会话已有③的 `session_id`，必须原样复用；若当前会话没有③，则生成新的当前会话标识。交付冒烟用例后传入 `--session-id` 和 `--merge-existing`：找到同会话③时累计到③创建的“生成用例（06）”记录，否则将④独立保存为一条“生成用例（06）”记录。不得使用其他会话的标识；完成记录前不得进入停止点或下一步。
