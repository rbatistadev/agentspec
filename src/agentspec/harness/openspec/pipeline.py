from __future__ import annotations

import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path

from agentspec.harness.openspec import evidence, tasks_lint


def _gate(name: str, status: str, issues: list[dict]) -> dict:
    return {"name": name, "status": status, "issues": issues}


def _issue_dict(
    severity: str,
    code: str,
    message: str,
    line: int | None = None,
    task: str | None = None,
) -> dict:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "line": line,
        "task": task,
    }


def _run_openspec_validate(change_name: str, repo_root: Path) -> dict:
    executable = shutil.which("openspec")

    if executable is None:
        return _gate(
            "openspec validate",
            "TOOL_ERROR",
            [_issue_dict("ERROR", "TOOL_ERROR", "openspec executable was not found on PATH.")],
        )

    command = [executable, "validate", "--strict", "--no-interactive", change_name]

    # npm/global Windows shims are .cmd/.bat and cannot be CreateProcess'd directly.
    if executable.lower().endswith((".cmd", ".bat")):
        command = ["cmd", "/c", *command]

    try:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return _gate(
            "openspec validate",
            "TOOL_ERROR",
            [_issue_dict("ERROR", "TOOL_ERROR", f"Could not run openspec validate: {exc}")],
        )

    if completed.returncode == 0:
        return _gate("openspec validate", "PASS", [])

    detail = (completed.stdout or completed.stderr or "").strip()
    return _gate(
        "openspec validate",
        "FAIL",
        [
            _issue_dict(
                "ERROR",
                "OPENSPEC_VALIDATE_FAILED",
                detail or f"openspec validate exited with code {completed.returncode}",
            )
        ],
    )


def _run_lint_gate(change_name: str, repo_root: Path) -> dict:
    tasks_path = repo_root / "openspec" / "changes" / change_name / "tasks.md"

    try:
        text = tasks_path.read_text(encoding="utf-8")
    except OSError as exc:
        return _gate(
            "lint",
            "TOOL_ERROR",
            [_issue_dict("ERROR", "TOOL_ERROR", f"Could not read {tasks_path}: {exc}")],
        )

    lines = text.splitlines()
    issues: list[tasks_lint.Issue] = []

    metadata = tasks_lint.parse_metadata(lines)
    tasks = tasks_lint.parse_tasks(lines, issues)

    tasks_lint.validate_metadata(tasks_path, metadata, issues)
    tasks_lint.validate_unique_ids(tasks, issues)

    for task in tasks:
        tasks_lint.validate_task_structure(task, issues)
        tasks_lint.validate_checkbox(task, issues)
        tasks_lint.validate_contract_sections(task, issues)
        tasks_lint.validate_placeholders(task, issues)

    tasks_lint.validate_dependencies(tasks, issues)

    issues.sort(
        key=lambda issue: (
            0 if issue.severity == "ERROR" else 1,
            issue.line if issue.line is not None else 10**9,
            issue.code,
        )
    )

    has_error = any(issue.severity == "ERROR" for issue in issues)
    return _gate("lint", "FAIL" if has_error else "PASS", [asdict(issue) for issue in issues])


def _run_evidence_gate(change_name: str, repo_root: Path) -> dict:
    change_root = repo_root / "openspec" / "changes" / change_name
    tasks_path = change_root / "tasks.md"

    try:
        packets = evidence.parse_tasks_file(tasks_path)
    except OSError as exc:
        return _gate(
            "evidence",
            "TOOL_ERROR",
            [_issue_dict("ERROR", "TOOL_ERROR", f"Could not read {tasks_path}: {exc}")],
        )

    issues = evidence.collect_evidence_issues(packets, change_root, repo_root)
    has_error = any(issue.severity == "ERROR" for issue in issues)
    return _gate("evidence", "FAIL" if has_error else "PASS", [asdict(issue) for issue in issues])


def run_pipeline(change_name: str, repo_root: Path) -> dict:
    repo_root = Path(repo_root)
    gates: list[dict] = []

    for runner in (_run_openspec_validate, _run_lint_gate, _run_evidence_gate):
        result = runner(change_name, repo_root)
        gates.append(result)

        if result["status"] == "TOOL_ERROR":
            return {"status": "TOOL_ERROR", "exit_code": 2, "gates": gates}

    any_fail = any(gate["status"] == "FAIL" for gate in gates)
    status = "FAIL" if any_fail else "PASS"
    exit_code = 1 if any_fail else 0

    return {"status": status, "exit_code": exit_code, "gates": gates}
