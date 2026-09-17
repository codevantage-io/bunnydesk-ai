# BunnyDesk AI plugin

The official BunnyDesk plugin for AI agents. It bundles the hosted BunnyDesk
MCP connection with the `bunnydesk-docs` skill so an agent can create, edit,
review, organize, and publish documentation while respecting BunnyDesk's draft
and renderer rules.

> **Pre-release:** The package is implemented, but it must not be tagged or
> advertised for installation until `python3 scripts/check_production.py`
> passes. The current public BunnyDesk deployment still needs the OAuth
> discovery behavior already present in the application source branch, and the
> server's MCP tools still need submission-grade safety annotations. Track the
> remaining gates in [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md).
> The installation commands below become usable after the initial `main` commit
> is reviewed and pushed.

## What is included

- A portable [Agent Plugins](https://agent-plugins.org/) package.
- The remote streamable HTTP MCP connection at `https://app.bunnydesk.ai/mcp/`.
- The `bunnydesk-docs` skill and focused authoring/workflow references.
- Compatibility manifests for OpenAI Codex, Claude Code, and Cursor.
- Marketplace catalogs for repository, direct-Git, and team distribution.
- Credential, manifest, path, and MCP-tool coverage validation.

The repository contains no BunnyDesk credentials or customer content. Once
the required server deployment is live, users authenticate directly with
BunnyDesk through browser OAuth.

## Install

### Codex and ChatGPT desktop

Add the GitHub repository as a marketplace source:

```bash
codex plugin marketplace add codevantage-io/bunnydesk-ai
```

Open Codex CLI, run `/plugins`, select the **BunnyDesk** marketplace, and
install **BunnyDesk**. Start a new session after installation so its skill and
MCP server are loaded.

For release-controlled environments, add the marketplace with
`--ref <release-tag>` rather than tracking the default branch.

### Claude Code

Add and install the marketplace from the shell:

```bash
claude plugin marketplace add codevantage-io/bunnydesk-ai
claude plugin install bunnydesk@bunnydesk-ai
```

The equivalent commands inside an interactive Claude Code session are:

```text
/plugin marketplace add codevantage-io/bunnydesk-ai
/plugin install bunnydesk@bunnydesk-ai
```

Use `/plugin marketplace update bunnydesk-ai` to refresh the catalog after a
new release. Claude discovers the package's `skills/` and `.mcp.json`
automatically.

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

For a team marketplace, an administrator can open **Dashboard → Plugins**,
choose **Add Marketplace → Import from Repo**, and import:

```text
https://github.com/codevantage-io/bunnydesk-ai
```

For local development, copy `plugins/bunnydesk` to
`~/.cursor/plugins/local/bunnydesk`, reload Cursor, and verify the plugin under
**Customize**. A general public one-click install requires acceptance into the
Cursor Marketplace; this repository does not claim that listing yet.

### Standalone skill fallback

Clients that support Agent Skills but not plugins can install only the skill:

```bash
npx skills add codevantage-io/bunnydesk-ai --skill bunnydesk-docs
```

This does not install the MCP connection. Configure
`https://app.bunnydesk.ai/mcp/` separately in that client.

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
6. Keep content as drafts unless live publication was explicitly authorized.

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
also audit the current MCP registry and hosted fallback skill:

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

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for the change and release workflow and
[SECURITY.md](SECURITY.md) for private vulnerability reporting. The plugin is
available under the [MIT License](LICENSE).
