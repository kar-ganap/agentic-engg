"""Tests for mid-loop compaction (`stance.tooluse.compaction`) + its `run_tool_loop` hook.

The §1.2 mechanism under test: three policies differ ONLY in how they treat *failed* tool
results when context crosses a budget (all drop success payloads; the last N turns stay verbatim):
  preserve_failures  -> failure kept VERBATIM (full actionable error)
  summarize_but_flag -> failure distilled to a one-line SIGNAL (error code only)
  summarize_uniform  -> failure dropped like any success (specifics dissolve; the anti-pattern)
Pure message->message function (operates on the tool_result blocks' `is_error` — no coupling to
ToolResult). The loop hook is OFF by default (existing behavior + the 229 tests unchanged).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from anthropic.types import TextBlock, ToolUseBlock

from stance.tooluse.compaction import Compaction, compact
from stance.tooluse.events import EventLogger, RefStore
from stance.tooluse.loop import run_tool_loop
from stance.tooluse.tools import make_tools

_NF = "NOT_FOUND: order O-9 not found; verify the id from a prior result, do not retry it."
_STUB = "[tool result omitted to reclaim context]"


def _tr(tid: str, content: str, is_error: bool = False) -> dict[str, Any]:
    return {"type": "tool_result", "tool_use_id": tid, "content": content, "is_error": is_error}


def _tr_msg(*blocks: dict[str, Any]) -> dict[str, Any]:
    return {"role": "user", "content": list(blocks)}


def _asst(text: str) -> dict[str, Any]:
    return {"role": "assistant", "content": [{"type": "text", "text": text}]}


# --- pure-function: the three policies differ only on FAILURE treatment ---------------------

def test_preserve_failures_keeps_error_verbatim_drops_success() -> None:
    msgs = [
        {"role": "user", "content": "task"},
        _asst("calling"), _tr_msg(_tr("a", _NF, is_error=True)),
        _asst("calling"), _tr_msg(_tr("b", "Users: U-1 Jane", is_error=False)),
        _asst("calling"), _tr_msg(_tr("c", "later", is_error=False)),  # protected (last turn)
    ]
    out = compact(msgs, "preserve_failures", keep_last_turns=1)
    assert out[2]["content"][0]["content"] == _NF          # failure kept verbatim
    assert out[4]["content"][0]["content"] == _STUB        # success payload dropped
    assert out[6]["content"][0]["content"] == "later"      # last turn untouched


def test_summarize_uniform_drops_failures_too() -> None:
    msgs = [_asst("x"), _tr_msg(_tr("a", _NF, is_error=True)),
            _asst("x"), _tr_msg(_tr("b", "Users: U-1", is_error=False)),
            _asst("x"), _tr_msg(_tr("c", "last", is_error=False))]
    out = compact(msgs, "summarize_uniform", keep_last_turns=1)
    assert out[1]["content"][0]["content"] == _STUB        # failure dissolves like a success
    assert out[3]["content"][0]["content"] == _STUB
    assert out[5]["content"][0]["content"] == "last"       # protected


def test_summarize_but_flag_signals_failure_without_detail() -> None:
    msgs = [_asst("x"), _tr_msg(_tr("a", _NF, is_error=True)),
            _asst("x"), _tr_msg(_tr("b", "ok", is_error=False)),
            _asst("x"), _tr_msg(_tr("c", "last", is_error=False))]
    out = compact(msgs, "summarize_but_flag", keep_last_turns=1)
    flagged = out[1]["content"][0]["content"]
    assert "NOT_FOUND" in flagged                          # the error CODE survives
    assert "do not retry" not in flagged and "O-9" not in flagged  # the actionable detail does NOT
    assert flagged != _NF and flagged != _STUB             # strictly between verbatim and dropped
    assert out[3]["content"][0]["content"] == _STUB


def test_last_turns_kept_verbatim_and_ids_preserved() -> None:
    msgs = [_asst("x"), _tr_msg(_tr("a", _NF, is_error=True)),
            _asst("x"), _tr_msg(_tr("b", _NF, is_error=True))]
    out = compact(msgs, "summarize_uniform", keep_last_turns=2)
    assert out[1]["content"][0]["content"] == _NF          # both within keep window → verbatim
    assert out[3]["content"][0]["content"] == _NF
    assert out[1]["content"][0]["tool_use_id"] == "a"      # tool_use_id never touched


def test_non_tool_result_messages_untouched() -> None:
    msgs = [{"role": "user", "content": "the task"}, _asst("thinking"),
            _tr_msg(_tr("a", "ok", is_error=False)), _asst("done")]
    out = compact(msgs, "summarize_uniform", keep_last_turns=0)
    assert out[0] == {"role": "user", "content": "the task"}  # initial task string untouched
    assert out[1] == _asst("thinking")
    assert out[3] == _asst("done")


# --- loop hook: OFF by default; fires on budget crossing -----------------------------------

def _usage(n: int) -> SimpleNamespace:
    return SimpleNamespace(input_tokens=n, output_tokens=5,
                           cache_read_input_tokens=0, cache_creation_input_tokens=0)


def _harness(tmp_path: Path) -> tuple[EventLogger, RefStore]:
    logger = EventLogger(events_path=tmp_path / "events.jsonl", runs_path=tmp_path / "runs.jsonl")
    return logger, RefStore(tmp_path / "refs")


def _bad_lookup_run(tmp_path: Path, compaction: Compaction | None, usages: list[int]) -> Any:
    """4 distinct failing get_order calls (bad ids → not_found, is_error) then an answer;
    `usages` sets context_size per turn so a budget can be crossed. Records messages seen."""
    logger, refs = _harness(tmp_path)
    seen: list[list[dict[str, Any]]] = []
    it = iter(usages)

    def fn(**kw: Any) -> SimpleNamespace:
        seen.append([dict(m) for m in kw["messages"]])  # snapshot what the model receives
        i = len(seen)
        u = _usage(next(it, usages[-1]))
        if i <= 4:
            blk: Any = ToolUseBlock(type="tool_use", id=f"t{i}", name="get_order",
                                    input={"order_id": f"O-BAD-{i}"})
            return SimpleNamespace(content=[blk], stop_reason="tool_use", usage=u)
        return SimpleNamespace(content=[TextBlock(type="text", text="done", citations=None)],
                               stop_reason="end_turn", usage=u)

    out = run_tool_loop(
        task="look things up", system="s", tools=_tools(), model="m",
        complete_fn=fn, logger=logger, refs=refs, run_id="rc", loop_guard=False, max_turns=8,
        compaction=compaction,
    )
    return out, seen


def _tools() -> Any:
    from stance.tooluse.domain import World
    return make_tools(World(), "A")  # empty world → every get_order is not_found (is_error)


def _stub_seen(seen: list[list[dict[str, Any]]]) -> bool:
    """Did any tool_result block the model received get dissolved to the stub?"""
    for msgs in seen:
        for m in msgs:
            content = m.get("content")
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("content") == _STUB:
                        return True
    return False


def test_compaction_off_by_default_never_fires(tmp_path: Path) -> None:
    out, seen = _bad_lookup_run(tmp_path, None, [100, 100, 9000, 9000, 9000])
    assert out.n_compactions == 0
    assert not _stub_seen(seen)  # every tool_result the model saw stayed verbatim


def test_compaction_fires_when_budget_crossed(tmp_path: Path) -> None:
    comp = Compaction(policy="summarize_uniform", budget_tokens=1000, keep_last_turns=1)
    out, seen = _bad_lookup_run(tmp_path, comp, [100, 100, 9000, 9000, 9000])
    assert out.n_compactions >= 1     # crossed at the 3rd call (9000 ≥ 1000)
    assert _stub_seen(seen)           # older failures dissolved to stubs


def test_compaction_does_not_fire_below_budget(tmp_path: Path) -> None:
    comp = Compaction(policy="summarize_uniform", budget_tokens=50000, keep_last_turns=1)
    out, seen = _bad_lookup_run(tmp_path, comp, [100, 100, 9000, 9000, 9000])
    assert out.n_compactions == 0
    assert not _stub_seen(seen)


def test_compaction_trigger_counts_cached_context(tmp_path: Path) -> None:
    """Regression: under prompt-caching input_tokens is only the uncached DELTA. The trigger must
    use the full fill (input + cache_read + cache_creation), else it never fires on a cached run."""
    logger, refs = _harness(tmp_path)
    n = {"i": 0}

    def fn(**kw: Any) -> SimpleNamespace:
        n["i"] += 1
        # tiny uncached delta, big cached prefix → full fill (5050) crosses budget, input (50) never
        u = SimpleNamespace(input_tokens=50, output_tokens=5,
                            cache_read_input_tokens=5000, cache_creation_input_tokens=0)
        if n["i"] <= 3:
            blk: Any = ToolUseBlock(type="tool_use", id=f"t{n['i']}", name="get_order",
                                    input={"order_id": f"O-BAD-{n['i']}"})
            return SimpleNamespace(content=[blk], stop_reason="tool_use", usage=u)
        return SimpleNamespace(content=[TextBlock(type="text", text="done", citations=None)],
                               stop_reason="end_turn", usage=u)

    comp = Compaction(policy="summarize_uniform", budget_tokens=1000, keep_last_turns=1)
    out = run_tool_loop(
        task="x", system="s", tools=_tools(), model="m", complete_fn=fn, logger=logger, refs=refs,
        run_id="rcache", loop_guard=False, max_turns=8, compaction=comp,
    )
    assert out.n_compactions >= 1  # input_tokens=50 never crosses 1000, but 50+5000 does


def _kinds(content: Any) -> list[str | None]:
    out = []
    for b in content:
        out.append(b.get("type") if isinstance(b, dict) else getattr(b, "type", None))
    return out


def _reasoning_run(tmp_path: Path, strip_reasoning: bool) -> list[list[dict[str, Any]]]:
    """One tool-use turn that emits BOTH reasoning text and a tool_use, then finishes; captures the
    message history the model sees on the next call."""
    logger, refs = _harness(tmp_path)
    seen: list[list[dict[str, Any]]] = []
    n = {"i": 0}

    def fn(**kw: Any) -> SimpleNamespace:
        seen.append([dict(m) for m in kw["messages"]])
        n["i"] += 1
        if n["i"] == 1:
            blocks: list[Any] = [
                TextBlock(type="text", text="Let me look up O-1042.", citations=None),
                ToolUseBlock(type="tool_use", id="t1", name="get_order",
                             input={"order_id": "O-1042"}),
            ]
            return SimpleNamespace(content=blocks, stop_reason="tool_use", usage=_usage(100))
        return SimpleNamespace(content=[TextBlock(type="text", text="done", citations=None)],
                               stop_reason="end_turn", usage=_usage(100))

    run_tool_loop(task="x", system="s", tools=_tools(), model="m", complete_fn=fn, logger=logger,
                  refs=refs, run_id="rr", loop_guard=False, max_turns=4,
                  strip_reasoning=strip_reasoning)
    return seen


def test_strip_reasoning_drops_tool_turn_text(tmp_path: Path) -> None:
    seen = _reasoning_run(tmp_path, strip_reasoning=True)
    asst = next(m for m in seen[1] if m["role"] == "assistant")  # turn-1 assistant, next-turn view
    assert "text" not in _kinds(asst["content"]) and "tool_use" in _kinds(asst["content"])


def test_default_persists_reasoning_text(tmp_path: Path) -> None:
    seen = _reasoning_run(tmp_path, strip_reasoning=False)
    asst = next(m for m in seen[1] if m["role"] == "assistant")
    assert "text" in _kinds(asst["content"])  # the self-preservation channel, on by default
