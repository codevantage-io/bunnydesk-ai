# Release checklist

Do not tag `v0.1.0` until every blocking item is complete.

## Repository

- [ ] Review and create the initial commit, then push `main`.
- [ ] Protect `main`: require pull requests, CI, and review; block force pushes and deletion.
- [ ] Confirm GitHub secret scanning and private vulnerability reporting are enabled.
- [ ] Confirm the release commit contains no credentials, customer data, hooks, or unreviewed executables.

## Static package validation

- [x] Portable Agent Plugins manifests validate against the 1.0.0 schemas.
- [x] Codex compatibility manifest and repository marketplace validate.
- [x] Claude Code marketplace and plugin pass strict validation.
- [x] Cursor marketplace and plugin validate against the current schemas.
- [x] `bunnydesk-docs` passes Agent Skills validation.
- [x] All 20 current MCP tools and all six BunnyDesk renderer components are documented.
- [x] Relative skill references resolve within the skill package.
- [x] Manifests use the production HTTPS endpoint and contain no static credentials.

Run:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py --source /path/to/bunnydesk
claude plugin validate . --strict
claude plugin validate plugins/bunnydesk --strict
```

The plugin repository cannot independently see new tools added to a private
BunnyDesk application checkout. The BunnyDesk application CI must run the
`--source` check, or an equivalent cross-repository contract check, whenever
MCP tools or the bundled plugin instructions change.

## Hosted MCP server — blocking

- [ ] Deploy the account-scoped OAuth implementation currently present in the BunnyDesk application source.
- [ ] Confirm an anonymous MCP request returns `401` with a `resource_metadata` URL in `WWW-Authenticate`.
- [ ] Confirm protected-resource and authorization-server metadata are valid JSON and mutually consistent.
- [ ] Add accurate `readOnlyHint`, `destructiveHint`, and `openWorldHint` annotations to every advertised MCP tool.
- [ ] Confirm tool authorization is enforced server-side for every account and site.

Run the read-only discovery check:

```bash
python3 scripts/check_production.py
```

## Live client verification — blocking

- [ ] Clean install from Git in Codex and authenticate through the browser.
- [ ] Clean install from Git in Claude Code and authenticate through the browser.
- [ ] Import/install in Cursor and authenticate through the browser.
- [ ] Upgrade each supported client from the previous plugin version.
- [ ] Verify `list_sites`, site selection, and `project_knowledge` discovery.
- [ ] Create and update a page with `publish=false`; verify it remains a draft.
- [ ] Upload representative image and video media without exposing local paths.
- [ ] Update sidebar navigation using `base_hash` and read it back.
- [ ] Approve a reviewed draft only after explicit authorization.
- [ ] Confirm destructive operations request or preserve explicit user authorization.

## Marketplace submission

- [ ] Add approved BunnyDesk logo/icon assets and screenshots where the target marketplace requires them.
- [ ] Prepare support/contact details, publisher verification, privacy and terms links, and permission explanations.
- [ ] Prepare positive, negative, edge-case, and out-of-scope evaluation prompts.
- [ ] Submit to the OpenAI universal plugin directory and Cursor Marketplace only after live verification passes.
- [ ] Publish immutable release notes and verify installation from the tagged plugin.
