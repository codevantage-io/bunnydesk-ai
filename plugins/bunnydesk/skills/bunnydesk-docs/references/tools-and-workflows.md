# BunnyDesk MCP tools and workflows

The connection is account-scoped. Only `list_sites` and `create_site` omit `site_id`; every other tool requires a site the authenticated user administers.

## Current tool inventory

| Area | Tool | Use and important behavior |
|---|---|---|
| Account | `list_sites` | Discover every accessible site and its `site_id`. Start here. |
| Account | `create_site` | Create an empty scratch site from a display name. |
| Site | `get_site_info` | Read identity, URL, page counts, spaces, pending drafts, and `project_knowledge`. |
| Site | `get_site_config` | Read theme, `brand_config`, `customize_ai`, and `custom_code`. |
| Site | `update_site_config` | Partially update supplied config sections and keys. |
| Pages | `list_pages` | List editable standard pages, publication state, user-draft state, URL, and sidebar presence. Content is omitted. |
| Pages | `get_page` | Read complete Markdown, SEO, and a selected version. `auto` prefers an editable user draft; use `version_uid` for an AI/review draft. |
| Pages | `create_page` | Create a standard page. Requires complete frontmatter/content; publishes by default; does not add navigation. |
| Pages | `update_page` | Replace normal page content or change slug/SEO. Content publishes by default; `publish=false` creates or continues the page's user draft. It does not modify a version selected through `list_drafts`. |
| Pages | `delete_page` | Permanently delete a page, all versions, and its navigation links. |
| Search | `search_pages` | Semantic search over published content only (default 5, maximum 25). Requires workspace AI credits. |
| Drafts | `list_drafts` | List user and AI drafts, including deletion drafts and task context. |
| Drafts | `update_draft` | Replace one exact pending draft by `version_uid` while preserving its task, source, and pending status. |
| Drafts | `approve_draft` | Publish a draft or execute a deletion draft; optional complete content override. |
| Drafts | `reject_draft` | Permanently discard a draft; may delete a never-published page. |
| Navigation | `get_site_navigation` | Read `sidebar`, `navbar`, or `footer`; sidebar also returns a concurrency hash and unlinked pages. |
| Navigation | `update_site_navigation` | Replace one complete navigation section; sidebar requires `base_hash`. |
| Media | `create_media_upload` | Host an image or video and return page-ready Markdown. It does not edit the page. |

Tool input schemas are advertised by MCP. Use those rather than copying or guessing optional fields.

## Page workflows

### Create a page

1. Discover the site and read `get_site_info`.
2. Search and list pages to avoid duplicates.
3. Call `create_page` with a complete document and normally `publish=false`.
4. If media is needed, follow the media workflow below and replace the temporary prose with returned Markdown through `update_page`.
5. Read the sidebar, add the new page UID, and replace the sidebar using the returned hash only when navigation was requested.
6. Read the page and navigation back.

### Edit an existing page

1. Find the page, then call `get_page`. Use `version="published"` when the requested baseline is specifically the live page; `auto` otherwise prefers an editable user draft.
2. Preserve the frontmatter, unrelated body content, SEO, and existing component `blockId` values unless the task changes them.
3. Send the full revised document to `update_page`, normally with `publish=false`.
4. Read back the intended version.

### Review drafts

Use `list_drafts`, then `get_page` with both `page_uid` and `version_uid`. AI-authored drafts are
intentionally not returned by ordinary `auto`/`draft` reads. If the user requests changes, send the
complete revised document to `update_draft` with that `version_uid`; this keeps the same version
pending and preserves its task and source. Do not use `update_page` for a selected review draft,
because it manages the page's separate user draft. Before approval, inspect `is_deletion`. After
approval, report `page_deleted` or any `removed_user_draft_uids`; after rejection, report
`page_deleted` when true.

## Media workflow

Media is page-scoped, so the page must exist first. Choose exactly one mode:

- Remote public image: pass `source_url` alone. BunnyDesk fetches and rehosts PNG, JPEG, GIF, or WebP up to 10 MB. This mode does not accept videos.
- Local image or any video: pass `filename`, `content_type`, and the exact `size_bytes` together. PUT the unchanged bytes to `upload_url` with the returned headers. Images may be up to 10 MB; MP4, QuickTime, and WebM video may be up to 100 MB. Direct upload requires BunnyDesk cloud storage.

When `upload_required=true`, use the returned `markdown` only after the PUT returns 2xx. If the upload fails or the byte size changes, request a new upload URL. Then read the page again and use `update_page` with the complete document. Never use `file://`, localhost/private URLs, `data:` URIs, or a temporary third-party upload as `source_url`.

## Navigation workflow

Read the chosen section immediately before changing it. Remove read-only `page_title` fields and send the complete `navigation` value.

- Sidebar is a list of spaces. Children are page/URL links or categories; use full page UIDs for page targets. Categories support one nested category level. Send the returned `hash` as `base_hash`; on a stale-hash error, read again and reapply the intended edit.
- Navbar is a flat list of links, buttons, or dropdowns; dropdown children are links.
- Footer is an object with columns, social links, and copyright. Social links must use HTTPS.

Array order is display order. Anything omitted from the replacement is deleted.

## Site configuration

Call `get_site_config` first. `update_site_config` accepts any of these partial sections:

- `brand_config`: theme, colors, fonts, logo URL configuration, and image options. Logo file upload remains dashboard-only.
- `customize_ai`: `custom_chat_prompt` and `project_knowledge`. The latter changes only when sent; an empty string clears it.
- `custom_code`: `custom_head_code` and `custom_body_code`. This is the only appropriate location for explicitly requested site-level HTML/JS; raw HTML is not page content.

Within a supplied section, omitted keys remain unchanged. Send only deliberate changes and read the result back.
