import tempfile
import unittest
from pathlib import Path

from agentspec.core.managed_files import PlanAction
from agentspec.integrations.codex.apply import apply_plan
from agentspec.integrations.codex.paths import CodexPaths
from agentspec.integrations.codex.plan import build_plan
from agentspec.integrations.codex.resources import (
    MANAGED_TOML_MARKER,
    load_global_instructions,
    load_managed_agents,
    load_managed_skills,
)


class CodexPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        codex_dir = root / ".codex"
        self.paths = CodexPaths(
            config_dir=codex_dir,
            config_file=codex_dir / "config.toml",
            agents_md=codex_dir / "AGENTS.md",
            agents_dir=codex_dir / "agents",
            skills_dir=root / ".agents" / "skills",
        )

    def _complete_plan(self):
        return build_plan(
            self.paths,
            load_global_instructions(),
            load_managed_agents(),
            load_managed_skills(),
        )

    def test_complete_setup_is_idempotent(self):
        first = self._complete_plan()
        apply_plan(first)
        second = self._complete_plan()

        self.assertEqual(second.agents_md.action, PlanAction.NO_CHANGE)
        self.assertTrue(
            all(item.action == PlanAction.NO_CHANGE for item in second.agents)
        )
        self.assertTrue(
            all(item.action == PlanAction.NO_CHANGE for item in second.skills)
        )

    def test_unowned_agent_is_blocked(self):
        path = self.paths.agents_dir / "sample.toml"
        path.parent.mkdir(parents=True)
        path.write_text('name = "mine"\n', encoding="utf-8")

        plan = build_plan(
            self.paths,
            "global",
            managed_agents={
                "sample.toml": f"{MANAGED_TOML_MARKER}\nname = \"managed\"\n"
            },
        )

        self.assertEqual(plan.agents[0].action, PlanAction.BLOCKED)


if __name__ == "__main__":
    unittest.main()
