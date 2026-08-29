# 智慧记运营测试专家 GitHub 首次发布 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将源码和目录安全推送到 GitHub，同时排除所有 ZIP/RAR、生成物、运行数据和凭据。

**Architecture:** 当前工作目录初始化为跟踪远程 `main` 的普通 Git 仓库，保留远程初始历史。根目录 `.gitignore` 负责长期阻止压缩包、生成目录和本机运行数据进入版本控制；首次提交只暂存明确允许的源码与文档目录。

**Tech Stack:** Git、GitHub HTTPS、PowerShell、Python unittest/AST

**Spec:** `docs/superpowers/specs/2026-08-29-github-publish.md`

## Global Constraints

- 不提交任何 `*.zip` 或 `*.rar`。
- 不提交 `deliverables/`。
- 不提交 `mysql_config.json`、`records.jsonl`、`.env*`、私钥或凭据。
- 保留远程 `main` 的既有历史，禁止强推。

---

### Task 1: 建立长期安全边界

**Files:**
- Create: `.gitignore`
- Preserve: `README.md`

**Interfaces:**
- Consumes: 本地源码目录与远程 `main`
- Produces: 后续同步共用的忽略规则

- [ ] **Step 1: 创建 `.gitignore`**

加入压缩包、生成目录、运行配置、运行记录、缓存、凭据和编辑器临时文件规则。

- [ ] **Step 2: 初始化本地仓库并接入远程历史**

运行：

```powershell
git init
git remote add origin https://github.com/hansonzhang0606-ux/ZHJ_test_expert.git
git fetch origin main
git checkout -b main --track origin/main
```

预期：本地 `main` 跟踪 `origin/main`，远程 README 保留。

### Task 2: 暂存并验证发布内容

**Files:**
- Add: `ZHJ_test_skills/**`（忽略的压缩包除外）
- Add: `docs/**`
- Add: `.gitignore`

**Interfaces:**
- Consumes: Task 1 的忽略规则
- Produces: 可审计的 Git 暂存区

- [ ] **Step 1: 运行回归测试与 AST 检查**

运行：

```powershell
python -m unittest discover -s .\ZHJ_test_skills\time-tracking-skill\tests -p test_*.py -v
python -c "import ast,pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('ZHJ_test_skills').rglob('*.py')]"
```

预期：测试零失败，全部 Python 文件可解析。

- [ ] **Step 2: 仅暂存允许目录**

运行：

```powershell
git add .gitignore README.md ZHJ_test_skills docs
```

- [ ] **Step 3: 审核暂存清单**

确认 `git diff --cached --name-only` 不包含 ZIP/RAR、`deliverables/`、运行配置或记录文件。

### Task 3: 提交、推送并远程复核

**Files:**
- Commit: Task 2 的已审核文件

**Interfaces:**
- Consumes: 已验证的暂存区
- Produces: GitHub `main` 上可持续更新的源码仓库

- [ ] **Step 1: 创建首次源码提交**

```powershell
git commit -m "feat: publish ZHJ testing expert skill suite"
```

- [ ] **Step 2: 推送到远程 `main`**

```powershell
git push -u origin main
```

- [ ] **Step 3: 远程复核**

运行 `git fetch origin main`、比较本地与远程提交，并用 `git ls-tree -r origin/main` 确认排除项不存在。

