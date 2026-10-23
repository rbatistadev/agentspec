from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodexPaths:
    config_dir: Path
    config_file: Path
    agents_md: Path
    agents_dir: Path
    skills_dir: Path


def resolve_codex_paths() -> CodexPaths:
    codex_home = Path(
        os.environ.get("CODEX_HOME", Path.home() / ".codex")
    ).expanduser()

    return CodexPaths(
        config_dir=codex_home,
        config_file=codex_home / "config.toml",
        agents_md=codex_home / "AGENTS.md",
        agents_dir=codex_home / "agents",
        skills_dir=Path.home() / ".agents" / "skills",
    )
