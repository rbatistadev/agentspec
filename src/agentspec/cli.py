from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version

from agentspec.commands import doctor, setup
from agentspec.harness.openspec import tasks_lint


def get_version() -> str:
    try:
        return version("agentspec")
    except PackageNotFoundError:
        return "0.0.0-dev"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentspec",
        description="AgentSpec CLI",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "doctor",
        help="Check the AgentSpec environment.",
    )

    setup_parser = subparsers.add_parser(
        "setup",
        help="Configure AgentSpec integrations.",
    )

    setup_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the changes AgentSpec would make without applying them.",
    )

    openspec_parser = subparsers.add_parser(
        "openspec",
        help="OpenSpec harness commands.",
    )

    openspec_subparsers = openspec_parser.add_subparsers(
        dest="openspec_command",
    )

    tasks_parser = openspec_subparsers.add_parser(
        "tasks",
        help="OpenSpec task commands.",
    )

    tasks_subparsers = tasks_parser.add_subparsers(
        dest="tasks_command",
    )

    # tasks_lint owns the arguments after this point.
    tasks_subparsers.add_parser(
        "lint",
        help="Lint an OpenSpec tasks.md execution contract.",
        add_help=False,
    )

    return parser


def main() -> int:
    parser = build_parser()

    # parse_known_args is intentional:
    # the tasks linter owns its own CLI arguments.
    args, remaining = parser.parse_known_args()

    if args.command == "doctor":
        if remaining:
            parser.error(
                f"unrecognized arguments: {' '.join(remaining)}"
            )

        return doctor.run()

    if args.command == "setup":
        if remaining:
            parser.error(
                f"unrecognized arguments: {' '.join(remaining)}"
            )

        return setup.run(dry_run=args.dry_run)

    if (
        args.command == "openspec"
        and args.openspec_command == "tasks"
        and args.tasks_command == "lint"
    ):
        return tasks_lint.main(
            remaining,
            prog="agentspec openspec tasks lint",
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())