from __future__ import annotations

import re


class ManagedBlockError(ValueError):
    """Raised when managed block markers are malformed."""


def _markers(block_id: str) -> tuple[str, str]:
    if not block_id or any(char.isspace() for char in block_id):
        raise ValueError("block_id must be non-empty and contain no whitespace")

    return (
        f"<!-- agentspec:{block_id}:start -->",
        f"<!-- agentspec:{block_id}:end -->",
    )


def render_managed_block(block_id: str, body: str) -> str:
    start, end = _markers(block_id)

    normalized_body = body.strip()

    if normalized_body:
        return f"{start}\n{normalized_body}\n{end}"

    return f"{start}\n{end}"


def upsert_managed_block(
    content: str,
    block_id: str,
    body: str,
) -> str:
    """
    Insert or replace one AgentSpec-managed block.

    Content outside the managed block is preserved.
    """
    start, end = _markers(block_id)
    replacement = render_managed_block(block_id, body)

    start_count = content.count(start)
    end_count = content.count(end)

    if start_count != end_count:
        raise ManagedBlockError(
            f"Malformed managed block '{block_id}': "
            f"{start_count} start marker(s), {end_count} end marker(s)"
        )

    if start_count > 1:
        raise ManagedBlockError(
            f"Multiple managed blocks found for '{block_id}'"
        )

    if start_count == 1:
        pattern = re.compile(
            rf"{re.escape(start)}.*?{re.escape(end)}",
            flags=re.DOTALL,
        )

        return pattern.sub(lambda _: replacement, content, count=1)

    if not content:
        return replacement + "\n"

    separator = "\n" if content.endswith("\n") else "\n\n"

    return content + separator + replacement + "\n"