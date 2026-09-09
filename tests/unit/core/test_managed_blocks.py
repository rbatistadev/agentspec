import unittest

from agentspec.core.managed_blocks import (
    ManagedBlockError,
    render_managed_block,
    upsert_managed_block,
)


class ManagedBlocksTests(unittest.TestCase):
    def test_render_block(self):
        result = render_managed_block(
            "openspec",
            "Use OpenSpec.",
        )

        self.assertEqual(
            result,
            "\n".join(
                [
                    "<!-- agentspec:openspec:start -->",
                    "Use OpenSpec.",
                    "<!-- agentspec:openspec:end -->",
                ]
            ),
        )

    def test_append_block_without_overwriting_existing_content(self):
        existing = """# User instructions

Keep this content.
"""

        result = upsert_managed_block(
            existing,
            "openspec",
            "Use OpenSpec.",
        )

        self.assertIn("# User instructions", result)
        self.assertIn("Keep this content.", result)
        self.assertIn("Use OpenSpec.", result)

    def test_replace_existing_block_only(self):
        existing = """# User instructions

Keep this.

<!-- agentspec:openspec:start -->
Old AgentSpec content.
<!-- agentspec:openspec:end -->

# CodeGraph

Keep this too.
"""

        result = upsert_managed_block(
            existing,
            "openspec",
            "New AgentSpec content.",
        )

        self.assertIn("Keep this.", result)
        self.assertIn("Keep this too.", result)
        self.assertNotIn("Old AgentSpec content.", result)
        self.assertIn("New AgentSpec content.", result)

    def test_upsert_is_idempotent(self):
        first = upsert_managed_block(
            "",
            "openspec",
            "Use OpenSpec.",
        )

        second = upsert_managed_block(
            first,
            "openspec",
            "Use OpenSpec.",
        )

        self.assertEqual(first, second)

    def test_rejects_unmatched_start_marker(self):
        content = """<!-- agentspec:openspec:start -->
broken
"""

        with self.assertRaises(ManagedBlockError):
            upsert_managed_block(
                content,
                "openspec",
                "Replacement",
            )

    def test_rejects_duplicate_blocks(self):
        content = """<!-- agentspec:openspec:start -->
one
<!-- agentspec:openspec:end -->

<!-- agentspec:openspec:start -->
two
<!-- agentspec:openspec:end -->
"""

        with self.assertRaises(ManagedBlockError):
            upsert_managed_block(
                content,
                "openspec",
                "Replacement",
            )


if __name__ == "__main__":
    unittest.main()