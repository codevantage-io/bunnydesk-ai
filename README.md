# BunnyDesk AI plugin

The official BunnyDesk plugin for AI agents. It bundles the hosted BunnyDesk
MCP connection with the `bunnydesk-docs` skill so an agent can create, edit,
review, organize, and publish documentation while respecting BunnyDesk's draft
and renderer rules.

> **Pre-release:** The package is implemented, but it must not be tagged or
> advertised for installation until `python3 scripts/check_production.py`
> passes. Verify the deployed OAuth discovery, MCP tool inventory, current draft/API-reference
> behavior, and submission-grade safety annotations against the application source. Track the
> remaining gates in [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md).
> The commands below describe the intended post-release installation flow; do
> not advertise or rely on them until production readiness and every blocking
> release-checklist item are complete.

## What is included

- A portable [Agent Plugins](https://agent-plugins.org/) package.
- The remote streamable HTTP MCP connection at `https://app.bunnydesk.ai/mcp/`.
- The `bunnydesk-docs` skill and focused authoring/workflow references.
- Exact-version draft editing, automatic changelog review, and OpenAPI reference upload/update guidance.
- Compatibility manifests for OpenAI Codex, Claude Code, and Cursor.
- Marketplace catalogs for repository, direct-Git, and team distribution.
- Credential, manifest, path, and MCP-tool coverage validation.

The repository contains no BunnyDesk credentials or customer content. Once
the required server deployment is live, users authenticate directly with
BunnyDesk through browser OAuth.

## Install

### Codex

Add the GitHub repository as a marketplace source, then install BunnyDesk from
that marketplace:

```bash
codex plugin marketplace add codevantage-io/bunnydesk-ai
codex plugin add bunnydesk@bunnydesk-ai
```

Start a new session after installation so its skill and MCP server are loaded.
Complete BunnyDesk browser OAuth when Codex prompts.

ChatGPT desktop installation is not available until BunnyDesk is accepted into
the OpenAI universal plugin directory; that submission remains release-gated.

For a release-controlled environment, Codex supports pinning the marketplace
source to an immutable release tag:

```bash
codex plugin marketplace add codevantage-io/bunnydesk-ai --ref <release-tag>
codex plugin add bunnydesk@bunnydesk-ai
```

### Claude Code

Add and install the marketplace from the shell:

```bash
claude plugin marketplace add codevantage-io/bunnydesk-ai --scope user
claude plugin install bunnydesk@bunnydesk-ai --scope user
```

The equivalent commands inside an interactive Claude Code session are:

```text
/plugin marketplace add codevantage-io/bunnydesk-ai
/plugin install bunnydesk@bunnydesk-ai
```

Use `/plugin marketplace update bunnydesk-ai` to refresh the catalog after a
new release. Claude discovers the package's `skills/` and `.mcp.json`
automatically. The current Claude marketplace command does not provide a
`--ref` option, so do not append a release-tag flag to these commands.

### Cursor

Cursor installs Agent Plugins and Cursor Plugins from its **Customize** view.
Add this Git marketplace from the shell:

```bash
cursor agent plugin marketplace add https://github.com/codevantage-io/bunnydesk-ai.git
```

Then run `cursor agent`, enter `/plugin`, choose `bunnydesk` from the
marketplace, and install it at user or project scope. Cursor does not currently
provide a documented non-interactive command to install an individual plugin
from that marketplace.

For a release-controlled environment, Cursor supports pinning the marketplace
index to a tag or commit:

```bash
cursor agent plugin marketplace add https://github.com/codevantage-io/bunnydesk-ai.git --git-ref <release-tag>
```

For a team marketplace, an administrator can open **Dashboard → Plugins**,
choose **Add Marketplace → Import from Repo**, and import:

```text
https://github.com/codevantage-io/bunnydesk-ai
```

For local development, copy `plugins/bunnydesk` to
`~/.cursor/plugins/local/bunnydesk`, reload Cursor, and verify the plugin under
**Customize**. A general public one-click install requires acceptance into the
Cursor Marketplace; this repository does not claim that listing yet.

## Connect and use

The MCP connection is designed to use browser OAuth; there is no API key to
paste into this repository or an agent configuration. Complete these steps
only after the production readiness check passes.

1. Start authentication when the client prompts, or use its MCP login command.
2. Authorize BunnyDesk in the browser.
3. Start with `list_sites` because the connection is account-scoped.
4. Select the returned `site_id`; create a site only when the request clearly
   calls for one.
5. Read `project_knowledge` and existing content before making changes.
6. Keep Markdown edits as drafts unless live publication was explicitly authorized. Use
   `update_draft` for a selected review version, not the page's separate user-draft path.
7. Review changelogs against current published content and use ordinary draft approval. Each
   received GitHub merge produces a separate Bunny task; there is no batching or special publish gate.
8. API references use `upsert_apireference` and publish immediately. Use a public spec URL or
   `create_media_upload(purpose="api_reference")` → PUT → upload-token finalization. They cannot
   be saved as Markdown drafts.

The complete tool inventory and procedures live in the skill's
[tools and workflows reference](plugins/bunnydesk/skills/bunnydesk-docs/references/tools-and-workflows.md).
Changelog source setup, manual sync, generation progress, and retry remain dashboard actions.
MCP can read, edit, and review generated changelog versions; it does not expose a generation command.

## Repository layout

```text
.
├── .agents/plugins/marketplace.json       # OpenAI/Codex repo marketplace
├── .claude-plugin/marketplace.json        # Claude Code marketplace
├── .cursor-plugin/marketplace.json        # Cursor marketplace
├── plugins/bunnydesk/
│   ├── plugin.json                        # Portable Agent Plugins manifest
│   ├── mcp.json                           # Portable MCP configuration
│   ├── .codex-plugin/plugin.json          # Codex compatibility manifest
│   ├── .claude-plugin/plugin.json         # Claude compatibility manifest
│   ├── .cursor-plugin/plugin.json         # Cursor compatibility manifest
│   ├── .mcp.json                          # Legacy client MCP configuration
│   └── skills/bunnydesk-docs/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/
├── docs/ARCHITECTURE.md
└── scripts/validate.py
```

Portable `plugin.json`, `mcp.json`, and `skills/` are canonical. The hidden
client manifests adapt the same package and must not carry separate copies of
the skill.

## Validate changes

Run the repository checks:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
```

While the BunnyDesk application repository is available alongside this one,
also audit its current MCP registry and renderer contract:

```bash
python3 scripts/validate.py --source /path/to/bunnydesk
```

Check that the deployed MCP endpoint exposes the OAuth discovery chain needed
by a clean installation:

```bash
python3 scripts/check_production.py
```

For Claude-specific validation:

```bash
claude plugin validate . --strict
claude plugin validate plugins/bunnydesk --strict
```

Before tagging a release, test a clean install and upgrade, then verify browser
OAuth and representative calls against production: site discovery, draft page
creation, media upload, navigation update, and draft approval. Do not publish a
release based only on static manifest validation.

Also verify exact-version draft edits remain pending, stale changelog confirmation preserves
review boundaries, and API references work through both URL and staged-file inputs. The upload
alone must not publish; a successful upsert publishes immediately. Test failure and expiry paths.
An updated source checkout does not update an installed client package or deploy the server;
release/install the matching plugin revision and start a new session after updating it.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for the change and release workflow and
[SECURITY.md](SECURITY.md) for private vulnerability reporting. The plugin is
available under the [MIT License](LICENSE).
