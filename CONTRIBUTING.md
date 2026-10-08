# Contributing

Thank you for helping improve the BunnyDesk agent plugin.

## Propose a change

1. Fork the repository and create a focused branch.
2. Keep plugin identity as `bunnydesk` and skill identity as `bunnydesk-docs`.
3. Never add credentials, customer data, or install-time executable hooks.
4. Run `python3 scripts/validate.py` from the repository root.
5. Open a pull request describing the user-facing effect and the clients tested.

Changes to MCP tool names or behavior should update the BunnyDesk server first.
Then update the skill, expected tool inventory, validation fixtures, changelog,
and release version together. Keep the skill focused on cross-tool judgment;
the MCP server's tool schemas remain the authority for call arguments.

## Release checklist

The authoritative, blocking checklist is
[`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md). In summary:

- Validate a clean marketplace install and an upgrade from the previous tag.
- Confirm the plugin contains no credentials and uses the production HTTPS endpoint.
- Test browser OAuth, `list_sites`, a draft page workflow, media upload, navigation update, and approval.
- Tag an immutable semantic version and publish release notes.
- Keep the released skill aligned with the BunnyDesk application's MCP tool registry and renderer contract.
