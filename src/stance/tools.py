"""Tools available to the raw agent loop.

A `Tool` couples three things:
- the Anthropic API spec (what the model sees when deciding to call)
- the Python callable (what the harness runs when the model does call)
- a `name` string that bridges the two

Phase 0.0 ships two trivial tools — `echo` and `add` — just to exercise
parse/dispatch in the loop. Real tools land starting in Module 2 (Phase 1.1).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Tool:
    """A tool the loop can dispatch to.

    `name` is the bridge between the model's tool_use block (which carries a
    name) and the harness's dispatch dict. `input_schema` is JSON Schema —
    the model uses it to format its tool_use input.
    """

    name: str
    description: str
    input_schema: dict[str, Any]
    fn: Callable[..., Any]

    def api_spec(self) -> dict[str, Any]:
        """Return the dict shape expected by `client.messages.create(tools=...)`."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


def _echo(text: str) -> str:
    return text


ECHO = Tool(
    name="echo",
    description=(
        "Returns the provided text verbatim. Use when the user explicitly "
        "asks to repeat, echo, or confirm a literal string without transformation."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to echo back.",
            },
        },
        "required": ["text"],
    },
    fn=_echo,
)


def _add(a: int, b: int) -> int:
    return a + b


ADD = Tool(
    name="add",
    description=(
        "Returns the integer sum of two numbers. Use when asked to add, sum, "
        "or compute a total of two integers."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "a": {"type": "integer", "description": "First addend."},
            "b": {"type": "integer", "description": "Second addend."},
        },
        "required": ["a", "b"],
    },
    fn=_add,
)


# Stable tool set for one agent run (M1 KV-cache discipline + Manus's
# logit-masking-over-tool-mutation guidance). Tuple, not list — the
# immutability is the contract, not just convention.
TOOLS: tuple[Tool, ...] = (ECHO, ADD)
