from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentspec.core.managed_files import (
    FilePlan,
    PlanAction,
    content_digest,
    plan_managed_block,
    plan_managed_file,
    plan_stale_managed_file,
)
from agentspec.core.paths import AgentSpecPaths

MANAGED_FILE_MARKER = "<!-- agentspec:managed -->"


@dataclass(frozen=True)
class OpenCodePlan:
    config_dir: Path
    agents_md: FilePlan

    agents_dir: Path
    agents: tuple[FilePlan, ...]

    commands_dir: Path
    commands: tuple[FilePlan, ...]


def build_plan(
    paths: AgentSpecPaths,
    global_instructions: str,
    managed_agents: dict[str, str] | None = None,
    managed_commands: dict[str, str] | None = None,
    stale_managed_commands: tuple[str, ...] = (),
) -> OpenCodePlan:
    managed_agents = managed_agents or {}
    managed_commands = managed_commands or {}

    agent_plans = tuple(
        plan_managed_file(
            paths.opencode_agents_dir / filename,
            content,
            MANAGED_FILE_MARKER,
        )
        for filename, content in managed_agents.items()
    )

    current_command_plans = tuple(
        plan_managed_file(
            paths.opencode_commands_dir / relative_path,
            content,
            MANAGED_FILE_MARKER,
        )
        for relative_path, content in managed_commands.items()
    )
    stale_command_plans = tuple(
        plan
        for relative_path in stale_managed_commands
        if (
            plan := plan_stale_managed_file(
                paths.opencode_commands_dir / relative_path,
                MANAGED_FILE_MARKER,
            )
        )
        is not None
    )

    return OpenCodePlan(
        config_dir=paths.opencode_config_dir,
        agents_md=plan_managed_block(
            paths.opencode_agents_md,
            "openspec",
            global_instructions,
        ),
        agents_dir=paths.opencode_agents_dir,
        agents=agent_plans,
        commands_dir=paths.opencode_commands_dir,
        commands=current_command_plans + stale_command_plans,
    )


__all__ = [
    "MANAGED_FILE_MARKER",
    "FilePlan",
    "OpenCodePlan",
    "PlanAction",
    "build_plan",
    "content_digest",
]
