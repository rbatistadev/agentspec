#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

TASK_CONTRACT_VERSION = "strict-v1"

GROUP_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")
TASK_RE = re.compile(
    r"^###\s+Task\s+(\d+\.\d+)\s+(?:—|–|-)\s+(.+?)\s*$",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")

TRACKED_CHECKBOX_RE = re.compile(
    r"^- \[([ xX])\]\s+"
    r"(\d+\.\d+)\s+"
    r"\[([^\]]+)\]\s+"
    r"(.+?)"
    r";\s*verify with\s+`([^`]+)`\s*$",
    re.IGNORECASE,
)

ANY_TASK_CHECKBOX_RE = re.compile(
    r"^- \[[ xX]\]\s+(\d+\.\d+)\b",
    re.IGNORECASE,
)

METADATA_RE = re.compile(
    r"<!--\s*"
    r"(task-contract|planning-baseline|openspec-change)"
    r"\s*:\s*(.*?)\s*-->",
    re.IGNORECASE,
)

PLACEHOLDER_RE = re.compile(
    r"<(?:"
    r"path|symbol|change|change-name|command|area|"
    r"application|layer|module|behavior|requirement|"
    r"scenario|task|task-id|sha|git-sha|name"
    r")(?:\s+[^>]*)?>",
    re.IGNORECASE,
)

VAGUE_VERIFICATION_RE = re.compile(
    r"\b("
    r"relevant tests?|"
    r"appropriate tests?|"
    r"verify manually|"
    r"manual verification|"
    r"tests? as needed|"
    r"run tests?"
    r")\b",
    re.IGNORECASE,
)

REQUIRED_SECTIONS = (
    "purpose",
    "spec contract",
    "design contract",
    "depends on",
    "scope",
    "read before editing",
    "verified current state",
    "required changes",
    "required behavior",
    "preserve",
    "forbidden changes",
    "tests to implement/update",
    "primary verification",
    "expected result",
    "done when",
    "stop and escalate if",
)


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    line: int | None = None
    task: str | None = None


@dataclass
class TaskPacket:
    task_id: str
    title: str
    group_id: str | None
    start_line: int
    end_line: int
    lines: list[str]
    sections: dict[str, list[str]]


def normalize_section(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def add_issue(
    issues: list[Issue],
    severity: str,
    code: str,
    message: str,
    *,
    line: int | None = None,
    task: str | None = None,
) -> None:
    issues.append(
        Issue(
            severity=severity,
            code=code,
            message=message,
            line=line,
            task=task,
        )
    )


def parse_metadata(lines: list[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}

    for line in lines:
        match = METADATA_RE.search(line)
        if not match:
            continue

        key = match.group(1).lower()
        value = match.group(2).strip()
        metadata[key] = value

    return metadata


def parse_sections(task_lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in task_lines:
        match = SECTION_RE.match(line.strip())
        if match:
            current = normalize_section(match.group(1))
            sections.setdefault(current, [])
            continue

        if current is not None:
            sections[current].append(line)

    return sections


def parse_tasks(lines: list[str], issues: list[Issue]) -> list[TaskPacket]:
    task_starts: list[tuple[int, re.Match[str], str | None]] = []
    current_group: str | None = None

    for index, line in enumerate(lines):
        group_match = GROUP_RE.match(line)
        if group_match:
            current_group = group_match.group(1)
            continue

        task_match = TASK_RE.match(line)
        if task_match:
            task_starts.append((index, task_match, current_group))

    tasks: list[TaskPacket] = []

    for position, (start, match, group_id) in enumerate(task_starts):
        end = (
            task_starts[position + 1][0]
            if position + 1 < len(task_starts)
            else len(lines)
        )

        # Stop at the next H2 group if it occurs before the next task.
        for index in range(start + 1, end):
            if GROUP_RE.match(lines[index]):
                end = index
                break

        packet_lines = lines[start:end]

        task = TaskPacket(
            task_id=match.group(1),
            title=match.group(2).strip(),
            group_id=group_id,
            start_line=start + 1,
            end_line=end,
            lines=packet_lines,
            sections=parse_sections(packet_lines),
        )
        tasks.append(task)

    if not tasks:
        add_issue(
            issues,
            "ERROR",
            "NO_TASKS",
            "No task packets using '### Task X.Y — ...' were found.",
        )

    return tasks


def nonempty(lines: Iterable[str]) -> bool:
    return any(line.strip() for line in lines)


def count_list_items(lines: Iterable[str]) -> int:
    return sum(1 for line in lines if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line))


def validate_metadata(
    path: Path,
    metadata: dict[str, str],
    issues: list[Issue],
) -> None:
    contract = metadata.get("task-contract")
    baseline = metadata.get("planning-baseline")
    change = metadata.get("openspec-change")

    if contract is None:
        add_issue(
            issues,
            "ERROR",
            "MISSING_TASK_CONTRACT",
            "Missing '<!-- task-contract: strict-v1 -->'.",
        )
    elif contract != TASK_CONTRACT_VERSION:
        add_issue(
            issues,
            "ERROR",
            "INVALID_TASK_CONTRACT",
            f"Expected task-contract '{TASK_CONTRACT_VERSION}', got '{contract}'.",
        )

    if baseline is None:
        add_issue(
            issues,
            "ERROR",
            "MISSING_BASELINE",
            "Missing '<!-- planning-baseline: <git-sha> -->'.",
        )
    elif not re.fullmatch(r"[0-9a-fA-F]{7,64}", baseline):
        add_issue(
            issues,
            "ERROR",
            "INVALID_BASELINE",
            f"Planning baseline is not a valid Git SHA: '{baseline}'.",
        )

    if change is None:
        add_issue(
            issues,
            "ERROR",
            "MISSING_CHANGE",
            "Missing '<!-- openspec-change: <change-name> -->'.",
        )
    elif not change.strip():
        add_issue(
            issues,
            "ERROR",
            "EMPTY_CHANGE",
            "openspec-change metadata is empty.",
        )

    # If this looks like openspec/changes/<name>/tasks.md, cross-check it.
    if (
        path.name.lower() == "tasks.md"
        and path.parent.parent.name == "changes"
        and change
        and path.parent.name != change
    ):
        add_issue(
            issues,
            "ERROR",
            "CHANGE_PATH_MISMATCH",
            (
                f"Metadata says change '{change}', but tasks.md lives under "
                f"'{path.parent.name}'."
            ),
        )


def validate_task_structure(
    task: TaskPacket,
    issues: list[Issue],
) -> None:
    major_group = task.task_id.split(".", 1)[0]

    if task.group_id is None:
        add_issue(
            issues,
            "ERROR",
            "TASK_WITHOUT_GROUP",
            "Task is not inside a numbered '## N. ...' group.",
            line=task.start_line,
            task=task.task_id,
        )
    elif task.group_id != major_group:
        add_issue(
            issues,
            "ERROR",
            "GROUP_ID_MISMATCH",
            (
                f"Task {task.task_id} is under group {task.group_id}, "
                f"but its ID requires group {major_group}."
            ),
            line=task.start_line,
            task=task.task_id,
        )

    missing = [section for section in REQUIRED_SECTIONS if section not in task.sections]

    for section in missing:
        add_issue(
            issues,
            "ERROR",
            "MISSING_SECTION",
            f"Missing mandatory section '**{section.title()}**'.",
            line=task.start_line,
            task=task.task_id,
        )

    for section in REQUIRED_SECTIONS:
        if section in task.sections and not nonempty(task.sections[section]):
            add_issue(
                issues,
                "ERROR",
                "EMPTY_SECTION",
                f"Section '**{section.title()}**' is empty.",
                line=task.start_line,
                task=task.task_id,
            )


def validate_checkbox(
    task: TaskPacket,
    issues: list[Issue],
) -> None:
    tracked: list[tuple[int, re.Match[str]]] = []

    for offset, line in enumerate(task.lines):
        match = TRACKED_CHECKBOX_RE.match(line.strip())
        if match:
            tracked.append((task.start_line + offset, match))

    if len(tracked) == 0:
        add_issue(
            issues,
            "ERROR",
            "MISSING_TRACKED_CHECKBOX",
            (
                "Task must contain exactly one tracked checkbox in the form "
                "'- [ ] X.Y [area] ...; verify with `<command>`'."
            ),
            line=task.start_line,
            task=task.task_id,
        )
        return

    if len(tracked) > 1:
        add_issue(
            issues,
            "ERROR",
            "MULTIPLE_TRACKED_CHECKBOXES",
            f"Task contains {len(tracked)} tracked checkboxes; expected exactly one.",
            line=task.start_line,
            task=task.task_id,
        )

    for line_no, match in tracked:
        checkbox_task_id = match.group(2)
        area = match.group(3).strip()
        command = match.group(5).strip()

        if checkbox_task_id != task.task_id:
            add_issue(
                issues,
                "ERROR",
                "CHECKBOX_ID_MISMATCH",
                (
                    f"Task heading is {task.task_id}, "
                    f"but checkbox is {checkbox_task_id}."
                ),
                line=line_no,
                task=task.task_id,
            )

        if not area:
            add_issue(
                issues,
                "ERROR",
                "EMPTY_AREA",
                "Tracked checkbox area is empty.",
                line=line_no,
                task=task.task_id,
            )

        if not command:
            add_issue(
                issues,
                "ERROR",
                "EMPTY_CHECKBOX_VERIFICATION",
                "Tracked checkbox has no verification command.",
                line=line_no,
                task=task.task_id,
            )

        if VAGUE_VERIFICATION_RE.search(command):
            add_issue(
                issues,
                "ERROR",
                "VAGUE_CHECKBOX_VERIFICATION",
                f"Verification command is not deterministic: '{command}'.",
                line=line_no,
                task=task.task_id,
            )

    # Catch another task ID checkbox hidden inside this packet.
    for offset, line in enumerate(task.lines):
        match = ANY_TASK_CHECKBOX_RE.match(line.strip())
        if match and match.group(1) != task.task_id:
            add_issue(
                issues,
                "ERROR",
                "FOREIGN_TASK_CHECKBOX",
                (
                    f"Task packet {task.task_id} contains checkbox "
                    f"for task {match.group(1)}."
                ),
                line=task.start_line + offset,
                task=task.task_id,
            )


def validate_contract_sections(
    task: TaskPacket,
    issues: list[Issue],
) -> None:
    spec = "\n".join(task.sections.get("spec contract", []))
    design = "\n".join(task.sections.get("design contract", []))
    scope = "\n".join(task.sections.get("scope", []))
    primary = "\n".join(task.sections.get("primary verification", []))
    stop = task.sections.get("stop and escalate if", [])
    read_before = task.sections.get("read before editing", [])

    if spec.strip():
        has_spec_reference = (
            "→" in spec or "->" in spec or "internal design task" in spec.lower()
        )
        if not has_spec_reference:
            add_issue(
                issues,
                "ERROR",
                "SPEC_CONTRACT_NOT_TRACEABLE",
                (
                    "Spec contract does not contain a traceable scenario reference "
                    "or the explicit internal-design-task marker."
                ),
                line=task.start_line,
                task=task.task_id,
            )

    if design.strip() and "design.md" not in design.lower():
        add_issue(
            issues,
            "WARNING",
            "DESIGN_CONTRACT_NOT_EXPLICIT",
            "Design contract does not explicitly reference design.md.",
            line=task.start_line,
            task=task.task_id,
        )

    if scope.strip():
        if "allowed production files" not in scope.lower():
            add_issue(
                issues,
                "ERROR",
                "MISSING_PRODUCTION_SCOPE",
                "Scope must explicitly declare 'Allowed production files'.",
                line=task.start_line,
                task=task.task_id,
            )

        if "allowed test files" not in scope.lower():
            add_issue(
                issues,
                "ERROR",
                "MISSING_TEST_SCOPE",
                "Scope must explicitly declare 'Allowed test files'.",
                line=task.start_line,
                task=task.task_id,
            )

        if "**" in scope or re.search(r"`[^`]*\*[^`]*`", scope):
            add_issue(
                issues,
                "WARNING",
                "BROAD_SCOPE_GLOB",
                "Scope contains a wildcard/glob; verify that the broad scope is justified.",
                line=task.start_line,
                task=task.task_id,
            )

    if primary.strip():
        if "`" not in primary and "```" not in primary:
            add_issue(
                issues,
                "ERROR",
                "PRIMARY_VERIFICATION_NOT_COMMAND",
                "Primary verification must contain an explicit command.",
                line=task.start_line,
                task=task.task_id,
            )

        if VAGUE_VERIFICATION_RE.search(primary):
            add_issue(
                issues,
                "ERROR",
                "VAGUE_PRIMARY_VERIFICATION",
                "Primary verification uses vague/non-deterministic wording.",
                line=task.start_line,
                task=task.task_id,
            )

    if stop and count_list_items(stop) < 3:
        add_issue(
            issues,
            "WARNING",
            "WEAK_STOP_CONDITIONS",
            (
                "STOP AND ESCALATE IF contains fewer than 3 explicit conditions. "
                "Confirm the worker has enough invalidation guards."
            ),
            line=task.start_line,
            task=task.task_id,
        )

    read_count = count_list_items(read_before)

    if read_count > 6:
        add_issue(
            issues,
            "WARNING",
            "LARGE_READ_SET",
            (
                f"Read before editing contains {read_count} items. "
                "Target 2–6 when possible to keep worker context narrow."
            ),
            line=task.start_line,
            task=task.task_id,
        )


def validate_placeholders(
    task: TaskPacket,
    issues: list[Issue],
) -> None:
    for offset, line in enumerate(task.lines):
        match = PLACEHOLDER_RE.search(line)
        if match:
            add_issue(
                issues,
                "ERROR",
                "UNRESOLVED_PLACEHOLDER",
                f"Unresolved template placeholder: '{match.group(0)}'.",
                line=task.start_line + offset,
                task=task.task_id,
            )


def parse_dependencies(task: TaskPacket) -> tuple[list[str], bool]:
    lines = task.sections.get("depends on", [])
    text = "\n".join(lines)

    dependencies = re.findall(r"\b\d+\.\d+\b", text)
    says_none = bool(re.search(r"\bnone\b", text, re.IGNORECASE))

    return list(dict.fromkeys(dependencies)), says_none


def validate_dependencies(
    tasks: list[TaskPacket],
    issues: list[Issue],
) -> None:
    task_ids = [task.task_id for task in tasks]
    task_set = set(task_ids)
    order = {task_id: index for index, task_id in enumerate(task_ids)}
    graph: dict[str, list[str]] = {task_id: [] for task_id in task_ids}

    for task in tasks:
        deps, says_none = parse_dependencies(task)

        if says_none and deps:
            add_issue(
                issues,
                "ERROR",
                "DEPENDENCY_NONE_CONFLICT",
                "Depends on contains both 'none' and task IDs.",
                line=task.start_line,
                task=task.task_id,
            )

        if not says_none and not deps:
            add_issue(
                issues,
                "ERROR",
                "DEPENDENCY_UNSPECIFIED",
                "Depends on must contain either 'none' or explicit task IDs.",
                line=task.start_line,
                task=task.task_id,
            )

        for dep in deps:
            if dep == task.task_id:
                add_issue(
                    issues,
                    "ERROR",
                    "SELF_DEPENDENCY",
                    f"Task {task.task_id} depends on itself.",
                    line=task.start_line,
                    task=task.task_id,
                )
                continue

            if dep not in task_set:
                add_issue(
                    issues,
                    "ERROR",
                    "UNKNOWN_DEPENDENCY",
                    f"Task depends on nonexistent task {dep}.",
                    line=task.start_line,
                    task=task.task_id,
                )
                continue

            graph[task.task_id].append(dep)

            if order[dep] >= order[task.task_id]:
                add_issue(
                    issues,
                    "ERROR",
                    "DEPENDENCY_ORDER",
                    (
                        f"Task {task.task_id} depends on {dep}, "
                        "but that dependency does not appear earlier."
                    ),
                    line=task.start_line,
                    task=task.task_id,
                )

    state: dict[str, int] = {task_id: 0 for task_id in task_ids}
    stack: list[str] = []

    def visit(task_id: str) -> None:
        if state[task_id] == 2:
            return

        if state[task_id] == 1:
            try:
                start = stack.index(task_id)
            except ValueError:
                start = 0

            cycle = stack[start:] + [task_id]

            add_issue(
                issues,
                "ERROR",
                "DEPENDENCY_CYCLE",
                "Dependency cycle detected: " + " -> ".join(cycle),
                task=task_id,
            )
            return

        state[task_id] = 1
        stack.append(task_id)

        for dep in graph[task_id]:
            visit(dep)

        stack.pop()
        state[task_id] = 2

    for task_id in task_ids:
        visit(task_id)


def validate_unique_ids(
    tasks: list[TaskPacket],
    issues: list[Issue],
) -> None:
    seen: dict[str, int] = {}

    for task in tasks:
        if task.task_id in seen:
            add_issue(
                issues,
                "ERROR",
                "DUPLICATE_TASK_ID",
                (
                    f"Task ID {task.task_id} is duplicated. "
                    f"First occurrence was line {seen[task.task_id]}."
                ),
                line=task.start_line,
                task=task.task_id,
            )
        else:
            seen[task.task_id] = task.start_line


def find_repo_root(start: Path) -> Path | None:
    current = start.resolve()

    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "openspec").is_dir():
            return candidate

    return None


def resolve_tasks_path(args: argparse.Namespace) -> Path:
    if args.change:
        root = find_repo_root(Path.cwd())
        if root is None:
            raise ValueError(
                "Could not find an OpenSpec repository root from the current directory."
            )

        return root / "openspec" / "changes" / args.change / "tasks.md"

    if args.path:
        return Path(args.path).expanduser().resolve()

    raise ValueError("Provide either a tasks.md path or --change <name>.")


def render_text(
    path: Path,
    tasks: list[TaskPacket],
    issues: list[Issue],
) -> None:
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    warnings = [issue for issue in issues if issue.severity == "WARNING"]

    print()
    print("OpenSpec tasks.md strict linter")
    print("=" * 32)
    print(f"File:     {path}")
    print(f"Tasks:    {len(tasks)}")
    print(f"Errors:   {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print()

    if issues:
        for issue in issues:
            location_parts: list[str] = []

            if issue.task:
                location_parts.append(f"task {issue.task}")

            if issue.line:
                location_parts.append(f"line {issue.line}")

            location = f" ({', '.join(location_parts)})" if location_parts else ""

            print(f"[{issue.severity}] {issue.code}{location}: {issue.message}")

        print()

    if errors:
        print("RESULT: FAIL")
    else:
        print("RESULT: PASS")


def render_json(
    path: Path,
    tasks: list[TaskPacket],
    metadata: dict[str, str],
    issues: list[Issue],
) -> None:
    errors = sum(issue.severity == "ERROR" for issue in issues)
    warnings = sum(issue.severity == "WARNING" for issue in issues)

    result = {
        "status": "FAIL" if errors else "PASS",
        "file": str(path),
        "contract": metadata.get("task-contract"),
        "change": metadata.get("openspec-change"),
        "planning_baseline": metadata.get("planning-baseline"),
        "task_count": len(tasks),
        "task_ids": [task.task_id for task in tasks],
        "errors": errors,
        "warnings": warnings,
        "issues": [asdict(issue) for issue in issues],
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))


def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Deterministic structural linter for strict-v1 "
            "OpenSpec tasks.md execution packets."
        )
    )

    parser.add_argument(
        "path",
        nargs="?",
        help="Path to tasks.md",
    )

    parser.add_argument(
        "--change",
        help=(
            "Resolve openspec/changes/<change>/tasks.md from the current repository."
        ),
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )

    return parser


def main(argv: list[str] | None = None, *, prog: str | None = None) -> int:
    parser = build_parser(prog)
    args = parser.parse_args(argv)

    if args.path and args.change:
        parser.error("Use either a positional path or --change, not both.")

    try:
        path = resolve_tasks_path(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not path.is_file():
        print(f"ERROR: tasks.md not found: {path}", file=sys.stderr)
        return 2

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Could not read {path}: {exc}", file=sys.stderr)
        return 2

    lines = text.splitlines()
    issues: list[Issue] = []

    metadata = parse_metadata(lines)
    tasks = parse_tasks(lines, issues)

    validate_metadata(path, metadata, issues)
    validate_unique_ids(tasks, issues)

    for task in tasks:
        validate_task_structure(task, issues)
        validate_checkbox(task, issues)
        validate_contract_sections(task, issues)
        validate_placeholders(task, issues)

    validate_dependencies(tasks, issues)

    issues.sort(
        key=lambda issue: (
            0 if issue.severity == "ERROR" else 1,
            issue.line if issue.line is not None else 10**9,
            issue.code,
        )
    )

    if args.json:
        render_json(path, tasks, metadata, issues)
    else:
        render_text(path, tasks, issues)

    return 1 if any(issue.severity == "ERROR" for issue in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
