"""Mid-loop context compaction (§1.2) — the failure-preservation experiment's mechanism.

A pure `messages -> messages` rewrite invoked by `run_tool_loop` when the running context crosses
a token budget. It rewrites *older* `tool_result` blocks (the last `keep_last_turns` tool-result
turns always stay verbatim — immediate state). Every policy DROPS successful tool-result payloads
(Anthropic tool-result-clearing / §5.2 "spent successes are distractors"); the policies differ
ONLY in how they treat FAILED results — so the failure treatment is the sole variable across arms:

  preserve_failures   failure kept VERBATIM (full actionable error line)
  summarize_but_flag  failure distilled to a one-line SIGNAL — the error CODE only, no detail
  summarize_uniform   failure dropped like any success (the anti-pattern: specifics dissolve)

Failure detection is the `is_error` flag the loop already stamps on each tool_result block
(loop.py) — no coupling to `ToolResult`. First cut: model-refusals / malformed outputs that are
NOT is_error are out of scope (ledgered). See docs/phases/phase-1.2-plan.md § Thread B.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

Policy = Literal["preserve_failures", "summarize_but_flag", "summarize_uniform"]

SUCCESS_STUB = "[tool result omitted to reclaim context]"
_SIGNAL_RE = re.compile(r"^\s*([A-Z][A-Z_]{2,}):")  # the crisp error CODE prefix (NOT_FOUND: …)


def _error_signal(content: str) -> str:
    """Distil a failed result to a one-line signal: the error CODE, dropping the actionable
    detail (the specific id, the 'do not retry' guidance). Falls back to a generic marker."""
    m = _SIGNAL_RE.match(content) if isinstance(content, str) else None
    code = m.group(1) if m else "ERROR"
    return f"[earlier tool call failed: {code}]"


@dataclass(frozen=True)
class Compaction:
    """Config for the `run_tool_loop` hook (off by default). Fires when the running context
    (fill-at-use `input_tokens`) reaches `budget_tokens`; the last `keep_last_turns` tool-result
    turns are never compacted."""

    policy: Policy
    budget_tokens: int
    keep_last_turns: int = 2


def _is_tool_result_msg(m: dict[str, Any]) -> bool:
    content = m.get("content")
    return (
        m.get("role") == "user"
        and isinstance(content, list)
        and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
    )


def _rewrite_block(block: dict[str, Any], policy: Policy) -> dict[str, Any]:
    if not (isinstance(block, dict) and block.get("type") == "tool_result"):
        return block
    is_error = bool(block.get("is_error", False))
    content = block.get("content", "")
    if policy == "summarize_uniform":
        new = SUCCESS_STUB
    elif policy == "preserve_failures":
        new = content if is_error else SUCCESS_STUB
    elif policy == "summarize_but_flag":
        new = _error_signal(content) if is_error else SUCCESS_STUB
    else:  # pragma: no cover - exhaustive over Policy
        raise ValueError(f"unknown compaction policy: {policy!r}")
    return {**block, "content": new}


def compact(
    messages: list[dict[str, Any]], policy: Policy, *, keep_last_turns: int = 2
) -> list[dict[str, Any]]:
    """Rewrite older tool_result blocks per `policy`; keep the last `keep_last_turns` tool-result
    turns (and all non-tool-result messages) verbatim. Pure — returns a new list; input intact."""
    tr_indices = [i for i, m in enumerate(messages) if _is_tool_result_msg(m)]
    protected = set(tr_indices[-keep_last_turns:]) if keep_last_turns > 0 else set()
    out: list[dict[str, Any]] = []
    for i, m in enumerate(messages):
        if _is_tool_result_msg(m) and i not in protected:
            out.append({**m, "content": [_rewrite_block(b, policy) for b in m["content"]]})
        else:
            out.append(m)
    return out
