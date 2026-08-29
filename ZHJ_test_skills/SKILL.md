---
name: zhj-test-skills
description: 智慧记运营测试八阶段工作流：从 Confluence 需求导出、文档转换、需求评审到测试用例、冒烟用例、入库、SVN 归档和需求归档；内置多业务线身份验证和 MySQL 工时追踪。用于智慧记运营、AI进销存、智慧记零售或国际版Ailit测试工作。
---

# 智慧记测试工作流套件

开始任何任务前，先阅读 `META_WORKFLOW.md` 和 `time-tracking-skill/references/zhj-eight-stage-workflow.md`。

必须先通过 MySQL `agent_team_roster` 验证员工姓名；多业务线员工按编号选择本次业务线。不得将业务线固定为“智慧记+运营系统”。

按照 META 工作流执行⓪、①、②、③、④、⑤、⑦、⑧。每个阶段完成后立即收集工时并写入本地 JSONL；不得二次确认，也不得在记录完成前进入下一阶段。③与④的反馈累计为同一条“生成用例（06）”记录。

用户说“查看时间统计”“时间报告”或“效能统计”时，调用 `time-tracking-skill/scripts/generate_time_analytics.py --biz-line <本次业务线>`；IDE 回复中给出 HTML 报告的完整本地路径。
