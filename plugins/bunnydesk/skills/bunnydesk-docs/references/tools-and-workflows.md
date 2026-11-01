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
| Pages | `list_pages` | List editable standard/changelog pages: published pages and user drafts. AI-only review pages and API references are excluded. Content is omitted. |
| Pages | `get_page` | Read complete Markdown, SEO, and a selected version. `auto` prefers a user draft; use `version_uid` for a review draft. |
| Pages | `create_page` | Create a standard page. Requires complete frontmatter/content; publishes by default; does not add navigation. |
| Pages | `update_page` | Replace normal page content or change slug/SEO. Content publishes by default; `publish=false` creates or continues the page's user draft. It does not modify a version selected through `list_drafts`. |
| Pages | `delete_page` | Permanently delete a page, all versions, and its navigation links. |
| Search | `search_pages` | Semantic search over published content only (default 5, maximum 25). Requires workspace AI credits. |
| Drafts | `list_drafts` | List pending user/AI versions, including changelogs, deletion drafts, task context. API references are excluded. |
| Drafts | `update_draft` | Replace one exact pending draft by `version_uid` while preserving its task, source, and pending status. |
| Drafts | `approve_draft` | Publish a draft or execute a deletion; optional complete content override. |
| Drafts | `reject_draft` | Permanently discard a draft; may delete a never-published page. |
| Navigation | `get_site_navigation` | Read `sidebar`, `navbar`, or `footer`; sidebar also returns a concurrency hash and unlinked pages. |
| Navigation | `update_site_navigation` | Replace one complete navigation section; sidebar requires `base_hash`. |
| Uploads | `create_media_upload` | `purpose="page_media"` (default) returns image/video Markdown; `purpose="api_reference"` stages a JSON/YAML spec and returns an upload token. |
| API references | `upsert_apireference` | Create/update a published OpenAPI reference from `api_spec_url` or an uploaded-file token. Publishes immediately; no draft stage. |

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

After editing, read the same `version_uid` back. After approving, read `version="published"`
and verify the published `version_uid`. A plain `auto` read can otherwise select a different
pending user draft. `update_draft` rejects published/rejected versions, deletion drafts, and
API-reference specifications.

### Changelog drafts and automatic generation

GitHub merged-PR webhooks independently run knowledge-gap detection and automatic generation
for changelog pages linked to that repository in the same site. Generation starts before any
knowledge-gap assignment to Bunny and adds no extra knowledge-gap entry. Gap detection itself
can produce zero, one, or several topics.

Each received merge immediately creates a separate normal Bunny task for every linked changelog,
even when other drafts are pending. There is no collection window or batch model. The instruction
uses the existing monthly create/update prompts and only that event's PR data. Bunny reads the
target page and saves through its ordinary edit tools, without changing sibling pending drafts.
Automatic webhooks include non-default-branch merges; manual history sync fetches default-branch
merges. No additional webhook-delivery/PR deduplication is provided.

Use the ordinary draft workflow: read the exact version, compare against current published
content, revise with `update_draft` if needed, then approve only when authorized. Publication
replaces the current page content without automatically merging it. There is no changelog-specific
stale flag or approval argument; review sibling drafts individually before publishing them too.

Automatic task creation checks the same workspace balance as knowledge-gap assignment. Without
credits it records a normal failed task and does not call AI or resume automatically after top-up.
Continue through Bunny chat after adding credits. Generation uses the standard agent credit
context, progress, checkpoint retries, stop and error handling. There is no separate changelog
retry button or recovery scheduler.

`list_drafts` lists pending page versions, not background task status: a failed or active task may
have no generated version yet. An unpublished changelog receives an empty working version before
Bunny edits it; do not mistake that placeholder for completed generation. Use dashboard **Drafts**
for progress, errors and follow-up chat. Do not fabricate completed work or poll absent versions.
MCP has no tool to configure changelog sources, trigger sync, or retry generation. Create/sync
through **Site Customization → Changelog**; `create_page` creates a standard page, not a special
changelog page. The plugin does not provide an assistant `/changelog` generation command.

## Media workflow

Use `create_media_upload` with `purpose="page_media"` (also the default). Media is page-scoped,
so the page must exist first. Choose exactly one mode:

- Remote public image: pass `source_url` alone. BunnyDesk fetches and rehosts PNG, JPEG, GIF, or WebP up to 10 MB. This mode does not accept videos.
- Local image or any video: pass `filename`, `content_type`, and the exact `size_bytes` together. PUT the unchanged bytes to `upload_url` with the returned headers. Images may be up to 10 MB; MP4, QuickTime, and WebM video may be up to 100 MB. Direct upload requires BunnyDesk cloud storage.

When `upload_required=true`, use the returned `markdown` only after the PUT returns 2xx. If the upload fails or the byte size changes, request a new upload URL. Then reread the content and save the complete document: `update_draft` for a selected review version, or `update_page` for a normal user edit. Never use `file://`, localhost/private URLs, `data:` URIs, or a temporary third-party upload as `source_url`.

## API-reference workflow

Use `upsert_apireference` for OpenAPI/Swagger specifications; never send them as Markdown.
Create with `title` and `slug`, or update an existing reference using its `page_uid`. Updates may
change title/slug alone, or replace the specification. Omitted fields stay unchanged. References
publish immediately; there is no `publish=false` or draft review step. Do not convert an ordinary
page into an API reference. Navigation is a separate operation when requested.

Require authorization for the immediate live effect, including title/slug-only updates. If the
user asked to keep everything in drafts, explain that API references cannot satisfy that request
and obtain a decision before calling `upsert_apireference`. Do not silently publish or create a
Markdown placeholder as if it were an API reference.

- Public spec URL: pass `api_spec_url` directly to `upsert_apireference`. The backend fetches and
  validates the specification using the dashboard rules.
- Local file: call `create_media_upload` with `purpose="api_reference"`, base `filename`, matching
  JSON/YAML `content_type`, and exact `size_bytes` (maximum 10 MB). Omit `page_uid`, `source_url`,
  and `alt_text`. PUT the unchanged bytes with returned headers. After PUT returns 2xx, call
  `upsert_apireference` with the returned `upload_token` and creation/update fields. The backend
  checks actual size and validates the specification before publishing. This upload returns no
  Markdown; it does not create or publish a page itself.

For JSON use `.json` with `application/json`; for YAML use `.yaml`/`.yml` with
`application/yaml` or a JSON/YAML MIME alias advertised by the tool. Follow the returned `method`,
`headers`, and `expires_in`. The upload token is bound to the requesting site and user and expires;
do not reuse it for another site/account. MCP requests are limited to 1 MB, so file bytes go to
the presigned PUT URL, not into the tool arguments. An upload that succeeded is still only staging
until the backend validates it and `upsert_apireference` returns a successful published result.

Use exactly one spec input: URL or upload token. Never expose a local file at a temporary public
URL. On an invalid/expired token or size mismatch, request a new upload. Retain the successful
upsert's `page_uid`, `version_uid`, publication status, and public URL for verification and future
updates: API references are excluded from ordinary MCP discovery. For later updates without that
UID, obtain it from the dashboard rather than selecting a similarly named Markdown page. On a
schema/encoding validation error, correct the spec before resubmitting; a missing upload requires
the PUT, not an unchanged finalization retry. An ambiguous create result should be checked in the
dashboard before repeating creation. No MCP tool exports the stored spec for a read-back.

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
