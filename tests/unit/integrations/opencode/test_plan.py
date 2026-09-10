import tempfile
import unittest
from pathlib import Path

from agentspec.core.paths import AgentSpecPaths
from agentspec.integrations.opencode.apply import apply_plan
from agentspec.integrations.opencode.plan import (
    MANAGED_FILE_MARKER,
    PlanAction,
    build_plan,
)
from agentspec.integrations.opencode.resources import (
    STALE_MANAGED_COMMANDS,
    load_global_instructions,
    load_managed_agents,
    load_managed_commands,
)


class OpenCodePlanTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        opencode_dir = root / "opencode"
        openspec_dir = root / "openspec"
        self.paths = AgentSpecPaths(
            openspec_config_dir=openspec_dir,
            openspec_config_file=openspec_dir / "config.json",
            opencode_config_dir=opencode_dir,
            opencode_config_file=opencode_dir / "opencode.json",
            opencode_agents_dir=opencode_dir / "agents",
            opencode_agents_md=opencode_dir / "AGENTS.md",
            opencode_commands_dir=opencode_dir / "commands",
        )
        self.command_path = opencode_dir / "commands" / "agentspec" / "sample.md"
        self.desired = f"{MANAGED_FILE_MARKER}\ndesired\n"

    def _plan_command(self):
        return build_plan(
            self.paths,
            "global",
            managed_commands={"agentspec/sample.md": self.desired},
        ).commands[0]

    def _write_command(self, content):
        self.command_path.parent.mkdir(parents=True, exist_ok=True)
        self.command_path.write_text(content, encoding="utf-8")

    def test_missing_managed_command_is_created(self):
        self.assertEqual(self._plan_command().action, PlanAction.CREATE)

    def test_identical_managed_command_is_unchanged(self):
        self._write_command(self.desired)

        self.assertEqual(self._plan_command().action, PlanAction.NO_CHANGE)

    def test_changed_owned_command_is_updated(self):
        self._write_command(f"{MANAGED_FILE_MARKER}\nold\n")

        self.assertEqual(self._plan_command().action, PlanAction.UPDATE)

    def test_existing_unowned_command_is_blocked(self):
        self._write_command("user owned\n")

        self.assertEqual(self._plan_command().action, PlanAction.BLOCKED)

    def _stale_plan(self):
        return build_plan(
            self.paths,
            "global",
            stale_managed_commands=STALE_MANAGED_COMMANDS,
        )

    def _stale_path(self):
        return self.paths.opencode_commands_dir / STALE_MANAGED_COMMANDS[0]

    def test_owned_obsolete_command_is_deleted(self):
        stale_path = self._stale_path()
        stale_path.parent.mkdir(parents=True, exist_ok=True)
        stale_path.write_text(f"{MANAGED_FILE_MARKER}\nold\n", encoding="utf-8")

        plan = self._stale_plan()

        self.assertEqual(plan.commands[0].action, PlanAction.DELETE)
        apply_plan(plan)
        self.assertFalse(stale_path.exists())

    def test_unowned_obsolete_command_is_blocked(self):
        stale_path = self._stale_path()
        stale_path.parent.mkdir(parents=True, exist_ok=True)
        stale_path.write_text("user owned\n", encoding="utf-8")

        self.assertEqual(self._stale_plan().commands[0].action, PlanAction.BLOCKED)

    def test_missing_obsolete_command_has_no_action(self):
        self.assertEqual(self._stale_plan().commands, ())

    def test_complete_setup_is_idempotent_after_cleanup(self):
        stale_path = self._stale_path()
        stale_path.parent.mkdir(parents=True, exist_ok=True)
        stale_path.write_text(f"{MANAGED_FILE_MARKER}\nold\n", encoding="utf-8")

        first = build_plan(
            self.paths,
            load_global_instructions(),
            load_managed_agents(),
            load_managed_commands(),
            STALE_MANAGED_COMMANDS,
        )
        apply_plan(first)
        second = build_plan(
            self.paths,
            load_global_instructions(),
            load_managed_agents(),
            load_managed_commands(),
            STALE_MANAGED_COMMANDS,
        )

        self.assertEqual(second.agents_md.action, PlanAction.NO_CHANGE)
        self.assertTrue(
            all(plan.action == PlanAction.NO_CHANGE for plan in second.agents)
        )
        self.assertTrue(
            all(plan.action == PlanAction.NO_CHANGE for plan in second.commands)
        )
        self.assertEqual(len(second.commands), len(load_managed_commands()))
        self.assertFalse(stale_path.exists())


if __name__ == "__main__":
    unittest.main()
