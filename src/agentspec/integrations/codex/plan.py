from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentspec.core.managed_files import (
    FilePlan,
    plan_managed_block,
    plan_managed_file,
)
from agentspec.integrations.codex.paths import CodexPaths
from agentspec.integrations.codex.resources import (
    MANAGED_MARKDOWN_MARKER,
    MANAGED_TOML_MARKER,
)


@dataclass(frozen=True)
class CodexPlan:
    config_dir: Path
    agents_md: FilePlan
    agents_dir: Path
    agents: tuple[FilePlan, ...]
    skills_dir: Path
    skills: tuple[FilePlan, ...]


def build_plan(
    paths: CodexPaths,
    global_instructions: str,
    managed_agents: dict[str, str] | None = None,
    managed_skills: dict[str, str] | None = None,
) -> CodexPlan:
    managed_agents = managed_agents or {}
    managed_skills = managed_skills or {}

    return CodexPlan(
        config_dir=paths.config_dir,
        agents_md=plan_managed_block(
            paths.agents_md,
            "openspec",
            global_instructions,
        ),
        agents_dir=paths.agents_dir,
        agents=tuple(
            plan_managed_file(
                paths.agents_dir / filename,
                content,
                MANAGED_TOML_MARKER,
            )
            for filename, content in managed_agents.items()
        ),
        skills_dir=paths.skills_dir,
        skills=tuple(
            plan_managed_file(
                paths.skills_dir / relative_path,
                content,
                MANAGED_MARKDOWN_MARKER,
            )
            for relative_path, content in managed_skills.items()
        ),
    )
