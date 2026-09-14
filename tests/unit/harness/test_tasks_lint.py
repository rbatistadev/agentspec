import unittest

from agentspec.harness.openspec import tasks_lint
from agentspec.harness.openspec.tasks_lint import TaskPacket


def _packet(area):
    line = f"- [ ] 1.1 [{area}] Do a thing; verify with `python -m unittest -v`"
    return TaskPacket(
        task_id="1.1",
        title="A task",
        group_id="1",
        start_line=1,
        end_line=2,
        lines=[line],
        sections={},
    )


class CanonicalAreaTests(unittest.TestCase):
    def test_non_canonical_area_warns_once(self):
        issues = []

        tasks_lint.validate_checkbox(_packet("weird-area"), issues)

        matches = [issue for issue in issues if issue.code == "NON_CANONICAL_AREA"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].severity, "WARNING")

    def test_canonical_area_produces_no_warning(self):
        for area in sorted(tasks_lint.CANONICAL_AREAS):
            with self.subTest(area=area):
                issues = []

                tasks_lint.validate_checkbox(_packet(area), issues)

                self.assertFalse(
                    any(issue.code == "NON_CANONICAL_AREA" for issue in issues)
                )

    def test_contract_version_is_preserved_and_area_warning_is_not_error(self):
        issues = []

        tasks_lint.validate_checkbox(_packet("weird-area"), issues)

        self.assertEqual(tasks_lint.TASK_CONTRACT_VERSION, "strict-v1")
        self.assertFalse(any(issue.severity == "ERROR" for issue in issues))


if __name__ == "__main__":
    unittest.main()
