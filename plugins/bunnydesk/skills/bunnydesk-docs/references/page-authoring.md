# BunnyDesk page authoring

## Complete document contract

Every `content_markdown` value is a complete document with YAML frontmatter and a body:

```markdown
---
title: "Configure webhooks"
summary: "Create and secure webhook endpoints."
---

## Create an endpoint

Choose a stable HTTPS URL that can receive POST requests.
```

`title` and `summary` must both be present; new pages require a non-empty summary. Slug and SEO are tool arguments, not frontmatter. BunnyDesk renders the page title separately, so do not repeat it as `#`; begin page sections at `##`.

## Markdown support

BunnyDesk uses Python-Markdown, not MDX and not GitHub-Flavored Markdown in every respect. Use ordinary headings, paragraphs, emphasis, links, images, blockquotes, ordered/unordered lists, definition lists, fenced code, pipe tables, and supported admonitions.

- Raw HTML is unsupported. Benign tags may appear as text and dangerous tags may be stripped. Use Markdown or the six components below.
- A single newline inside a paragraph becomes a visible break. Do not hard-wrap prose; use blank lines between blocks.
- Use pipe tables with a header and separator row. Keep cells short; merged cells and nested block content are unsupported.
- Use fenced code with only a language token, such as ` ```python `. Titles or filenames after the language are stripped; put them in prose above the fence. Code spans and fences preserve literal component examples.
- Admonitions support `note|info`, `warning|caution`, `danger|error`, and `tip|success`. Indent their body four spaces. They do not work inside components; use `Callout` there.

## Components

Quote every attribute value. Unknown attributes are ignored; unknown `type` values use the component default. Preserve existing `blockId="..."` exactly and never invent one. Do not place headings inside components because they do not receive anchors or enter the page table of contents.

### Callout

```markdown
<Callout type="warning" title="Back up first" icon="triangle-alert" link="/restore-ab12cd34">
Restoring a snapshot overwrites the live database.
</Callout>
```

Types: `info` (default), `warning`, `success`, `tip`. Optional attributes: `title`, Lucide `icon`, and `link`. For a top-level red/destructive notice, use `!!! danger` because `error` is not a Callout type.

### Card

```markdown
<Card type="highlight" title="Quickstart" icon="rocket" link="/start-ab12cd34">
Get online in five minutes.
</Card>
```

Types: `default`, `highlight`, `info`. Optional attributes: `title`, Lucide `icon`, and `link`. A card is clickable only when `link` is set.

### Accordion

```markdown
<Accordion title="What counts as active?" icon="users">
Anyone who signed in during the billing period.
</Accordion>
```

Supported authoring attributes are `title` and Lucide `icon`. Accordions start collapsed; a `collapsed` attribute has no effect.

### Column and Cols

Use `Column` as the grid and one `Cols` wrapper per cell:

```markdown
<Column>
<Cols>
<Card title="Install">Package managers and binaries.</Card>
</Cols>
<Cols>
<Card title="Configure">Environment variables and flags.</Card>
</Cols>
</Column>
```

The renderer derives the count from the `Cols` children, overriding `cols` when children exist. Keep grids to 2–4 cells and never use `Cols` outside `Column`.

### Video

`Video` is the only void component. Prefer the exact self-closing Markdown returned by `create_media_upload`:

```markdown
<Video src="https://cdn.example.com/tour.mp4" caption="Dashboard tour" />
```

`src` is required. Existing videos may also use `caption`/`title`, `autoplay`, `loop`, `muted`, `playsinline`, `controls`, `poster`, `width`, and `height`; preserve them unless changing playback. Do not substitute raw `<video>` or `<iframe>`.

Component bodies cap leading whitespace at three spaces. Use fenced code, indent nested lists by 2–3 spaces, and replace a nested admonition with `Callout`.

## Links and media

For an internal page link, reuse the path from its returned `public_url`, including the trailing short page ID:

```markdown
[Configure billing](/configure-billing-ab12cd34)
```

Use `/` for the site root and complete `https://` URLs externally. Do not invent slug-only paths. The same rule applies to component `link` attributes.

Page images and videos should use BunnyDesk-hosted URLs returned by `create_media_upload`. Images use ordinary Markdown with useful alt text; a Markdown image title renders as a visible caption:

```markdown
![Dashboard overview](https://cdn.example.com/dashboard.png "After first login")
```

PDFs and other documents cannot be embedded as page media; summarize them or link appropriately instead.

## Converting other documentation

| Source construct | BunnyDesk form |
|---|---|
| Note/info, tip/check, warning | `Callout` with `info`, `tip`/`success`, or `warning` |
| Danger/error | Top-level `!!! danger` |
| Card group/grid | `Card` inside `Column` / `Cols` |
| Details/expandable | `Accordion` |
| Tabs/code groups | Consecutive `###` sections with separate fences |
| Steps | Ordered list or one `###` section per step |
| Image frame | Bare Markdown image |
| Source frontmatter | Keep only BunnyDesk `title` and `summary`; pass slug/SEO as tool arguments |

Convert rather than publish platform-specific MDX, directives, imports, snippets, tabs, steps, card groups, GitHub alerts, Mermaid/PlantUML, math, or footnotes literally.

## Pre-write check

- Correct site and `project_knowledge`.
- No duplicate page or overlooked draft.
- Complete frontmatter and body; no repeated `#` title.
- No raw HTML or unsupported platform components.
- Closing tags on `Callout`, `Card`, `Accordion`, `Column`, and `Cols`; self-closing `Video`.
- Quoted attributes, preserved `blockId`, and correctly paired `Column`/`Cols`.
- Bare language tokens on fences; no component-nested headings/admonitions.
- Canonical BunnyDesk internal links and successfully hosted media.
