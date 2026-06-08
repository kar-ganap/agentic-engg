"""Categorized accumulator for prompt construction with token bookkeeping.

Owns the system prompt, tool specs, and message history that will be sent to
`messages.create()`. Maintains running per-category token totals
(system / tools / history / retrieved) by counting each piece at set/append
time via Anthropic's `count_tokens` endpoint.

Implements the C + API count_tokens approach (Phase 0.0 decision):

- **Static pieces** (system, tools) — counted once at set-time via
  stub-message baseline subtraction: count_tokens needs non-empty messages,
  so we count each section against a known minimal baseline (stub alone)
  and subtract to isolate the marginal contribution.

- **Dynamic pieces** (messages) — counted **cumulatively against the running
  messages list**. Each valid append calls count_tokens on the full list and
  takes the delta from the previous running total. Counting is **deferred**
  for messages that leave the conversation in a state count_tokens rejects
  (an assistant message containing tool_use blocks awaiting tool_result);
  the next valid append catches up the deferred contribution.

The deferral exists because Anthropic's count_tokens validates conversation
structure (not just tokenizes): assistant tool_use must be followed by user
tool_result, or the request 400s. This was caught by the real-API smoke
test, which is why we have one.

Trade-off: for the assistant-tool_use case, the deferred message and its
paired tool_result get pair-level granularity rather than per-message
granularity. **Total history tokens remain exact.** Trends are exact;
absolute totals are within ~1–2% of a full-request count due to small
structural-framing differences between roles.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Sequence
from typing import Any

from stance.tools import Tool

_STUB_MESSAGE: dict[str, Any] = {"role": "user", "content": "."}
_EPHEMERAL: dict[str, str] = {"type": "ephemeral"}


def with_cache_breakpoints(
    *,
    system: str | None,
    tools: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    after_tools: bool = True,
    after_system: bool = True,
    end_history: bool = True,
) -> dict[str, Any]:
    """Return `messages.create` kwargs with ephemeral `cache_control` breakpoints.

    Caching follows the documented hierarchy ``tools → system → messages``; a
    breakpoint marks "cache everything up to and including this block." We place
    up to 3: after the last tool, on the system block, and on the last block of
    the last message (the moving end-of-history breakpoint). Inputs are NOT
    mutated (deep-copied). Flags let a caller omit a breakpoint (e.g. to isolate
    a single layer). See `docs/phases/phase-1.0-exercise-B-plan.md`.
    """
    out: dict[str, Any] = {}

    tools = copy.deepcopy(tools)
    if after_tools and tools:
        tools[-1] = {**tools[-1], "cache_control": dict(_EPHEMERAL)}
    if tools:
        out["tools"] = tools

    if system is not None:
        # cache_control requires system to be a list of content blocks.
        out["system"] = (
            [{"type": "text", "text": system, "cache_control": dict(_EPHEMERAL)}]
            if after_system
            else system
        )

    messages = copy.deepcopy(messages)
    if end_history and messages:
        last = messages[-1]
        content = last["content"]
        if isinstance(content, str):
            last["content"] = [
                {"type": "text", "text": content, "cache_control": dict(_EPHEMERAL)}
            ]
        elif isinstance(content, list) and content:
            content[-1] = {**content[-1], "cache_control": dict(_EPHEMERAL)}
    out["messages"] = messages
    return out


def _has_unmatched_tool_use(message: dict[str, Any]) -> bool:
    """True iff the message is an assistant message containing tool_use blocks.

    Anthropic's count_tokens (and messages.create) validates conversation
    structure: tool_use blocks in an assistant message must be followed by a
    user message with matching tool_result blocks. Passing such a message
    as the trailing entry raises a 400. Used to decide when to defer counting.
    """
    if message.get("role") != "assistant":
        return False
    content = message.get("content")
    if not isinstance(content, list):
        return False
    for block in content:
        # Block may be a dict (constructed by user/tests) or a typed Anthropic
        # response class (TextBlock / ToolUseBlock). Handle both.
        btype = getattr(block, "type", None)
        if btype is None and isinstance(block, dict):
            btype = block.get("type")
        if btype == "tool_use":
            return True
    return False


class CategorizedContext:
    """Owns prompt state and maintains per-category token bookkeeping."""

    def __init__(self, count_fn: Callable[..., int], *, model: str) -> None:
        """Initialize with a token-counting function and target model.

        Args:
            count_fn: Variadic callable matching Anthropic's `count_tokens`
                signature, returning an int (input_tokens). Typical wiring is
                ``lambda **kw: client.messages.count_tokens(**kw).input_tokens``.
                Dependency-injected so tests can pass a cheap deterministic stub.
            model: Model name passed through to `count_fn`. Use the same model
                you'll pass to `messages.create()`.
        """
        self._count_fn = count_fn
        self._model = model
        self._system: str | None = None
        self._tool_specs: list[dict[str, Any]] = []
        self._messages: list[dict[str, Any]] = []
        self._tokens: dict[str, int] = {
            "system": 0,
            "tools": 0,
            "history": 0,
            "retrieved": 0,
        }
        # Baseline: count of just the stub message with no system, no tools.
        # Subtracted from per-section counts to isolate marginal contribution.
        self._stub_count: int = self._count_fn(
            model=self._model, messages=[_STUB_MESSAGE]
        )
        # Running cumulative token count of self._messages, used by append_message
        # to compute per-append deltas. Stays at 0 while no valid messages exist.
        self._cumulative_history_count: int = 0

    def set_system(self, prompt: str | None) -> None:
        """Set (or clear) the system prompt; recount and replace the bucket."""
        self._system = prompt
        if prompt is None:
            self._tokens["system"] = 0
            return
        with_system = self._count_fn(
            model=self._model,
            messages=[_STUB_MESSAGE],
            system=prompt,
        )
        self._tokens["system"] = with_system - self._stub_count

    def set_tools(self, tools: Sequence[Tool]) -> None:
        """Set the tool list; recount and replace the tools bucket."""
        self._tool_specs = [t.api_spec() for t in tools]
        if not self._tool_specs:
            self._tokens["tools"] = 0
            return
        with_tools = self._count_fn(
            model=self._model,
            messages=[_STUB_MESSAGE],
            tools=self._tool_specs,
        )
        self._tokens["tools"] = with_tools - self._stub_count

    def append_message(self, message: dict[str, Any]) -> None:
        """Append a message; bump the history bucket by its marginal cost.

        Uses cumulative counting + delta against the running messages list.
        **Defers** the count when the new message would leave the conversation
        in a state count_tokens rejects (an assistant message with tool_use
        blocks awaiting tool_result). The deferred contribution is rolled in
        on the next append that completes the conversation. See module
        docstring for rationale.
        """
        self._messages.append(message)
        if _has_unmatched_tool_use(message):
            # Deferred: count_tokens would 400 on this incomplete state. The
            # next append (the tool_result) will trigger the count on the
            # cumulative list, naturally accounting for this message too.
            return
        new_total = self._count_fn(model=self._model, messages=self._messages)
        delta = new_total - self._cumulative_history_count
        self._cumulative_history_count = new_total
        self._tokens["history"] += delta

    def snapshot(self) -> dict[str, int]:
        """Return a copy of the current per-category token totals."""
        return dict(self._tokens)

    @property
    def system(self) -> str | None:
        return self._system

    @property
    def tools(self) -> list[dict[str, Any]]:
        """Read-only view; mutation does not bypass the counter (shallow copy)."""
        return list(self._tool_specs)

    @property
    def messages(self) -> list[dict[str, Any]]:
        """Read-only view; mutation does not bypass the counter (shallow copy)."""
        return list(self._messages)
