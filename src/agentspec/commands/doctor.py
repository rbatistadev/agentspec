from __future__ import annotations
from agentspec.integrations.opencode.plan import build_plan
from agentspec.integrations.opencode.resources import (
    load_global_instructions,
)

import shutil

from agentspec.core.paths import resolve_paths


def _check_command(name: str) -> bool:
    return shutil.which(name) is not None


def run() -> int:
    checks = {
        "openspec": _check_command("openspec"),
        "opencode": _check_command("opencode"),
        "git": _check_command("git"),
    }

    paths = resolve_paths()
    opencode_plan = build_plan(
        paths,
        load_global_instructions(),
    )

    print("AgentSpec doctor")
    print()

    for name, available in checks.items():
        marker = "✓" if available else "✗"
        status = "available" if available else "not found"
        print(f"{marker} {name}: {status}")

    print()
    print("Resolved paths")
    print()
    print(f"OpenSpec config: {paths.openspec_config_file}")
    print(f"OpenCode config: {paths.opencode_config_file}")
    print(f"OpenCode agents: {paths.opencode_agents_dir}")

    print()
    print("OpenCode integration")
    print()
    print(f"AGENTS.md: {opencode_plan.agents_md.action.value}")
    print(f"  Path: {opencode_plan.agents_md.path}")
    print(f"  Reason: {opencode_plan.agents_md.reason}")

    return 0 if all(checks.values()) else 1