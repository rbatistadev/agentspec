import os
import tempfile
import unittest

from agentspec.integrations.opencode.plan import MANAGED_FILE_MARKER
from agentspec.integrations.opencode.resources import (
    load_managed_agents,
    load_managed_commands,
)


EXPECTED_COMMANDS = {
    f"agentspec/openspec/{name}.md"
    for name in (
        "explore",
        "new",
        "continue",
        "status",
        "update",
        "audit",
        "apply",
        "verify",
        "sync",
        "archive",
        "bulk-archive",
    )
}


class OpenCodeResourcesTests(unittest.TestCase):
    def test_orchestrator_is_a_managed_agent(self):
        agents = load_managed_agents()

        self.assertIn("agentspec-openspec-orchestrator.md", agents)
        self.assertIn(
            "model: opencode-go/deepseek-v4-flash",
            agents["agentspec-openspec-orchestrator.md"],
        )
        self.assertIn(
            MANAGED_FILE_MARKER,
            agents["agentspec-openspec-orchestrator.md"],
        )

    def test_apply_worker_is_a_managed_cheap_agent(self):
        agents = load_managed_agents()

        self.assertIn("agentspec-openspec-apply-worker.md", agents)
        self.assertIn(
            "model: opencode-go/deepseek-v4-flash",
            agents["agentspec-openspec-apply-worker.md"],
        )
        self.assertIn(
            MANAGED_FILE_MARKER,
            agents["agentspec-openspec-apply-worker.md"],
        )

    def test_recon_agent_cannot_edit_or_delegate(self):
        recon = load_managed_agents()["agentspec-openspec-recon.md"]

        self.assertIn("action: edit", recon)
        self.assertIn("action: subagent", recon)
        self.assertGreaterEqual(recon.count("effect: deny"), 2)

    def test_orchestrator_routes_apply_to_the_apply_worker(self):
        orchestrator = load_managed_agents()[
            "agentspec-openspec-orchestrator.md"
        ]

        self.assertIn(
            'resource: "agentspec-openspec-apply-worker"',
            orchestrator,
        )
        self.assertIn(
            "delegate the named change synchronously to\n"
            "agentspec-openspec-apply-worker",
            orchestrator,
        )

    def test_complete_public_command_surface_is_loaded(self):
        commands = load_managed_commands()

        self.assertEqual(set(commands), EXPECTED_COMMANDS)
        for path, content in commands.items():
            self.assertTrue(content.startswith("---\n"))
            self.assertIn(MANAGED_FILE_MARKER, content)
            self.assertGreater(
                content.index(MANAGED_FILE_MARKER),
                content.find("---", 3),
            )
            self.assertIn("subagent: true", content)
            self.assertIn("subtask: true", content)
            expected_agent = (
                "agentspec-openspec-auditor"
                if path.endswith("/audit.md")
                else "agentspec-openspec-orchestrator"
            )
            self.assertIn(f"agent: {expected_agent}", content)

    def test_resource_loading_is_independent_of_working_directory(self):
        original_directory = os.getcwd()

        with tempfile.TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                self.assertEqual(set(load_managed_commands()), EXPECTED_COMMANDS)
            finally:
                os.chdir(original_directory)


class AgentTemplateGateTests(unittest.TestCase):
    def test_orchestrator_references_the_pipeline(self):
        orchestrator = load_managed_agents()["agentspec-openspec-orchestrator.md"]

        self.assertIn("agentspec openspec validate", orchestrator)

    def test_taskwriter_references_the_pipeline(self):
        taskwriter = load_managed_agents()["agentspec-openspec-taskwriter.md"]

        self.assertIn("agentspec openspec validate", taskwriter)

    def test_auditor_references_the_pipeline(self):
        auditor = load_managed_agents()["agentspec-openspec-auditor.md"]

        self.assertIn("agentspec openspec validate", auditor)


if __name__ == "__main__":
    unittest.main()
