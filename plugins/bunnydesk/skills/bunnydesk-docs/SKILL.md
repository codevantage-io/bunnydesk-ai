---
name: bunnydesk-docs
description: Create, edit, review, publish, organize, and style documentation sites through the BunnyDesk MCP server. Use for BunnyDesk pages, drafts, navigation, configuration, media, SEO, redirects, or migrations from another documentation platform.
---

# Operate BunnyDesk documentation

BunnyDesk's MCP server provides the tools; this skill defines the safe workflow and authored format. Follow the user's instructions and the selected site's `project_knowledge`. Do not add installation, account signup, connection, or OAuth instructions to documentation pages.

## Load the relevant guidance

- Read [references/tools-and-workflows.md](references/tools-and-workflows.md) before using BunnyDesk MCP tools. It contains the complete current tool inventory and cross-tool workflows.
- Read [references/page-authoring.md](references/page-authoring.md) before creating, rewriting, or converting page content.

## Orient before changing anything

1. Call `list_sites`. Reuse the intended site; create one only when the request or repository clearly implies that outcome. Otherwise ask for its name before `create_site`.
2. Pass the returned `site_id` to every site-scoped tool. A connection may administer multiple sites; never infer a site from prior calls.
3. Call `get_site_info` before substantial work and apply its `project_knowledge`.
4. Before creating or editing content, use `search_pages` to locate related published pages. Because search excludes drafts and may be unavailable without AI credits, use `list_pages` when drafts or a complete inventory matter.
5. Read an existing page with `get_page` before changing it. `update_page` replaces any supplied document; omit `content_markdown` for metadata-only changes.

Treat tool errors as actionable results. Correct the arguments or workflow; do not retry an unchanged call.

Use site, page, and version UIDs only as tool arguments. In user-facing updates, identify sites by name and pages by title/slug; identify drafts by page title plus task or source.

## Preserve review and publication boundaries

`create_page` and content-bearing `update_page` publish by default. Set `publish=false` unless the user explicitly requests immediate publication or has clearly authorized a workflow whose outcome is a live site.

`publish=false` applies only to content. Slug, SEO, and `noindex` changes made through `update_page` take effect immediately; redirect changes also apply immediately. Avoid combining reviewable content with an unapproved settings change.

For draft review:

1. Call `list_drafts`.
2. Read the candidate with `get_page(page_uid=..., version_uid=...)`.
3. Approve or reject only when the user authorized that disposition.

`approve_draft` may permanently delete a page when `is_deletion=true`, and it may remove competing user drafts. `reject_draft` is irreversible and may remove a never-published page. Report these outcomes. Before `delete_page`, confirm unless the current request explicitly names the exact page and authorizes permanent deletion.

Do not attempt to modify API-reference pages: BunnyDesk manages them in the dashboard.

## Preserve replacement-style data

- `content_markdown` is the complete page document.
- `seo_metadata` replaces the complete SEO object. Read and resend all keys that must remain.
- Share images use `seo_metadata.image`; `noindex=true` excludes indexing. Follow the reference's share-image upload workflow without changing the article body.
- Navigation updates replace an entire navigation section. Always read, modify, and send the complete value. Sidebar updates also require the latest returned `hash` as `base_hash`.
- Site configuration updates are partial by section and key. Read first, then send only intended changes.
- Preserve existing component `blockId` values exactly. Never invent them.

## Finish with a read-back

After mutation, verify the affected resource with its corresponding read tool. For multi-step work, also confirm that pages are in the intended sidebar location, internal links use BunnyDesk-returned targets, uploaded media is hosted by BunnyDesk, and any content meant for review remains a draft.
