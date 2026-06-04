"""Raw agent loop — calls the model in a turn-by-turn loop, dispatching tool
uses and accumulating history until the model stops calling tools.

No framework. The two external dependencies are dependency-injected
(`complete_fn` for messages.create, `count_fn` for count_tokens) so the loop
is testable without a real Anthropic client. See PLAN.md § Phase 0.0 for the
design rationale.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from anthropic.types import Message, TextBlock, ToolUseBlock

from stance.context import CategorizedContext
from stance.instrumentation import BudgetLogger
from stance.tools import Tool


def _extract_text(content_blocks: list[Any]) -> str:
    """Concatenate text from any TextBlock entries; ignore other block types."""
    return "".join(b.text for b in content_blocks if isinstance(b, TextBlock))


def run_loop(
    *,
    task: str,
    system: str,
    tools: Sequence[Tool],
    model: str,
    complete_fn: Callable[..., Message],
    count_fn: Callable[..., int],
    logger: BudgetLogger,
    max_turns: int = 10,
    max_tokens: int = 1024,
) -> str:
    """Run the agent loop and return the model's final text response.

    Args:
        task: The initial user message kicking off the run.
        system: The system prompt.
        tools: Tools the model may call this run. Must be a stable set —
            see M1 KV-cache discipline (don't mutate between turns).
        model: Model name (passed to both DI hooks).
        complete_fn: Function that calls the model. Wire as
            ``lambda **kw: client.messages.create(**kw)`` for the real client.
        count_fn: Function that counts tokens. Wire as
            ``lambda **kw: client.messages.count_tokens(**kw).input_tokens``.
        logger: BudgetLogger receiving per-turn category snapshots.
        max_turns: Hard cap on loop iterations.
        max_tokens: Max output tokens per model call (Anthropic API requirement).

    Returns:
        The model's final text response (concatenated TextBlock contents).

    Raises:
        RuntimeError: max_turns hit without the model producing a terminal
            response. Loud failure by design — a chain that runs forever is
            a bug to surface, not absorb.
        KeyError: model emits a tool_use for a name not in `tools`. Same rationale.
        Exception: tool execution exceptions bubble up. Phase 0.0 tools can't
            fail; per-call error handling lands in M2 (Phase 1.1).
    """
    # --- Step 0: one-time setup --------------------------------------------
    ctx = CategorizedContext(count_fn, model=model)
    ctx.set_system(system)
    ctx.set_tools(tools)
    dispatch: dict[str, Tool] = {tool.name: tool for tool in tools}
    ctx.append_message({"role": "user", "content": task})
    logger.new_run()

    # --- Step 1: turn-by-turn loop -----------------------------------------
    for turn in range(max_turns):
        # (1) Snapshot tokens BEFORE the call; log to BudgetLogger.
        logger.record(turn=turn, categories=ctx.snapshot(), model=model)

        # (2) Call the model.
        response = complete_fn(
            model=model,
            system=ctx.system,
            tools=ctx.tools,
            messages=ctx.messages,
            max_tokens=max_tokens,
        )

        # (3) Append the assistant's response to history (even if it's the
        #     final answer — keeps history complete for the return / logs).
        ctx.append_message({"role": "assistant", "content": response.content})

        # (4) Stop condition: anything other than "tool_use" means we're done.
        if response.stop_reason != "tool_use":
            return _extract_text(response.content)

        # (5) Dispatch each tool_use block. Multiple per turn are possible
        #     (Anthropic supports parallel tool calls); we handle them serially.
        tool_result_blocks: list[dict[str, Any]] = []
        for block in response.content:
            if not isinstance(block, ToolUseBlock):
                continue
            tool = dispatch[block.name]
            result = tool.fn(**block.input)
            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                }
            )

        # (6) Append ALL tool results as a single user-role message
        #     (Anthropic convention: one user message containing the list
        #     of tool_result blocks, in the same order as the tool_use blocks).
        ctx.append_message({"role": "user", "content": tool_result_blocks})

    raise RuntimeError(f"Loop hit max_turns={max_turns} without a terminal response")
