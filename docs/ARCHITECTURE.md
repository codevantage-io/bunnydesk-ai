# BunnyDesk agent plugin architecture

## Package boundary

The repository is a marketplace source. The installable package lives at
`plugins/bunnydesk` and has two stable identities:

- plugin: `bunnydesk`
- skill: `bunnydesk-docs`

The portable Agent Plugins files (`plugin.json`, `mcp.json`, `skills/`) are the
primary representation. Client-specific manifests are compatibility adapters;
they must point to the same MCP endpoint and skill instead of maintaining
separate instruction copies.

## Runtime flow

```text
agent client
  -> installs plugins/bunnydesk
  -> loads bunnydesk-docs
  -> connects to https://app.bunnydesk.ai/mcp/
  -> completes browser OAuth with BunnyDesk
  -> lists account sites and selects a site_id
  -> reads before writing; Markdown remains pending unless publication is authorized
```

The plugin contains no application server, proxy, access token, or customer
content. Authorization and tenant isolation are enforced by the hosted
BunnyDesk MCP server.

Review versions are edited by `version_uid` with `update_draft`, preserving their task and pending
status. Normal `update_page(publish=false)` edits the separate user draft. Automatic changelogs
are initiated by the application's GitHub webhook routing, not plugin hooks. Each merge creates
one task per linked changelog and runs through the same Bunny agent as assigned knowledge gaps.
Credits, progress, checkpoint retries and publication use the standard draft flow; no batch model
or changelog-specific stale-publication gate is required.

OpenAPI references use `upsert_apireference` and publish immediately. A spec URL goes directly to
the backend; local files use `create_media_upload(purpose="api_reference")`, an HTTP PUT, and
token finalization. The backend owns size, site/user binding, token expiry, and spec validation.
The complete workflows live in the canonical skill's `references/tools-and-workflows.md`.

## Source of truth

`plugins/bunnydesk/skills/bunnydesk-docs/` is the canonical BunnyDesk skill.
The application serves setup instructions that direct supported clients to
install this plugin; it does not host, vendor, or download a second skill
package.

Installed clients load the packaged skill from their selected plugin revision. Updating this
checkout does not rewrite installed caches or redeploy BunnyDesk. Release and install a matching
revision through the supported client workflow; verify the deployed server advertises the required
tools and arguments. Capability claims must follow that server, not only the source branch.

CI in both repositories should compare the application MCP tool registry and
renderer contract with this canonical skill. Those checks must not require an
application-hosted skill file or byte-identical duplicate packaging.

## Versioning and release controls

- Use semantic versions in every manifest.
- Tag immutable releases and document changes in `CHANGELOG.md`.
- Protect `main`; require pull-request review and successful validation.
- Pin production consumers to a tag or reviewed commit where supported.
- Do not add hooks unless a concrete workflow requires their local execution.
- Keep the stable MCP URL unchanged across ordinary plugin releases.

## Compatibility policy

Portable Agent Plugins metadata is canonical. A compatibility manifest may be
kept while a supported client still requires it. Unsupported speculative files
are not added: each adapter must be backed by current vendor documentation and
must pass that client's validator when one exists.
