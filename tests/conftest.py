"""Shared test helpers for the stance test suite.

Pytest auto-discovers this file. Helpers defined here are importable from
any test file as ``from tests.conftest import <name>``.

NOTE: we deliberately do NOT call load_dotenv() here. Secrets are read from
.env directly via stance.secrets (never the shell) — the real-API smoke tests
build their client with stance.secrets.anthropic_api_key(). See lessons §0.10.
"""

from __future__ import annotations

from typing import Any


class FakeCounter:
    """Deterministic mock count_fn for CategorizedContext / loop tests.

    Returns total length of string content (messages + system + serialized
    tools). Records every call's kwargs in ``.calls`` for wiring verification.
    Numbers are arbitrary but monotonic in content size — enough to verify
    replace-vs-accumulate and snapshot semantics without hard-coding tokenizer
    output.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> int:
        self.calls.append(
            {"model": model, "messages": messages, "system": system, "tools": tools}
        )
        n = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                n += len(content)
            elif isinstance(content, list):
                # Any content block: dict (text / tool_use / tool_result) or
                # typed Anthropic class (TextBlock / ToolUseBlock). str() gives
                # a representative size; what matters here is monotonicity for
                # replace-vs-accumulate semantics, not real tokenizer output.
                for block in content:
                    n += len(str(block))
        if system:
            n += len(system)
        if tools:
            for tool in tools:
                n += len(str(tool))
        return n
