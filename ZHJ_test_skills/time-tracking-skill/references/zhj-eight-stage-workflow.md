# 智慧记运营测试八阶段时间追踪规则

## 会话开始（任何阶段前）

1. 检查任一既有本机 MySQL 配置；没有配置时，调用 `scripts/init_mysql_config.py --biz-line <本次业务线> --template --no-interactive --quiet` 生成本机模板，待员工填写后继续。
2. 调用 `python scripts/load_roster.py --json`，让员工盲输姓名并作精确匹配；不得展示花名册，不得以 `team_roster.yaml` 替代。
3. `agent_team_roster` 每行只有中文 `biz_line`，没有 `biz_line_code` 数组。脚本按姓名聚合该员工的多行业务线记录；若聚合后有多个中文业务线，按返回顺序展示编号选项。选择后再通过统一映射派生写入时间表的编码：“智慧记+运营系统”→`ZHJ`、“AI进销存”→`AIJXC`、“智慧记零售”→`ZHJLS`、“国际版Ailit”→`AILIT`；不得默认或写死为 ZHJ。
4. 业务线确定后调用 `python scripts/register_sync_tasks.py --biz-line <本次业务线>`。定时任务注册失败不阻塞主流程，但要给出脚本输出的原因。

## 每阶段完成后（立即执行）

交付产物后先展示该阶段参考时间，并立即询问“这一步为你节省了多少时间？可输入小时、人天或采纳”。在员工输入后直接调用 `record_time_saved.py` 保存；**不再二次确认**，且在保存（或记录 0 小时）前不得展示下一步或进入下一阶段。

员工拒绝填写时最多追问两次，仍拒绝则以 `--hours 0 --remark "用户未反馈"` 保存，不阻塞主流程。1 人天 = 8 小时。记录时传入本阶段智能体开始、结束时间和分钟数。

| 阶段 | 脚本参数 | 特别规则 |
|---|---|---|
| ⓪ 导出需求 | `--step "导出需求" --step-code 00` | 单条记录 |
| ① 转 MD | `--step "文档整理" --step-code 01` | 单条记录 |
| ② 需求评审 | `--step "需求评审" --step-code 02` | 单条记录 |
| ③ 生成测试用例 | `--step "生成用例" --step-code 06` | 创建 `06` 记录 |
| ④ 生成冒烟用例 | `--step "生成用例" --step-code 06 --merge-existing` | 与③累计为同一条记录 |
| ⑤ AI 对比入库 | `--step "AI 对比入库" --step-code 05` | 单条记录 |
| ⑦ SVN 归档上传 | `--step "SVN 归档上传" --step-code 08` | 单条记录 |
| ⑧ 需求归档 | `--step "入库知识库" --step-code 07` | 单条记录 |

完整命令形态：

```bash
python time-tracking-skill/scripts/record_time_saved.py \
  --employee "<员工>" --user-story "<故事编号与名称>" \
  --step "<步骤名称>" --step-code <编码> --hours <小时> \
  --biz-line "<本次选择的业务线>" \
  --agent-start-time "<ISO时间>" --agent-end-time "<ISO时间>" \
  --agent-duration-minutes <分钟>
```

本地 JSONL 是唯一原始数据源。系统在 09:00、12:00、18:00 幂等同步至公共 MySQL `agent_time_tracking` 表；`mysql_config.json` 含密码，只能存在于测试人员本机，不得打包。
