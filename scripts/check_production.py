#!/usr/bin/env python3
"""Read-only production readiness check for BunnyDesk MCP OAuth discovery."""

from __future__ import annotations

import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MCP_URL = "https://app.bunnydesk.ai/mcp/"
TIMEOUT_SECONDS = 15


def get_json(url: str) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "bunnydesk-plugin-check/0.1",
        },
    )
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        content_type = response.headers.get_content_type()
        if content_type != "application/json":
            raise RuntimeError(
                f"{url} returned {content_type}, expected application/json"
            )
        value = json.load(response)
    if not isinstance(value, dict):
        raise TypeError(f"{url} returned a non-object JSON document")
    return value


def main() -> int:
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    ).encode()
    request = Request(
        MCP_URL,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "User-Agent": "bunnydesk-plugin-check/0.1",
        },
    )
    try:
        urlopen(request, timeout=TIMEOUT_SECONDS)
    except HTTPError as exc:
        if exc.code != 401:
            raise RuntimeError(
                f"anonymous MCP initialize returned HTTP {exc.code}, expected 401"
            ) from exc
        challenge = exc.headers.get("WWW-Authenticate", "")
    else:
        raise RuntimeError("anonymous MCP initialize unexpectedly succeeded")

    match = re.search(r'resource_metadata="([^"]+)"', challenge)
    if not match:
        raise RuntimeError(
            "MCP 401 is missing WWW-Authenticate resource_metadata OAuth discovery URL"
        )
    resource_metadata_url = match.group(1)
    protected = get_json(resource_metadata_url)
    if protected.get("resource") not in {MCP_URL, MCP_URL.rstrip("/")}:
        raise RuntimeError(
            "protected-resource metadata identifies a different MCP resource"
        )
    authorization_servers = protected.get("authorization_servers")
    if not isinstance(authorization_servers, list) or not authorization_servers:
        raise RuntimeError("protected-resource metadata has no authorization_servers")

    issuer = authorization_servers[0].rstrip("/")
    authorization = get_json(f"{issuer}/.well-known/oauth-authorization-server")
    required = {
        "issuer",
        "authorization_endpoint",
        "token_endpoint",
        "registration_endpoint",
    }
    missing = sorted(required - authorization.keys())
    if missing:
        raise RuntimeError(
            f"authorization-server metadata is missing: {', '.join(missing)}"
        )

    print("Production MCP OAuth discovery is ready.")
    print(f"MCP: {MCP_URL}")
    print(f"Protected resource metadata: {resource_metadata_url}")
    print(f"Authorization server: {issuer}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, TypeError, URLError, json.JSONDecodeError) as exc:
        print(f"Production readiness check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
