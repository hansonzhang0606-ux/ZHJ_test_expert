---
name: svn-archive
description: Upload test-case XMind files (AI version + reviewed version) and review report to SVN for project archival. Creates a v{version} folder under the SVN retail test-case path and imports files via `svn mkdir` + `svn import`. Only upload (import/add/commit) is allowed — never delete. This skill should be used when the user needs to archive test cases to SVN, upload to SVN, 归档到SVN, 上传用例到SVN. Triggers include "上传SVN", "SVN归档", "归档用例", "svn archive".
agent_created: true
---

# SVN Archive Skill

## Overview

Upload test-case artifacts (AI XMind, reviewed XMind, review report) to SVN for project archival. Creates `v{version}/` folder under the SVN retail test-case path and imports files. **Upload-only** — never delete.

## When to Use

- User asks to archive test cases to SVN / 上传SVN / SVN归档
- Project end (⑦ 项目归档 step): upload ai.xmind + reviewed.xmind + 评审报告.md
- User mentions "上传用例到SVN", "归档到SVN", "svn archive"

## Prerequisites

1. **SlikSVN installed**: `C:\Program Files\SlikSVN\bin\svn.exe` (add to PATH optional; script uses full path)
2. **SVN credentials cached**: run `svn info <URL> --username <user> --password <pass>` once to cache; subsequent calls are passwordless. Credentials NOT stored in this skill.
3. **SVN server reachable**: `http://192.168.204.100` (intranet)
4. **Files to upload exist**: ai.xmind / reviewed.xmind / 评审报告.md in `最新需求/{标题}/`

## SVN Target Path

```
http://192.168.204.100/svn/zhihuiji/trunk/doc/05测试文档/测试用例/零售版/v{版本}/
```
(URL-encoded in script: `05%e6.../%e9%9b%b6%e5%94%ae%e7%89%88/`)

## ⚠️ Safety Rules (Mandatory)

| Rule | Description |
|------|-------------|
| **Upload-only** | Only `svn mkdir` + `svn import` allowed. NEVER use `svn delete` |
| **Auto-execute upload** | AI lists files + target path and executes upload automatically; no manual confirmation required |
| **No credential storage** | Passwords are NOT stored in skill/memory; rely on svn auth cache |
| **去重跳过** | 上传前先 `svn info` 检查文件是否已存在于 SVN，已存在则跳过（去重），不删除重传 |

## Workflow

### Step 1: Locate files to upload

Default file set (from `最新需求/{标题}/`):
- `{标题}_测试用例_详细版_v1.0-ai.xmind` (AI 生成版)
- `{标题}_测试用例_详细版reviewed.xmind` (评审版)
- `{标题}_评审报告.md` (评审报告)

### Step 2: Determine version

Extract version from requirement title (e.g. "智慧记零售版本 V1.6.1" → `v1.6.1`). Confirm with user if ambiguous.

### Step 3: Check SVN target folder

`svn info <base_url>/v{version}/` — check if folder exists.
- Exists → skip mkdir, import files directly
- Not exists → `svn mkdir -m "创建 v{version} 归档目录"` first

### Step 4: List files and auto-execute upload

**AI lists:**
- Files to upload (path + size)
- Target SVN path
- Whether mkdir is needed

Then executes the upload immediately (upload-only, deduplicated). No manual confirmation required.

### Step 5: Execute upload

For each file: `svn import <local_file> <target_url>/<filename> -m "归档 v{version}: <filename>"`

Report success/failure per file.

## Using the Script

```bash
PYTHON="py -3"
SCRIPT=".qwen/skills/svn-archive/scripts/svn_upload.py"

$PYTHON "$SCRIPT" \
  --version v1.6.1 \
  --files "file1.xmind" "file2.xmind" "file3.md"
```

Arguments:
- `--version` (required): e.g. `v1.6.1` (target folder = `v1.6.1/`)
- `--files` (required): one or more local file paths to upload
- `--base-url` (optional): SVN base URL (defaults to retail test-case path)

> The script performs `svn mkdir` (if needed) + `svn import` only. It does NOT delete. Credentials rely on svn auth cache (passwordless after first cache).

## Output

- Each file uploaded to `零售版/v{version}/<filename>` in SVN
- Console reports per-file success/failure + final SVN revision

## Notes

- If a file already exists in SVN (checked via `svn info` before upload), skip it (dedup) — do NOT delete & reupload.
- SlikSVN path: `C:\Program Files\SlikSVN\bin\svn.exe` (script uses this full path; add to PATH for convenience).
- First-time setup: run `svn info <URL> --username huiying_zhan --password <pass>` once to cache credentials.

## 时间追踪

上传归档完成后按 `../time-tracking-skill/references/zhj-eight-stage-workflow.md` 立即记录“SVN 归档上传（08）”；完成记录前不得进入下一步。
