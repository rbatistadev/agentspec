from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

from agentspec.integrations.opencode.resources import (
    load_global_instructions,
    load_managed_agents as load_opencode_agents,
    load_managed_commands as load_opencode_commands,
)

MANAGED_TOML_MARKER = "# agentspec:managed"
MANAGED_MARKDOWN_MARKER = "<!-- agentspec:managed -->"
WRITABLE_AGENTS = {
    "agentspec-openspec-apply-worker",
    "agentspec-openspec-taskwriter",
}


def _split_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        raise ValueError("AgentSpec template has no frontmatter.")

    end = content.find("\n---\n", 4)
    if end == -1:
        raise ValueError("AgentSpec template has malformed frontmatter.")

    metadata = {}
    for line in content[4:end].splitlines():
        if line and not line.startswith((" ", "-")):
            key, separator, value = line.partition(":")
            if separator:
                metadata[key] = value.strip()

    body = content[end + 5 :].strip()
    body = body.removeprefix(MANAGED_MARKDOWN_MARKER).strip()
    return metadata, body


def _codex_agent_body(body: str) -> str:
    body = body.replace(
        "the general OpenCode subagent",
        "the built-in Codex worker agent",
    )
    return re.sub(
        r"\bgeneral\b(?!-)",
        "the built-in Codex worker agent",
        body,
    )


def load_managed_agents() -> dict[str, str]:
    agents = {}

    for filename, template in load_opencode_agents().items():
        metadata, body = _split_frontmatter(template)
        name = PurePosixPath(filename).stem
        instructions = (
            _codex_agent_body(body)
            if name == "agentspec-openspec-orchestrator"
            else body
        )
        sandbox = (
            ""
            if name in WRITABLE_AGENTS
            else 'sandbox_mode = "read-only"\n'
        )
        agents[f"{name}.toml"] = (
            f"{MANAGED_TOML_MARKER}\n"
            f"name = {json.dumps(name)}\n"
            f"description = {json.dumps(metadata['description'])}\n"
            f"{sandbox}"
            f"developer_instructions = {json.dumps(instructions)}\n"
        )

    return agents


def load_managed_skills() -> dict[str, str]:
    skills = {}

    for relative_path, template in load_opencode_commands().items():
        metadata, body = _split_frontmatter(template)
        operation = PurePosixPath(relative_path).stem
        name = f"agentspec-openspec-{operation}"
        agent = metadata["agent"]
        body = body.replace("$ARGUMENTS", "the user's arguments")
        skills[f"{name}/SKILL.md"] = (
            "---\n"
            f"name: {name}\n"
            f"description: {json.dumps(metadata['description'])}\n"
            "---\n\n"
            f"{MANAGED_MARKDOWN_MARKER}\n\n"
            f"Delegate this request synchronously to the {agent} custom agent "
            "and return its result.\n\n"
            f"{body}\n"
        )

    return skills


__all__ = [
    "MANAGED_MARKDOWN_MARKER",
    "MANAGED_TOML_MARKER",
    "load_global_instructions",
    "load_managed_agents",
    "load_managed_skills",
]
