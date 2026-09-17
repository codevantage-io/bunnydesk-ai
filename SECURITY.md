# Security policy

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability, exposed credential,
or customer-data concern. Use GitHub's private vulnerability reporting for
this repository. If that option is unavailable, contact the BunnyDesk team
through the support channel published at <https://bunnydesk.ai/>.

Include the affected file or endpoint, reproduction steps, expected impact,
and any suggested mitigation. Do not access data that does not belong to you.

## Supported versions

Security fixes are applied to the latest tagged release. Consumers should pin
a release tag or reviewed commit and upgrade after reviewing release notes.

## Trust boundaries

This repository contains public instructions and declarative MCP connection
metadata. It must never contain BunnyDesk access tokens, OAuth client secrets,
customer content, private keys, or environment files. Once the release-gating
production check passes, authentication happens between the installed client
and `https://app.bunnydesk.ai/mcp/` through BunnyDesk's browser OAuth flow.
