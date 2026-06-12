"""The Module 2 agentic tool-use loop (`run_tool_loop`).

Extends the Phase 0.0 cycle for the tool-use experiments. New vs 0.0 (whose
philosophy was fail-LOUD): **fail as DATA** — agent failures (wrong-tool, not_found,
runaway) are recorded, not raised, because they ARE the measurement. So:

- error-as-data dispatch (via `tools.dispatch` — never raises),
- a rich per-turn `CallEvent` (incl. `usage`; `usage.input_tokens` = fill-at-use),
- a toggleable loop-guard (whole-run, K=2, warn-then-break),
- a crash-robust `RunRecord` (written in a `finally`, every exit path).

Provider-agnostic via `complete_fn` (DeepSeek compat or a Claude anchor); tools are
declared + stable (gate-confirmed → clean structured tool_use). The loop logs RAW
only — all metrics are scorer-derived. See docs/phases/phase-1.1-plan.md
§ "Loop & generator design".
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from anthropic.types import Message, ToolUseBlock

from stance.tools import Tool
from stance.tooluse.events import CallEvent, EventLogger, RefStore, RunRecord
from stance.tooluse.tools import ToolResult, dispatch

# Guard corrective is ALWAYS crisp — off the terminal_style axis, part of "guard on".
_GUARD_CORRECTIVE = (
    "LOOP DETECTED: you already called {name} with these exact arguments; the result is "
    "identical. Do not repeat it — use a different tool or give your final answer."
)


@dataclass
class RunOutcome:
    """Minimal return — the trajectory lives in the logged events/run record."""

    run_id: str
    final_answer: str
    terminal_status: str


def _text(content: list[Any]) -> str:
    """Concatenate the text blocks (ignore thinking / tool_use)."""
    return "".join(getattr(b, "text", "") for b in content if getattr(b, "type", None) == "text")


def _usage(u: Any) -> dict[str, int]:
    """Pull the raw counts off response.usage (input_tokens IS fill-at-use)."""
    return {
        "input_tokens": getattr(u, "input_tokens", 0),
        "output_tokens": getattr(u, "output_tokens", 0),
        "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0),
        "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0),
    }


def _signature(name: str, args: dict[str, Any]) -> str:
    """Exact (tool, normalized-args) signature for the loop-guard."""
    return name + "|" + json.dumps(args, sort_keys=True)


def run_tool_loop(
    *,
    task: str,
    system: str,
    tools: Sequence[Tool],
    model: str,
    complete_fn: Callable[..., Message],
    logger: EventLogger,
    refs: RefStore,
    run_id: str,
    cell_id: str | None = None,
    task_id: str | None = None,
    seed: int | None = None,
    terminal_style: str = "crisp",
    loop_guard: bool = True,
    max_turns: int = 20,
    max_tokens: int = 2048,
    raise_on_crash: bool = True,
) -> RunOutcome:
    """Run the agent over `task` with `tools`; log a `CallEvent` per turn and a
    crash-robust `RunRecord`. `loop_guard`/`terminal_style` are experimental knobs.
    `max_turns` should exceed the deepest legitimate chain (the #4 depth axis → ~20)."""
    tool_specs = [t.api_spec() for t in tools]  # declared once, passed unchanged (stable → cache)
    messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
    seen: dict[str, int] = {}  # loop-guard ledger: signature -> count (whole-run)
    final_answer = ""
    final_ref: str | None = None
    note: str | None = None
    terminal_status = "max_turns"  # pessimistic default — overwritten only on an early exit
    started = time.time()

    try:
        for turn in range(max_turns):
            response = complete_fn(
                model=model,
                system=system,
                tools=tool_specs,
                messages=messages,
                max_tokens=max_tokens,
            )
            messages.append({"role": "assistant", "content": response.content})  # full content
            usage = _usage(response.usage)

            # --- final-answer path ------------------------------------------
            if response.stop_reason != "tool_use":
                final_answer = _text(response.content)
                final_ref = refs.store(final_answer)
                terminal_status = "complete"
                logger.log_event(
                    CallEvent(
                        run_id=run_id, turn_index=turn, is_tool_call=False, is_final=True,
                        cell_id=cell_id, task_id=task_id, seed=seed, model=model,
                        stop_reason=response.stop_reason, usage=usage,
                        context_size_at_call=usage["input_tokens"], response_ref=final_ref,
                    )
                )
                break

            # --- tool_use path ----------------------------------------------
            tool_result_blocks: list[dict[str, Any]] = []
            broke = False
            for block in response.content:
                if not isinstance(block, ToolUseBlock):
                    continue
                name = block.name
                args: dict[str, Any] = dict(block.input)
                sig = _signature(name, args)
                seen[sig] = seen.get(sig, 0) + 1
                guard_action: str | None = None

                if loop_guard and seen[sig] >= 3:  # STRIKE 2 → break
                    logger.log_event(
                        CallEvent(
                            run_id=run_id, turn_index=turn, is_tool_call=True, model=model,
                            cell_id=cell_id, task_id=task_id, seed=seed,
                            tool_called=name, arguments=args, usage=usage,
                            context_size_at_call=usage["input_tokens"],
                            stop_reason=response.stop_reason, guard_action="break",
                        )
                    )
                    broke = True
                    break

                if loop_guard and seen[sig] == 2:  # STRIKE 1 → warn (don't re-run the tool)
                    guard_action = "warn"
                    result = ToolResult(
                        content=_GUARD_CORRECTIVE.format(name=name),
                        is_error=True,
                        error_type="loop_repeat",
                    )
                else:  # normal dispatch (itself loud->data)
                    result = dispatch(tools, name, args, terminal_style=terminal_style)

                args_valid = (
                    result.error_type is None or not result.error_type.startswith("schema:")
                )
                logger.log_event(
                    CallEvent(
                        run_id=run_id, turn_index=turn, is_tool_call=True, model=model,
                        cell_id=cell_id, task_id=task_id, seed=seed,
                        tool_called=name, arguments=args, args_valid=args_valid,
                        is_error=result.is_error, error_type=result.error_type,
                        response_format=result.response_format,
                        response_size_tokens=result.size_tokens,
                        extracted_ids=result.extracted_ids,
                        response_ref=refs.store(result.content),
                        usage=usage, context_size_at_call=usage["input_tokens"],
                        stop_reason=response.stop_reason, guard_action=guard_action,
                    )
                )
                tool_result_blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result.content,
                        "is_error": result.is_error,
                    }
                )

            if broke:
                terminal_status = "loop_guard"
                break
            messages.append({"role": "user", "content": tool_result_blocks})
    except Exception as e:  # unhandled throw = API hard-fail or code bug (NOT an agent failure)
        terminal_status = "crash"
        note = repr(e)
        if raise_on_crash:
            raise
    finally:
        logger.log_run(
            RunRecord(
                run_id=run_id, cell_id=cell_id, task_id=task_id, seed=seed, model=model,
                started=started, ended=time.time(), terminal_status=terminal_status,
                final_answer_ref=final_ref, note=note,
            )
        )

    return RunOutcome(run_id=run_id, final_answer=final_answer, terminal_status=terminal_status)
