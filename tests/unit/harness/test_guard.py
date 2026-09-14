import tempfile
import unittest
from pathlib import Path

from agentspec.harness.openspec import guard


def _write_tasks(repo_root, name, body):
    change_dir = repo_root / "openspec" / "changes" / name
    change_dir.mkdir(parents=True, exist_ok=True)
    (change_dir / "tasks.md").write_text(body, encoding="utf-8")
    return change_dir


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.repo_root = Path(self.temp_dir.name)

    def _change(self, verdict, name):
        return next(change for change in verdict["changes"] if change["name"] == name)

    def test_non_strict_active_change_is_flagged(self):
        _write_tasks(self.repo_root, "loose-change", "## 1. Group\n\nNo metadata.\n")

        verdict = guard.run_guard(self.repo_root)

        self.assertEqual(verdict["status"], "FAIL")
        self.assertEqual(verdict["exit_code"], 1)
        matches = [
            issue for issue in verdict["issues"] if issue["code"] == "NON_STRICT_TASKS"
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["severity"], "ERROR")
        self.assertIn("loose-change", matches[0]["message"])
        self.assertIn("/agentspec/openspec/continue", matches[0]["message"])

    def test_archived_non_strict_change_is_excluded(self):
        _write_tasks(
            self.repo_root,
            "archive/old-change",
            "## 1. Group\n\nNo metadata.\n",
        )

        verdict = guard.run_guard(self.repo_root)

        self.assertEqual(verdict["status"], "PASS")
        self.assertEqual(verdict["exit_code"], 0)
        self.assertEqual(verdict["scanned"], 0)
        self.assertFalse(
            any(issue["code"] == "NON_STRICT_TASKS" for issue in verdict["issues"])
        )

    def test_change_without_tasks_is_not_compiled(self):
        (self.repo_root / "openspec" / "changes" / "planning").mkdir(parents=True)

        verdict = guard.run_guard(self.repo_root)

        self.assertEqual(verdict["status"], "PASS")
        self.assertEqual(verdict["exit_code"], 0)
        change = self._change(verdict, "planning")
        self.assertEqual(change["status"], "not_compiled")
        self.assertEqual(change["issues"], [])

    def test_unreadable_tasks_yields_tool_error(self):
        (self.repo_root / "openspec" / "changes" / "broken" / "tasks.md").mkdir(
            parents=True
        )

        verdict = guard.run_guard(self.repo_root)

        self.assertEqual(verdict["status"], "TOOL_ERROR")
        self.assertEqual(verdict["exit_code"], 2)
        codes = [issue["code"] for issue in verdict["issues"]]
        self.assertIn("TOOL_ERROR", codes)

    def test_missing_repo_root_yields_empty_pass(self):
        verdict = guard.run_guard(self.repo_root)

        self.assertEqual(verdict["status"], "PASS")
        self.assertEqual(verdict["exit_code"], 0)
        self.assertEqual(verdict["scanned"], 0)
        self.assertEqual(verdict["issues"], [])


if __name__ == "__main__":
    unittest.main()
