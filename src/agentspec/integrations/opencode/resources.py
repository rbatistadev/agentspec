from __future__ import annotations

from importlib.resources import files

STALE_MANAGED_COMMANDS = (
    "agentspec/audit.md",
    "agentspec/tasks.md",
)


def load_global_instructions() -> str:
    resource = (
        files("agentspec.integrations.opencode")
        / "templates"
        / "global-instructions.md"
    )

    return resource.read_text(encoding="utf-8")


def load_managed_agents() -> dict[str, str]:
    agents_dir = files("agentspec.integrations.opencode") / "templates" / "agents"

    return {
        "agentspec-openspec-orchestrator.md": (
            agents_dir / "openspec-orchestrator.md"
        ).read_text(encoding="utf-8"),
        "agentspec-openspec-apply-worker.md": (
            agents_dir / "openspec-apply-worker.md"
        ).read_text(encoding="utf-8"),
        "agentspec-openspec-recon.md": (agents_dir / "openspec-recon.md").read_text(
            encoding="utf-8"
        ),
        "agentspec-openspec-reason.md": (agents_dir / "openspec-reason.md").read_text(
            encoding="utf-8"
        ),
        "agentspec-openspec-architect.md": (
            agents_dir / "openspec-architect.md"
        ).read_text(encoding="utf-8"),
        "agentspec-openspec-taskwriter.md": (
            agents_dir / "openspec-taskwriter.md"
        ).read_text(encoding="utf-8"),
        "agentspec-openspec-auditor.md": (agents_dir / "openspec-auditor.md").read_text(
            encoding="utf-8"
        ),
    }


def load_managed_commands() -> dict[str, str]:
    commands_dir = files("agentspec.integrations.opencode") / "templates" / "commands"
    openspec_dir = commands_dir / "agentspec" / "openspec"
    names = (
        "explore",
        "new",
        "continue",
        "status",
        "update",
        "audit",
        "apply",
        "verify",
        "sync",
        "archive",
        "bulk-archive",
    )

    return {
        f"agentspec/openspec/{name}.md": (openspec_dir / f"{name}.md").read_text(
            encoding="utf-8"
        )
        for name in names
    }
