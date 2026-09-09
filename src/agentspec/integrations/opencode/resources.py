from __future__ import annotations

from importlib.resources import files


def load_global_instructions() -> str:
    resource = (
        files("agentspec.integrations.opencode")
        / "templates"
        / "global-instructions.md"
    )

    return resource.read_text(encoding="utf-8")

def load_managed_agents() -> dict[str, str]:
    agents_dir = (
        files("agentspec.integrations.opencode")
        / "templates"
        / "agents"
    )

    return {
        "agentspec-openspec-recon.md": (
            agents_dir / "openspec-recon.md"
        ).read_text(encoding="utf-8"),
        "agentspec-openspec-reason.md": (
            agents_dir / "openspec-reason.md"
        ).read_text(encoding="utf-8"),
        "agentspec-openspec-architect.md": (
            agents_dir / "openspec-architect.md"
        ).read_text(encoding="utf-8"),
        "agentspec-openspec-taskwriter.md": (
            agents_dir / "openspec-taskwriter.md"
        ).read_text(encoding="utf-8"),
        "agentspec-openspec-auditor.md": (
            agents_dir / "openspec-auditor.md"
        ).read_text(encoding="utf-8"),
    }