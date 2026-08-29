# DMP Test Case Excel Template Format

The DMP (Defect Management Platform) test-case import template is a 24-column Excel with 3 sheets. Only `sheet1` holds case data; `dropdown_items_sheet` and `basedata_items_sheet` are auxiliary and preserved as-is from the template.

## Sheet1 Structure

| Row | Content |
|-----|---------|
| 1 | Title row: `用例管理 # dmp_testcase` (merged across columns) |
| 2 | Instructions (merged) |
| 3 | English field names |
| 4 | Chinese field descriptions (input guidance) |
| 5+ | Case data rows |

## Column Spec (24 columns)

| Col | English | Chinese | Required | Description |
|-----|---------|---------|----------|-------------|
| A | team | *项目组 | Yes | e.g. `智慧记AI零售` |
| B | caseGroup | *功能路径（用例分组） | Yes | `2026-零售版{version}-{需求简称}`, levels separated by `-` |
| C | number | 用例编号 | No | 1, 2, 3… |
| D | name | *功能点（用例名称） | Yes | Case name |
| E | caseLabels | 用例标签 | No | Multiple labels comma-separated (often empty) |
| F | preCondition | 功能说明（前置条件） | No | Precondition text |
| G | input | input（步骤描述） | No | Test steps, numbered, newline-separated within cell |
| H | output | output（预期结果） | No | Expected results, numbered, newline-separated within cell |
| I | product | *产品 | Yes | e.g. `零售` |
| J | modulePath | *模块路径 | Yes | e.g. `智慧记AI零售-AI零售`, levels separated by `-` |
| K | version | 适用版本 | No | e.g. `v1.6.1` |
| L | caseType | *用例类型 | Yes | e.g. `功能测试` |
| M | source | 来源 | No | e.g. `需求文档` |
| N | caseLevel | 用例级别 | No | `P0` / `P1` / `P2` / `P3` |
| O | manager | *责任人 | Yes | Person name (use 工号 if duplicate names) |
| P | autoState | 已实现自动化 | No | `是` / `否` |
| Q | relateReqCode | 关联用户故事 | No | PRJ code, multiple newline-separated |
| R | workload | 工作量（分钟） | No | Positive integer |
| S | remarks | 备注 | No | Free text (often user-story name) |
| T | separator | 分隔符 | No | Custom separator for B/H columns |
| U | autoCaseId | 接口自动化用例ID | No | - |
| V | autoCaseName | 接口自动化用例名称 | No | - |
| W | autoProductId | 接口自动化产品ID | No | - |
| X | autoVersionId | 接口自动化版本ID | No | - |

## Formatting Notes

- **Multi-value cells (G, H, Q)**: use in-cell line breaks (`\n`), not separate rows.
- **Steps/expected numbering**: prefix each item with `1.`, `2.`, etc.
- **Example parentheses**: remove illustrative numeric parentheses like `（8）` or `（10-2=8）` from expected results; keep descriptive parentheses like `（前置条件）`.
- **Row height**: set ≈80 for data rows to fit multi-line steps/expected.
- **Wrap text + borders**: apply to all data cells for readability.

## Example Data Row (row 5)

```
A: 智慧记AI零售
B: 2026-零售版v1.6.1-退款单作废
C: 1
D: App端退款单作废完整流程
E: (empty)
F: 存在已退款的销售单及退款单，App登录有权限账号
G: 1.进入退款单列表\n2.点击'...'→作废→确认
H: 1.作废成功，退款单状态变更\n2.各模块数据同步更新
I: 零售
J: 智慧记AI零售-AI零售
K: v1.6.1
L: 功能测试
M: 需求文档
N: P0
O: 詹惠英
P: 否
Q: PRJ-00762593
R: (empty)
S: 【AI零售 1.6.1】退款单支持作废功能
T-X: (empty)
```

## Template Location

```
.qwen/knowledge-base/testcases/冒烟用例/模板：用户故事名称(便于DMP查找).xlsx
```

## Reference Example

```
.qwen/knowledge-base/testcases/冒烟用例/零售版v1.5.0/小票打印模板优化.xlsx
```
