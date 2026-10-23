#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from agentspec.harness.openspec.tasks_lint import (
    Issue,
    add_issue,
    find_repo_root,
    parse_metadata,
)


def run_guard(repo_root: Path | None) -> dict:  # noqa: PLR0912
    changes: list[dict] = []
    issues: list[Issue] = []

    if repo_root is None:
        return {
            "status": "PASS",
            "exit_code": 0,
            "scanned": 0,
            "changes": [],
            "issues": [],
        }

    changes_dir = Path(repo_root) / "openspec" / "changes"

    if not changes_dir.is_dir():
        return {
            "status": "PASS",
            "exit_code": 0,
            "scanned": 0,
            "changes": [],
            "issues": [],
        }

    for change_dir in sorted(changes_dir.iterdir(), key=lambda path: path.name):
        if not change_dir.is_dir():
            continue

        if "archive" in change_dir.relative_to(changes_dir).parts:
            continue

        name = change_dir.name
        tasks_path = change_dir / "tasks.md"
        change_issues: list[Issue] = []

        if not tasks_path.exists():
            status = "not_compiled"
            contract = None
        else:
            try:
                text = tasks_path.read_text(encoding="utf-8")
            except OSError as exc:
                status = "tool_error"
                contract = None
                add_issue(
                    change_issues,
                    "ERROR",
                    "TOOL_ERROR",
                    f"Change '{name}' tasks.md could not be read: {exc}",
                )
            else:
                contract = parse_metadata(text.splitlines()).get("task-contract")
                if contract == "strict-v1":
                    status = "strict"
                else:
                    status = "non_strict"
                    found = contract if contract else "missing"
                    add_issue(
                        change_issues,
                        "ERROR",
                        "NON_STRICT_TASKS",
                        (
                            f"Change '{name}' tasks.md is not strict-v1 "
                            f"(found: {found}). Recompile with "
                            f"/agentspec/openspec/continue {name}."
                        ),
                    )

        issues.extend(change_issues)
        changes.append(
            {
                "name": name,
                "tasks_path": str(tasks_path),
                "contract": contract,
                "status": status,
                "issues": [asdict(issue) for issue in change_issues],
            }
        )

    if any(change["status"] == "tool_error" for change in changes):
        status = "TOOL_ERROR"
        exit_code = 2
    elif any(change["status"] == "non_strict" for change in changes):
        status = "FAIL"
        exit_code = 1
    else:
        status = "PASS"
        exit_code = 0

    return {
        "status": status,
        "exit_code": exit_code,
        "scanned": len(changes),
        "changes": changes,
        "issues": [asdict(issue) for issue in issues],
    }


def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Repo-wide guard flagging active OpenSpec changes whose "
            "tasks.md is not strict-v1."
        ),
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the verdict as JSON.",
    )

    return parser


def main(argv: list[str] | None = None, *, prog: str | None = None) -> int:
    parser = build_parser(prog)
    args = parser.parse_args(argv)

    verdict = run_guard(find_repo_root(Path.cwd()))

    if args.json:
        print(json.dumps(verdict, indent=2, ensure_ascii=False))
    else:
        print(f"Guard: {verdict['status']} (scanned {verdict['scanned']})")
        for issue in verdict["issues"]:
            print(f"[{issue['severity']}] {issue['code']}: {issue['message']}")

    return verdict["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
