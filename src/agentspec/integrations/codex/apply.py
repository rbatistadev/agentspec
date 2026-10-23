from __future__ import annotations

from agentspec.core.managed_files import ApplyError, apply_file
from agentspec.integrations.codex.plan import CodexPlan


def apply_plan(plan: CodexPlan) -> None:
    apply_file(plan.agents_md)

    for agent in plan.agents:
        apply_file(agent)

    for skill in plan.skills:
        apply_file(skill)


__all__ = ["ApplyError", "apply_plan"]
