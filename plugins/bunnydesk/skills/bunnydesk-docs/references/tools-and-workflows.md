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
| Pages | `get_page` | Read complete Markdown, SEO, `noindex`, and a selected version. `auto` prefers an editable user draft; use `version_uid` for an AI/review draft. |
| Pages | `create_page` | Create a standard page. Requires complete frontmatter/content; publishes by default; does not add navigation. |
| Pages | `update_page` | Replace content or change slug, SEO, or `noindex`. Content publishes by default; settings changes are immediate. |
| Pages | `delete_page` | Permanently delete a page, all versions, and its navigation links. Update or remove redirects targeting the page first. |
| Search | `search_pages` | Semantic search over published content only (default 5, maximum 25). Requires workspace AI credits. |
| Drafts | `list_drafts` | List user and AI drafts, including deletion drafts and task context. |
| Drafts | `approve_draft` | Publish a draft or execute a deletion draft; optional complete content override. |
| Drafts | `reject_draft` | Permanently discard a draft; may delete a never-published page. |
| Navigation | `get_site_navigation` | Read `sidebar`, `navbar`, or `footer`; sidebar also returns a concurrency hash and unlinked pages. |
| Navigation | `update_site_navigation` | Replace one complete navigation section; sidebar requires `base_hash`. |
| Media | `create_media_upload` | Host an image or video and return page-ready Markdown. It does not edit the page. |
| Redirects | `list_redirects` | Read the site's rules, rule UIDs, and current destinations. |
| Redirects | `upsert_redirects` | Validate or apply inline rules or CSV mappings, keyed by source path. Defaults to a dry run. |
| Redirects | `delete_redirect` | Delete one site-owned rule by `redirect_uid`. |

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

Use `list_drafts`, then `get_page` with both `page_uid` and `version_uid`. AI-authored drafts are intentionally not returned by ordinary `auto`/`draft` reads. Before approval, inspect `is_deletion`. After approval, report `page_deleted` or any `removed_user_draft_uids`; after rejection, report `page_deleted` when true.

## Media workflow

Media is page-scoped, so the page must exist first. Choose exactly one mode:

- Remote public image: pass `source_url` alone. BunnyDesk fetches and rehosts PNG, JPEG, GIF, or WebP up to 10 MB. This mode does not accept videos.
- Local image or any video: pass `filename`, `content_type`, and the exact `size_bytes` together. Send the unchanged bytes to `upload_url` using the returned `method` (PUT) and `headers`. Images may be up to 10 MB; MP4, QuickTime, and WebM video may be up to 100 MB. Direct upload requires BunnyDesk cloud storage.

When `upload_required=true`, use the returned `markdown` only after the PUT returns 2xx. If the upload fails or the byte size changes, request a new upload URL. For an article embed, read the page again and use `update_page` with the complete document; for a share image, follow the workflow below. Never use `file://`, localhost/private URLs, `data:` URIs, or a temporary third-party upload as `source_url`.

## SEO, indexing, and share images

`get_page` returns these settings, and `update_page` can change them without sending content:

- Use text for `seo_metadata.title` and `description`, and a string list for `keywords`.
- `seo_metadata.image` is the public share-image URL. An empty string restores the site-logo/default fallback.
- `noindex=true` excludes the page from search-engine indexing and the sitemap. Set it to `false` to clear that explicit preference; hidden-page rules may still exclude the page.

Hosted pages generate Open Graph and Twitter tags from these values. Separate OG-specific title and description overrides are not implemented. These settings apply immediately even with `publish=false`.

To upload a new share image:

1. Call `create_media_upload` for the existing page with the image's `filename`, `content_type`, and actual `size_bytes`.
2. Upload the file's bytes to the returned `upload_url` using its `method` and unchanged `headers`. Continue only after a 2xx response.
3. Take the public image URL from the returned `markdown`. The tool does not return a separate `public_url` field; `upload_url` is the temporary upload target, not the share-image URL.
4. Read `get_page` again. Preserve every existing `seo_metadata` key that should remain and set `image` to the uploaded image's public URL.
5. Call `update_page` with that complete `seo_metadata` object, without `content_markdown`, then read back to verify. Uploading alone does not update the page, and a share image does not need a Markdown embed in its body.

## Redirect workflow

1. Call `list_redirects` for the selected `site_id` before changing its rules.
2. Call `upsert_redirects` with either `rules` or `csv_url`, never both. Each inline rule needs `from_path` and exactly one of `target_page_uid` or `target_url`. Page targets must be published on the same site.
3. Preview first with `dry_run=true`, which is the default. Inspect `errors` and the `create`, `update`, and `unchanged` counts; row errors can be returned in a normal tool result.
4. Apply the intended batch with `dry_run=false`. The server validates again and saves the whole batch or nothing. Confirm `applied=true` and empty `errors`, then read the rules back.
5. To remove a rule, pass its `redirect_uid` to `delete_redirect` and verify with `list_redirects`.

Source paths are relative to the site's root. Upserts use the site and normalized source path as the key. CSV files require the ordered header `from_path,to_url`, at most 500 data rows, and at most 1 MB. A CSV must already be available at an accessible public URL; `create_media_upload` accepts images and video, not CSV files.

Each call downloads the CSV again; keep its contents unchanged between preview and apply.

Rules return permanent 301 redirects when requests reach BunnyDesk. Old domains must route to BunnyDesk or have forwarding configured with their provider. Redirect rules are not generated automatically during site import.

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
