# 智慧记运营测试套件时间追踪 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为智慧记运营测试套件八个阶段提供多业务线、MySQL 同步的节省工时追踪能力，并生成 IDE 与 WorkBuddy 安装包。

**Architecture:** 复用 time-tracking-skill 的本地 JSONL 与 MySQL 同步链路，扩展步骤配置和记录脚本的会话内合并语义。八个现有 Skill 与 META 工作流均引用同一份追踪规则；两个宿主包只在入口和展示方式上不同。

**Tech Stack:** Markdown Skill instructions, Python 3.8+ standard library, bundled PyMySQL, PowerShell ZIP packaging.

**Spec:** `docs/superpowers/specs/2026-08-28-zhj-time-tracking-design.md`

## Global Constraints

- 身份验证始终读取 MySQL `agent_team_roster`，不读取本地 YAML 花名册。
- 多业务线成员必须编号选择；不得将业务线写死为 ZHJ。
- 时间数据先本地 JSONL、再 09:00/12:00/18:00 幂等同步至 `agent_time_tracking`。
- MySQL 密码与 `mysql_config.json` 不得进入任何包。
- 八步均收集时间；③与④仅保留一条 `06` 记录并累计三项时长。

---

### Task 1: 建立八步时间映射与合并记录行为

**Files:**
- Create: `ZHJ_test_skills/time-tracking-skill/tests/test_record_time_saved.py`
- Modify: `ZHJ_test_skills/time-tracking-skill/scripts/record_time_saved.py`
- Modify: `ZHJ_test_skills/time-tracking-skill/config/time_tracking_config.yaml`

**Interfaces:**
- Produces: `record(..., merge_existing=False)`；当 `merge_existing=True` 时更新同会话员工、故事、步骤、业务线的最后一条记录。

- [ ] **Step 1: Write the failing test**

```python
def test_merge_existing_accumulates_stage_three_and_four(tmp_path, monkeypatch):
    first = record('李静', 'PRJ-1 示例', '生成用例', '06', hours=2, biz_line='智慧记+运营系统', skip_validation=True)
    merged = record('李静', 'PRJ-1 示例', '生成用例', '06', hours=1.5, biz_line='智慧记+运营系统', skip_validation=True, merge_existing=True)
    assert merged['time_saved_hours'] == 3.5
    assert len(read_records('智慧记+运营系统')) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest ZHJ_test_skills/time-tracking-skill/tests/test_record_time_saved.py -v`

Expected: FAIL because `merge_existing` is unsupported.

- [ ] **Step 3: Write minimal implementation**

Add the `--merge-existing` CLI flag and, before appending, replace the latest matching JSONL row using the session/employee/story/step/business-line match. Add codes 00, 05 and 08 plus their reference intervals.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest ZHJ_test_skills/time-tracking-skill/tests/test_record_time_saved.py -v`

Expected: PASS.

### Task 2: 将追踪规则嵌入八个阶段

**Files:**
- Modify: `ZHJ_test_skills/META_WORKFLOW.md`
- Modify: `ZHJ_test_skills/8个Skill简单操作说明.md`
- Modify: eight `ZHJ_test_skills/*/SKILL.md` files
- Modify: `ZHJ_test_skills/time-tracking-skill/SKILL.md`
- Modify: `ZHJ_test_skills/time-tracking-skill/prompts/time_tracking.md`

- [ ] **Step 1: Add the shared session-start protocol**

Require MySQL roster validation and numbered business-line selection before the first workflow action.

- [ ] **Step 2: Add the shared completion protocol**

Require immediate collection, direct save, and no next-step option before recording; use `--merge-existing` at stage ④ only.

- [ ] **Step 3: Verify the package has all eight mappings**

Run a Python validation script that loads the YAML mapping and confirms codes `00,01,02,05,06,07,08` and eight workflow references.

### Task 3: Produce host-installable packages

**Files:**
- Create: `deliverables/ZHJ_test_skills_IDE.zip`
- Create: `deliverables/ZHJ_test_skills_WorkBuddy.zip`
- Create: `deliverables/安装说明.md`

- [ ] **Step 1: Build IDE ZIP**

Package `ZHJ_test_skills/`, including time-tracking-skill and excluding local credentials.

- [ ] **Step 2: Build WorkBuddy ZIP**

Create WorkBuddy expert metadata, registration scripts, and a copied skill suite; package them without local credentials.

- [ ] **Step 3: Validate archives**

List both ZIP contents; assert expected entries exist and reject `mysql_config.json`, `records.jsonl`, and `.git` entries.
