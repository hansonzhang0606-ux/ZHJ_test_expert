---
name: time-tracking-skill
description: >-
  测试人员时间节省追踪 Skill（通用多业务线版）。在工作流每个步骤完成后强制收集
  节省时间数据，本地 JSONL 记录 + 定时任务幂等同步到共享 MySQL 数据库，可生成
  HTML 可视化分析报告。支持多业务线（效贷/泾渭云/效融/小贷/
  智慧记+运营系统/AI进销存/智慧记零售/国际版Ailit），业务线通过配置与花名册动态识别。
  v1.5.2：身份识别从读 team_roster.yaml 改为实时查 MySQL agent_team_roster 表（多副本/多机器花名册永远最新）。
  触发场景：记录测试工作节省时间、时间节省统计、效能追踪、工时统计、时间报告。
---

# 测试人员时间节省追踪 Skill

> **智慧记运营套件覆盖规则**：本套件的八阶段映射、跨业务线选择、③④累计和“反馈后直接保存（无二次确认）”以 [`references/zhj-eight-stage-workflow.md`](references/zhj-eight-stage-workflow.md) 为准；其规则优先于本文件中的通用旧口径。

> 从「效贷测试专家」抽取而来的独立子 Skill，用于嵌入其他测试团队的 Skill 套件。
> 核心能力：**追踪并量化测试工作中 AI 为每位测试人员节省的时间**。

## 一、能力概览

| 能力 | 说明 |
|------|------|
| 强制反馈 | 工作流每个步骤完成后，强制收集节省时间（不可跳过） |
| 直接保存 | 员工反馈后立即写入；智慧记运营套件不要求二次确认 |
| 身份验证 | 盲输入 + 花名册精确匹配；保存前硬校验员工在职及业务线归属，失败不写入 |
| 多业务线 | 一份 Skill 服务多条业务线，数据按业务线隔离 |
| 本地优先 | 业务数据先写本地 JSONL、再由定时任务同步 MySQL；但保存前的实时花名册校验仍依赖 MySQL，校验失败必须拒写 |
| MySQL 同步 | 本地 JSONL 幂等 upsert 到共享 MySQL（离线可用，pymysql 已打包） |
| 可视化报告 | HTML 报告（内置 JS 筛选面板）+ CSV 导出，报告必展示 |
| 双宿主兼容 | WorkBuddy（`present_files` 展示）与 IDE（VSCode/OpenCode/Claude Code 等，给文件路径）均可运行 |

## 二、目录结构

```
time-tracking-skill/
├── SKILL.md                          # 本文件
├── README.md                         # 使用与部署说明
├── prompts/
│   └── time_tracking.md              # 执行规则（AI 遵循的完整工作流）
├── config/
│   ├── time_tracking_config.yaml     # 主配置（default_biz_line、storage_mode、MySQL 等）
│   └── team_roster.yaml              # 花名册【已弃用，人员改存 MySQL agent_team_roster】
└── scripts/
    ├── biz_line_helper.py            # 业务线解析助手（统一入口）
    ├── record_time_saved.py          # 记录节省时间（写本地 JSONL）
    ├── generate_time_analytics.py    # 生成 HTML/CSV 分析报告
    ├── sync_to_excel.py              # Excel 集中存储（可选附加）
    ├── sync_to_mysql.py              # MySQL 幂等同步（时间节省数据 → agent_time_tracking）
    ├── sync_roster_to_mysql.py       # 花名册同步【已弃用】
    ├── load_roster.py                # 实时查 MySQL agent_team_roster，AI 身份识别用（v1.5.2）
    ├── init_mysql_config.py          # 初始化本机 MySQL 配置（一次性）
    ├── mysql_config.json.template    # MySQL 配置模板
    ├── sync_task.bat                 # Windows 定时任务入口（每日 09:00 / 12:00 / 18:00）
    ├── config_loader.py              # 配置加载器
    └── pymysql/                      # 打包的纯 Python MySQL 驱动
```

## 三、部署必做（仅一步）

编辑 `config/time_tracking_config.yaml`，设置（**智慧记有三个子业务线，须填子业务线全称，不可填统称"智慧记"**）：

```yaml
default_biz_line: "智慧记+运营系统"   # 或 AI进销存 / 智慧记零售
```

支持的业务线及编码：

| 编码 | 业务线 |
|------|--------|
| XD | 效贷 |
| JWY | 泾渭云 |
| XR | 效融 |
| XXD | 小贷 |
| ZHJ | 智慧记+运营系统 |
| AIJXC | AI进销存 |
| ZHJLS | 智慧记零售 |
| AILIT | 国际版Ailit |

> 若未设置，脚本运行时会明确报错提示，不会静默写入错误业务线。

## 四、快速开始

