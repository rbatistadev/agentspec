from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentspec.core.managed_blocks import (
    ManagedBlockError,
    upsert_managed_block,
)
from agentspec.core.paths import AgentSpecPaths

MANAGED_FILE_MARKER = "<!-- agentspec:managed -->"


class PlanAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    NO_CHANGE = "NO_CHANGE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class FilePlan:
    path: Path
    action: PlanAction
    reason: str
    desired_content: str | None
    current_digest: str | None


@dataclass(frozen=True)
class OpenCodePlan:
    config_dir: Path
    agents_md: FilePlan
    agents_dir: Path
    agents: tuple[FilePlan, ...]


def content_digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _plan_agents_md(
    path: Path,
    desired_body: str,
) -> FilePlan:
    exists = path.exists()
    current = _read_text(path) if exists else ""

    try:
        desired = upsert_managed_block(
            current,
            "openspec",
            desired_body,
        )
    except ManagedBlockError as exc:
        return FilePlan(
            path=path,
            action=PlanAction.BLOCKED,
            reason=str(exc),
            desired_content=None,
            current_digest=content_digest(current) if exists else None,
        )

    if not exists:
        return FilePlan(
            path=path,
            action=PlanAction.CREATE,
            reason="Global AGENTS.md does not exist.",
            desired_content=desired,
            current_digest=None,
        )

    digest = content_digest(current)

    if current == desired:
        return FilePlan(
            path=path,
            action=PlanAction.NO_CHANGE,
            reason="AgentSpec managed block is already current.",
            desired_content=desired,
            current_digest=digest,
        )

    return FilePlan(
        path=path,
        action=PlanAction.UPDATE,
        reason="AgentSpec managed block differs from desired state.",
        desired_content=desired,
        current_digest=digest,
    )


def build_plan(
    paths: AgentSpecPaths,
    global_instructions: str,
    managed_agents: dict[str, str] | None = None,
) -> OpenCodePlan:
    managed_agents = managed_agents or {}

    agent_plans = tuple(
        _plan_managed_file(
            paths.opencode_agents_dir / filename,
            content,
        )
        for filename, content in managed_agents.items()
    )

    return OpenCodePlan(
        config_dir=paths.opencode_config_dir,
        agents_md=_plan_agents_md(
            paths.opencode_agents_md,
            global_instructions,
        ),
        agents_dir=paths.opencode_agents_dir,
        agents=agent_plans,
    )

def _plan_managed_file(
    path: Path,
    desired_content: str,
) -> FilePlan:
    if MANAGED_FILE_MARKER not in desired_content:
        return FilePlan(
            path=path,
            action=PlanAction.BLOCKED,
            reason="AgentSpec source template has no managed-file marker.",
            desired_content=None,
            current_digest=None,
        )

    if not path.exists():
        return FilePlan(
            path=path,
            action=PlanAction.CREATE,
            reason="AgentSpec managed file does not exist.",
            desired_content=desired_content,
            current_digest=None,
        )

    current = _read_text(path)
    digest = content_digest(current)

    if current == desired_content:
        return FilePlan(
            path=path,
            action=PlanAction.NO_CHANGE,
            reason="AgentSpec managed file is already current.",
            desired_content=desired_content,
            current_digest=digest,
        )

    if MANAGED_FILE_MARKER not in current:
        return FilePlan(
            path=path,
            action=PlanAction.BLOCKED,
            reason=("Target file exists but is not marked as owned by AgentSpec."),
            desired_content=None,
            current_digest=digest,
        )

    return FilePlan(
        path=path,
        action=PlanAction.UPDATE,
        reason="AgentSpec managed file differs from desired state.",
        desired_content=desired_content,
        current_digest=digest,
    )
