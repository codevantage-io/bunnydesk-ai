#!/usr/bin/env python3
"""Validate the public BunnyDesk plugin without contacting customer services."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ModuleNotFoundError as exc:
    print(
        "Validation dependency missing. Run: python3 -m pip install -r requirements-dev.txt",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "bunnydesk"
SKILL = PLUGIN / "skills" / "bunnydesk-docs" / "SKILL.md"
ENDPOINT = "https://app.bunnydesk.ai/mcp/"
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
EXPECTED_TOOLS = {
    "list_sites",
    "create_site",
    "get_site_info",
    "get_site_config",
    "update_site_config",
    "list_pages",
    "get_page",
    "create_page",
    "update_page",
    "delete_page",
    "search_pages",
    "get_site_navigation",
    "update_site_navigation",
    "list_drafts",
    "update_draft",
    "approve_draft",
    "reject_draft",
    "create_media_upload",
}
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    "generic bearer token": re.compile(
        r"Bearer\s+[A-Za-z0-9._~+/-]{20,}", re.IGNORECASE
    ),
}
REQUIRED_COMPONENTS = {"Callout", "Card", "Accordion", "Column", "Cols", "Video"}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.checks = 0

    def require(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.errors.append(message)

    def json(self, path: Path) -> dict:
        self.require(path.is_file(), f"missing JSON file: {path.relative_to(ROOT)}")
        if not path.is_file():
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.errors.append(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
            return {}
        self.require(
            isinstance(value, dict),
            f"JSON root must be an object: {path.relative_to(ROOT)}",
        )
        return value if isinstance(value, dict) else {}


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip("\"'")
    return result


def find_mcp_urls(value: object) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if (
                key in {"url", "serverUrl"}
                and isinstance(child, str)
                and "/mcp" in child
            ):
                urls.append(child)
            urls.extend(find_mcp_urls(child))
    elif isinstance(value, list):
        for child in value:
            urls.extend(find_mcp_urls(child))
    return urls


def validate_json_files(v: Validation) -> dict[Path, dict]:
    documents: dict[Path, dict] = {}
    for path in sorted(ROOT.rglob("*.json")):
        if ".git" in path.parts:
            continue
        documents[path] = v.json(path)
    v.require(bool(documents), "repository contains no JSON manifests")
    return documents


def validate_json_schemas(v: Validation, documents: dict[Path, dict]) -> None:
    pairs = (
        (
            ROOT / "schemas" / "agent-plugins" / "plugin.schema.json",
            PLUGIN / "plugin.json",
        ),
        (
            ROOT / "schemas" / "agent-plugins" / "mcp.schema.json",
            PLUGIN / "mcp.json",
        ),
    )
    for schema_path, document_path in pairs:
        schema = documents.get(schema_path, {})
        document = documents.get(document_path, {})
        try:
            Draft202012Validator.check_schema(schema)
            errors = sorted(
                Draft202012Validator(schema).iter_errors(document),
                key=lambda error: list(error.absolute_path),
            )
        except SchemaError as exc:
            v.require(False, f"could not apply {schema_path.relative_to(ROOT)}: {exc}")
            continue
        detail = "; ".join(error.message for error in errors[:3])
        v.require(
            not errors,
            f"{document_path.relative_to(ROOT)} fails its vendored schema: {detail}",
        )


def validate_portable_manifests(v: Validation, documents: dict[Path, dict]) -> str:
    manifest_path = PLUGIN / "plugin.json"
    mcp_path = PLUGIN / "mcp.json"
    manifest = documents.get(manifest_path, {})
    mcp = documents.get(mcp_path, {})

    v.require(
        manifest.get("$schema") == PLUGIN_SCHEMA,
        "plugin.json uses the wrong Agent Plugins schema",
    )
    v.require(
        manifest.get("name") == "bunnydesk", "portable plugin name must be bunnydesk"
    )
    version = manifest.get("version", "")
    v.require(
        isinstance(version, str) and bool(SEMVER.fullmatch(version)),
        "plugin version must be semantic",
    )
    v.require(
        manifest.get("license") == "MIT",
        "plugin license must match the repository MIT license",
    )
    v.require(
        mcp.get("$schema") == MCP_SCHEMA, "mcp.json uses the wrong Agent Plugins schema"
    )
    servers = mcp.get("mcpServers", {})
    server = servers.get("bunnydesk", {}) if isinstance(servers, dict) else {}
    v.require(
        server.get("type") == "streamable-http",
        "portable MCP transport must be streamable-http",
    )
    v.require(
        server.get("url") == ENDPOINT,
        "portable MCP endpoint must be the production BunnyDesk URL",
    )
    v.require(
        "headers" not in server,
        "public MCP metadata must not contain static authentication headers",
    )
    return version if isinstance(version, str) else ""


def validate_compatibility(
    v: Validation, documents: dict[Path, dict], version: str
) -> None:
    compat_path = PLUGIN / ".codex-plugin" / "plugin.json"
    compat = documents.get(compat_path, {})
    if compat:
        v.require(
            compat.get("name") == "bunnydesk",
            "Codex compatibility name must be bunnydesk",
        )
        v.require(
            compat.get("version") == version,
            "portable and Codex manifest versions differ",
        )
        v.require(
            compat.get("skills") == "./skills/",
            "Codex compatibility skill path must be ./skills/",
        )
        v.require(
            compat.get("mcpServers") == "./.mcp.json",
            "Codex compatibility MCP path must be ./.mcp.json",
        )

    marketplace_path = ROOT / ".agents" / "plugins" / "marketplace.json"
    marketplace = documents.get(marketplace_path, {})
    if marketplace:
        entries = marketplace.get("plugins", [])
        entry = next(
            (
                item
                for item in entries
                if isinstance(item, dict) and item.get("name") == "bunnydesk"
            ),
            {},
        )
        source = entry.get("source", {}) if isinstance(entry, dict) else {}
        v.require(
            source.get("path") == "./plugins/bunnydesk",
            "Codex marketplace path must resolve from repository root",
        )
        policy = entry.get("policy", {}) if isinstance(entry, dict) else {}
        v.require(
            policy.get("installation") in {"AVAILABLE", "INSTALLED_BY_DEFAULT"},
            "marketplace installation policy is missing",
        )
        v.require(
            policy.get("authentication") in {"ON_INSTALL", "ON_USE"},
            "marketplace authentication policy is missing",
        )


def validate_skill(v: Validation) -> None:
    v.require(SKILL.is_file(), "missing bunnydesk-docs/SKILL.md")
    if not SKILL.is_file():
        return
    text = SKILL.read_text(encoding="utf-8")
    skill_markdown = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(SKILL.parent.rglob("*.md"))
    )
    metadata = frontmatter(text)
    v.require(
        metadata.get("name") == "bunnydesk-docs",
        "skill frontmatter name must be bunnydesk-docs",
    )
    v.require(
        bool(metadata.get("description")), "skill frontmatter requires a description"
    )
    v.require(
        SKILL.parent.name == metadata.get("name"),
        "skill folder must match its frontmatter name",
    )
    missing = sorted(
        tool
        for tool in EXPECTED_TOOLS
        if re.search(rf"\b{re.escape(tool)}\b", skill_markdown) is None
    )
    v.require(
        not missing,
        f"skill package does not mention current MCP tools: {', '.join(missing)}",
    )
    v.require(
        "publish=false" in text,
        "skill must document the draft-first publish=false workflow",
    )
    v.require(
        "project_knowledge" in text, "skill must require project_knowledge discovery"
    )
    v.require("base_hash" in text, "skill must document safe sidebar navigation writes")

    skill_root = SKILL.parent.resolve()
    markdown_paths = sorted(SKILL.parent.rglob("*.md"))
    for markdown_path in markdown_paths:
        markdown = markdown_path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(markdown):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or urlparse(target).scheme or target.startswith("/"):
                continue
            resolved = (markdown_path.parent / target).resolve()
            v.require(
                resolved.is_relative_to(skill_root),
                f"skill link escapes its package: {markdown_path.relative_to(ROOT)} -> {target}",
            )
            v.require(
                resolved.is_file(),
                f"broken skill link: {markdown_path.relative_to(ROOT)} -> {target}",
            )

    authoring_path = SKILL.parent / "references" / "page-authoring.md"
    authoring = (
        authoring_path.read_text(encoding="utf-8") if authoring_path.is_file() else ""
    )
    missing_components = sorted(
        component
        for component in REQUIRED_COMPONENTS
        if f"<{component}" not in authoring
    )
    v.require(
        not missing_components,
        f"page authoring reference omits components: {', '.join(missing_components)}",
    )

    openai_yaml = SKILL.parent / "agents" / "openai.yaml"
    v.require(openai_yaml.is_file(), "missing agents/openai.yaml")
    if not openai_yaml.is_file():
        return
    try:
        openai = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        v.require(False, f"invalid agents/openai.yaml: {exc}")
        return
    v.require(isinstance(openai, dict), "agents/openai.yaml root must be an object")
    if not isinstance(openai, dict):
        return
    interface = openai.get("interface", {})
    v.require(isinstance(interface, dict), "openai.yaml interface must be an object")
    if isinstance(interface, dict):
        v.require(bool(interface.get("display_name")), "openai.yaml needs display_name")
        v.require(
            bool(interface.get("short_description")),
            "openai.yaml needs short_description",
        )
        v.require(
            "$bunnydesk-docs" in str(interface.get("default_prompt", "")),
            "openai.yaml default_prompt must invoke $bunnydesk-docs",
        )
    dependencies = openai.get("dependencies", {})
    tools = dependencies.get("tools", []) if isinstance(dependencies, dict) else []
    mcp_dependencies = [
        tool for tool in tools if isinstance(tool, dict) and tool.get("type") == "mcp"
    ]
    v.require(len(mcp_dependencies) == 1, "openai.yaml must declare one MCP dependency")
    if len(mcp_dependencies) == 1:
        dependency = mcp_dependencies[0]
        v.require(
            dependency.get("value") == "bunnydesk",
            "MCP dependency name must be bunnydesk",
        )
        v.require(
            dependency.get("transport") == "streamable_http",
            "openai.yaml MCP transport must be streamable_http",
        )
        v.require(
            dependency.get("url") == ENDPOINT,
            "openai.yaml MCP dependency must use the production endpoint",
        )
    policy = openai.get("policy", {})
    v.require(
        isinstance(policy, dict) and policy.get("allow_implicit_invocation") is True,
        "bunnydesk-docs must allow implicit invocation",
    )


def validate_repository(v: Validation, documents: dict[Path, dict]) -> None:
    for name in (
        "README.md",
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
    ):
        v.require((ROOT / name).is_file(), f"missing repository file: {name}")

    for path, document in documents.items():
        for url in find_mcp_urls(document):
            parsed = urlparse(url)
            v.require(
                parsed.scheme == "https",
                f"non-HTTPS MCP URL in {path.relative_to(ROOT)}: {url}",
            )
            v.require(
                url == ENDPOINT,
                f"unexpected MCP URL in {path.relative_to(ROOT)}: {url}",
            )

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            v.require(
                pattern.search(text) is None,
                f"possible {label} in {path.relative_to(ROOT)}",
            )


def validate_installation_docs(v: Validation) -> None:
    """Keep published onboarding aligned with the supported client CLIs."""
    readme_path = ROOT / "README.md"
    if not readme_path.is_file():
        return
    readme = readme_path.read_text(encoding="utf-8")
    required_commands = {
        "Codex marketplace": "codex plugin marketplace add codevantage-io/bunnydesk-ai",
        "Codex install": "codex plugin add bunnydesk@bunnydesk-ai",
        "Claude marketplace": (
            "claude plugin marketplace add codevantage-io/bunnydesk-ai --scope user"
        ),
        "Claude install": "claude plugin install bunnydesk@bunnydesk-ai --scope user",
        "Cursor marketplace": (
            "cursor agent plugin marketplace add "
            "https://github.com/codevantage-io/bunnydesk-ai.git"
        ),
        "Cursor release pin": "--git-ref <release-tag>",
    }
    for label, command in required_commands.items():
        v.require(command in readme, f"README is missing the {label} command")
    v.require(
        "--ref <release-tag>" in readme,
        "README must document Codex release-tag pinning",
    )
    v.require(
        "must not be tagged or\n> advertised for installation" in readme
        and "scripts/check_production.py" in readme,
        "README must preserve the production OAuth pre-release gate",
    )
    v.require(
        "run `/plugins`" not in readme,
        "README must use the supported Codex CLI install command, not /plugins",
    )
    for stale_reference in (
        "Standalone skill fallback",
        "npx skills add",
        "Configure\n`https://app.bunnydesk.ai/mcp/` separately",
    ):
        v.require(
            stale_reference not in readme,
            "README must not describe the removed app-hosted standalone skill fallback",
        )


def validate_source(v: Validation, source: Path) -> None:
    tools_dir = source / "apps" / "mcp" / "tools"
    renderer_path = source / "apps" / "hosted_sites" / "markdown_extensions.py"
    v.require(tools_dir.is_dir(), f"BunnyDesk MCP tools not found: {tools_dir}")
    v.require(
        renderer_path.is_file(),
        f"BunnyDesk renderer registry not found: {renderer_path}",
    )
    if tools_dir.is_dir():
        names: set[str] = set()
        pattern = re.compile(
            r'^@(?:site_)?tool\(\s*\n?\s*["\']([a-z0-9_]+)["\']', re.MULTILINE
        )
        for path in tools_dir.glob("*.py"):
            names.update(pattern.findall(path.read_text(encoding="utf-8")))
        v.require(
            names == EXPECTED_TOOLS,
            f"MCP tool drift: expected {sorted(EXPECTED_TOOLS)}, found {sorted(names)}",
        )
    if renderer_path.is_file():
        try:
            module = ast.parse(renderer_path.read_text(encoding="utf-8"))
            registry = next(
                node.value
                for node in module.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name)
                    and target.id == "COMPONENT_REGISTRY"
                    for target in node.targets
                )
            )
            renderer_components = set(ast.literal_eval(registry))
        except (StopIteration, SyntaxError, ValueError) as exc:
            v.require(False, f"cannot read BunnyDesk renderer registry: {exc}")
            return
        v.require(
            renderer_components == REQUIRED_COMPONENTS,
            "renderer component drift: "
            f"expected {sorted(REQUIRED_COMPONENTS)}, found {sorted(renderer_components)}",
        )
        authoring_path = SKILL.parent / "references" / "page-authoring.md"
        authoring = (
            authoring_path.read_text(encoding="utf-8")
            if authoring_path.is_file()
            else ""
        )
        missing_components = sorted(
            component
            for component in renderer_components
            if f"<{component}" not in authoring
        )
        v.require(
            not missing_components,
            "plugin page authoring reference omits renderer components: "
            f"{', '.join(missing_components)}",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        help="optional path to the BunnyDesk application repository for transition drift checks",
    )
    args = parser.parse_args()

    validation = Validation()
    documents = validate_json_files(validation)
    validate_json_schemas(validation, documents)
    version = validate_portable_manifests(validation, documents)
    validate_compatibility(validation, documents, version)
    validate_skill(validation)
    validate_repository(validation, documents)
    validate_installation_docs(validation)
    if args.source:
        validate_source(validation, args.source.resolve())
    else:
        print(
            "Note: upstream BunnyDesk source drift was not checked (pass --source to enable it)."
        )

    if validation.errors:
        print(
            f"Validation failed with {len(validation.errors)} error(s):",
            file=sys.stderr,
        )
        for error in validation.errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Validated BunnyDesk plugin: {validation.checks} checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
