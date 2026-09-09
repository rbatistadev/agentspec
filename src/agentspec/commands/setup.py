from __future__ import annotations

from agentspec.core.paths import resolve_paths
from agentspec.integrations.opencode.apply import ApplyError, apply_plan
from agentspec.integrations.opencode.plan import PlanAction, build_plan
from agentspec.integrations.opencode.resources import (
    load_global_instructions,
    load_managed_agents,
)


def _print_plan(plan) -> None:
    print("OpenCode")
    print()

    print(
        f"{plan.agents_md.action.value}: "
        f"{plan.agents_md.path}"
    )
    print(f"  {plan.agents_md.reason}")

    for agent in plan.agents:
        print()
        print(f"{agent.action.value}: {agent.path}")
        print(f"  {agent.reason}")


def run(*, dry_run: bool) -> int:
    paths = resolve_paths()

    plan = build_plan(
        paths,
        load_global_instructions(),
        load_managed_agents(),
    )

    print("AgentSpec setup")
    print()

    if dry_run:
        print("Mode: dry-run")
        print()

    _print_plan(plan)

    blocked = (
        plan.agents_md.action == PlanAction.BLOCKED
        or any(
            agent.action == PlanAction.BLOCKED
            for agent in plan.agents
        )
    )

    if blocked:
        print()
        print(
            "Setup cannot proceed because the current "
            "configuration is unsafe to modify."
        )
        return 1

    if dry_run:
        return 0

    try:
        apply_plan(plan)
    except ApplyError as exc:
        print()
        print(f"ERROR: {exc}")
        return 1

    print()
    print("Applied successfully.")

    return 0