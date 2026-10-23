from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentspec.core.managed_blocks import (
    ManagedBlockError,
    upsert_managed_block,
)


class PlanAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    NO_CHANGE = "NO_CHANGE"
    BLOCKED = "BLOCKED"
    DELETE = "DELETE"


@dataclass(frozen=True)
class FilePlan:
    path: Path
    action: PlanAction
    reason: str
    desired_content: str | None
    current_digest: str | None


class ApplyError(RuntimeError):
    pass


def content_digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def plan_managed_block(
    path: Path,
    block_id: str,
    desired_body: str,
) -> FilePlan:
    exists = path.exists()
    current = _read_text(path) if exists else ""

    try:
        desired = upsert_managed_block(current, block_id, desired_body)
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


def plan_managed_file(
    path: Path,
    desired_content: str,
    marker: str,
) -> FilePlan:
    if marker not in desired_content:
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

    if marker not in current:
        return FilePlan(
            path=path,
            action=PlanAction.BLOCKED,
            reason="Target file exists but is not marked as owned by AgentSpec.",
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


def plan_stale_managed_file(path: Path, marker: str) -> FilePlan | None:
    if not path.exists():
        return None

    current = _read_text(path)
    digest = content_digest(current)

    if marker not in current:
        return FilePlan(
            path=path,
            action=PlanAction.BLOCKED,
            reason="Obsolete target exists but is not marked as owned by AgentSpec.",
            desired_content=None,
            current_digest=digest,
        )

    return FilePlan(
        path=path,
        action=PlanAction.DELETE,
        reason="Obsolete AgentSpec-managed resource must be removed.",
        desired_content=None,
        current_digest=digest,
    )


def _read_current(path: Path) -> str | None:
    if not path.exists():
        return None

    return path.read_text(encoding="utf-8")


def _verify_precondition(plan: FilePlan) -> None:
    current = _read_current(plan.path)

    if plan.action == PlanAction.CREATE:
        if current is not None:
            raise ApplyError(
                f"Refusing to create {plan.path}: file appeared after planning."
            )
        return

    if plan.action in {PlanAction.UPDATE, PlanAction.DELETE}:
        if current is None:
            raise ApplyError(
                f"Refusing to {plan.action.value.lower()} {plan.path}: "
                "file disappeared after planning."
            )

        if content_digest(current) != plan.current_digest:
            raise ApplyError(
                f"Refusing to {plan.action.value.lower()} {plan.path}: "
                "file changed after planning."
            )


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            delete=False,
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        ) as handle:
            handle.write(content)
            temp_path = Path(handle.name)

        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def apply_file(plan: FilePlan) -> None:
    if plan.action == PlanAction.BLOCKED:
        raise ApplyError(
            f"Cannot apply blocked plan for {plan.path}: {plan.reason}"
        )

    if plan.action == PlanAction.NO_CHANGE:
        return

    if plan.action == PlanAction.DELETE:
        _verify_precondition(plan)
        plan.path.unlink()
        return

    if plan.desired_content is None:
        raise ApplyError(f"Plan for {plan.path} has no desired content.")

    _verify_precondition(plan)
    _atomic_write(plan.path, plan.desired_content)