```bash
# 1. 记录一条节省时间（花名册校验 + 写入本地 JSONL）
python scripts/record_time_saved.py \
  --employee "詹惠英" \
  --user-story "PRJ-00888888-【智慧记】测试需求" \
  --step "文档整理" --step-code "01" \
  --hours 4 --biz-line "智慧记+运营系统"

# 2. 生成分析报告（HTML，内置筛选面板）
python scripts/generate_time_analytics.py --biz-line "智慧记+运营系统"

# 3. 生成个人报告
python scripts/generate_time_analytics.py --biz-line "智慧记+运营系统" --person "詹惠英"

# 4. MySQL 初始化（首次会话由 AI 自动完成；手动方式：需管理员告知数据库密码）
python scripts/init_mysql_config.py --biz-line "智慧记+运营系统" --password "xxx" --no-interactive --employee "詹惠英" --quiet

# 5. 手动同步到 MySQL（幂等；日常由定时任务 09:00/12:00/18:00 自动执行）
python scripts/sync_to_mysql.py --biz-line "智慧记+运营系统"
```

## 五、核心概念

### 业务线（biz_line）
- 每条业务线的数据隔离存储在 `~/.workbuddy/data/time-tracking/{biz_line}/`
- 脚本通过 `--biz-line` 参数指定；未指定时读取 `default_biz_line`
- `agent_team_roster` 每行只有中文 `biz_line`；脚本按员工聚合多行后，在运行时派生 `biz_line_code` 数组供身份确认选择

### 身份验证
- 会话开始时 AI 查询 MySQL `agent_team_roster` 表，盲输入姓名精确匹配
- 表内不读取 `biz_line_code`；编码由 `biz_line_helper.py` 根据中文 `biz_line` 派生
- `record_time_saved.py` 每次保存前硬校验姓名、在职状态和所选中文业务线归属；查询失败或校验失败直接拒绝写入并提示联系管理员，无 fallback、无跳过参数
- 会话启动时 AI 自动检查 `mysql_config.json`：缺失则向用户索要密码并**自动调用 `init_mysql_config.py` 完成初始化**（无需手动开 CMD）；配置或花名册连接恢复前可以继续非追踪工作，但不得保存任何时间记录

### ③/④会话记录与合并
- “生成用例（06）”必须传 `--session-id`；③、④各自都允许独立记录
- 同一会话依次完成③和④时，④复用③的标识并传 `--merge-existing`，累计为同一条记录；不同会话不得合并
- ③保存后原样展示脚本的继续④提醒；④找不到同会话③记录时，脚本将④独立保存

### 存储模式（storage_mode）
- `mysql`（默认）：身份校验通过后写本地 JSONL + 定时任务同步共享 MySQL，供团队汇总
- `local`：仅改变时间数据的存储/同步方式；保存前仍必须连接 MySQL 完成身份及业务线校验
- `excel`：本地 JSONL + Excel 文件（可选附加）

## 六、详细执行规则

AI 在每个步骤完成后如何收集时间、如何生成报告，详见 `prompts/time_tracking.md`。
该文件是给 AI 读的执行规则，测试人员无需关心。

## 七、依赖说明

| 依赖 | 用途 | 是否需要安装 |
|------|------|------------|
| pymysql | MySQL 同步 | 否（已打包进 scripts/pymysql/） |
| openpyxl | Excel 同步（可选） | 是（`pip install openpyxl`） |
| PyYAML | 花名册解析 | 否（有简易解析兜底） |

> 本 Skill 为 MySQL-only，**不依赖腾讯文档连接器**。

## 八、宿主环境适配（双场景）

本 Skill 同时支持两类使用场景，数据最终都同步到**同一张 MySQL 表**（`agent_time_tracking`，
按 `biz_line_code` 区分业务线）：

| 场景 | 形态 | 驱动入口 | 报告展示方式 |
|------|------|---------|------------|
| **WorkBuddy 测试专家** | 智能体（agent） | `agent.md` + 内嵌本 Skill | 调用 `present_files` 在右侧面板打开 HTML 预览 |
| **IDE skill 套件** | 纯 Skill 包 | `SKILL.md`（VSCode / OpenCode / Claude Code 等可加载） | 回复中给出报告文件完整路径，用户用浏览器打开 |

> - **脚本层完全宿主无关**：全部脚本是纯命令行（`.py` / `.bat`），两类场景共用，无需重复开发
> - **记录链路一致**：每步时间 → 本地 `records.jsonl` → `sync_to_mysql.py`（定时任务 09:00/12:00/18:00）→ 共享 MySQL
> - **幂等键兼容**：`record_key = MD5(biz_line_code|employee|user_story|step_code|timestamp)`，同表并存不冲突
> - **本机配置共用**：`mysql_config.json` 是本机私有配置，同一台电脑两种工具共用一份
