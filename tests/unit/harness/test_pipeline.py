import unittest
from pathlib import Path
from unittest import mock

from agentspec.cli import build_parser
from agentspec.harness.openspec import pipeline


def _gate(name, status):
    return {"name": name, "status": status, "issues": []}


class PipelineTests(unittest.TestCase):
    def test_run_pipeline_returns_status_and_gates_keys(self):
        with (
            mock.patch.object(pipeline, "_run_openspec_validate", return_value=_gate("openspec validate", "PASS")),
            mock.patch.object(pipeline, "_run_lint_gate", return_value=_gate("lint", "PASS")),
            mock.patch.object(pipeline, "_run_evidence_gate", return_value=_gate("evidence", "PASS")),
        ):
            result = pipeline.run_pipeline("change", Path("."))

        self.assertIn("status", result)
        self.assertIn("gates", result)
        self.assertEqual(result["status"], "PASS")

    def test_failing_evidence_gate_fails_pipeline(self):
        with (
            mock.patch.object(pipeline, "_run_openspec_validate", return_value=_gate("openspec validate", "PASS")),
            mock.patch.object(pipeline, "_run_lint_gate", return_value=_gate("lint", "PASS")),
            mock.patch.object(pipeline, "_run_evidence_gate", return_value=_gate("evidence", "FAIL")),
        ):
            result = pipeline.run_pipeline("change", Path("."))

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["exit_code"], 1)

    def test_tool_error_yields_exit_code_2_and_short_circuits(self):
        lint_mock = mock.Mock(return_value=_gate("lint", "PASS"))
        evidence_mock = mock.Mock(return_value=_gate("evidence", "PASS"))

        with (
            mock.patch.object(pipeline, "_run_openspec_validate", return_value=_gate("openspec validate", "TOOL_ERROR")),
            mock.patch.object(pipeline, "_run_lint_gate", lint_mock),
            mock.patch.object(pipeline, "_run_evidence_gate", evidence_mock),
        ):
            result = pipeline.run_pipeline("change", Path("."))

        self.assertEqual(result["status"], "TOOL_ERROR")
        self.assertEqual(result["exit_code"], 2)
        lint_mock.assert_not_called()
        evidence_mock.assert_not_called()

    def test_any_fail_yields_exit_code_1_and_lists_every_failing_gate(self):
        with (
            mock.patch.object(pipeline, "_run_openspec_validate", return_value=_gate("openspec validate", "FAIL")),
            mock.patch.object(pipeline, "_run_lint_gate", return_value=_gate("lint", "FAIL")),
            mock.patch.object(pipeline, "_run_evidence_gate", return_value=_gate("evidence", "PASS")),
        ):
            result = pipeline.run_pipeline("change", Path("."))

        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(len(result["gates"]), 3)
        failing = [gate["name"] for gate in result["gates"] if gate["status"] == "FAIL"]
        self.assertEqual(failing, ["openspec validate", "lint"])

    def test_gate_order_is_fixed(self):
        calls = []

        def record(name, status):
            def runner(change_name, repo_root):
                calls.append(name)
                return _gate(name, status)

            return runner

        with (
            mock.patch.object(pipeline, "_run_openspec_validate", record("openspec validate", "PASS")),
            mock.patch.object(pipeline, "_run_lint_gate", record("lint", "PASS")),
            mock.patch.object(pipeline, "_run_evidence_gate", record("evidence", "PASS")),
        ):
            pipeline.run_pipeline("change", Path("."))

        self.assertEqual(calls, ["openspec validate", "lint", "evidence"])


class PipelineCoverageTests(unittest.TestCase):
    def test_pipeline_is_deterministic(self):
        patchers = [
            mock.patch.object(pipeline, "_run_openspec_validate", return_value=_gate("openspec validate", "PASS")),
            mock.patch.object(pipeline, "_run_lint_gate", return_value=_gate("lint", "FAIL")),
            mock.patch.object(pipeline, "_run_evidence_gate", return_value=_gate("evidence", "PASS")),
        ]

        for patcher in patchers:
            patcher.start()

        try:
            first = pipeline.run_pipeline("change", Path("."))
            second = pipeline.run_pipeline("change", Path("."))
        finally:
            for patcher in patchers:
                patcher.stop()

        self.assertEqual(first, second)


class PipelineCLITests(unittest.TestCase):
    def test_validate_subcommand_exists(self):
        parser = build_parser()

        args = parser.parse_args(
            ["openspec", "validate", "--change", "control-layer", "--json"]
        )

        self.assertEqual(args.openspec_command, "validate")
        self.assertEqual(args.change, "control-layer")
        self.assertTrue(args.json)


if __name__ == "__main__":
    unittest.main()
