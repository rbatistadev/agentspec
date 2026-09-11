from __future__ import annotations

from agentspec.core.managed_files import ApplyError, PlanAction
from agentspec.core.paths import resolve_paths
from agentspec.integrations.codex.apply import apply_plan as apply_codex_plan
from agentspec.integrations.codex.paths import resolve_codex_paths
from agentspec.integrations.codex.plan import build_plan as build_codex_plan
from agentspec.integrations.codex.resources import (
    load_global_instructions as load_codex_global_instructions,
    load_managed_agents as load_codex_agents,
    load_managed_skills,
)
from agentspec.integrations.opencode.apply import (
    apply_plan as apply_opencode_plan,
)
from agentspec.integrations.opencode.plan import (
    build_plan as build_opencode_plan,
)
from agentspec.integrations.opencode.resources import (
    STALE_MANAGED_COMMANDS,
    load_global_instructions,
    load_managed_agents,
    load_managed_commands,
)


def _print_plan(title, agents_md, resources) -> None:
    print(title)
    print()
    print(f"{agents_md.action.value}: {agents_md.path}")
    print(f"  {agents_md.reason}")

    for resource in resources:
        print()
        print(f"{resource.action.value}: {resource.path}")
        print(f"  {resource.reason}")


def _is_blocked(agents_md, resources) -> bool:
    return agents_md.action == PlanAction.BLOCKED or any(
        resource.action == PlanAction.BLOCKED
        for resource in resources
    )


def run(*, dry_run: bool, target: str = "opencode") -> int:
    plans = []

    if target in {"opencode", "all"}:
        opencode_plan = build_opencode_plan(
            resolve_paths(),
            load_global_instructions(),
            load_managed_agents(),
            load_managed_commands(),
            STALE_MANAGED_COMMANDS,
        )
        plans.append(
            (
                "OpenCode",
                opencode_plan,
                (*opencode_plan.agents, *opencode_plan.commands),
                apply_opencode_plan,
            )
        )

    if target in {"codex", "all"}:
        codex_plan = build_codex_plan(
            resolve_codex_paths(),
            load_codex_global_instructions(),
            load_codex_agents(),
            load_managed_skills(),
        )
        plans.append(
            (
                "Codex",
                codex_plan,
                (*codex_plan.agents, *codex_plan.skills),
                apply_codex_plan,
            )
        )

    print("AgentSpec setup")
    print()

    if dry_run:
        print("Mode: dry-run")
        print()

    for index, (title, plan, resources, _) in enumerate(plans):
        if index:
            print()
        _print_plan(title, plan.agents_md, resources)

    if any(
        _is_blocked(plan.agents_md, resources)
        for _, plan, resources, _ in plans
    ):
        print()
        print(
            "Setup cannot proceed because the current "
            "configuration is unsafe to modify."
        )
        return 1

    if dry_run:
        return 0

    try:
        for _, plan, _, apply_plan in plans:
            apply_plan(plan)
    except ApplyError as exc:
        print()
        print(f"ERROR: {exc}")
        return 1

    print()
    print("Applied successfully.")
    return 0
