import tempfile
import unittest
from pathlib import Path

from agentspec.harness.openspec import evidence
from agentspec.harness.openspec.tasks_lint import TaskPacket


def _packet(sections):
    return TaskPacket(
        task_id="1.1",
        title="Test task",
        group_id="1",
        start_line=1,
        end_line=2,
        lines=[],
        sections=sections,
    )


class EvidenceModuleTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.repo_root = Path(self.temp_dir.name)
        self.change_root = self.repo_root / "openspec" / "changes" / "test-change"

    def _write_spec(self, scenario):
        spec_dir = self.change_root / "specs" / "test"
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / "spec.md").write_text(
            f"## ADDED Requirements\n\n#### Scenario: {scenario}\n",
            encoding="utf-8",
        )

    def _write_design(self, heading):
        self.change_root.mkdir(parents=True, exist_ok=True)
        (self.change_root / "design.md").write_text(
            f"# Design\n\n### {heading}\n",
            encoding="utf-8",
        )

    def test_collect_evidence_issues_returns_list(self):
        self._write_spec("Some scenario")
        self._write_design("D1")

        result = evidence.collect_evidence_issues(
            [_packet({})], self.change_root, self.repo_root
        )

        self.assertIsInstance(result, list)

    def test_parse_tasks_file_parses_packets(self):
        tasks_path = self.repo_root / "tasks.md"
        tasks_path.write_text(
            "<!-- task-contract: strict-v1 -->\n\n"
            "## 1. Group\n\n"
            "### Task 1.1 - Do a thing\n\n"
            "**Purpose**\n\n"
            "Do it.\n",
            encoding="utf-8",
        )

        packets = evidence.parse_tasks_file(tasks_path)

        self.assertTrue(packets)
        self.assertEqual(packets[0].task_id, "1.1")


class EvidenceCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.repo_root = Path(self.temp_dir.name)
        self.change_root = self.repo_root / "openspec" / "changes" / "test-change"

    def _write_spec(self, scenario):
        spec_dir = self.change_root / "specs" / "test"
        spec_dir.mkdir(parents=True, exist_ok=True)
        (spec_dir / "spec.md").write_text(
            f"## ADDED Requirements\n\n#### Scenario: {scenario}\n",
            encoding="utf-8",
        )

    def _write_design(self, heading):
        self.change_root.mkdir(parents=True, exist_ok=True)
        (self.change_root / "design.md").write_text(
            f"# Design\n\n### {heading}\n",
            encoding="utf-8",
        )

    def _run(self, sections, patch_which=None):
        packets = [_packet(sections)]

        if patch_which is None:
            return evidence.collect_evidence_issues(
                packets, self.change_root, self.repo_root
            )

        with unittest.mock.patch.object(
            evidence.shutil, "which", return_value=patch_which
        ):
            return evidence.collect_evidence_issues(
                packets, self.change_root, self.repo_root
            )

    def test_matching_spec_scenario_produces_no_issue(self):
        self._write_spec("A file reference is checked against the repository")

        issues = self._run(
            {
                "spec contract": [
                    "- `specs/test/spec.md` → `Requirement: R` → "
                    "`Scenario: A file reference is checked against the repository`",
                ],
            }
        )

        self.assertFalse(
            any(issue.code == "EVIDENCE_UNRESOLVED_SPEC" for issue in issues)
        )

    def test_fabricated_spec_scenario_produces_fail(self):
        self._write_spec("Real scenario")

        issues = self._run(
            {
                "spec contract": [
                    "- `specs/test/spec.md` → `Requirement: R` → "
                    "`Scenario: Fabricated scenario`",
                ],
            }
        )

        matches = [issue for issue in issues if issue.code == "EVIDENCE_UNRESOLVED_SPEC"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].severity, "ERROR")

    def test_matching_design_heading_produces_no_issue(self):
        self._write_design("D1 Real decision")

        issues = self._run(
            {
                "design contract": [
                    "- `design.md` → `D1 Real decision` — note",
                ],
            }
        )

        self.assertFalse(
            any(issue.code == "EVIDENCE_UNRESOLVED_DESIGN" for issue in issues)
        )

    def test_fabricated_design_heading_produces_fail(self):
        self._write_design("D1 Real decision")

        issues = self._run(
            {
                "design contract": [
                    "- `design.md` → `D9 Fabricated decision` — note",
                ],
            }
        )

        matches = [issue for issue in issues if issue.code == "EVIDENCE_UNRESOLVED_DESIGN"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].severity, "ERROR")

    def test_design_heading_with_backticks_resolves(self):
        self._write_design("D3 — One pipeline entry point: `agentspec openspec validate`")

        issues = self._run(
            {
                "design contract": [
                    "- `design.md` → `D3 — One pipeline entry point: agentspec openspec validate` — note",
                ],
            }
        )

        self.assertFalse(
            any(issue.code == "EVIDENCE_UNRESOLVED_DESIGN" for issue in issues)
        )

    def test_existing_file_produces_no_issue(self):
        (self.repo_root / "src").mkdir(parents=True)
        (self.repo_root / "src" / "foo.py").write_text("", encoding="utf-8")

        issues = self._run(
            {
                "scope": [
                    "- Allowed production files:",
                    "  - `src/foo.py`",
                ],
            }
        )

        self.assertFalse(
            any(issue.code == "EVIDENCE_MISSING_FILE" for issue in issues)
        )

    def test_nonexistent_file_produces_fail(self):
        issues = self._run(
            {
                "scope": [
                    "- Allowed production files:",
                    "  - `src/does_not_exist.py`",
                ],
            }
        )

        matches = [issue for issue in issues if issue.code == "EVIDENCE_MISSING_FILE"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].severity, "ERROR")

    def test_create_entry_with_existing_parent_produces_no_issue(self):
        (self.repo_root / "tests").mkdir(parents=True)

        issues = self._run(
            {
                "scope": [
                    "- Allowed test files:",
                    "  - `tests/test_foo.py` — CREATE",
                ],
            }
        )

        self.assertFalse(
            any(
                issue.code in ("EVIDENCE_MISSING_FILE", "EVIDENCE_MISSING_PARENT")
                for issue in issues
            )
        )

    def test_create_entry_with_missing_parent_produces_fail(self):
        issues = self._run(
            {
                "scope": [
                    "- Allowed test files:",
                    "  - `missing_dir/test_foo.py` — CREATE",
                ],
            }
        )

        matches = [issue for issue in issues if issue.code == "EVIDENCE_MISSING_PARENT"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].severity, "ERROR")

    def test_resolvable_command_produces_no_issue(self):
        issues = self._run(
            {"primary verification": ["`python -m unittest -v`"]},
            patch_which="/usr/bin/python",
        )

        self.assertFalse(
            any(issue.code == "EVIDENCE_COMMAND_UNRESOLVED" for issue in issues)
        )

    def test_unresolvable_command_produces_warning(self):
        issues = self._run(
            {"primary verification": ["`definitely-not-a-real-command-xyz --flag`"]},
            patch_which=None,
        )

        matches = [issue for issue in issues if issue.code == "EVIDENCE_COMMAND_UNRESOLVED"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].severity, "WARNING")

    def test_fabricated_reference_produces_fail(self):
        self._write_spec("Real scenario")
        self._write_design("D1 Real")

        issues = self._run(
            {
                "spec contract": [
                    "- `specs/test/spec.md` → `Requirement: R` → `Scenario: Fabricated`",
                ],
                "design contract": [
                    "- `design.md` → `D9 Fabricated` — note",
                ],
                "scope": [
                    "- Allowed production files:",
                    "  - `src/fabricated.py`",
                ],
            }
        )

        self.assertTrue(any(issue.severity == "ERROR" for issue in issues))


if __name__ == "__main__":
    unittest.main()
