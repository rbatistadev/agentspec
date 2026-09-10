from __future__ import annotations

import re
import shutil
from pathlib import Path

from agentspec.harness.openspec.tasks_lint import (
    Issue,
    TaskPacket,
    add_issue,
    parse_tasks,
)

SPEC_SCENARIO_HEADING_RE = re.compile(r"^####\s+Scenario:\s*(.+?)\s*$")
DESIGN_HEADING_RE = re.compile(r"^(?:##|###)\s+(.+?)\s*$")

SCENARIO_REF_RE = re.compile(r"`\s*Scenario:\s*([^`]+?)\s*`", re.IGNORECASE)
DESIGN_REF_RE = re.compile(
    r"`\s*design\.md\s*`\s*(?:\u2192|->)\s*`\s*([^`]+?)\s*`",
    re.IGNORECASE,
)

ALLOWED_FILES_HEADING_RE = re.compile(
    r"^\s*[-*]\s*Allowed\s+(production|test)\s+files\s*:\s*$",
    re.IGNORECASE,
)
FILE_ENTRY_RE = re.compile(r"^\s*[-*]\s+`([^`]+)`\s*(.*)$")
CREATE_MARKER_RE = re.compile(r"(?:\u2014|\u2013|-)\s*CREATE\s*$", re.IGNORECASE)

COMMAND_RE = re.compile(r"`([^`]+)`")


def _normalize_reference(text: str) -> str:
    return re.sub(r"`+", "", text).strip()


def parse_tasks_file(tasks_path: Path) -> list[TaskPacket]:
    text = Path(tasks_path).read_text(encoding="utf-8")
    return parse_tasks(text.splitlines(), [])


def _spec_scenario_headings(change_root: Path) -> set[str]:
    headings: set[str] = set()
    specs_dir = change_root / "specs"

    if not specs_dir.is_dir():
        return headings

    for spec_path in specs_dir.glob("**/*.md"):
        for line in spec_path.read_text(encoding="utf-8").splitlines():
            match = SPEC_SCENARIO_HEADING_RE.match(line)
            if match:
                headings.add(_normalize_reference(match.group(1)))

    return headings


def _design_headings(change_root: Path) -> set[str]:
    headings: set[str] = set()
    design_path = change_root / "design.md"

    if not design_path.is_file():
        return headings

    for line in design_path.read_text(encoding="utf-8").splitlines():
        match = DESIGN_HEADING_RE.match(line)
        if match:
            headings.add(_normalize_reference(match.group(1)))

    return headings


def _check_spec_references(
    packet: TaskPacket,
    scenario_headings: set[str],
    issues: list[Issue],
) -> None:
    for line in packet.sections.get("spec contract", []):
        for match in SCENARIO_REF_RE.finditer(line):
            name = _normalize_reference(match.group(1))
            if name and name not in scenario_headings:
                add_issue(
                    issues,
                    "ERROR",
                    "EVIDENCE_UNRESOLVED_SPEC",
                    f"Spec scenario '{name}' does not resolve to any '#### Scenario:' heading.",
                    line=packet.start_line,
                    task=packet.task_id,
                )


def _check_design_references(
    packet: TaskPacket,
    design_headings: set[str],
    issues: list[Issue],
) -> None:
    for line in packet.sections.get("design contract", []):
        for match in DESIGN_REF_RE.finditer(line):
            heading = _normalize_reference(match.group(1))
            if heading and heading not in design_headings:
                add_issue(
                    issues,
                    "ERROR",
                    "EVIDENCE_UNRESOLVED_DESIGN",
                    f"Design heading '{heading}' does not resolve to any heading in design.md.",
                    line=packet.start_line,
                    task=packet.task_id,
                )


def _check_allowed_files(
    packet: TaskPacket,
    repo_root: Path,
    issues: list[Issue],
) -> None:
    mode: str | None = None

    for line in packet.sections.get("scope", []):
        heading_match = ALLOWED_FILES_HEADING_RE.match(line)
        if heading_match:
            mode = heading_match.group(1).lower()
            continue

        if mode is None:
            continue

        if re.match(r"^[-*]\s+", line):
            mode = None
            continue

        entry_match = FILE_ENTRY_RE.match(line)
        if not entry_match:
            continue

        rel = entry_match.group(1).strip()
        suffix = entry_match.group(2).strip()
        path = repo_root / rel

        if CREATE_MARKER_RE.search(suffix):
            if not path.parent.is_dir():
                add_issue(
                    issues,
                    "ERROR",
                    "EVIDENCE_MISSING_PARENT",
                    f"Allowed file '{rel}' is marked CREATE but its parent directory does not exist.",
                    line=packet.start_line,
                    task=packet.task_id,
                )
        elif not path.exists():
            add_issue(
                issues,
                "ERROR",
                "EVIDENCE_MISSING_FILE",
                f"Allowed file '{rel}' does not exist relative to the repository root.",
                line=packet.start_line,
                task=packet.task_id,
            )


def _check_verification_command(
    packet: TaskPacket,
    issues: list[Issue],
) -> None:
    text = "\n".join(packet.sections.get("primary verification", []))
    match = COMMAND_RE.search(text)

    if not match:
        return

    command = match.group(1).strip()
    tokens = command.split()

    if not tokens:
        return

    first_token = tokens[0].strip("'\"")

    if not first_token:
        return

    if shutil.which(first_token) is None:
        add_issue(
            issues,
            "WARNING",
            "EVIDENCE_COMMAND_UNRESOLVED",
            f"Primary verification command '{command}' references an executable that does not resolve on PATH.",
            line=packet.start_line,
            task=packet.task_id,
        )


def collect_evidence_issues(
    packets: list[TaskPacket],
    change_root: Path,
    repo_root: Path,
) -> list[Issue]:
    change_root = Path(change_root)
    repo_root = Path(repo_root)

    scenario_headings = _spec_scenario_headings(change_root)
    design_headings = _design_headings(change_root)

    issues: list[Issue] = []

    for packet in packets:
        _check_spec_references(packet, scenario_headings, issues)
        _check_design_references(packet, design_headings, issues)
        _check_allowed_files(packet, repo_root, issues)
        _check_verification_command(packet, issues)

    return issues
