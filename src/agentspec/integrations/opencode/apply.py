from __future__ import annotations

from agentspec.core.managed_files import ApplyError, apply_file
from agentspec.integrations.opencode.plan import OpenCodePlan


def apply_plan(plan: OpenCodePlan) -> None:
    apply_file(plan.agents_md)

    for agent in plan.agents:
        apply_file(agent)

    for command in plan.commands:
        apply_file(command)


__all__ = ["ApplyError", "apply_plan"]
