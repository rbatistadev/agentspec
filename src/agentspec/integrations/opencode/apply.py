from __future__ import annotations

import os
import tempfile
from pathlib import Path

from agentspec.integrations.opencode.plan import (
    FilePlan,
    OpenCodePlan,
    PlanAction,
    content_digest,
)


class ApplyError(RuntimeError):
    pass


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

    if plan.action == PlanAction.UPDATE:
        if current is None:
            raise ApplyError(
                f"Refusing to update {plan.path}: file disappeared after planning."
            )

        current_digest = content_digest(current)

        if current_digest != plan.current_digest:
            raise ApplyError(
                f"Refusing to update {plan.path}: "
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


def _apply_file(plan: FilePlan) -> None:
    if plan.action == PlanAction.BLOCKED:
        raise ApplyError(
            f"Cannot apply blocked plan for {plan.path}: {plan.reason}"
        )

    if plan.action == PlanAction.NO_CHANGE:
        return

    if plan.desired_content is None:
        raise ApplyError(
            f"Plan for {plan.path} has no desired content."
        )

    _verify_precondition(plan)
    _atomic_write(plan.path, plan.desired_content)


def apply_plan(plan: OpenCodePlan) -> None:
    _apply_file(plan.agents_md)

    for agent in plan.agents:
        _apply_file(agent)