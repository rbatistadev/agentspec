from __future__ import annotations

import shutil

from agentspec.core.paths import resolve_paths
from agentspec.integrations.codex.paths import resolve_codex_paths
from agentspec.integrations.codex.plan import build_plan as build_codex_plan
from agentspec.integrations.codex.resources import (
    load_global_instructions as load_codex_global_instructions,
)
from agentspec.integrations.opencode.plan import (
    build_plan as build_opencode_plan,
)
from agentspec.integrations.opencode.resources import (
    load_global_instructions,
)


def _check_command(name: str) -> bool:
    return shutil.which(name) is not None


def run() -> int:
    checks = {
        "openspec": _check_command("openspec"),
        "opencode": _check_command("opencode"),
        "codex": _check_command("codex"),
        "git": _check_command("git"),
    }

    paths = resolve_paths()
    codex_paths = resolve_codex_paths()
    opencode_plan = build_opencode_plan(
        paths,
        load_global_instructions(),
    )
    codex_plan = build_codex_plan(
        codex_paths,
        load_codex_global_instructions(),
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
    print(f"Codex config: {codex_paths.config_file}")
    print(f"Codex agents: {codex_paths.agents_dir}")
    print(f"Codex skills: {codex_paths.skills_dir}")

    for title, plan in (
        ("OpenCode", opencode_plan),
        ("Codex", codex_plan),
    ):
        print()
        print(f"{title} integration")
        print()
        print(f"AGENTS.md: {plan.agents_md.action.value}")
        print(f"  Path: {plan.agents_md.path}")
        print(f"  Reason: {plan.agents_md.reason}")

    required = checks["openspec"] and checks["git"]
    supported_host = checks["opencode"] or checks["codex"]
    return 0 if required and supported_host else 1
