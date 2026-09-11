import tomllib
import unittest

from agentspec.integrations.codex.resources import (
    MANAGED_MARKDOWN_MARKER,
    MANAGED_TOML_MARKER,
    load_managed_agents,
    load_managed_skills,
)


class CodexResourcesTests(unittest.TestCase):
    def test_opencode_agents_are_rendered_as_valid_codex_agents(self):
        agents = load_managed_agents()

        self.assertEqual(len(agents), 7)
        for filename, content in agents.items():
            self.assertTrue(filename.endswith(".toml"))
            self.assertIn(MANAGED_TOML_MARKER, content)
            parsed = tomllib.loads(content)
            self.assertEqual(parsed["name"], filename.removesuffix(".toml"))
            self.assertNotIn("model", parsed)

        orchestrator = tomllib.loads(
            agents["agentspec-openspec-orchestrator.toml"]
        )
        self.assertIn(
            "built-in Codex worker agent",
            orchestrator["developer_instructions"],
        )
        self.assertNotIn(
            "OpenCode",
            orchestrator["developer_instructions"],
        )

    def test_opencode_commands_are_rendered_as_codex_skills(self):
        skills = load_managed_skills()

        self.assertEqual(len(skills), 11)
        self.assertIn(
            "agentspec-openspec-apply/SKILL.md",
            skills,
        )
        for relative_path, content in skills.items():
            name = relative_path.split("/", 1)[0]
            self.assertIn(f"name: {name}", content)
            self.assertIn(MANAGED_MARKDOWN_MARKER, content)
            self.assertNotIn("$ARGUMENTS", content)
            self.assertIn("custom agent", content)


if __name__ == "__main__":
    unittest.main()
