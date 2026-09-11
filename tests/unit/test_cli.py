import unittest

from agentspec.cli import build_parser


class SetupCLITests(unittest.TestCase):
    def test_setup_defaults_to_opencode(self):
        args = build_parser().parse_args(["setup"])

        self.assertEqual(args.target, "opencode")

    def test_setup_accepts_codex_target(self):
        args = build_parser().parse_args(["setup", "--target", "codex"])

        self.assertEqual(args.target, "codex")


if __name__ == "__main__":
    unittest.main()
