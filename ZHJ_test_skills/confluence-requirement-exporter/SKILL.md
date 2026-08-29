---
name: confluence-requirement-exporter
description: Export Confluence requirement pages to Word documents and download all attachments. Supports two modes - original requirements (zip attachments) and latest requirements (raw images in folder). This skill should be used when the user needs to export a Confluence page as Word with attachments, archive Confluence content locally, or download requirement documents and images. Triggers include "导出Confluence需求", "下载Confluence页面为Word", "导出原需求", "导出最新需求", "下载需求附件", "export Confluence page".
agent_created: true
---

# Confluence Requirement Exporter

## Overview

Export Confluence requirement pages to Word documents and download all attachments. Designed for Kingdee Confluence instances (finkms.kingdee.com) using Cookie-based authentication. Supports two export modes for different requirement types.

## When to Use

- User provides a Confluence page URL (containing `pageId`) and asks to export it as Word
- User needs to download all attachments from a Confluence page
- User mentions "导出原需求", "导出最新需求", "下载Confluence", "需求文档下载", "旧需求：", "新需求："
- User wants to archive a Confluence requirement document with its images

## Chat Input Protocol (primary usage — no file editing needed)

The user does NOT need to edit any config. They just type in chat. Parse the input and call the script with CLI args.

### Input format the user uses

**With cookie (full self-contained request):**
```
cookie: <paste full cookie string>
旧需求：https://finkms.kingdee.com/pages/viewpage.action?pageId=91076209
```
or
```
cookie: <paste full cookie string>
新需求：https://finkms.kingdee.com/pages/viewpage.action?pageId=100658642
```

**Authentication priority: username/password (Basic Auth) > cookie**

**Account/password (recommended, persistent, never expires):**
- The script auto-reads `~/.workbuddy/confluence_auth.json` (username + password_base64). If present, uses Basic Auth — no cookie needed.
- **First-time setup**: if the user sends `配置confluence：账号=xxx, 密码=yyy`, AI creates `~/.workbuddy/confluence_auth.json` with the password base64-encoded. One-time setup; subsequent exports are passwordless.
- Password is base64-encoded (not plaintext); the file lives in the user home dir (not in the project path), so it does NOT leak when the project is copied to another machine.

**Cookie (fallback, expires):**
- If the user provides a cookie in the message, use it (most recent wins).
- If no cookie and no auth config, ask the user to either send `配置confluence：账号=xxx, 密码=yyy` or provide a cookie.
- Cookie expires after hours of inactivity; never assume an old cookie is still valid.

### How to parse

1. **Mode**: 
   - "旧需求" / "原需求" / "历史需求" → `ORIGINAL`
   - "新需求" / "最新需求" → `LATEST`
   - If neither keyword present but the URL is given, ask which mode, OR infer: prefer the explicit keyword; default to asking if ambiguous.
2. **pageId**: extract from `pageId=` in the URL. Also accept a bare pageId.
3. **cookie**: take the value after `cookie:` / `Cookie:` in the message. It may be a full `key=value; key2=value2` string.
4. **配置confluence (first-time setup)**: if the message matches `配置confluence[:：]\s*账号\s*=\s*(.+?)\s*,\s*密码\s*=\s*(.+)`, AI creates `~/.workbuddy/confluence_auth.json` with `{"username":"<account>","password_base64":"<base64 of password>","note":"Confluence Basic Auth credentials"}` (base64-encode the password), then confirms "✅ 配置完成，后续导出免密". No export is performed in this step.

### How to invoke (AI runs this)

```bash
PYTHON="py -3"
SCRIPT=".qwen/skills/confluence-requirement-exporter/scripts/export_confluence.py"

$PYTHON "$SCRIPT" --page-id 91076209 --cookie "<cookie string>" --mode ORIGINAL
```

- `--mode ORIGINAL` for 旧需求/原需求
- `--mode LATEST` for 新需求/最新需求
- Quote the cookie string; it contains `;` and `=` which must be passed as one argument.

### After export

- Report the output paths (Word doc + zip for ORIGINAL; folder + images/ for LATEST).
- If the run failed with a login page, tell the user the cookie expired and ask them to re-paste a fresh cookie via F12.

## Two Export Modes

### Mode 1: Original Requirement (原需求)

For archiving original/historical requirement documents.

```
.qwen/knowledge-base/requirements/
├── 原需求/
│   └── {title}.doc              ← Word document
└── 原图片/
    └── {title}.zip              ← All attachments zipped (original filenames preserved)
```

### Mode 2: Latest Requirement (最新需求)

For current/latest requirement documents with structured directory.

```
最新需求/
└── {title}/                     ← Folder named after page title
    ├── {title}.doc              ← Word document
    └── images/                  ← Attachments as raw files (NOT zipped)
        ├── image2026-XX.png
        └── ...
```

**Key difference**: Original mode zips attachments; Latest mode stores them as raw files in an `images/` subfolder.

## Prerequisites

1. **Cookie**: Obtain the Confluence authentication cookie from the browser. Key cookie fields:
   - `JSESSIONID` - Session identifier
   - `seraph.confluence` - Confluence authentication token
