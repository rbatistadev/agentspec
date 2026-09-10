from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentSpecPaths:
    openspec_config_dir: Path
    openspec_config_file: Path

    opencode_config_dir: Path
    opencode_config_file: Path
    opencode_agents_dir: Path
    opencode_agents_md: Path
    opencode_commands_dir: Path


def _env_path(name: str) -> Path | None:
    value = os.environ.get(name)

    if not value:
        return None

    return Path(value).expanduser()


def resolve_openspec_config_dir() -> Path:
    """
    Resolve OpenSpec's machine-level configuration directory.

    Precedence:
    1. XDG_CONFIG_HOME
    2. APPDATA on Windows
    3. ~/.config on macOS/Linux
    """
    xdg_config_home = _env_path("XDG_CONFIG_HOME")

    if xdg_config_home is not None:
        return xdg_config_home / "openspec"

    if os.name == "nt":
        appdata = _env_path("APPDATA")

        if appdata is not None:
            return appdata / "openspec"

    return Path.home() / ".config" / "openspec"


def resolve_opencode_config_dir() -> Path:
    """
    Resolve the directory AgentSpec should use for OpenCode-managed
    global resources such as agents.

    Precedence:
    1. OPENCODE_CONFIG_DIR
    2. XDG_CONFIG_HOME
    3. ~/.config/opencode
    """
    custom_config_dir = _env_path("OPENCODE_CONFIG_DIR")

    if custom_config_dir is not None:
        return custom_config_dir

    xdg_config_home = _env_path("XDG_CONFIG_HOME")

    if xdg_config_home is not None:
        return xdg_config_home / "opencode"

    return Path.home() / ".config" / "opencode"


def resolve_paths() -> AgentSpecPaths:
    openspec_dir = resolve_openspec_config_dir()
    opencode_dir = resolve_opencode_config_dir()

    return AgentSpecPaths(
        openspec_config_dir=openspec_dir,
        openspec_config_file=openspec_dir / "config.json",
        opencode_config_dir=opencode_dir,
        opencode_config_file=opencode_dir / "opencode.json",
        opencode_agents_dir=opencode_dir / "agents",
        opencode_agents_md=opencode_dir / "AGENTS.md",
        opencode_commands_dir=opencode_dir / "commands",
    )