# Release checklist

Do not tag `v0.1.0` until every blocking item is complete.

## Repository

- [ ] Review pending release changes and push the release commit.
- [ ] Protect `main`: require pull requests, CI, and review; block force pushes and deletion.
- [ ] Confirm GitHub secret scanning and private vulnerability reporting are enabled.
- [ ] Confirm the release commit contains no credentials, customer data, hooks, or unreviewed executables.

## Static package validation

- [x] Portable Agent Plugins manifests validate against the 1.0.0 schemas.
- [x] Codex compatibility manifest and repository marketplace validate.
- [x] Claude Code marketplace and plugin pass strict validation.
- [x] Cursor marketplace and plugin validate against the current schemas.
- [x] `bunnydesk-docs` passes Agent Skills validation.
- [x] Every current MCP tool in the source-checked inventory and all six renderer components are documented.
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
MCP tools or the renderer contract change.

## Hosted MCP server — blocking

- [ ] Deploy the account-scoped OAuth implementation currently present in the BunnyDesk application source.
- [ ] Deploy the matching exact-draft editing, API-reference upload/upsert, and automatic changelog implementation, including its migrations and worker/beat configuration.
- [ ] Confirm advertised schemas include `update_draft`, `upsert_apireference`, API-reference upload purpose, and stale changelog approval confirmation.
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
- [ ] Read a selected AI/changelog version with `version_uid`, edit using `update_draft`, and verify its UID, task, source, and pending status are preserved.
- [ ] Verify a GitHub merge independently reaches knowledge-gap processing and the linked changelog flow, with separate tasks for each received event.
- [ ] Verify changelogs use ordinary single/bulk/MCP draft approval without a stale flag or special confirmation; verify manual edits and sibling drafts are preserved.
- [ ] Verify no-credit, failed, and stopped changelog tasks use standard Bunny errors/chat/retries, without automatic top-up recovery or a separate changelog retry control.
- [ ] Upload representative image and video media without exposing local paths.
- [ ] Create and replace API references from a public spec URL and a staged JSON/YAML file; verify PUT precedes finalization and upsert publishes immediately.
- [ ] Verify spec validation, actual-size mismatch, expired token, and cross-site/user token failures; verify no placeholder page is published by upload alone.
- [ ] Verify metadata-only API-reference updates and UID retention, separate requested navigation updates, and draft-only requests do not silently publish references.
- [ ] Update sidebar navigation using `base_hash` and read it back.
- [ ] Approve a reviewed draft only after explicit authorization.
- [ ] Confirm destructive operations request or preserve explicit user authorization.

## Marketplace submission

- [ ] Add approved BunnyDesk logo/icon assets and screenshots where the target marketplace requires them.
- [ ] Prepare support/contact details, publisher verification, privacy and terms links, and permission explanations.
- [ ] Prepare positive, negative, edge-case, and out-of-scope evaluation prompts.
- [ ] Submit to the OpenAI universal plugin directory and Cursor Marketplace only after live verification passes.
- [ ] Publish immutable release notes after live verification passes.