2. **Page URL or Page ID**: The Confluence page URL or just the pageId.
3. **Export Mode**: Determine whether it's an original or latest requirement.

## Determining Export Mode

- If user says "原需求" or provides a historical requirement URL → **Mode 1 (Original)**
- If user says "最新需求" or provides a current/latest requirement URL → **Mode 2 (Latest)**
- If unclear, ask the user which mode to use

## Workflow

### Step 1: Parse the Page URL and Extract pageId

Extract the `pageId` from the Confluence URL. Example:
- URL: `https://finkms.kingdee.com/pages/viewpage.action?pageId=85146953`
- pageId: `85146953`

### Step 2: Get the Page Title (for file/folder naming)

```
GET {BASE_URL}/rest/api/content/{pageId}?expand=title
```
The `title` field in the JSON response is used as the base name for output files and folders.

### Step 3: Export the Page as Word

```
GET {BASE_URL}/exportword?pageId={pageId}
```
- Response Content-Type: `application/vnd.ms-word;charset=UTF-8`
- Response format: MHTML (MIME HTML) - Confluence's standard Word export format
- Save with `.doc` extension

**Important**: Do NOT treat the MHTML response as a "login page" just because it contains `<html>`. The MHTML format starts with `Date:` / `Message-ID:` / `MIME-Version:` headers and is a valid Word document.

### Step 4: Get the Attachment List

```
GET {BASE_URL}/rest/api/content/{pageId}/child/attachment?limit=200&start={start}
```
Response contains a `results` array. Each attachment has:
- `title` - original filename (e.g., `image2025-7-23_9-48-56.png`)
- `_links.download` - relative download path

Use pagination (`_links.next`) if more than 200 attachments.

### Step 5: Download Attachments (mode-dependent)

**Mode 1 (Original)**: Download all attachments, package into a single zip file preserving original filenames.

**Mode 2 (Latest)**: Download all attachments as raw files directly into the `images/` subfolder, preserving original filenames. No zip.

### Step 6: Sanitize Filenames

**Windows filename restrictions**: `\ / : * ? " < > |` are NOT allowed.

Replace all forbidden characters with `_` (underscore). This applies to:
- Word document filename
- Zip filename (Mode 1)
- Folder name (Mode 2)

Example: `零售版V1.1 收银/订单/会员/营销` → `零售版V1.1 收银_订单_会员_营销`

### Step 7: Save Files to Specified Directories

**Mode 1 (Original)**:
- Word document → `原需求\{safe_title}.doc`
- Attachment zip → `原图片\{safe_title}.zip`

**Mode 2 (Latest)**:
- Create folder → `最新需求\{safe_title}\`
- Word document → `最新需求\{safe_title}\{safe_title}.doc`
- Attachments → `最新需求\{safe_title}\images\{original_filename}`

## Using the Script

The script `scripts/export_confluence.py` automates the entire workflow.

### Preferred: pass everything via CLI (no editing)

```bash
python export_confluence.py --page-id 91076209 \
    --cookie "JSESSIONID=...; seraph.confluence=..." \
    --mode ORIGINAL
```

Arguments:
- `--page-id` — Confluence pageId (required)
- `--cookie` — full cookie string (required; expires frequently)
- `--mode` — `ORIGINAL` or `LATEST` (default `ORIGINAL`)
- `--base-url` — override Confluence base URL (default `https://finkms.kingdee.com`)

### Optional: edit config as defaults

The top of the script has project-specific paths (`WORD_OUTPUT_DIR`, `ATTACHMENT_OUTPUT_DIR`, `LATEST_REQ_BASE`, `BASE_URL`) and fallback defaults (`DEFAULT_PAGE_ID`, `DEFAULT_COOKIE_STR`, `DEFAULT_MODE`). CLI args always override these. Only edit this section when deploying to a different machine/workspace.

## Cookie Acquisition

1. Open the Confluence page in a browser (Chrome/Edge)
2. Press F12 → Network tab → Refresh page
3. Click the main document request
4. Copy the `Cookie` header value from Request Headers

**Cookie expiration**: Cookies (especially `JSESSIONID`) expire after hours of inactivity. If the API returns HTML login pages instead of JSON, the cookie has expired.

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| API returns HTML login page | Cookie expired | Re-obtain cookie from browser |
| 404 on REST API | Invalid pageId or no access | Verify pageId and permissions |
| Word export flagged as "login page" | MHTML contains `<html>` | Normal - MHTML is HTML-based Word format |
| `FileNotFoundError` creating zip/folder | Filename contains `/` | Replace `/` with `_` (automatic via sanitize_filename) |
| 0 attachments found | No attachments or pagination needed | Check `?limit=200` and `_links.next` |

## Resources

### scripts/
- `export_confluence.py` - Main script supporting both ORIGINAL and LATEST export modes

### references/
- `confluence_api.md` - Confluence REST API reference for page export and attachment operations

## 时间追踪

交付后按 `../time-tracking-skill/references/zhj-eight-stage-workflow.md` 立即记录“导出需求（00）”；完成记录前不得进入下一步。
