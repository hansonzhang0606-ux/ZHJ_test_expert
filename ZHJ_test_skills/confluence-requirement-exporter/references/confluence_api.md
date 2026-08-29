# Confluence REST API Reference

## Base URL

Kingdee Confluence: `https://finkms.kingdee.com`

## Authentication

Cookie-based authentication. Pass the full cookie string in the `Cookie` HTTP header.

Key cookie fields:
- `JSESSIONID` - Servlet session ID
- `seraph.confluence` - Confluence authentication token (format: `userID%3Ahash`)

## Endpoints

### 1. Get Page Content / Title

```
GET /rest/api/content/{pageId}?expand=title
```

**Response:**
```json
{
  "id": "85146953",
  "type": "page",
  "title": "零售版V1.1 收银/订单/会员/营销",
  "space": {...},
  "version": {...},
  "_links": {
    "webui": "/pages/viewpage.action?pageId=85146953",
    "self": "https://finkms.kingdee.com/rest/api/content/85146953"
  }
}
```

### 2. Export Page as Word

```
GET /exportword?pageId={pageId}
```

**Response:**
- Content-Type: `application/vnd.ms-word;charset=UTF-8`
- Format: MHTML (MIME HTML) - multipart/related document
- Starts with MIME headers: `Date:`, `Message-ID:`, `MIME-Version: 1.0`
- Contains `Content-Type: multipart/related; boundary=...`
- Inside: `text/html` part with Word XML namespaces (`xmlns:o`, `xmlns:w`, etc.)

**Important:** The MHTML format is HTML-based but is a valid Word document. Do not treat the presence of `<html>` as an error/login page.

### 3. Get Page Attachments

```
GET /rest/api/content/{pageId}/child/attachment?limit={limit}&start={start}
```

**Parameters:**
- `limit` - Number of results per page (default: 25, max: 200)
- `start` - Start index for pagination (default: 0)

**Response:**
```json
{
  "results": [
    {
      "id": "att85146954",
      "type": "attachment",
      "title": "image2025-7-23_9-48-56.png",
      "metadata": {
        "mediaType": "image/png"
      },
      "extensions": {
        "fileSize": "54983",
        "mediaType": "image/png"
      },
      "_links": {
        "download": "/download/attachments/85146953/image2025-7-23_9-48-56.png?version=1&modificationDate=1753235336000&api=v2",
        "self": "https://finkms.kingdee.com/rest/api/content/att85146954"
      }
    }
  ],
  "_links": {
    "next": "/rest/api/content/85146953/child/attachment?limit=200&start=200",
    "self": "..."
  }
}
```

**Pagination:** If `_links.next` exists, there are more results. Follow the next link to get the next page.

### 4. Download Attachment

```
GET {download_link}
```

Where `download_link` is the value from `_links.download` in the attachment response. Prepend `BASE_URL` if it starts with `/`.

**Full URL example:**
```
https://finkms.kingdee.com/download/attachments/85146953/image2025-7-23_9-48-56.png?version=1&modificationDate=1753235336000&api=v2
```

**Response:** Binary file content (the actual attachment file).

## Error Handling

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Process response |
| 401 | Unauthorized | Cookie expired - re-authenticate |
| 403 | Forbidden | No permission to access page |
| 404 | Not Found | Invalid pageId or attachment |
| 500 | Server Error | Retry or contact admin |

## Login Page Detection

If the cookie is expired, Confluence returns an HTML login page (HTTP 200) instead of the expected content. Detect this by:

1. **REST API responses**: Check if response is valid JSON. If it's HTML, cookie is expired.
2. **File downloads**: Check if first 500 bytes contain `<html` and `login`/`password` keywords.
3. **Word export**: The MHTML format contains `<html>` but also contains `MIME-Version` and `multipart/related` - do NOT flag as login page.

## File Size Considerations

- Word exports can be 5-25 MB for pages with many images
- Total attachment size can be 10-300 MB depending on content
- Allow sufficient time for downloads (use 60s timeout per request)
- For large pages, consider downloading attachments in parallel (though sequential is more reliable)
